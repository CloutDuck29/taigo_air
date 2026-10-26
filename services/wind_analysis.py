
import math


DIRECTIONS = [
    "С", "СВ", "В", "ЮВ",
    "Ю", "ЮЗ", "З", "СЗ"
]

DIRECTION_NAMES = [
    "север", "северо-восток",
    "восток", "юго-восток",
    "юг", "юго-запад",
    "запад", "северо-запад"
]


def direction_name(angle):
    index = int((angle % 360 + 22.5) // 45) % 8
    return DIRECTION_NAMES[index]


def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    x = math.sin(delta_lon) * math.cos(lat2)

    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1) * math.cos(lat2)
        * math.cos(delta_lon)
    )

    return (math.degrees(math.atan2(x, y)) + 360) % 360


def analyze_wind(source, home, wind_direction, wind_speed):
    bearing = calculate_bearing(
        source["latitude"],
        source["longitude"],
        home["latitude"],
        home["longitude"]
    )

    bearing_index = int((bearing + 22.5) // 45) % 8
    bearing_name = DIRECTIONS[bearing_index]

    result = {
        "bearing": round(bearing, 1),
        "bearing_name": bearing_name,
        "wind_to": None,
        "wind_from_name": None,
        "wind_to_name": None,
        "angle_difference": None,
        "position": "Нет данных о ветре",
        "position_code": "unknown"
    }

    if wind_direction is None or wind_speed is None:
        return result

    wind_to = (wind_direction + 180) % 360

    difference = abs(
        (bearing - wind_to + 180) % 360 - 180
    )

    result.update({
        "wind_to": round(wind_to, 1),
        "wind_from_name": direction_name(wind_direction),
        "wind_to_name": direction_name(wind_to),
        "angle_difference": round(difference, 1)
    })

    if wind_speed < 0.5:
        result["position"] = "Направление ветра неустойчиво"
        result["position_code"] = "calm"

    elif difference <= 30:
        result["position"] = "Дом по направлению ветра"
        result["position_code"] = "downwind"

    elif difference <= 60:
        result["position"] = "Дом рядом с направлением ветра"
        result["position_code"] = "edge"

    else:
        result["position"] = "Дом вне основного направления ветра"
        result["position_code"] = "outside"

    return result
