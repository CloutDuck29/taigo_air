
const windowModeSelect = document.getElementById("window-mode");
const windowModeStatus = document.getElementById("window-mode-status");

async function loadWindowMode() {
    try {
        const response = await fetch("/api/window-mode");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Ошибка загрузки");
        }

        windowModeSelect.value = data.window_mode;
        windowModeStatus.textContent = "Режим загружен.";

    } catch (error) {
        windowModeStatus.textContent = error.message;
    }
}

windowModeSelect.addEventListener("change", async () => {
    windowModeSelect.disabled = true;
    windowModeStatus.textContent = "Сохранение...";

    try {
        const response = await fetch("/api/window-mode", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                window_mode: windowModeSelect.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Ошибка сохранения");
        }

        windowModeStatus.textContent = "Режим окна сохранён.";

    } catch (error) {
        windowModeStatus.textContent = error.message;
    } finally {
        windowModeSelect.disabled = false;
    }
});

loadWindowMode();
