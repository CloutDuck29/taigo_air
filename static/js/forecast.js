
"use strict";

const forecastStatus = document.getElementById("forecast-status");
const forecastTable = document.getElementById("forecast-table");
const airExchangeInput = document.getElementById("air-exchange");
const calculateButton = document.getElementById("calculate-forecast");

let forecastRequestId = 0;
let forecastController = null;

function setForecastText(id, value) {
    document.getElementById(id).textContent = value;
}

function clearForecastResults() {
    forecastTable.replaceChildren();

    setForecastText("room-volume", "—");
    setForecastText("air-flow", "—");

    setForecastText("recommendation-decision", "Нет расчёта");
    setForecastText("recommendation-time", "—");
    setForecastText(
        "recommendation-reason",
        "Укажи корректную кратность воздухообмена."
    );

    const warningsList = document.getElementById(
        "recommendation-warnings"
    );

    warningsList.replaceChildren();

    const item = document.createElement("li");
    item.textContent = "Нет актуального расчёта";
    warningsList.appendChild(item);

    setForecastText(
        "forecast-limitations",
        "Актуальный прогноз отсутствует."
    );
}

function addForecastRow(result) {
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
        cell.textContent = value ?? "—";
        row.appendChild(cell);
    }

    forecastTable.appendChild(row);
}

function showForecastRecommendation(recommendation) {
    setForecastText(
        "recommendation-decision",
        recommendation.decision ?? "Не определено"
    );

    let recommendedTime = "Не определено";

    if (recommendation.recommended_minutes === 0) {
        recommendedTime = "Сейчас не рекомендуется";
    } else if (recommendation.recommended_minutes != null) {
        recommendedTime =
            `${recommendation.recommended_minutes} мин`;
    }

    setForecastText(
        "recommendation-time",
        recommendedTime
    );

    setForecastText(
        "recommendation-reason",
        recommendation.reason ?? "Нет объяснения."
    );

    const warningsList = document.getElementById(
        "recommendation-warnings"
    );

    warningsList.replaceChildren();

    const warnings = Array.isArray(recommendation.warnings)
        ? recommendation.warnings
        : [];

    if (warnings.length === 0) {
        const item = document.createElement("li");

        item.textContent =
            "Дополнительных предупреждений нет";

        warningsList.appendChild(item);
        return;
    }

    for (const warning of warnings) {
        const item = document.createElement("li");
        item.textContent = warning;
        warningsList.appendChild(item);
    }
}

async function calculateForecast(save = false) {
    const requestId = ++forecastRequestId;

    // Отменяем предыдущий запрос при новом расчёте.
    if (forecastController) {
        forecastController.abort();
    }

    forecastController = null;

    const rawValue = airExchangeInput.value.trim().replace(",", ".");

    const ach = rawValue === ""
        ? NaN
        : Number(rawValue);

    clearForecastResults();

    if (
        !Number.isFinite(ach) ||
        ach < 0.1 ||
        ach > 30
    ) {
        forecastStatus.textContent =
            "Укажи кратность воздухообмена от 0,1 до 30.";

        return;
    }

    const controller = new AbortController();
    forecastController = controller;

    calculateButton.disabled = true;

    forecastStatus.textContent = save
        ? "Расчёт и сохранение прогноза..."
        : "Обновление прогноза...";

    try {
        const params = new URLSearchParams({
            ach: String(ach),
            save: save ? "1" : "0"
        });

        const response = await fetch(
            `/api/forecast?${params.toString()}`,
            {
                signal: controller.signal,
                cache: "no-store"
            }
        );

        const data = await response.json();

        // Не отображаем результат устаревшего запроса.
        if (requestId !== forecastRequestId) {
            return;
        }

        if (!response.ok) {
            throw new Error(
                data.error || "Не удалось рассчитать прогноз"
            );
        }

        if (
            !Array.isArray(data.results) ||
            !data.recommendation
        ) {
            throw new Error("Получены неполные данные прогноза");
        }

        setForecastText(
            "room-volume",
            data.volume_m3 ?? "—"
        );

        setForecastText(
            "air-flow",
            data.air_flow_m3_h ?? "—"
        );

        setForecastText(
            "forecast-limitations",
            data.limitations ??
            "Расчёт использует упрощённую модель."
        );

        for (const result of data.results) {
            addForecastRow(result);
        }

        showForecastRecommendation(data.recommendation);

        forecastStatus.textContent = save
            ? "Прогноз рассчитан и сохранён в историю."
            : "Прогноз автоматически обновлён.";

    } catch (error) {
        if (requestId !== forecastRequestId) {
            return;
        }

        if (error.name === "AbortError") {
            return;
        }

        clearForecastResults();

        forecastStatus.textContent =
            error.message || "Ошибка расчёта прогноза.";

        console.error(error);

    } finally {
        if (requestId === forecastRequestId) {
            forecastController = null;
            calculateButton.disabled = false;
        }
    }
}

// Ручной расчёт с сохранением в SQLite.
calculateButton.addEventListener("click", () => {
    console.log("Кнопка нажата");

    forecastStatus.textContent = "Кнопка нажата. Запускаю расчёт...";

    calculateForecast(true);
});

// Изменение значения запускает новый расчёт без сохранения.
airExchangeInput.addEventListener("change", () => {
    calculateForecast(false);
});

// При редактировании скрываем старую рекомендацию.
airExchangeInput.addEventListener("input", () => {
    forecastRequestId++;

    if (forecastController) {
        forecastController.abort();
        forecastController = null;
    }

    calculateButton.disabled = false;

    clearForecastResults();

    forecastStatus.textContent =
        "Значение изменено. Рассчитай прогноз.";
});

// Первый автоматический расчёт.
calculateForecast(false);

// Обновление каждые 60 секунд.
setInterval(() => {
    if (!document.hidden && !forecastController) {
        calculateForecast(false);
    }
}, 60000);

// Обновление после возвращения на страницу.
document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !forecastController) {
        calculateForecast(false);
    }
});
