
import math


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

    wind_to = (wind_direction + 180) % 360

    difference = abs(
        (bearing - wind_to + 180) % 360 - 180
    )

    if wind_speed < 0.5:
        position = "Слабый ветер"
    elif difference <= 30:
        position = "По ветру"
    elif difference <= 60:
        position = "На границе сектора"
    else:
        position = "Вне сектора"

    directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
    bearing_name = directions[int((bearing + 22.5) // 45) % 8]

    return {
        "bearing": round(bearing, 1),
        "bearing_name": bearing_name,
        "wind_to": round(wind_to, 1),
        "angle_difference": round(difference, 1),
        "position": position
    }
