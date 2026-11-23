

def get_recommendation(
    forecast,
    indoor_co2,
    indoor_pm25,
    indoor_temperature,
    outdoor_pm25,
    settings=None
):

    """
    Учебная система рекомендаций.

    Пороги и допустимое охлаждение являются
    настраиваемыми сценарными критериями,
    а не медицинскими нормативами.
    """


    settings = settings or {}

    CO2_TARGET = settings.get("co2_target", 1000)
    CO2_PREFERRED = settings.get("co2_preferred", 800)
    PM25_LIMIT = settings.get("pm25_limit", 35)
    MAX_TEMPERATURE_DROP = settings.get(
        "max_temperature_drop", 3.0
    )


    results = forecast["results"]
    outdoor_warnings = []

    if outdoor_pm25 > indoor_pm25:
        outdoor_warnings.append(
            "PM2.5 снаружи выше, чем внутри. "
            "При проветривании концентрация частиц "
            "может увеличиться."
        )

    if outdoor_pm25 > PM25_LIMIT:
        outdoor_warnings.append(
            "PM2.5 снаружи превышает заданный порог."
        )
    # Если показатели в пределах нормы,
    # проветривание по ним не требуется.
    if indoor_co2 <= CO2_TARGET and indoor_pm25 <= PM25_LIMIT:
        return {
            "decision": "Проветривание не требуется",
            "recommended_minutes": 0,
            "reason": (
                "CO₂ и PM2.5 находятся в пределах "
                "заданных порогов. Проветривание "
                "по этим показателям сейчас не требуется."
            ),
            "warnings": []
        }
    # CO2 в норме, но PM2.5 превышает порог
    if indoor_co2 <= CO2_TARGET and indoor_pm25 > PM25_LIMIT:
        return {
            "decision": "Подходящего сценария нет",
            "recommended_minutes": None,
            "reason": (
                f"CO₂ в пределах нормы, но PM2.5 "
                f"составляет {indoor_pm25} мкг/м³ "
                f"при заданном пределе {PM25_LIMIT} мкг/м³. "
                "Среди рассчитанных вариантов нет "
                "проветривания, удовлетворяющего "
                "ограничениям по загрязнению "
                "и охлаждению."
            ),
            "warnings": [
                "PM2.5 внутри превышает заданный порог",
                "Проверь наружное загрязнение"
            ]
        }

    candidates = []

    for result in results:
        temp_drop = (
            indoor_temperature - result["temperature"]
        )

        co2_ok = result["co2"] <= CO2_TARGET
        pm25_ok = result["pm25"] <= PM25_LIMIT
        temp_ok = temp_drop <= MAX_TEMPERATURE_DROP

        if co2_ok and pm25_ok and temp_ok:
            candidates.append(result)

    # Выбираем самый короткий подходящий сценарий
    if candidates:
        best = min(
            candidates,
            key=lambda item: item["minutes"]
        )

        return {
            "decision": "Проветрить",
            "recommended_minutes": best["minutes"],
            "reason": (
                f"За {best['minutes']} минут CO₂ "
                f"по модели снизится до "
                f"{best['co2']} ppm, "
                f"PM2.5 составит "
                f"{best['pm25']} мкг/м³. "
                "Охлаждение укладывается "
                "в заданное ограничение."
            ),
            "warnings": outdoor_warnings
        }

    # Если CO2 нормальный, а подходящих
    # вариантов нет, проветривать необязательно
    if indoor_co2 <= CO2_TARGET:
        return {
            "decision": "Проветривание не требуется",
            "recommended_minutes": 0,
            "reason": (
                "CO₂ ниже заданного порога. "
                "Среди рассчитанных сценариев "
                "нет варианта, удовлетворяющего "
                "всем ограничениям."
            ),
            "warnings": [
                "Проверь наружное загрязнение и температуру"
            ]
        }

    # При повышенном CO2, если ни один
    # сценарий не удовлетворяет ограничениям
    return {
        "decision": "Подходящего сценария нет",
        "recommended_minutes": None,
        "reason": (
            "CO₂ превышает заданный порог, "
            "но ни один из вариантов "
            "5–20 минут не удовлетворяет "
            "всем ограничениям по CO₂, "
            "PM2.5 и охлаждению."
        ),
                "warnings": outdoor_warnings + [
            "Проверь температуру и наружное загрязнение",
            "Рассмотри более короткое проветривание "
            "или другой момент времени"
        ]
    }

