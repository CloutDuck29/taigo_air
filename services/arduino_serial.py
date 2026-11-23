
import serial
import serial.tools.list_ports


def find_arduino():
    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        if (
            "usbmodem" in port.device.lower()
            or "usbserial" in port.device.lower()
            or "arduino" in port.description.lower()
        ):
            return port.device

    return None


def test_connection():
    port = find_arduino()

    if not port:
        print("Arduino не найдена")
        return

    print(f"Arduino найдена: {port}")

    try:
        with serial.Serial(
            port,
            baudrate=9600,
            timeout=2
        ) as arduino:

            print("Подключено. Читаем данные...")

            while True:
                line = arduino.readline().decode(
                    "utf-8",
                    errors="replace"
                ).strip()

                if line:
                    print(line)

    except serial.SerialException as error:
        print(f"Ошибка подключения: {error}")

    except KeyboardInterrupt:
        print("\nЧтение остановлено")


if __name__ == "__main__":
    test_connection()
