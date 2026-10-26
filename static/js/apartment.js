
const apartmentForm = document.getElementById("apartment-form");
const apartmentStatus = document.getElementById("apartment-status");
const directionSelect = document.getElementById("apartment-direction");

const directionDegrees = {
    N: 0,
    NE: 45,
    E: 90,
    SE: 135,
    S: 180,
    SW: 225,
    W: 270,
    NW: 315
};

const windowDirectionLayer = L.layerGroup().addTo(map);

function updateWindowArrow() {
    windowDirectionLayer.clearLayers();

    if (selectedLat === null || selectedLon === null) {
        return;
    }

    const radians =
        directionDegrees[directionSelect.value] * Math.PI / 180;

    const length = 150;

    const north = Math.cos(radians) * length;
    const east = Math.sin(radians) * length;

    const endLat = selectedLat + north / 111320;
    const endLon = selectedLon +
        east / (111320 * Math.cos(selectedLat * Math.PI / 180));

    L.polyline(
        [[selectedLat, selectedLon], [endLat, endLon]],
        {
            color: "#e11d48",
            weight: 5
        }
    ).addTo(windowDirectionLayer);

    L.circleMarker([endLat, endLon], {
        radius: 5,
        color: "#e11d48",
        fillColor: "#e11d48",
        fillOpacity: 1
    }).addTo(windowDirectionLayer);
}

// Стрелка меняется при выборе направления окна
directionSelect.addEventListener(
    "change",
    updateWindowArrow
);

// И при выборе другого дома
map.on("click", updateWindowArrow);

// Показываем сохранённое направление
updateWindowArrow();

apartmentForm.addEventListener("submit", async (event) => {
    event.preventDefault();

if (selectedLat === null || selectedLon === null) {
    const message = "Сначала выбери дом на карте.";

    apartmentStatus.textContent = message;

    document.getElementById(
        "map-save-status"
    ).textContent = message;

    return;
}

    const data = {
        latitude: selectedLat,
        longitude: selectedLon,
        floor: Number(
            document.getElementById("apartment-floor").value
        ),
        window_direction: directionSelect.value,
        room_area: Number(
            document.getElementById("apartment-area").value
        ),
        ceiling_height: Number(
            document.getElementById("apartment-height").value
        )
    };

const button = document.getElementById("map-save-button");

    button.disabled = true;
    apartmentStatus.textContent = "Сохранение...";
document.getElementById(
    "map-save-status"
).textContent = "Сохраняем расположение...";
    try {
        const response = await fetch(
            "/api/map/apartment",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Ошибка сохранения"
            );
        }

        document.getElementById(
            "apartment-address"
        ).textContent = result.address;
document.getElementById(
    "map-address-preview"
).textContent = result.address;

document.getElementById(
    "map-address-state"
).textContent = "Сохранённый дом";

document.getElementById(
    "map-save-status"
).textContent = "Расположение сохранено";
        document.getElementById(
            "map-status"
        ).textContent = "Точка и параметры сохранены.";


apartmentStatus.textContent =
    "Квартира успешно сохранена!";

updateWindowArrow();

// Пересчитываем расстояния и анализ ветра
if (typeof loadIndustry === "function") {
    await loadIndustry();
}

    } catch (error) {
        apartmentStatus.textContent = error.message;
        document.getElementById(
    "map-save-status"
).textContent = "Не удалось сохранить: " + error.message;
        console.error(error);
    } finally {
        button.disabled = false;
    }
});
