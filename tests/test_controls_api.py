
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import app
from services import database


class ControlsApiTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(
            database,
            "DB_PATH",
            Path(self.temp_dir.name) / "controls_test.db"
        )
        self.db_patch.start()
        database.init_db()

        database.save_home({
            "address": "Тестовая квартира",
            "latitude": 54.99,
            "longitude": 73.37,
            "floor": 5,
            "window_direction": "N",
            "room_area": 20,
            "ceiling_height": 2.8
        })

        self.client = app.test_client()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_get_window_mode(self):
        response = self.client.get("/api/window-mode")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["window_mode"], "closed"
        )

    def test_set_window_mode(self):
        response = self.client.post(
            "/api/window-mode",
            json={"window_mode": "tilt"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            database.get_home()["window_mode"], "tilt"
        )

    def test_invalid_window_mode(self):
        response = self.client.post(
            "/api/window-mode",
            json={"window_mode": "invalid"}
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_simulation_co2(self):
        response = self.client.post(
            "/api/simulation",
            json={"co2": -100}
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_simulation_window(self):
        response = self.client.post(
            "/api/simulation",
            json={"window_open": "yes"}
        )
        self.assertEqual(response.status_code, 400)

    def test_valid_simulation(self):
        with patch("main.update_sensor_data") as update, \
             patch("main.save_measurement"):

            update.return_value = {
                "co2": 900,
                "window_open": True
            }

            response = self.client.post(
                "/api/simulation",
                json={
                    "co2": 900,
                    "window_open": True
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["co2"], 900
        )
        update.assert_called_once()


if __name__ == "__main__":
    unittest.main()
