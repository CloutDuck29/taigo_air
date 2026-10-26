
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

// По умолчанию карта не перехватывает прокрутку
map.dragging.disable();
map.scrollWheelZoom.disable();

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
    ).textContent = "Точка выбрана. Заполни параметры и нажми «Сохранить квартиру».";
}

// Показываем ранее сохранённую точку
if (hasCoordinates) {
    selectPoint(selectedLat, selectedLon);

    document.getElementById(
        "map-status"
    ).textContent = "Показана сохранённая точка дома.";
}

// Выбираем дом нажатием на карту

let addressRequestId = 0;

async function previewSelectedAddress(latitude, longitude) {
    const requestId = ++addressRequestId;

    const addressElement =
        document.getElementById("map-address-preview");

    const stateElement =
        document.getElementById("map-address-state");

    addressElement.textContent = "Определяем адрес...";
    stateElement.textContent = "Изменения не сохранены";

    try {
        const params = new URLSearchParams({
            lat: latitude.toString(),
            lon: longitude.toString()
        });

        const response = await fetch(
            `/api/map/address?${params}`,
            { cache: "no-store" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Адрес недоступен");
        }

        // Не показываем ответ от ранее выбранной точки
        if (requestId !== addressRequestId) return;

        addressElement.textContent = data.address;

    } catch (error) {
        if (requestId !== addressRequestId) return;

        addressElement.textContent =
            `Точка: ${latitude.toFixed(6)}, ` +
            longitude.toFixed(6);

        stateElement.textContent =
            "Не удалось определить адрес";
    }
}

// Сохранённый адрес показываем при загрузке
if (hasCoordinates) {
    const savedAddress = document.getElementById(
        "apartment-address"
    )?.textContent.trim();

    document.getElementById(
        "map-address-preview"
    ).textContent = savedAddress || "Адрес не определён";

    document.getElementById(
        "map-address-state"
    ).textContent = "Сохранённый дом";
}

// При выборе нового дома обновляем адрес
map.on("click", function(event) {
    const latitude = event.latlng.lat;
    const longitude = event.latlng.lng;

    selectPoint(latitude, longitude);

    previewSelectedAddress(latitude, longitude);

    document.getElementById(
        "map-status"
    ).textContent =
        "Новая точка выбрана. Проверь адрес и сохрани.";
});


