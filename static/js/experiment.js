
const startButton = document.getElementById(
    "start-experiment"
);

const finishButton = document.getElementById(
    "finish-experiment"
);

const statusElement = document.getElementById(
    "experiment-status"
);

const idElement = document.getElementById(
    "experiment-id"
);

const resultElement = document.getElementById(
    "experiment-result"
);

let activeExperimentId = null;
let requestInProgress = false;


async function restoreActiveExperiment() {
    startButton.disabled = true;
    finishButton.disabled = true;
    statusElement.textContent =
        "Проверяем активный эксперимент...";

    try {
        const response = await fetch("/api/experiment/active");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Ошибка загрузки эксперимента"
            );
        }

        if (data.experiment) {
            activeExperimentId = data.experiment.id;

            idElement.textContent = activeExperimentId;
            startButton.disabled = true;
            finishButton.disabled = false;

            statusElement.textContent =
                "Активный эксперимент восстановлен.";

            resultElement.textContent =
                "Эксперимент продолжается. " +
                "После изменения показаний нажми «Завершить».";
        } else {
            activeExperimentId = null;
            startButton.disabled = false;
            finishButton.disabled = true;

            statusElement.textContent =
                "Активных экспериментов нет.";
        }

    } catch (error) {
        statusElement.textContent =
            "Не удалось проверить эксперимент: " +
            error.message;
    }
}

restoreActiveExperiment();


startButton.addEventListener("click", async () => {
    if (requestInProgress || activeExperimentId !== null) {
        return;
    }

    requestInProgress = true;
    startButton.disabled = true;
    statusElement.textContent = "Запускаем эксперимент...";

    try {
        const response = await fetch(
            "/api/experiment/start",
            { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Не удалось начать эксперимент"
            );
        }

        activeExperimentId = data.experiment_id;
        idElement.textContent = activeExperimentId;

        finishButton.disabled = false;
        resultElement.textContent =
            "Эксперимент выполняется.";

        statusElement.textContent =
            "Эксперимент начат. Измени показания симулятора.";

    } catch (error) {
        statusElement.textContent = error.message;
        startButton.disabled = false;
    } finally {
        requestInProgress = false;
    }
});

finishButton.addEventListener("click", async () => {
    if (requestInProgress || activeExperimentId === null) {
        return;
    }

    const minutes = Number(
        document.getElementById("actual-minutes").value
    );

    if (!Number.isFinite(minutes) ||
        minutes <= 0 || minutes > 120) {
        statusElement.textContent =
            "Укажи длительность от 0.1 до 120 минут.";
        return;
    }

    requestInProgress = true;
    finishButton.disabled = true;
    statusElement.textContent = "Завершаем эксперимент...";

    try {
        const response = await fetch(
            "/api/experiment/finish",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    experiment_id: activeExperimentId,
                    actual_minutes: minutes
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Не удалось завершить эксперимент"
            );
        }

        statusElement.textContent =
            "Эксперимент завершён и сохранён в SQLite.";


resultElement.textContent =
    `Эксперимент №${activeExperimentId} завершён. ` +
    `Продолжительность: ${minutes} мин.`;

const completedId = activeExperimentId;

activeExperimentId = null;
startButton.disabled = false;

// Получаем сравнение из SQLite
const comparisonStatus = document.getElementById(
    "comparison-status"
);
const comparisonTable = document.getElementById(
    "comparison-table"
);

comparisonTable.replaceChildren();
comparisonStatus.textContent = "Загрузка результатов...";

try {
    const resultResponse = await fetch(
        `/api/experiment/results/${completedId}`
    );

    const resultData = await resultResponse.json();

    if (!resultResponse.ok) {
        throw new Error(
            resultData.error || "Ошибка получения результатов"
        );
    }

    if (resultData.status === "no_comparison") {
        comparisonStatus.textContent = resultData.message;
    } else {
        for (const item of resultData.comparison) {
            const row = document.createElement("tr");

            const values = [
                item.name,
                `${item.predicted} ${item.unit}`,
                `${item.actual} ${item.unit}`,
                `${item.error} ${item.unit}`
            ];

            for (const value of values) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            }

            comparisonTable.appendChild(row);
        }

        comparisonStatus.textContent =
            resultData.input_mode === "simulation"
                ? "Сравнение выполнено на данных симулятора."
                : "Сравнение выполнено.";
    }

} catch (error) {
    comparisonStatus.textContent =
        "Эксперимент сохранён, но сравнение не загружено: " +
        error.message;
}


    } catch (error) {
        statusElement.textContent = error.message;
        finishButton.disabled = false;
    } finally {
        requestInProgress = false;
    }
});
