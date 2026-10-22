
import unittest

from services.ventilation import estimate_ventilation


class VentilationTests(unittest.TestCase):

    def estimate(self, **kwargs):
        params = {
            "window_mode": "tilt",
            "window_direction": "N",
            "wind_direction": None,
            "wind_speed": None,
            "floor": 5
        }
        params.update(kwargs)
        return estimate_ventilation(**params)

    def test_closed_window(self):
        result = self.estimate(window_mode="closed")

        self.assertEqual(result["ach_min"], 0)
        self.assertEqual(result["ach_max"], 0)
        self.assertIsNone(result["ach_estimate"])

    def test_micro_window(self):
        result = self.estimate(window_mode="micro")

        self.assertEqual(result["ach_min"], 0.1)
        self.assertEqual(result["ach_max"], 0.5)

    def test_tilt_window(self):
        result = self.estimate(window_mode="tilt")

        self.assertEqual(result["ach_min"], 0.5)
        self.assertEqual(result["ach_max"], 2.0)

    def test_open_window(self):
        result = self.estimate(window_mode="open")

        self.assertEqual(result["ach_min"], 1.0)
        self.assertEqual(result["ach_max"], 5.0)

    def test_windward(self):
        result = self.estimate(wind_direction=0)

        self.assertEqual(
            result["wind_exposure"], "windward"
        )

    def test_leeward(self):
        result = self.estimate(wind_direction=180)

        self.assertEqual(
            result["wind_exposure"], "leeward"
        )

    def test_side_wind(self):
        result = self.estimate(wind_direction=90)

        self.assertEqual(
            result["wind_exposure"], "side"
        )

    def test_angle_wraparound(self):
        result = self.estimate(
            window_direction="N",
            wind_direction=350
        )

        self.assertEqual(
            result["angle_difference"], 10
        )
        self.assertEqual(
            result["wind_exposure"], "windward"
        )

    def test_unknown_wind(self):
        result = self.estimate()

        self.assertEqual(
            result["wind_exposure"], "unknown"
        )
        self.assertIsNone(result["angle_difference"])

    def test_invalid_window_mode(self):
        with self.assertRaises(ValueError):
            self.estimate(window_mode="invalid")

    def test_invalid_window_direction(self):
        with self.assertRaises(ValueError):
            self.estimate(window_direction="INVALID")

    def test_negative_wind_speed(self):
        with self.assertRaises(ValueError):
            self.estimate(wind_speed=-5)

    def test_nan_wind_direction(self):
        with self.assertRaises(ValueError):
            self.estimate(wind_direction=float("nan"))

    def test_uncalibrated_model(self):
        result = self.estimate()

        self.assertFalse(result["calibrated"])


if __name__ == "__main__":
    unittest.main()
