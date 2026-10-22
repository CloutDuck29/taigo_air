
const scenarioStatus = document.getElementById(
    "scenario-status"
);

const scenarioTable = document.getElementById(
    "scenario-table"
);

async function loadScenarios() {
    scenarioStatus.textContent = "Расчёт сценариев...";

    try {
        const response = await fetch(
            "/api/forecast/scenarios"
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Ошибка расчёта сценариев"
            );
        }

        scenarioTable.replaceChildren();


if (data.status === "closed") {
    scenarioStatus.textContent = data.message;

    document.getElementById(
        "scenario-decision"
    ).textContent = "Окно закрыто";

    document.getElementById(
        "scenario-time"
    ).textContent = "—";

    document.getElementById(
        "scenario-reason"
    ).textContent =
        "Выбери режим проветривания на главной странице.";

    return;
}


        for (const scenario of data.scenarios) {
            for (const result of scenario.results) {
                const row = document.createElement("tr");

                const values = [
                    `${scenario.label} (${scenario.ach} ч⁻¹)`,
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

                scenarioTable.appendChild(row);
            }
        }

const recommendation = data.recommendation;

document.getElementById(
    "scenario-decision"
).textContent = recommendation.decision;

document.getElementById(
    "scenario-time"
).textContent =
    recommendation.recommended_minutes !== null
        ? `${recommendation.recommended_minutes} мин`
        : recommendation.possible_minutes != null
            ? `${recommendation.possible_minutes} мин (условно)`
            : "Не определено";

document.getElementById(
    "scenario-reason"
).textContent = recommendation.reason;


        scenarioStatus.textContent =
            `Режим окна: ${data.window_label}. ` +
            "Сценарии рассчитаны автоматически.";

    } catch (error) {
        scenarioStatus.textContent = error.message;
        console.error(error);
    }
}

loadScenarios();

setInterval(() => {
    if (!document.hidden) {
        loadScenarios();
    }
}, 60000);
