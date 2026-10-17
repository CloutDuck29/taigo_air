import csv
import io
import json
from flask import Response
from services.industry import get_industrial_sources
import requests
from flask import Flask, render_template, jsonify, request
from services.geocoding import get_address
from services.dispersion import calculate_plume
from services.weather import get_weather
from services.wind_analysis import analyze_wind
from services.air_quality import get_air_quality
from services.forecast import forecast_ventilation
from services.recommendations import get_recommendation
from services.sensors import get_sensor_data, update_sensor_data
from services.database import (
    init_db,
    save_measurement,
    get_measurements,
    get_home,
    save_home,
    save_forecast_run,
    get_forecast_runs,
    get_settings,
    save_settings
)

app = Flask(__name__)
init_db()


@app.route("/forecast/history")
def forecast_history():
    runs = get_forecast_runs(limit=100)

    return render_template(
        "forecast_history.html",
        runs=runs
    )


@app.route("/forecast/export")
def forecast_export():
    runs = get_forecast_runs(limit=10000)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "ID",
        "Дата",
        "Адрес",
        "Режим",
        "CO2 внутри (ppm)",
        "PM2.5 снаружи (мкг/м3)",
        "Температура внутри (C)",
        "Температура снаружи (C)",
        "Воздухообмен (1/ч)",
        "Решение",
        "Рекомендуемое время (мин)",
        "Причина",
        "Сценарий (мин)",
        "Прогноз CO2 (ppm)",
        "Прогноз PM2.5 (мкг/м3)",
        "Прогноз температуры (C)",
        "Энергия воздухообмена (Втч)"
    ])

    for run in reversed(runs):
        results = json.loads(run["results_json"])

        for result in results:
            writer.writerow([
                run["id"],
                run["created_at"],
                run["address"],
                run["input_mode"],
                run["indoor_co2"],
                run["outdoor_pm25"],
                run["indoor_temperature"],
                run["outdoor_temperature"],
                run["air_changes_per_hour"],
                run["recommendation"],
                run["recommended_minutes"],
                run["reason"],
                result.get("minutes"),
                result.get("co2"),
                result.get("pm25"),
                result.get("temperature"),
                result.get("heat_loss_wh")
            ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=taigoair_forecasts.csv"
        }
    )


@app.route("/api/forecast")
def forecast_api():
    home = get_home()
    settings = get_settings()
    if not home or not home["room_area"] or not home["ceiling_height"]:
        return jsonify({
            "error": "Сначала укажи площадь и высоту комнаты"
        }), 400

    sensors = get_sensor_data()
    air = get_air_quality()
    weather = get_weather()

    if air.get("status") != "ok":
        return jsonify({
            "error": "Наружное загрязнение недоступно"
        }), 503

    if weather.get("status") != "ok":
        return jsonify({
            "error": "Погодные данные недоступны"
        }), 503

    try:
        ach = float(request.args.get(
            "ach", settings["air_changes_per_hour"]
        ))
        required = [
            sensors.get("co2"),
            sensors.get("pm25"),
            sensors.get("temperature_inside"),
            air.get("pm25"),
            weather.get("temperature")
        ]

        if any(value is None for value in required):
            return jsonify({
                "error": "Недостаточно данных для прогноза"
            }), 422

        forecast = forecast_ventilation(
            indoor_co2=float(sensors["co2"]),
            indoor_pm25=float(sensors["pm25"]),
            indoor_temperature=float(
                sensors["temperature_inside"]
            ),
            outdoor_pm25=float(air["pm25"]),
            outdoor_temperature=float(
                weather["temperature"]
            ),
            room_area=float(home["room_area"]),
            ceiling_height=float(home["ceiling_height"]),
            air_changes_per_hour=ach,
            outdoor_co2=settings["outdoor_co2"]
        )

        forecast["input_sources"] = {
            "indoor": sensors.get("mode"),
            "outdoor_pm25": "Open-Meteo Air Quality",
            "outdoor_temperature": "Open-Meteo Weather",
            "outdoor_co2": "Assumed 420 ppm"
        }


        recommendation = get_recommendation(
            forecast=forecast,
            indoor_co2=float(sensors["co2"]),
            indoor_pm25=float(sensors["pm25"]),
            indoor_temperature=float(
                sensors["temperature_inside"]
            ),
            outdoor_pm25=float(air["pm25"]),
            settings=settings

        )

        forecast["recommendation"] = recommendation

        run_id = save_forecast_run(
            home=home,
            sensors=sensors,
            air=air,
            weather=weather,
            forecast=forecast
        )

        forecast["run_id"] = run_id

        return jsonify(forecast)

    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400


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


