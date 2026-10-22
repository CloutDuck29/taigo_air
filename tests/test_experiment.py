
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services import database


class ExperimentTests(unittest.TestCase):

    def setUp(self):
        # Для каждого теста создаём отдельную временную БД.
        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_patch = patch.object(
            database,
            "DB_PATH",
            Path(self.temp_dir.name) / "test_taigoair.db"
        )
        self.db_patch.start()
        database.init_db()

        self.home = {
            "address": "Тестовая квартира"
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
                    "co2": 788.6,
                    "pm25": 11.69,
                    "temperature": 20.66
                },
                {
                    "minutes": 10,
                    "co2": 736.6,
                    "pm25": 11.43,
                    "temperature": 18.26
                }
            ]
        }

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def start(self):
        return database.start_experiment(
            self.home,
            self.sensors,
            self.forecast
        )

    def test_start_experiment(self):
        experiment_id = self.start()

        experiment = database.get_experiment(experiment_id)

        self.assertEqual(experiment["status"], "running")
        self.assertEqual(experiment["initial_co2"], 850)
        self.assertEqual(experiment["initial_pm25"], 12)
        self.assertIsNone(experiment["ended_at"])

    def test_forecast_saved_correctly(self):
        experiment_id = self.start()
        experiment = database.get_experiment(experiment_id)

        saved = json.loads(
            experiment["predicted_results_json"]
        )

        self.assertEqual(saved, self.forecast["results"])

    def test_second_active_experiment_forbidden(self):
        self.start()

        with self.assertRaises(ValueError):
            self.start()

    def test_finish_experiment(self):
        experiment_id = self.start()

        final_sensors = {
            "co2": 700,
            "pm25": 11,
            "temperature_inside": 21
        }

        database.finish_experiment(
            experiment_id,
            final_sensors,
            10
        )

        experiment = database.get_experiment(experiment_id)

        self.assertEqual(experiment["status"], "completed")
        self.assertEqual(experiment["actual_minutes"], 10)
        self.assertEqual(experiment["final_co2"], 700)
        self.assertEqual(experiment["final_pm25"], 11)
        self.assertEqual(experiment["final_temperature"], 21)
        self.assertIsNotNone(experiment["ended_at"])

    def test_cannot_finish_twice(self):
        experiment_id = self.start()

        database.finish_experiment(
            experiment_id, self.sensors, 10
        )

        with self.assertRaises(ValueError):
            database.finish_experiment(
                experiment_id, self.sensors, 15
            )

    def test_unknown_experiment(self):
        self.assertIsNone(database.get_experiment(99999))

    def test_cannot_finish_unknown_experiment(self):
        with self.assertRaises(ValueError):
            database.finish_experiment(
                99999, self.sensors, 10
            )

    def test_history(self):
        first_id = self.start()

        database.finish_experiment(
            first_id, self.sensors, 10
        )

        second_id = self.start()
        history = database.get_experiments()

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["id"], second_id)
        self.assertEqual(history[1]["id"], first_id)

    def test_can_start_after_completion(self):
        first_id = self.start()

        database.finish_experiment(
            first_id, self.sensors, 10
        )

        second_id = self.start()

        self.assertNotEqual(first_id, second_id)
        self.assertEqual(
            database.get_experiment(second_id)["status"],
            "running"
        )


if __name__ == "__main__":
    unittest.main()
