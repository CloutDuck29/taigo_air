
import math

from services.wind_analysis import calculate_bearing


def calculate_plume(
    source,
    home,
    wind_direction,
    wind_speed,
    emission_rate=1.0,
    effective_height=30.0
):
    """
    Учебная стационарная гауссова модель.

    emission_rate: условный выброс, г/с
    effective_height: эффективная высота, м

    Допущения:
    - ровная местность;
    - постоянный ветер;
    - нейтральная устойчивость атмосферы;
    - одна точка выброса на предприятие;
    - концентрация рассчитывается у земли.
    """

    # Направление переноса воздуха
    wind_to = (wind_direction + 180) % 360

    # Азимут от источника к дому
    bearing = calculate_bearing(
        source["latitude"],
        source["longitude"],
        home["latitude"],
        home["longitude"]
    )

    # Угловая разница
    angle = math.radians(
        (bearing - wind_to + 180) % 360 - 180
    )

    # Расстояние от источника до дома
    distance = source["distance_km"] * 1000

    # Продольная и поперечная координаты
    x = distance * math.cos(angle)
    y = distance * math.sin(angle)

    result = {
        "source_id": source["id"],
        "source_name": source["name"],
        "distance_km": source["distance_km"],
        "downwind_m": round(x, 1),
        "crosswind_m": round(y, 1),
        "scenario": "Учебная модель, не реальный выброс",
        "concentration_ug_m3": 0.0
    }

    # Если дом расположен против ветра,
    # модель не рассчитывает шлейф в этой точке
    if x <= 0:
        result["status"] = "Против направления переноса"
        return result

    # При почти штиле модель не применима
    if wind_speed < 0.5:
        result["status"] = "Слишком слабый ветер"
        result["concentration_ug_m3"] = None
        return result

    # Приближение Pasquill-Gifford,
    # класс устойчивости D (нейтральный)
    sigma_y = (
        0.08 * x / math.sqrt(1 + 0.0001 * x)
    )
    sigma_z = (
        0.06 * x / math.sqrt(1 + 0.0015 * x)
    )

    # Стационарная гауссова модель
    concentration_g_m3 = (
        emission_rate
        / (math.pi * wind_speed * sigma_y * sigma_z)
        * math.exp(
            -(y ** 2) / (2 * sigma_y ** 2)
        )
        * math.exp(
            -(effective_height ** 2)
            / (2 * sigma_z ** 2)
        )
    )

    # г/м³ -> мкг/м³
    concentration_ug_m3 = concentration_g_m3 * 1_000_000

    result["concentration_ug_m3"] = round(
        concentration_ug_m3, 6
    )
    result["status"] = "Сценарий рассчитан"

    return result


def calculate_plume_at_point(
    x,
    y,
    wind_speed,
    emission_rate=1.0,
    effective_height=30.0
):
    """
    Учебная гауссова модель концентрации
    в точке (x, y), где:

    x — расстояние по ветру, м;
    y — поперечное смещение, м.

    Результат: условная концентрация, мкг/м³.
    """

    if x <= 0 or wind_speed < 0.5:
        return 0.0

    sigma_y = (
        0.08 * x / math.sqrt(1 + 0.0001 * x)
    )

    sigma_z = (
        0.06 * x / math.sqrt(1 + 0.0015 * x)
    )

    concentration = (
        emission_rate
        / (math.pi * wind_speed * sigma_y * sigma_z)
        * math.exp(
            -y ** 2 / (2 * sigma_y ** 2)
        )
        * math.exp(
            -effective_height ** 2
            / (2 * sigma_z ** 2)
        )
    )

    return concentration * 1_000_000
