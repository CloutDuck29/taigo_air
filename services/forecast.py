
import math

FORECAST_MINUTES = [5, 10, 15, 20]

# Временное предположение о наружном CO2.
# Позже заменим измерением или пользовательской настройкой.
OUTDOOR_CO2_PPM = 420.0

# Ориентировочные свойства воздуха
AIR_DENSITY = 1.2        # кг/м3
AIR_HEAT_CAPACITY = 1005  # Дж/(кг * К)


def forecast_ventilation(
    indoor_co2,
    indoor_pm25,
    indoor_temperature,
    outdoor_pm25,
    outdoor_temperature,
    room_area,
    ceiling_height,
    air_changes_per_hour=3.0,
    outdoor_co2=OUTDOOR_CO2_PPM,
):
    """
    Упрощённая модель хорошо перемешанного помещения.

    Допущения:
    - постоянная кратность воздухообмена;
    - нет дополнительных источников CO2;
    - нет источников и осаждения PM2.5;
    - PM2.5 проникает с эффективностью 100%;
    - температура наружного воздуха постоянная;
    - тепловая инерция мебели и стен не учитывается.

    Результаты являются сценарным прогнозом,
    а не подтверждённым прогнозом для квартиры.
    """

    values = [
        indoor_co2, indoor_pm25, indoor_temperature,
        outdoor_pm25, outdoor_temperature,
        room_area, ceiling_height,
        air_changes_per_hour, outdoor_co2
    ]

    if not all(math.isfinite(v) for v in values):
        raise ValueError("Параметры должны быть конечными числами")

    if room_area <= 0 or ceiling_height <= 0:
        raise ValueError("Неверные размеры помещения")

    if not 0 < air_changes_per_hour <= 30:
        raise ValueError("Кратность воздухообмена должна быть от 0 до 30")

    if min(indoor_co2, indoor_pm25, outdoor_pm25, outdoor_co2) < 0:
        raise ValueError("Концентрации не могут быть отрицательными")

    volume = room_area * ceiling_height
    air_flow_m3_h = volume * air_changes_per_hour

    results = []

    for minutes in FORECAST_MINUTES:
        hours = minutes / 60
        factor = math.exp(-air_changes_per_hour * hours)

        co2 = outdoor_co2 + (
            indoor_co2 - outdoor_co2
        ) * factor

        pm25 = outdoor_pm25 + (
            indoor_pm25 - outdoor_pm25
        ) * factor

        temperature = outdoor_temperature + (
            indoor_temperature - outdoor_temperature
        ) * factor

        # Тепловая энергия, вынесенная воздухообменом,
        # при фиксированной разнице температур.
        heat_loss_wh = (
            AIR_DENSITY
            * AIR_HEAT_CAPACITY
            * air_flow_m3_h
            * hours
            * max(indoor_temperature - outdoor_temperature, 0)
            / 3600
        )

        results.append({
            "minutes": minutes,
            "co2": round(co2, 1),
            "pm25": round(pm25, 2),
            "temperature": round(temperature, 2),
            "heat_loss_wh": round(heat_loss_wh, 1)
        })

    return {
        "status": "ok",
        "model": "well-mixed room",
        "volume_m3": round(volume, 2),
        "air_changes_per_hour": air_changes_per_hour,
        "air_flow_m3_h": round(air_flow_m3_h, 2),
        "outdoor_co2_assumed": outdoor_co2,
        "results": results,
        "limitations": (
            "Учебный сценарий без источников CO2, "
            "осаждения частиц и тепловой инерции помещения"
        )
    }
