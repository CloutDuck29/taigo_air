
import unittest

from services.recommendations import get_scenario_recommendation


class RecommendationTests(unittest.TestCase):

    def setUp(self):
        self.settings = {
            "co2_target": 700,
            "pm25_limit": 25,
            "max_temperature_drop": 3
        }

    def make_scenarios(self, co2_values, temperature=21):
        scenarios = []

        for code, co2 in zip(
            ("low", "middle", "high"), co2_values
        ):
            scenarios.append({
                "code": code,
                "results": [{
                    "minutes": 15,
                    "co2": co2,
                    "pm25": 10,
                    "temperature": temperature
                }]
            })

        return scenarios

    def recommend(self, scenarios, indoor_co2=850):
        return get_scenario_recommendation(
            scenarios=scenarios,
            indoor_co2=indoor_co2,
            indoor_pm25=12,
            outdoor_pm25=10,
            indoor_temperature=23.5,
            settings=self.settings
        )

    def test_ventilation_not_required(self):
        result = self.recommend(
            self.make_scenarios([650, 620, 600]),
            indoor_co2=650
        )
        self.assertEqual(
            result["decision"],
            "Проветривание не требуется"
        )

    def test_all_scenarios_suitable(self):
        result = self.recommend(
            self.make_scenarios([690, 650, 600])
        )
        self.assertEqual(
            result["decision"],
            "Подходит во всех сценариях"
        )

    def test_only_high_suitable(self):
        result = self.recommend(
            self.make_scenarios([800, 750, 650])
        )
        self.assertEqual(
            result["decision"],
            "Зависит от воздухообмена"
        )

    def test_none_suitable(self):
        result = self.recommend(
            self.make_scenarios([800, 750, 710])
        )
        self.assertEqual(
            result["decision"],
            "Подходящего сценария нет"
        )

    def test_excessive_cooling(self):
        result = self.recommend(
            self.make_scenarios(
                [690, 650, 600],
                temperature=19
            )
        )
        self.assertEqual(
            result["decision"],
            "Подходящего сценария нет"
        )


if __name__ == "__main__":
    unittest.main()
