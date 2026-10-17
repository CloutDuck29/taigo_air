async function updateSensors() {
    try {
        const response = await fetch("/api/sensors");

        if (!response.ok) {
            throw new Error("Ошибка получения данных");
        }

        const data = await response.json();

        document.getElementById("co2").textContent =
            data.co2 ?? "Нет данных";

        document.getElementById("pm1").textContent =
            data.pm1 ?? "Нет данных";

        document.getElementById("pm25").textContent =
            data.pm25 ?? "Нет данных";

        document.getElementById("pm10").textContent =
            data.pm10 ?? "Нет данных";

        document.getElementById("temp-inside").textContent =
            data.temperature_inside ?? "Нет данных";

        document.getElementById("temp-outside").textContent =
            data.temperature_outside ?? "Нет данных";

        document.getElementById("humidity-inside").textContent =
            data.humidity_inside ?? "Нет данных";

        document.getElementById("humidity-outside").textContent =
            data.humidity_outside ?? "Нет данных";

        document.getElementById("pressure-inside").textContent =
            data.pressure_inside ?? "Нет данных";

        document.getElementById("pressure-outside").textContent =
            data.pressure_outside ?? "Нет данных";

        document.getElementById("window").textContent =
            data.window_open ? "Открыто" : "Закрыто";

        document.getElementById("fan").textContent =
            data.fan_on ? "Включён" : "Выключен";

        document.getElementById("updated").textContent =
            data.timestamp ?? "Нет данных";

        document.getElementById("mode").textContent =
            data.mode === "simulation"
                ? "Тестовые данные"
                : "Реальные измерения";

        const warnings = [];

        if (data.co2 !== null && data.co2 > 1000) {
            warnings.push("Повышенный CO₂");
        }

        if (data.pm25 !== null && data.pm25 > 35) {
            warnings.push("Повышенный PM2.5");
        }

        document.getElementById("warnings").textContent =
            warnings.length
                ? warnings.join("; ")
                : "Предупреждений нет";

        document.getElementById("connection").textContent =
            data.mode === "simulation"
                ? "Arduino не подключена (симуляция)"
                : "Режим реальных измерений";

    } catch (error) {
        document.getElementById("connection").textContent =
            "Ошибка связи с сервером";
        console.error(error);
    }
}

updateSensors();
setInterval(updateSensors, 5000);


const simulationForm = document.getElementById(
    "simulation-form"
);

simulationForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const values = {
        co2: Number(
            document.getElementById("sim-co2").value
        ),
        pm25: Number(
            document.getElementById("sim-pm25").value
        ),
        temperature_inside: Number(
            document.getElementById("sim-temperature").value
        ),
        window_open: document.getElementById(
            "sim-window"
        ).checked
    };

    try {
        const response = await fetch("/api/simulation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(values)
        });

        if (!response.ok) {
            throw new Error("Не удалось обновить данные");
        }

        document.getElementById(
            "simulation-result"
        ).textContent = "Показания обновлены";

        await updateSensors();

    } catch (error) {
        document.getElementById(
            "simulation-result"
        ).textContent = "Ошибка: " + error.message;
    }
});
