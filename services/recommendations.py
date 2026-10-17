

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

    # Если наружный воздух грязнее внутреннего
    if outdoor_pm25 > indoor_pm25:
        if indoor_co2 <= CO2_TARGET:
            return {
                "decision": "Подождать",
                "recommended_minutes": 0,
                "reason": (
                    "CO₂ не превышает заданный порог, "
                    "а наружная PM2.5 выше внутренней. "
                    "Проветривание может увеличить "
                    "концентрацию частиц."
                ),
                "warnings": [
                    "Наружная PM2.5 выше внутренней"
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
            "warnings": []
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
        "warnings": [
            "Проверь температуру и наружное загрязнение",
            "Рассмотри более короткое проветривание "
            "или другой момент времени"
        ]
    }
