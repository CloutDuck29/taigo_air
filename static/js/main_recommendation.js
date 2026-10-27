
function renderMainOutdoorContext(context) {
    const details = document.getElementById(
        "main-outdoor-details"
    );

    const content = document.getElementById(
        "main-outdoor-content"
    );

    if (!details || !content) return;

    if (!context) {
        details.hidden = true;
        details.open = false;
        content.replaceChildren();
        return;
    }

    details.hidden = false;
    content.replaceChildren();

    const addRow = (label, value) => {
        const row = document.createElement("div");
        row.className = "main-outdoor-row";

        const name = document.createElement("span");
        name.textContent = label;

        const result = document.createElement("strong");
        result.textContent = value;

        row.append(name, result);
        content.appendChild(row);
    };

    const formatNumber = (value, digits = 0) =>
        value == null || !Number.isFinite(Number(value))
            ? "—"
            : Number(value).toLocaleString("ru-RU", {
                maximumFractionDigits: digits
            });

    addRow(
        "PM2.5 снаружи",
        `${formatNumber(context.pm25, 1)} мкг/м³`
    );

    addRow(
        "EU AQI",
        formatNumber(context.aqi)
    );

    addRow(
        "Предприятия по ветру",
        context.industry_status === "ok"
            ? String(context.industry_count ?? 0)
            : "Нет данных"
    );

    if (context.pm25_comparison === "higher") {
        addRow(
            "Сравнение PM2.5",
            "Снаружи выше"
        );
    } else if (
        context.pm25_comparison === "not_higher"
    ) {
        addRow(
            "Сравнение PM2.5",
            "Снаружи не выше"
        );
    }

    const note = document.createElement("p");
    note.className = "main-outdoor-note";
    note.textContent =
        "Промышленный перенос определяется по ветру. " +
        "Это не измерение загрязнения у дома.";

    content.appendChild(note);
}


async function loadMainRecommendation() {
    const modeElement = document.getElementById(
        "main-window-mode"
    );

    const decisionElement = document.getElementById(
        "main-recommendation-decision"
    );

    const timeElement = document.getElementById(
        "main-recommendation-time"
    );

    const reasonElement = document.getElementById(
        "main-recommendation-reason"
    );

    if (!modeElement || !decisionElement ||
        !timeElement || !reasonElement) {
        return;
    }

    try {
        const response = await fetch(
            "/api/forecast/scenarios"
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Не удалось получить прогноз"
            );
        }
        renderMainOutdoorContext(
    data.status === "closed"
        ? null
        : data.outdoor_context
);

        modeElement.textContent =
            data.window_label ||
            (data.status === "closed" ? "Закрыто" : "—");


if (data.status === "closed") {
    const recommendation = data.recommendation;

    decisionElement.textContent =
        recommendation?.decision || "Окно закрыто";

    timeElement.textContent =
        recommendation?.recommended_minutes != null
            ? `${recommendation.recommended_minutes} мин`
            : "Не определено";

    reasonElement.textContent =
        recommendation?.reason ||
        "Выбери режим проветривания для расчёта.";

    return;
}


        const recommendation = data.recommendation;

        decisionElement.textContent =
            recommendation.decision;

        if (recommendation.recommended_minutes != null) {
            timeElement.textContent =
                `${recommendation.recommended_minutes} мин`;
        } else if (recommendation.possible_minutes != null) {
            timeElement.textContent =
                `${recommendation.possible_minutes} мин (условно)`;
        } else {
            timeElement.textContent = "Не определено";
        }

        reasonElement.textContent =
            recommendation.reason;

} catch (error) {
    renderMainOutdoorContext(null);
    modeElement.textContent = "—";
        decisionElement.textContent =
            "Прогноз недоступен";
        timeElement.textContent = "—";
        reasonElement.textContent = error.message;
    }
}

loadMainRecommendation();

setInterval(() => {
    if (!document.hidden) {
        loadMainRecommendation();
    }
}, 60000);

document.addEventListener(
    "visibilitychange",
    () => {
        if (!document.hidden) {
            loadMainRecommendation();
        }
    }
);

// Обновляем рекомендацию сразу после смены режима окна.
document.addEventListener(
    "change",
    (event) => {
        if (event.target.id === "window-mode") {
            setTimeout(loadMainRecommendation, 500);
        }
    }
);


async function updateWindowSensorStatus() {
    const sensorElement = document.getElementById(
        "main-window-sensor"
    );

    const warningElement = document.getElementById(
        "main-window-warning"
    );

    if (!sensorElement || !warningElement) return;

    try {
        const [sensorResponse, modeResponse] =
            await Promise.all([
                fetch("/api/sensors"),
                fetch("/api/window-mode")
            ]);

        if (!sensorResponse.ok || !modeResponse.ok) {
            throw new Error("Данные недоступны");
        }

        const sensors = await sensorResponse.json();
        const mode = await modeResponse.json();

        if (typeof sensors.window_open !== "boolean") {
            throw new Error("Нет состояния датчика окна");
        }

        const actualOpen = sensors.window_open;
        const selectedMode = mode.window_mode;

const modeElement = document.getElementById(
    "main-window-mode"
);

if (modeElement) {
    const modeLabels = {
        closed: "Закрыто",
        micro: "Микропроветривание",
        tilt: "Откинуто",
        open: "Распахнуто"
    };

    modeElement.textContent =
        modeLabels[selectedMode] || "Неизвестно";
}

        sensorElement.textContent =
            actualOpen ? "Открыто" : "Закрыто";

        if (selectedMode === "closed" && actualOpen) {
            warningElement.textContent =
                "Датчик показывает открытое окно, " +
                "но выбран сценарий «Закрыто». " +
                "Уточни режим проветривания.";
        } else if (
            selectedMode !== "closed" && !actualOpen
        ) {
            warningElement.textContent =
                "Окно по датчику закрыто. " +
                "Прогноз показывает, что может " +
                "произойти после его открытия.";
        } else {
            warningElement.textContent =
                "Состояние датчика соответствует " +
                "выбранному сценарию.";
        }

    } catch (error) {
        sensorElement.textContent = "Нет данных";
        warningElement.textContent = error.message;
    }
}

updateWindowSensorStatus();

setInterval(updateWindowSensorStatus, 5000);

document.addEventListener("change", (event) => {
    if (event.target.id === "window-mode") {
        setTimeout(updateWindowSensorStatus, 700);
    }
});
