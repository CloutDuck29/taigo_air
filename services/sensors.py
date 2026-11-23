from services.arduino_bridge import get_hardware_data
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
    hardware = get_hardware_data()

    if hardware is not None:
        data = {
            "mode": "hardware",
            "connected": True,
            "co2": None,
            "pm1": None,
            "pm25": None,
            "pm10": None,
            "temperature_inside": None,
            "temperature_outside": None,
            "humidity_inside": None,
            "humidity_outside": None,
            "pressure_inside": None,
            "pressure_outside": None,
            "window_open": None,
            "fan_on": None,
        }

        data.update(hardware)

    else:
        data = {
            **sensor_data,
            "mode": "simulation",
            "connected": False,
        }

    data["timestamp"] = datetime.now().strftime(
        "%d.%m.%Y %H:%M:%S"
    )

    return data



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
