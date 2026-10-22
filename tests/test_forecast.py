
import math
import unittest

from services.forecast import forecast_ventilation


class ForecastTests(unittest.TestCase):

    def setUp(self):
        self.params = {
            "indoor_co2": 850,
            "indoor_pm25": 12,
            "indoor_temperature": 23.5,
            "outdoor_pm25": 10,
            "outdoor_temperature": 5,
            "room_area": 20,
            "ceiling_height": 2.8,
            "air_changes_per_hour": 2,
            "outdoor_co2": 450
        }

    def test_volume_and_air_flow(self):
        result = forecast_ventilation(**self.params)

        self.assertEqual(result["volume_m3"], 56)
        self.assertEqual(result["air_flow_m3_h"], 112)

    def test_forecast_times(self):
        result = forecast_ventilation(**self.params)

        minutes = [
            point["minutes"]
            for point in result["results"]
        ]

        self.assertEqual(minutes, [5, 10, 15, 20])

    def test_co2_decreases(self):
        result = forecast_ventilation(**self.params)

        values = [
            point["co2"]
            for point in result["results"]
        ]

        self.assertEqual(values, sorted(values, reverse=True))

    def test_temperature_decreases(self):
        result = forecast_ventilation(**self.params)

        values = [
            point["temperature"]
            for point in result["results"]
        ]

        self.assertEqual(values, sorted(values, reverse=True))

    def test_heat_loss_increases(self):
        result = forecast_ventilation(**self.params)

        values = [
            point["heat_loss_wh"]
            for point in result["results"]
        ]

        self.assertEqual(values, sorted(values))

    def test_energy_formula(self):
        result = forecast_ventilation(**self.params)

        factor = math.exp(-2 * 5 / 60)

        expected = (
            1.2 * 1005 * 56 * 18.5
            * (1 - factor) / 3600
        )

        self.assertAlmostEqual(
            result["results"][0]["heat_loss_wh"],
            expected,
            delta=0.1
        )

    def test_invalid_room_area(self):
        params = self.params.copy()
        params["room_area"] = 0

        with self.assertRaises(ValueError):
            forecast_ventilation(**params)

    def test_invalid_ach(self):
        params = self.params.copy()
        params["air_changes_per_hour"] = -1

        with self.assertRaises(ValueError):
            forecast_ventilation(**params)

    def test_invalid_concentration(self):
        params = self.params.copy()
        params["indoor_pm25"] = -10

        with self.assertRaises(ValueError):
            forecast_ventilation(**params)

    def test_nan_input(self):
        params = self.params.copy()
        params["indoor_co2"] = float("nan")

        with self.assertRaises(ValueError):
            forecast_ventilation(**params)


if __name__ == "__main__":
    unittest.main()
