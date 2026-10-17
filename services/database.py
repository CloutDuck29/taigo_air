
import sqlite3
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
