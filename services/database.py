
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "taigoair.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL,
                co2 REAL,
                pm1 REAL,
                pm25 REAL,
                pm10 REAL,
                temperature_inside REAL,
                temperature_outside REAL,
                humidity_inside REAL,
                humidity_outside REAL,
                pressure_inside REAL,
                pressure_outside REAL,
                window_open INTEGER,
                fan_on INTEGER
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS homes (
                id INTEGER PRIMARY KEY,
                address TEXT NOT NULL DEFAULT '',
                latitude REAL,
                longitude REAL,
                floor INTEGER,
                window_direction TEXT NOT NULL DEFAULT 'N',
                room_area REAL,
                ceiling_height REAL
            )
        """)


        connection.execute("""
            CREATE TABLE IF NOT EXISTS forecast_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                address TEXT,
                input_mode TEXT,
                indoor_co2 REAL,
                indoor_pm25 REAL,
                indoor_temperature REAL,
                outdoor_pm25 REAL,
                outdoor_temperature REAL,
                outdoor_co2 REAL,
                room_volume REAL,
                air_changes_per_hour REAL,
                recommendation TEXT,
                recommended_minutes INTEGER,
                reason TEXT,
                results_json TEXT NOT NULL
            )
        """)


        connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                co2_target REAL NOT NULL,
                co2_preferred REAL NOT NULL,
                pm25_limit REAL NOT NULL,
                max_temperature_drop REAL NOT NULL,
                outdoor_co2 REAL NOT NULL,
                air_changes_per_hour REAL NOT NULL
            )
        """)





def save_measurement(data):
    fields = [
        "mode", "co2", "pm1", "pm25", "pm10",
        "temperature_inside", "temperature_outside",
        "humidity_inside", "humidity_outside",
        "pressure_inside", "pressure_outside",
        "window_open", "fan_on"
    ]

    values = [data.get(field) for field in fields]

    with get_connection() as connection:
        connection.execute(
            f"""
            INSERT INTO measurements (
                timestamp, {", ".join(fields)}
            )
            VALUES ({", ".join(["?"] * (len(fields) + 1))})
            """,
            [datetime.now().isoformat(timespec="seconds"), *values]
        )


def get_measurements(limit=100):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM measurements
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return [dict(row) for row in rows]


def get_home():
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM homes WHERE id = 1"
        ).fetchone()

    return dict(row) if row else None


def save_home(data):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO homes (
                id, address, latitude, longitude,
                floor, window_direction,
                room_area, ceiling_height
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                address = excluded.address,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                floor = excluded.floor,
                window_direction = excluded.window_direction,
                room_area = excluded.room_area,
                ceiling_height = excluded.ceiling_height
        """, (
            data["address"],
            data["latitude"],
            data["longitude"],
            data["floor"],
            data["window_direction"],
            data["room_area"],
            data["ceiling_height"]
        ))


def save_forecast_run(home, sensors, air, weather, forecast):
    recommendation = forecast.get("recommendation", {})

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO forecast_runs (
                created_at,
                address,
                input_mode,
                indoor_co2,
                indoor_pm25,
                indoor_temperature,
                outdoor_pm25,
                outdoor_temperature,
                outdoor_co2,
                room_volume,
                air_changes_per_hour,
                recommendation,
                recommended_minutes,
                reason,
                results_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            home.get("address"),
            sensors.get("mode"),
            sensors.get("co2"),
            sensors.get("pm25"),
            sensors.get("temperature_inside"),
            air.get("pm25"),
            weather.get("temperature"),
            forecast.get("outdoor_co2_assumed"),
            forecast.get("volume_m3"),
            forecast.get("air_changes_per_hour"),
            recommendation.get("decision"),
            recommendation.get("recommended_minutes"),
            recommendation.get("reason"),
            json.dumps(
                forecast.get("results", []),
                ensure_ascii=False
            )
        ))

        return cursor.lastrowid


def get_forecast_runs(limit=100):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM forecast_runs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


DEFAULT_SETTINGS = {
    "co2_target": 1000.0,
    "co2_preferred": 800.0,
    "pm25_limit": 35.0,
    "max_temperature_drop": 3.0,
    "outdoor_co2": 420.0,
    "air_changes_per_hour": 3.0
}


def get_settings():
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM settings WHERE id = 1"
        ).fetchone()

    if row is None:
        return DEFAULT_SETTINGS.copy()

    return {
        key: row[key]
        for key in DEFAULT_SETTINGS
    }


def save_settings(settings):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO settings (
                id, co2_target, co2_preferred,
                pm25_limit, max_temperature_drop,
                outdoor_co2, air_changes_per_hour
            )
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                co2_target = excluded.co2_target,
                co2_preferred = excluded.co2_preferred,
                pm25_limit = excluded.pm25_limit,
                max_temperature_drop = excluded.max_temperature_drop,
                outdoor_co2 = excluded.outdoor_co2,
                air_changes_per_hour =
                    excluded.air_changes_per_hour
        """, tuple(
            settings[key] for key in DEFAULT_SETTINGS
        ))
