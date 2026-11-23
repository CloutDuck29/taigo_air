from services.forecast import forecast_ventilation
from services.recommendations import get_scenario_recommendation

settings = {
    "co2_target": 1000,
    "pm25_limit": 35,
    "max_temperature_drop": 3,
}

def check(name, co2, pm_inside, pm_outside,
          temp_outside, expected):

    scenarios = []

    for code, ach in [
        ("low", 1.0),
        ("middle", 3.0),
        ("high", 5.0),
    ]:
        forecast = forecast_ventilation(
            indoor_co2=co2,
            indoor_pm25=pm_inside,
            indoor_temperature=24,
            outdoor_pm25=pm_outside,
            outdoor_temperature=temp_outside,
            room_area=20,
            ceiling_height=2.5,
            air_changes_per_hour=ach,
        )

        scenarios.append({
            "code": code,
            "results": forecast["results"]
        })

    result = get_scenario_recommendation(
        scenarios=scenarios,
        indoor_co2=co2,
        indoor_pm25=pm_inside,
        outdoor_pm25=pm_outside,
        indoor_temperature=24,
        settings=settings
    )

    actual = result["decision"]
    passed = actual == expected

    print(
        "✅" if passed else "❌",
        name
    )
    print("   Решение:", actual)
    print(
        "   Время:",
        result.get("recommended_minutes")
        or result.get("possible_minutes")
        or "Не требуется / не определено"
    )
    if not passed:
        print("   Ожидалось:", expected)

    return passed


results = [
    check(
        "1. Оба показателя нормальные",
        700, 12, 8, 20,
        "Проветривание не требуется"
    ),

    check(
        "2. Высокий CO2, тепло снаружи",
        1300, 12, 8, 24,
        "Зависит от воздухообмена"
    ),

    check(
        "3. Высокий CO2, холодно снаружи",
        1300, 12, 8, 0,
        "Условное проветривание"
    ),

    check(
        "4. Высокий CO2, грязно снаружи",
        1300, 12, 80, 0,
        "Подходящего сценария нет"
    ),

    check(
        "5. CO2 нормальный, PM2.5 повышен",
        700, 60, 8, 20,
        "Зависит от воздухообмена"
    ),
]

print()
print("ИТОГ:", sum(results), "из", len(results))