@app.route("/map")
def map_page():
    return render_template("map.html", home=get_home())



@app.route("/api/map/home", methods=["POST"])
def save_map_home():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Неверные данные"}), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Некорректные координаты"}), 400

    if not (
        54.5 <= latitude <= 55.5
        and 72.5 <= longitude <= 74.5
    ):
        return jsonify({
            "error": "Выбери точку в Омске или окрестностях"
        }), 400

    home = get_home()

    if home is None:
        return jsonify({
            "error": "Сначала заполни страницу «Мой дом»"
        }), 400

    address = get_address(latitude, longitude)

    # Не оставляем старый адрес для новой точки
    if not address:
        address = (
            f"Точка на карте: "
            f"{latitude:.6f}, {longitude:.6f}"
        )

    save_home({
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "floor": home["floor"],
        "window_direction": home["window_direction"],
        "room_area": home["room_area"],
        "ceiling_height": home["ceiling_height"]
    })

    return jsonify({
        "status": "ok",
        "address": address,
        "latitude": latitude,
        "longitude": longitude
    })



@app.route("/api/industry")
def industry_api():
    home = get_home()

    if (
        not home
        or home["latitude"] is None
        or home["longitude"] is None
    ):
        return jsonify({
            "error": "Сначала выбери дом на карте"
        }), 400

    try:
        sources = get_industrial_sources(
            home["latitude"],
            home["longitude"]
        )

        weather = get_weather()
        wind = None

        if weather.get("status") == "ok":
            direction = weather.get("wind_direction")
            speed = weather.get("wind_speed")

            if direction is not None and speed is not None:
                wind = {
                    "direction": direction,
                    "speed": speed,
                    "time": weather.get("timestamp")
                }

                for source in sources:
                    source["wind_analysis"] = analyze_wind(
                        source, home, direction, speed
                    )

        return jsonify({
            "status": "ok",
            "sources": sources,
            "count": len(sources),
            "wind": wind
        })

    except (OSError, ValueError, KeyError):
        app.logger.exception("Ошибка анализа предприятий")
        return jsonify({
            "error": "Не удалось выполнить анализ"
        }), 500



@app.route("/api/plume")
def plume_api():
    import math

    home = get_home()

    if (
        not home
        or home["latitude"] is None
        or home["longitude"] is None
    ):
        return jsonify({
            "error": "Сначала выбери дом на карте"
        }), 400

    try:
        emission_rate = float(
            request.args.get("emission", 1.0)
        )
        effective_height = float(
            request.args.get("height", 30.0)
        )

        if (
            not math.isfinite(emission_rate)
            or not 0.01 <= emission_rate <= 100
        ):
            raise ValueError("Выброс: от 0.01 до 100 г/с")

        if (
            not math.isfinite(effective_height)
            or not 1 <= effective_height <= 300
        ):
            raise ValueError("Высота: от 1 до 300 м")

    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

    weather = get_weather()

    if weather.get("status") != "ok":
        return jsonify({
            "error": "Погода недоступна"
        }), 503

    direction = weather.get("wind_direction")
    speed = weather.get("wind_speed")

    if direction is None or speed is None:
        return jsonify({
            "error": "Нет данных о ветре"
        }), 503

    if speed < 0.5:
        return jsonify({
            "error": "При слабом ветре модель неприменима"
        }), 422

    sources = get_industrial_sources(
        home["latitude"],
        home["longitude"]
    )

    results = [
        calculate_plume(
            source=source,
            home=home,
            wind_direction=direction,
            wind_speed=speed,
            emission_rate=emission_rate,
            effective_height=effective_height
        )
        for source in sources
    ]

    return jsonify({
        "status": "ok",
        "results": results,
        "sources": sources,
        "wind_direction": direction,
        "wind_speed": speed,
        "wind_time": weather.get("timestamp"),
        "emission_rate_g_s": emission_rate,
        "effective_height_m": effective_height,
        "model": "Учебная гауссова модель",
        "disclaimer": (
            "Используются условные параметры выброса. "
            "Это не реальная карта загрязнения."
        )
    })



