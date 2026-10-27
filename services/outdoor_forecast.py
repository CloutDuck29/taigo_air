
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

OMSK_TIMEZONE = ZoneInfo("Asia/Omsk")
FORECAST_HOURS = (3, 6, 12)


def get_outdoor_forecast(latitude, longitude):
    common = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "Asia/Omsk",
        "forecast_hours": 16
    }

    weather_params = {
        **common,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "ms"
    }

    air_params = {
        **common,
        "hourly": "pm2_5,european_aqi"
    }

    try:
        weather_response = requests.get(
            WEATHER_URL,
            params=weather_params,
            timeout=12
        )
        weather_response.raise_for_status()

        air_response = requests.get(
            AIR_URL,
            params=air_params,
            timeout=15
        )
        air_response.raise_for_status()

        weather = weather_response.json()["hourly"]
        air = air_response.json()["hourly"]

        weather_by_time = {
            time: index
            for index, time in enumerate(weather["time"])
        }

        air_by_time = {
            time: index
            for index, time in enumerate(air["time"])
        }

        now = datetime.now(OMSK_TIMEZONE)
        results = []

        for hours in FORECAST_HOURS:
            target = now + timedelta(hours=hours)

            # Округляем до ближайшего целого часа.
            target = (
                target + timedelta(minutes=30)
            ).replace(minute=0, second=0, microsecond=0)

            time_key = target.strftime("%Y-%m-%dT%H:%M")

            weather_index = weather_by_time.get(time_key)
            air_index = air_by_time.get(time_key)

            def value(series, index, key):
                if index is None:
                    return None

                values = series.get(key, [])

                if index >= len(values):
                    return None

                return values[index]

            direction = value(
                weather, weather_index, "wind_direction_10m"
            )

            speed = value(
                weather, weather_index, "wind_speed_10m"
            )

            pm25 = value(
                air, air_index, "pm2_5"
            )

            aqi = value(
                air, air_index, "european_aqi"
            )

            results.append({
                "hours_ahead": hours,
                "time": time_key,
                "wind_direction": direction,
                "wind_speed": speed,
                "wind_to": (
                    (direction + 180) % 360
                    if direction is not None else None
                ),
                "pm25": pm25,
                "european_aqi": aqi
            })

        return {
            "status": "ok",
            "source": "Open-Meteo",
            "model_note": (
                "Почасовой модельный прогноз для координат дома. "
                "Не измерение воздуха у окна."
            ),
            "results": results
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ):
        return {
            "status": "error",
            "message": "Не удалось получить почасовой прогноз"
        }
