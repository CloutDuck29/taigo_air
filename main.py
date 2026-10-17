
from flask import Flask, render_template, jsonify, request
from services.weather import get_weather
from services.air_quality import get_air_quality
from services.sensors import get_sensor_data, update_sensor_data
from services.database import (
    init_db,
    save_measurement,
    get_measurements,
    get_home,
    save_home
)

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sensors")
def sensors_api():
    return jsonify(get_sensor_data())


@app.route("/api/simulation", methods=["POST"])
def simulation_api():
    values = request.get_json(silent=True)

    if not isinstance(values, dict):
        return jsonify({"error": "Некорректные данные"}), 400

    allowed_ranges = {
        "co2": (0, 10000),
        "pm25": (0, 1000),
        "temperature_inside": (-30, 60)
    }

    for field, (minimum, maximum) in allowed_ranges.items():
        if field in values:
            value = values[field]

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not minimum <= value <= maximum
            ):
                return jsonify({
                    "error": f"Недопустимое значение {field}"
                }), 400

    if "window_open" in values:
        if not isinstance(values["window_open"], bool):
            return jsonify({
                "error": "Некорректное состояние окна"
            }), 400

    data = update_sensor_data(values)
    save_measurement(data)

    return jsonify(data)


@app.route("/history")
def history():
    measurements = get_measurements()
    return render_template(
        "history.html",
        measurements=measurements
    )


@app.route("/home", methods=["GET", "POST"])
def home():
    error = None
    saved = False

    if request.method == "POST":
        try:
            address = request.form.get("address", "").strip()
            floor = int(request.form["floor"])
            room_area = float(request.form["room_area"])
            ceiling_height = float(request.form["ceiling_height"])

            direction = request.form["window_direction"]

            latitude_text = request.form.get(
                "latitude", ""
            ).strip()

            longitude_text = request.form.get(
                "longitude", ""
            ).strip()

            latitude = (
                float(latitude_text) if latitude_text else None
            )
            longitude = (
                float(longitude_text) if longitude_text else None
            )

            allowed_directions = {
                "N", "NE", "E", "SE",
                "S", "SW", "W", "NW"
            }

            if not address:
                raise ValueError("Укажи адрес")

            if floor < 1 or floor > 100:
                raise ValueError("Некорректный этаж")

            if not 0 < room_area <= 1000:
                raise ValueError("Некорректная площадь")

            if not 1.5 <= ceiling_height <= 10:
                raise ValueError("Некорректная высота потолка")

            if direction not in allowed_directions:
                raise ValueError("Некорректное направление окна")

            if latitude is not None and not -90 <= latitude <= 90:
                raise ValueError("Некорректная широта")

            if longitude is not None and not -180 <= longitude <= 180:
                raise ValueError("Некорректная долгота")

            save_home({
                "address": address,
                "floor": floor,
                "window_direction": direction,
                "room_area": room_area,
                "ceiling_height": ceiling_height,
                "latitude": latitude,
                "longitude": longitude
            })

            saved = True

        except (ValueError, KeyError) as exc:
            error = str(exc)

    return render_template(
        "home.html",
        home=get_home(),
        saved=saved,
        error=error
    )


@app.route("/api/weather")
def weather_api():
    weather = get_weather()

    if weather["status"] == "error":
        return jsonify(weather), 503

    return jsonify(weather)


@app.route("/api/air-quality")
def air_quality_api():
    data = get_air_quality()

    if data["status"] == "error":
        return jsonify(data), 503

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