@app.route("/forecast")
def forecast_page():
    return render_template(
        "forecast.html",
        settings=get_settings()
    )



@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    error = None
    saved = False

    if request.method == "POST":
        try:
            values = {
                "co2_target": float(
                    request.form["co2_target"]
                ),
                "co2_preferred": float(
                    request.form["co2_preferred"]
                ),
                "pm25_limit": float(
                    request.form["pm25_limit"]
                ),
                "max_temperature_drop": float(
                    request.form["max_temperature_drop"]
                ),
                "outdoor_co2": float(
                    request.form["outdoor_co2"]
                ),
                "air_changes_per_hour": float(
                    request.form["air_changes_per_hour"]
                )
            }

            import math

            if not all(math.isfinite(v) for v in values.values()):
                raise ValueError("Все значения должны быть конечными")

            if not 400 <= values["co2_target"] <= 5000:
                raise ValueError("Порог CO₂: от 400 до 5000 ppm")

            if not 350 <= values["co2_preferred"] <= values["co2_target"]:
                raise ValueError(
                    "Предпочтительный CO₂ должен быть "
                    "не выше порогового"
                )

            if not 1 <= values["pm25_limit"] <= 500:
                raise ValueError("PM2.5: от 1 до 500 мкг/м³")

            if not 0 <= values["max_temperature_drop"] <= 15:
                raise ValueError("Охлаждение: от 0 до 15 °C")

            if not 300 <= values["outdoor_co2"] <= 2000:
                raise ValueError("Наружный CO₂: от 300 до 2000 ppm")

            if not 0.1 <= values["air_changes_per_hour"] <= 30:
                raise ValueError("Воздухообмен: от 0,1 до 30 ч⁻¹")

            save_settings(values)
            saved = True

        except (ValueError, KeyError) as exc:
            error = str(exc)

    return render_template(
        "settings.html",
        settings=get_settings(),
        saved=saved,
        error=error
    )



@app.route("/api/map/apartment", methods=["POST"])
def save_map_apartment():
    import math

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Некорректные данные"}), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        floor = int(data["floor"])
        room_area = float(data["room_area"])
        ceiling_height = float(data["ceiling_height"])
        direction = data["window_direction"]

        if not all(math.isfinite(v) for v in [
            latitude, longitude, room_area, ceiling_height
        ]):
            raise ValueError("Некорректные числовые данные")

        if not (54.5 <= latitude <= 55.5
                and 72.5 <= longitude <= 74.5):
            raise ValueError(
                "Выбери дом в Омске или окрестностях"
            )

        if not 1 <= floor <= 100:
            raise ValueError("Этаж должен быть от 1 до 100")

        if not 0 < room_area <= 1000:
            raise ValueError("Неверная площадь комнаты")

        if not 1.5 <= ceiling_height <= 10:
            raise ValueError("Неверная высота потолка")

        if direction not in {
            "N", "NE", "E", "SE",
            "S", "SW", "W", "NW"
        }:
            raise ValueError("Неверное направление окна")

    except (KeyError, ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

    # Определяем адрес только после проверки параметров
    old_home = get_home()

    same_point = (
        old_home is not None
        and old_home["latitude"] is not None
        and old_home["longitude"] is not None
        and abs(old_home["latitude"] - latitude) < 0.000001
        and abs(old_home["longitude"] - longitude) < 0.000001
    )

    if same_point:
        address = old_home["address"]
    else:
        address = get_address(latitude, longitude)

    if not address:
        address = (
            f"Точка на карте: "
            f"{latitude:.6f}, {longitude:.6f}"
        )

    save_home({
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "floor": floor,
        "window_direction": direction,
        "room_area": room_area,
        "ceiling_height": ceiling_height
    })

    return jsonify({
        "status": "ok",
        "message": "Квартира сохранена",
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "floor": floor,
        "window_direction": direction,
        "room_area": room_area,
        "ceiling_height": ceiling_height
    })



if __name__ == "__main__":
    app.run(debug=True, port=5000)
