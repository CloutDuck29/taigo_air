
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import app
from services import database


class ExperimentApiTests(unittest.TestCase):

    def setUp(self):
        # Создаём отдельную временную базу для каждого теста
        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_patch = patch.object(
            database,
            "DB_PATH",
            Path(self.temp_dir.name) / "test_api.db"
        )
        self.db_patch.start()
        database.init_db()

        self.client = app.test_client()

        self.home = {
            "address": "Тестовая квартира",
            "room_area": 20,
            "ceiling_height": 2.8,
            "window_direction": "N",
            "floor": 5,
            "window_mode": "tilt"
        }

        self.sensors = {
            "mode": "simulation",
            "co2": 850,
            "pm25": 12,
            "temperature_inside": 23.5
        }

        self.forecast = {
            "air_changes_per_hour": 2,
            "results": [
                {
                    "minutes": 5,
                    "co2": 790,
                    "pm25": 12,
                    "temperature": 22
                },
                {
                    "minutes": 10,
                    "co2": 740,
                    "pm25": 11,
                    "temperature": 21
                }
            ]
        }

    def tearDown(self):
        # Удаляем временную базу
        self.db_patch.stop()
        self.temp_dir.cleanup()

    # -------------------------------------
    # Запуск и завершение экспериментов
    # -------------------------------------

    def test_start_and_finish(self):
        with patch("main.get_home", return_value=self.home), \
             patch("main.get_sensor_data", return_value=self.sensors), \
             patch(
                 "main.forecast_api",
                 return_value=app.response_class(
                     response='{"status":"ok","results":[]}',
                     mimetype="application/json"
                 )
             ):

            response = self.client.post(
                "/api/experiment/start"
            )

            self.assertEqual(response.status_code, 200)

            experiment_id = response.get_json()["experiment_id"]

            finish = self.client.post(
                "/api/experiment/finish",
                json={
                    "experiment_id": experiment_id,
                    "actual_minutes": 10
                }
            )

            self.assertEqual(finish.status_code, 200)

            saved = database.get_experiment(experiment_id)

            self.assertEqual(saved["status"], "completed")
            self.assertEqual(saved["actual_minutes"], 10)

    def test_finish_invalid_duration(self):
        response = self.client.post(
            "/api/experiment/finish",
            json={
                "experiment_id": 1,
                "actual_minutes": -5
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_finish_unknown_experiment(self):
        with patch(
            "main.get_sensor_data",
            return_value=self.sensors
        ):
            response = self.client.post(
                "/api/experiment/finish",
                json={
                    "experiment_id": 99999,
                    "actual_minutes": 10
                }
            )

        self.assertEqual(response.status_code, 400)

    def test_results_unknown_experiment(self):
        response = self.client.get(
            "/api/experiment/results/99999"
        )

        self.assertEqual(response.status_code, 404)

    def test_active_experiment(self):
        experiment_id = database.start_experiment(
            self.home,
            self.sensors,
            self.forecast
        )

        response = self.client.get(
            "/api/experiment/active"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.get_json()["experiment"]["id"],
            experiment_id
        )

    # -------------------------------------
    # Сравнение прогноза и реальных данных
    # -------------------------------------

    def test_results_exact_time(self):
        experiment_id = database.start_experiment(
            self.home,
            self.sensors,
            self.forecast
        )

        database.finish_experiment(
            experiment_id,
            {
                "co2": 735,
                "pm25": 12,
                "temperature_inside": 20.5
            },
            10
        )

        response = self.client.get(
            f"/api/experiment/results/{experiment_id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "ok")

        comparison = {
            item["name"]: item
            for item in data["comparison"]
        }

        self.assertEqual(
            comparison["CO₂"]["predicted"], 740
        )
        self.assertEqual(
            comparison["CO₂"]["actual"], 735
        )
        self.assertEqual(
            comparison["CO₂"]["error"], 5
        )

    def test_results_interpolation(self):
        experiment_id = database.start_experiment(
            self.home,
            self.sensors,
            self.forecast
        )

        database.finish_experiment(
            experiment_id,
            {
                "co2": 770,
                "pm25": 11.5,
                "temperature_inside": 21.5
            },
            7.5
        )

        response = self.client.get(
            f"/api/experiment/results/{experiment_id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        comparison = {
            item["name"]: item
            for item in data["comparison"]
        }

        # Между 790 ppm (5 мин) и 740 ppm (10 мин)
        # ожидаем 765 ppm на 7,5-й минуте.
        self.assertEqual(
            comparison["CO₂"]["predicted"], 765
        )
        self.assertEqual(
            comparison["CO₂"]["actual"], 770
        )
        self.assertEqual(
            comparison["CO₂"]["error"], 5
        )

    def test_results_outside_forecast_range(self):
        experiment_id = database.start_experiment(
            self.home,
            self.sensors,
            self.forecast
        )

        database.finish_experiment(
            experiment_id,
            self.sensors,
            15
        )

        response = self.client.get(
            f"/api/experiment/results/{experiment_id}"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.get_json()["status"],
            "no_comparison"
        )


if __name__ == "__main__":
    unittest.main()
