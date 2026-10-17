
from datetime import datetime

# Тестовые показания КОТОРЫЕ В ДАЛЬНЕЙШЕМ БУДУТ БРАТЬСЯ ИЗ ДАТЧИКОВ
sensor_data = {
    "mode": "simulation",
    "co2": 850,
    "pm1": 5,
    "pm25": 12,
    "pm10": 18,

    "temperature_inside": 23.5,
    "temperature_outside": 8.2,

    "humidity_inside": 45,
    "humidity_outside": 67,

    "pressure_inside": 755,
    "pressure_outside": 755,

    "window_open": False,
    "fan_on": False,
}


def get_sensor_data():
    return {
        **sensor_data,
        "timestamp": datetime.now().strftime(
            "%d.%m.%Y %H:%M:%S"
        )
    }


def update_sensor_data(values):
    allowed = {
        "co2", "pm1", "pm25", "pm10",
        "temperature_inside",
        "temperature_outside",
        "humidity_inside",
        "humidity_outside",
        "pressure_inside",
        "pressure_outside",
        "window_open",
        "fan_on"
    }

    for key in allowed:
        if key in values:
            sensor_data[key] = values[key]

    return get_sensor_data()
