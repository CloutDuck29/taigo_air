
import json
import math
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "industries.json"
)


def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(
        min(1, math.sqrt(a))
    )


def get_industrial_sources(latitude, longitude):
    with open(DATA_PATH, encoding="utf-8") as file:
        data = json.load(file)

    sources = []

    for source in data["sources"]:
        lat = source["latitude"]
        lon = source["longitude"]

        distance = calculate_distance(
            latitude, longitude, lat, lon
        )

        sources.append({
            **source,
            "distance_km": round(distance, 2)
        })

    sources.sort(
        key=lambda item: item["distance_km"]
    )

    return sources
