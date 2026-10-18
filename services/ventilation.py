
import math

# Предварительные сценарные диапазоны, ч^-1.
# НЕ измеренные и НЕ универсальные нормативы.
# Эти значения нужны для тестирования алгоритма.
SCENARIO_RANGES = {
    "closed": (0.0, 0.0),
    "micro": (0.1, 0.5),
    "tilt": (0.5, 2.0),
    "open": (1.0, 5.0)
}

WINDOW_LABELS = {
    "closed": "Закрыто",
    "micro": "Микропроветривание",
    "tilt": "Откинуто",
    "open": "Распахнуто"
}

DIRECTION_DEGREES = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SW": 225,
    "W": 270,
    "NW": 315
}


def estimate_ventilation(
    window_mode,
    window_direction,
    wind_direction=None,
    wind_speed=None,
    floor=None
):
    """
    Экспериментальная оценка воздухообмена.

    Ветер используется для классификации
    расположения окна относительно потока.

    Этаж сохраняется в результатах, но без
    параметров здания не используется в формуле.

    Диапазоны ACH являются сценарными,
    а не измеренными значениями.
    """

    if window_mode not in SCENARIO_RANGES:
        raise ValueError("Неизвестный режим окна")

    if window_direction not in DIRECTION_DEGREES:
        raise ValueError("Неверное направление окна")

    ach_min, ach_max = SCENARIO_RANGES[window_mode]

    wind_exposure = "unknown"
    angle_difference = None

    if wind_direction is not None:
        wind_direction = float(wind_direction)

        if not math.isfinite(wind_direction):
            raise ValueError("Неверное направление ветра")

        window_angle = DIRECTION_DEGREES[window_direction]

        # Метеорологическое направление ветра:
        # откуда дует ветер.
        angle_difference = abs(
            (wind_direction - window_angle + 180) % 360
            - 180
        )

        if angle_difference <= 45:
            wind_exposure = "windward"
        elif angle_difference >= 135:
            wind_exposure = "leeward"
        else:
            wind_exposure = "side"

    if wind_speed is not None:
        wind_speed = float(wind_speed)

        if not math.isfinite(wind_speed) or wind_speed < 0:
            raise ValueError("Неверная скорость ветра")

    # Пока ветер не меняет ACH численно:
    # для этого нужны данные о здании,
    # площади проёма и калибровка.
    return {
        "status": "ok",
        "window_mode": window_mode,
        "window_label": WINDOW_LABELS[window_mode],
        "ach_min": ach_min,
        "ach_max": ach_max,
        "ach_estimate": (
            round((ach_min + ach_max) / 2, 2)
            if window_mode != "closed"
            else None
        ),
        "wind_exposure": wind_exposure,
        "angle_difference": angle_difference,
        "wind_speed": wind_speed,
        "floor": floor,
        "calibrated": False,
        "limitations": (
            "Предварительный диапазон для проверки алгоритма. "
            "Не является измеренной кратностью воздухообмена. "
            "Влияние ветра и этажа пока не откалибровано."
        )
    }
