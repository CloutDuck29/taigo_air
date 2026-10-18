
// Отдельная карта исследовательского режима
const map = L.map("research-map").setView(
    [54.99, 73.37],
    11
);

map.attributionControl.setPrefix(false);

L.tileLayer(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(map);

// Подключаем существующую логику TaigoPlume
// через отдельный скрипт plume.js.
