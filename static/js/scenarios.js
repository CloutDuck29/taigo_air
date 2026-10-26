
"use strict";

const scenarioStatus = document.getElementById("scenario-status");
const scenarioTable = document.getElementById("scenario-table");

let scenarioInProgress = false;

function setScenarioText(id, value) {
    document.getElementById(id).textContent = value;
}

function clearScenarios() {
    scenarioTable.replaceChildren();

    setScenarioText("scenario-decision", "—");
    setScenarioText("scenario-time", "—");
    setScenarioText(
        "scenario-reason",
        "Ожидание расчёта."
    );
}

function addScenarioRow(scenario, result) {
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
        cell.textContent = value ?? "—";
        row.appendChild(cell);
    }

    scenarioTable.appendChild(row);
}

async function loadScenarios() {
    if (scenarioInProgress) {
        return;
    }

    scenarioInProgress = true;
    scenarioStatus.textContent = "Расчёт сценариев...";

    try {
        const response = await fetch(
            "/api/forecast/scenarios",
            { cache: "no-store" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Ошибка расчёта сценариев"
            );
        }

        clearScenarios();

        if (data.status === "closed") {
            scenarioStatus.textContent =
                data.message || "Окно закрыто.";

            setScenarioText(
                "scenario-decision",
                "Окно закрыто"
            );

            setScenarioText("scenario-time", "—");

            setScenarioText(
                "scenario-reason",
                "Выбери режим проветривания на главной странице."
            );

            return;
        }

        if (
            !Array.isArray(data.scenarios) ||
            !data.recommendation
        ) {
            throw new Error("Получены неполные данные сценариев");
        }

        for (const scenario of data.scenarios) {
            for (const result of scenario.results || []) {
                addScenarioRow(scenario, result);
            }
        }

        const recommendation = data.recommendation;

        // Сокращаем только отображение длинного решения.
        const decision = recommendation.decision ===
            "Зависит от воздухообмена"
                ? "Зависит от условий"
                : recommendation.decision ?? "Не определено";

        setScenarioText(
            "scenario-decision",
            decision
        );

        let scenarioTime = "Не определено";

        if (recommendation.recommended_minutes != null) {
            scenarioTime =
                `${recommendation.recommended_minutes} мин`;

        } else if (recommendation.possible_minutes != null) {
            scenarioTime =
                `${recommendation.possible_minutes} мин (условно)`;
        }

        setScenarioText(
            "scenario-time",
            scenarioTime
        );

        setScenarioText(
            "scenario-reason",
            recommendation.reason ?? "Нет объяснения."
        );

        scenarioStatus.textContent =
            `Режим окна: ${data.window_label ?? "не определён"}. ` +
            "Сценарии рассчитаны автоматически.";

    } catch (error) {
        clearScenarios();

        scenarioStatus.textContent =
            error.message || "Ошибка расчёта сценариев.";

        console.error(error);

    } finally {
        scenarioInProgress = false;
    }
}

// Первоначальная загрузка.
loadScenarios();

// Автоматическое обновление раз в минуту.
setInterval(() => {
    if (!document.hidden) {
        loadScenarios();
    }
}, 60000);

// Обновление при возвращении на страницу.
document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
        loadScenarios();
    }
});
