
async function updateWeather() {
    const status = document.getElementById(
        "weather-status"
    );

    status.textContent = "Обновление...";

    try {
        const response = await fetch("/api/weather");

        if (!response.ok) {
            throw new Error("Сервер погоды недоступен");
        }

        const data = await response.json();

        const fields = {
            "weather-location": data.location,
            "weather-temperature": data.temperature,
            "weather-humidity": data.humidity,
            "weather-pressure": data.pressure,
            "weather-wind-speed": data.wind_speed,
            "weather-wind-direction": data.wind_direction,
            "weather-time": data.timestamp
        };

        for (const [id, value] of Object.entries(fields)) {
            document.getElementById(id).textContent =
                value ?? "Нет данных";
        }

        status.textContent = "Данные получены";

    } catch (error) {
        status.textContent = "Ошибка получения погоды";
        console.error(error);
    }
}

updateWeather();

// Проверяем погоду раз в 10 минут
setInterval(updateWeather, 600000);
