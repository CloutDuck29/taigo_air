
const OMSK = [54.99, 73.37];


const homeCoordinates = document.getElementById(
    "home-coordinates"
);

const savedHome = {
    latitude: homeCoordinates.dataset.latitude === ""
        ? null
        : Number(homeCoordinates.dataset.latitude),

    longitude: homeCoordinates.dataset.longitude === ""
        ? null
        : Number(homeCoordinates.dataset.longitude)
};


const hasCoordinates =
    savedHome.latitude != null &&
    savedHome.longitude != null;

let selectedLat = hasCoordinates
    ? savedHome.latitude
    : null;

let selectedLon = hasCoordinates
    ? savedHome.longitude
    : null;

const startPoint = hasCoordinates
    ? [selectedLat, selectedLon]
    : OMSK;

const map = L.map("map", {
    zoomControl: true,
    attributionControl: true
}).setView(
    startPoint,
    hasCoordinates ? 15 : 11
);

// Убираем логотип Leaflet
map.attributionControl.setPrefix(false);

// Загружаем карту OpenStreetMap
L.tileLayer(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }
).addTo(map);

let homeMarker = null;

// Выбираем точку на карте
function selectPoint(latitude, longitude) {
    selectedLat = latitude;
    selectedLon = longitude;

    document.getElementById(
        "selected-lat"
    ).textContent = latitude.toFixed(6);

    document.getElementById(
        "selected-lon"
    ).textContent = longitude.toFixed(6);

    if (homeMarker) {
        homeMarker.setLatLng([latitude, longitude]);
    } else {
        homeMarker = L.marker([
            latitude,
            longitude
        ]).addTo(map);
    }

    homeMarker
        .bindPopup("Выбранное расположение дома")
        .openPopup();

    document.getElementById(
        "map-status"
    ).textContent = "Точка выбрана. Сохрани координаты.";
}

// Показываем ранее сохранённую точку
if (hasCoordinates) {
    selectPoint(selectedLat, selectedLon);

    document.getElementById(
        "map-status"
    ).textContent = "Показана сохранённая точка дома.";
}

// Выбираем дом нажатием на карту
map.on("click", function (event) {
    selectPoint(
        event.latlng.lat,
        event.latlng.lng
    );
});

// Сохраняем координаты в SQLite
document.getElementById(
    "save-location"
).addEventListener("click", async function () {
    const status = document.getElementById(
        "map-status"
    );

    if (selectedLat === null || selectedLon === null) {
        status.textContent = "Сначала выбери точку.";
        return;
    }

    status.textContent = "Сохранение...";

    try {
        const response = await fetch("/api/map/home", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                latitude: selectedLat,
                longitude: selectedLon
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Ошибка сохранения"
            );
        }

        status.textContent =
            "Координаты и адрес успешно сохранены!";

        document.getElementById(
            "home-address"
        ).textContent = result.address;

    } catch (error) {
        status.textContent = error.message;
        console.error(error);
    }
});
