
import time
import requests

from services.database import get_home

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

OMSK_LAT = 54.99
OMSK_LON = 73.37

CACHE_SECONDS = 1800

air_quality_cache = {
    "key": None,
    "data": None,
    "expires": 0
}


def get_air_quality():
    home = get_home()

    if (
        home
        and home["latitude"] is not None
        and home["longitude"] is not None
    ):
        latitude = home["latitude"]
        longitude = home["longitude"]
        location = "Координаты дома"
    else:
        latitude = OMSK_LAT
        longitude = OMSK_LON
        location = "Центр Омска"

    cache_key = (latitude, longitude)

    if (
        air_quality_cache["key"] == cache_key
        and time.monotonic() < air_quality_cache["expires"]
    ):
        return air_quality_cache["data"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "pm2_5",
            "pm10",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "carbon_monoxide",
            "ozone",
            "european_aqi"
        ]),
        "timezone": "Asia/Omsk"
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=15
        )
        response.raise_for_status()

        result = response.json()
        current = result["current"]

        air_quality = {
            "status": "ok",
            "source": "Open-Meteo / CAMS",
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "pm25": current.get("pm2_5"),
            "pm10": current.get("pm10"),
            "no2": current.get("nitrogen_dioxide"),
            "so2": current.get("sulphur_dioxide"),
            "co": current.get("carbon_monoxide"),
            "o3": current.get("ozone"),
            "aqi": current.get("european_aqi"),
            "timestamp": current.get("time")
        }

        air_quality_cache.update({
            "key": cache_key,
            "data": air_quality,
            "expires": time.monotonic() + CACHE_SECONDS
        })

        return air_quality

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ):
        return {
            "status": "error",
            "message": "Не удалось получить данные о загрязнении"
        }
