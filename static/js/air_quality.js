
function getAqiAssessment(aqi) {
    if (aqi == null) return "Нет данных";

    if (aqi <= 20) return "Хорошее";
    if (aqi <= 40) return "Удовлетворительное";
    if (aqi <= 60) return "Умеренное загрязнение";
    if (aqi <= 80) return "Плохое";
    if (aqi <= 100) return "Очень плохое";

    return "Крайне плохое";
}


async function updateAirQuality() {
    const status = document.getElementById("air-status");

    status.textContent = "Обновление...";

    try {
        const response = await fetch("/api/air-quality");

        if (!response.ok) {
            throw new Error("Ошибка API загрязнения");
        }

        const data = await response.json();

        const fields = {
            "air-location": data.location,
            "air-pm25": data.pm25,
            "air-pm10": data.pm10,
            "air-no2": data.no2,
            "air-so2": data.so2,
            "air-co": data.co,
            "air-o3": data.o3,
            "air-aqi": data.aqi,
            "air-time": data.timestamp
        };

        for (const [id, value] of Object.entries(fields)) {
            document.getElementById(id).textContent =
                value ?? "Нет данных";
        }

        document.getElementById(
            "air-assessment"
        ).textContent = getAqiAssessment(data.aqi);

        status.textContent = "Данные получены";

    } catch (error) {
        status.textContent = "Ошибка получения данных";

        const ids = [
            "air-location", "air-pm25", "air-pm10",
            "air-no2", "air-so2", "air-co",
            "air-o3", "air-aqi", "air-time",
            "air-assessment"
        ];

        for (const id of ids) {
            document.getElementById(id).textContent =
                "Нет данных";
        }

        console.error(error);
    }
}

updateAirQuality();

// Обновляем раз в 30 минут
setInterval(updateAirQuality, 1800000);
