
import time
import requests

from services.database import get_home

API_URL = "https://api.open-meteo.com/v1/forecast"

# Центр Омска — временные координаты
OMSK_LAT = 54.99
OMSK_LON = 73.37

CACHE_SECONDS = 600

weather_cache = {
    "key": None,
    "data": None,
    "expires": 0
}


def get_weather():
    home = get_home()

    if home and home["latitude"] is not None \
            and home["longitude"] is not None:
        latitude = home["latitude"]
        longitude = home["longitude"]
        location = "Координаты дома"
    else:
        latitude = OMSK_LAT
        longitude = OMSK_LON
        location = "Центр Омска"

    cache_key = (latitude, longitude)

    if (
        weather_cache["key"] == cache_key
        and time.monotonic() < weather_cache["expires"]
    ):
        return weather_cache["data"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m"
        ]),
        "wind_speed_unit": "ms",
        "timezone": "Asia/Omsk"
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        result = response.json()
        current = result["current"]

        weather = {
            "status": "ok",
            "source": "Open-Meteo",
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "pressure": current.get("surface_pressure"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "timestamp": current.get("time")
        }

        weather_cache.update({
            "key": cache_key,
            "data": weather,
            "expires": time.monotonic() + CACHE_SECONDS
        })

        return weather

    except (requests.RequestException, ValueError, KeyError):
        return {
            "status": "error",
            "message": "Не удалось получить погоду"
        }
