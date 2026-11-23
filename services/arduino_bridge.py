
import os
import threading
import time

import serial
import serial.tools.list_ports

_lock = threading.Lock()
_latest = None
_last_received = 0
_started = False
_connection = None

STALE_SECONDS = 10


def find_arduino():
    configured = os.getenv("TAIGOAIR_SERIAL_PORT")
    if configured:
        return configured

    for port in serial.tools.list_ports.comports():
        name = port.device.lower()
        if (
            "usbmodem" in name
            or "usbserial" in name
            or "arduino" in port.description.lower()
        ):
            return port.device

    return None


def parse_line(line, data):
    fields = {
        "CO2:": ("co2", float),
        "PM1.0:": ("pm1", int),
        "PM2.5:": ("pm25", int),
        "PM10:": ("pm10", int),
        "TEMPERATURE:": ("temperature_inside", float),
        "PRESSURE:": ("pressure_inside", float),
    }

    if line == "CO2: NO SIGNAL":
        data["co2"] = None
        return

    if line == "HUMIDITY: NOT SUPPORTED":
        data["humidity_inside"] = None
        return

    if line == "PMS5003: NO DATA":
        for key in ("pm1", "pm25", "pm10"):
            data[key] = None
        return

    if line == "CLIMATE SENSOR: NOT FOUND":
        data["temperature_inside"] = None
        data["pressure_inside"] = None
        return

    if line.startswith("WINDOW:"):
        state = line.split(":", 1)[1].strip()
        if state in ("OPEN", "CLOSED"):
            data["window_open"] = state == "OPEN"
        return


    if line.startswith("SERVO ANGLE:"):
        try:
            data["servo_angle"] = int(
                line.split(":", 1)[1].strip().split()[0]
            )
        except (ValueError, IndexError):
            pass
        return

    if line.startswith("SERVO TARGET:"):
        try:
            data["servo_target"] = int(
                line.split(":", 1)[1].strip().split()[0]
            )
        except (ValueError, IndexError):
            pass
        return

    if line.startswith("SERVO STATUS:"):
        status = line.split(":", 1)[1].strip()

        if status in ("MOVING", "IDLE"):
            data["servo_status"] = status

        return


    if line.startswith("FAN REQUEST:"):
        state = line.split(":", 1)[1].strip()
        if state in ("ON", "OFF"):
            data["fan_on"] = state == "ON"
        return

    for prefix, (key, convert) in fields.items():
        if line.startswith(prefix):
            try:
                value = convert(
                    line.split(":", 1)[1].strip().split()[0]
                )

                # Arduino передаёт гПа,
                # сайт использует мм рт. ст.
                if key == "pressure_inside":
                    value = round(value * 0.750061683, 1)

                if (
                    key == "temperature_inside"
                    and not -30 <= value <= 60
                ):
                    return

                if (
                    key == "pressure_inside"
                    and not 300 <= value <= 900
                ):
                    return

                data[key] = value
            except (ValueError, IndexError):
                pass
            return


def reader():
    global _latest, _last_received, _connection

    while True:
        port = find_arduino()

        if not port:
            print("TaigoAir: Arduino не найдена")
            time.sleep(3)
            continue

        try:
            print(f"TaigoAir: подключение к {port}")

            with serial.Serial(
                port,
                baudrate=9600,
                timeout=1,
                write_timeout=1
            ) as connection:

                with _lock:
                    _connection = connection
                    _latest = None

                frame = {}

                # При открытии порта Arduino может
                # перезапуститься — это нормально.
                time.sleep(2)
                connection.reset_input_buffer()

                while True:
                    line = connection.readline().decode(
                        "utf-8",
                        errors="replace"
                    ).strip()


                    if line == "===== TaigoAir =====":
                        frame = {}


                    elif line == "====================":

                        if "window_open" in frame:

                            with _lock:
                                _latest = frame.copy()

                                _last_received = time.monotonic()

                    elif line:
                        parse_line(line, frame)

        except (serial.SerialException, OSError) as error:
            print(f"TaigoAir: ошибка USB: {error}")
            time.sleep(3)

        finally:
            with _lock:
                _connection = None
                _latest = None
                _last_received = 0

def start_arduino_reader():
    global _started

    if _started:
        return

    _started = True

    threading.Thread(
        target=reader,
        daemon=True,
        name="taigoair-serial"
    ).start()


def get_hardware_data():
    with _lock:
        if _latest is None:
            return None

        if time.monotonic() - _last_received > STALE_SECONDS:
            return None

        return _latest.copy()


def send_arduino_command(command):
    allowed = {"WINDOW_OPEN", "WINDOW_CLOSE", "STATUS"}

    if command not in allowed:
        return False

    with _lock:
        connection = _connection

        if connection is None or not connection.is_open:
            return False

        try:
            connection.write(
                (command + "\n").encode("utf-8")
            )
            connection.flush()
            return True

        except (serial.SerialException, OSError):
            return False
