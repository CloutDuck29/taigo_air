
import unittest
from unittest.mock import patch

from main import app


class ForecastApiTests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

        self.home = {
            "room_area": 20,
            "ceiling_height": 2.8,
            "window_direction": "N",
            "floor": 5,
            "window_mode": "tilt"
        }

        self.settings = {
            "co2_target": 700,
            "pm25_limit": 25,
            "max_temperature_drop": 3,
            "outdoor_co2": 450
        }

        self.sensors = {
            "co2": 850,
            "pm25": 12,
            "temperature_inside": 23.5
        }

    def test_closed_window_without_internet(self):
        home = dict(self.home)
        home["window_mode"] = "closed"

        with patch("main.get_home", return_value=home), \
             patch("main.get_settings", return_value=self.settings), \
             patch("main.get_sensor_data", return_value=self.sensors), \
             patch(
                 "main.get_air_quality",
                 side_effect=RuntimeError("Нет интернета")
             ), \
             patch(
                 "main.get_weather",
                 side_effect=RuntimeError("Нет погоды")
             ):

            response = self.client.get(
                "/api/forecast/scenarios"
            )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "closed")
        self.assertEqual(
            data["recommendation"]["decision"],
            "Есть превышение заданных порогов"
        )

    def test_external_service_failure(self):
        with patch("main.get_home", return_value=self.home), \
             patch("main.get_settings", return_value=self.settings), \
             patch("main.get_sensor_data", return_value=self.sensors), \
             patch(
                 "main.get_air_quality",
                 side_effect=RuntimeError("Нет соединения")
             ):

            response = self.client.get(
                "/api/forecast/scenarios"
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json()["status"],
            "unavailable"
        )

    def test_missing_home(self):
        with patch("main.get_home", return_value=None):
            response = self.client.get(
                "/api/forecast/scenarios"
            )

        self.assertEqual(response.status_code, 400)

    def test_normal_scenarios(self):
        air = {
            "status": "ok",
            "pm25": 10
        }

        weather = {
            "status": "ok",
            "temperature": 5,
            "wind_direction": 0,
            "wind_speed": 3
        }

        with patch("main.get_home", return_value=self.home), \
             patch("main.get_settings", return_value=self.settings), \
             patch("main.get_sensor_data", return_value=self.sensors), \
             patch("main.get_air_quality", return_value=air), \
             patch("main.get_weather", return_value=weather):

            response = self.client.get(
                "/api/forecast/scenarios"
            )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["scenarios"]), 3)

        for scenario in data["scenarios"]:
            self.assertEqual(
                len(scenario["results"]), 4
            )

    def test_air_quality_unavailable(self):
        with patch("main.get_home", return_value=self.home), \
             patch("main.get_settings", return_value=self.settings), \
             patch("main.get_sensor_data", return_value=self.sensors), \
             patch(
                 "main.get_air_quality",
                 return_value={"status": "error"}
             ), \
             patch(
                 "main.get_weather",
                 return_value={"status": "ok"}
             ):

            response = self.client.get(
                "/api/forecast/scenarios"
            )

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
