
async function calculateForecast() {
    const status = document.getElementById("forecast-status");
    const table = document.getElementById("forecast-table");

    const ach = Number(
        document.getElementById("air-exchange").value
    );

    table.replaceChildren();

    if (!Number.isFinite(ach) || ach <= 0 || ach > 30) {
        status.textContent =
            "Укажи кратность воздухообмена от 0.1 до 30";
        return;
    }

    status.textContent = "Выполняется расчёт...";

    try {
        const response = await fetch(
            `/api/forecast?ach=${encodeURIComponent(ach)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Не удалось рассчитать прогноз"
            );
        }

        document.getElementById("room-volume").textContent =
            data.volume_m3;

        document.getElementById("air-flow").textContent =
            data.air_flow_m3_h;

        document.getElementById(
            "forecast-limitations"
        ).textContent = data.limitations;

        for (const result of data.results) {
            const row = document.createElement("tr");

            const values = [
                `${result.minutes} мин`,
                result.co2,
                result.pm25,
                result.temperature,
                result.heat_loss_wh
            ];

            for (const value of values) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            }

            table.appendChild(row);
        }


        const recommendation = data.recommendation;

        document.getElementById(
            "recommendation-decision"
        ).textContent = recommendation.decision;

        document.getElementById(
            "recommendation-time"
        ).textContent =
            recommendation.recommended_minutes === null
                ? "Не определено"
                : recommendation.recommended_minutes === 0
                    ? "Сейчас не рекомендуется"
                    : `${recommendation.recommended_minutes} мин`;

        document.getElementById(
            "recommendation-reason"
        ).textContent = recommendation.reason;

        const warningsList = document.getElementById(
            "recommendation-warnings"
        );

        warningsList.replaceChildren();

        if (recommendation.warnings.length === 0) {
            const item = document.createElement("li");
            item.textContent = "Дополнительных предупреждений нет";
            warningsList.appendChild(item);
        } else {
            for (const warning of recommendation.warnings) {
                const item = document.createElement("li");
                item.textContent = warning;
                warningsList.appendChild(item);
            }
        }


        status.textContent =
            "Сценарный прогноз рассчитан.";

    } catch (error) {
        status.textContent = error.message;
        console.error(error);
    }
}

document.getElementById(
    "calculate-forecast"
).addEventListener("click", calculateForecast);