def get_scenario_recommendation(scenarios, indoor_co2,
                                indoor_pm25, outdoor_pm25,
                                indoor_temperature, settings):
    """
    Сравнение трёх сценариев воздухообмена.
    Диапазоны ACH предварительные и не откалиброваны.
    """

    co2_target = settings.get("co2_target", 1000)
    pm25_limit = settings.get("pm25_limit", 35)
    max_drop = settings.get("max_temperature_drop", 3)


    if indoor_co2 <= co2_target and indoor_pm25 <= pm25_limit:
        return {
            "decision": "Проветривание не требуется",
            "recommended_minutes": 0,
            "reason": (
                "Текущие CO₂ и PM2.5 не превышают "
                "заданные пороги. Дополнительное "
                "проветривание по этим критериям "
                "сейчас не требуется."
            ),
            "comparisons": []
        }


    if not scenarios:
        return {
            "decision": "Нет данных",
            "recommended_minutes": None,
            "reason": "Сценарии не рассчитаны"
        }

    # Временные интервалы, присутствующие у всех сценариев
    common_minutes = set(
        point["minutes"] for point in scenarios[0]["results"]
    )

    for scenario in scenarios[1:]:
        common_minutes &= {
            point["minutes"] for point in scenario["results"]
        }

    comparisons = []

    for minutes in sorted(common_minutes):
        suitable = []

        for scenario in scenarios:
            point = next(
                p for p in scenario["results"]
                if p["minutes"] == minutes
            )

            temperature_drop = (
                indoor_temperature - point["temperature"]
            )

            if (
                point["co2"] <= co2_target
                and point["pm25"] <= pm25_limit
                and temperature_drop <= max_drop
            ):
                suitable.append(scenario["code"])

        comparisons.append({
            "minutes": minutes,
            "suitable": suitable,
            "total": len(scenarios)
        })

    all_suitable = [
        item for item in comparisons
        if len(item["suitable"]) == len(scenarios)
    ]

    partly_suitable = [
        item for item in comparisons
        if item["suitable"]
    ]

    if all_suitable:
        minutes = all_suitable[0]["minutes"]

        return {
            "decision": "Подходит во всех сценариях",
            "recommended_minutes": minutes,
            "reason": (
                f"На {minutes}-й минуте все три сценария "
                "удовлетворяют заданным ограничениям "
                "по CO₂, PM2.5 и охлаждению."
            ),
            "comparisons": comparisons
        }

    if partly_suitable:
        best = partly_suitable[0]

        return {
            "decision": "Зависит от воздухообмена",
            "recommended_minutes": None,
            "possible_minutes": best["minutes"],
            "reason": (
                f"При {best['minutes']} минутах ограничения "
                "выполняются только в некоторых сценариях. "
                "Без измерения воздухообмена нельзя "
                "подтвердить подходящую длительность."
            ),
            "comparisons": comparisons
        }
    # Условный вариант, если ни один сценарий
    # не удовлетворяет всем ограничениям.

    first_minutes = min(common_minutes) if common_minutes else None

    if first_minutes is not None:
        first_points = [
            next(
                point for point in scenario["results"]
                if point["minutes"] == first_minutes
            )
            for scenario in scenarios
        ]

        # Есть ли улучшение CO2 хотя бы в одном сценарии?
        co2_improves = any(
            point["co2"] < indoor_co2
            for point in first_points
        )

        # Не допускаем условной рекомендации,
        # если прогнозируется превышение PM2.5.
        pm25_acceptable = all(
            point["pm25"] <= pm25_limit
            for point in first_points
        )

        # Проверяем, что наружная концентрация
        # частиц не выше внутренней.
        outdoor_acceptable = outdoor_pm25 <= indoor_pm25

        if co2_improves and pm25_acceptable and outdoor_acceptable:
            return {
                "decision": "Условное проветривание",
                "recommended_minutes": None,
                "possible_minutes": first_minutes,
                "reason": (
                    f"Можно рассмотреть проветривание "
                    f"на {first_minutes} минут. "
                    "CO₂ по модели будет снижаться, "
                    "но допустимое охлаждение "
                    "или целевая концентрация CO₂ "
                    "могут быть не достигнуты."
                ),
                "warnings": [
                    "Время условное, воздухообмен не измерен",
                    "Возможно охлаждение выше заданного предела",
                    "Прогноз температуры не учитывает "
                    "отопление и тепловую инерцию помещения"
                ],
                "comparisons": comparisons
            }
    failures = {
        "co2": 0,
        "pm25": 0,
        "temperature": 0
    }

    total_points = 0

    for scenario in scenarios:
        for point in scenario["results"]:
            total_points += 1

            if point["co2"] > co2_target:
                failures["co2"] += 1

            if point["pm25"] > pm25_limit:
                failures["pm25"] += 1

            temperature_drop = (
                indoor_temperature - point["temperature"]
            )

            if temperature_drop > max_drop:
                failures["temperature"] += 1

    reasons = []

    if failures["co2"]:
        reasons.append(
            f"CO₂ не достигает цели {co2_target} ppm "
            f"в {failures['co2']} из {total_points} расчётов"
        )

    if failures["pm25"]:
        reasons.append(
            f"PM2.5 превышает предел {pm25_limit} мкг/м³ "
            f"в {failures['pm25']} из {total_points} расчётов"
        )

    if failures["temperature"]:
        reasons.append(
            f"Охлаждение превышает {max_drop} °C "
            f"в {failures['temperature']} из "
            f"{total_points} расчётов"
        )

    reason = (
        ". ".join(reasons) + "."
        if reasons
        else "Подходящий вариант не найден."
    )

    return {
        "decision": "Подходящего сценария нет",
        "recommended_minutes": None,
        "reason": reason,
        "comparisons": comparisons
    }
