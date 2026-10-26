
"use strict";

document.addEventListener("DOMContentLoaded", async () => {
    const element = document.getElementById("home-air-map");
    const status = document.getElementById("home-air-map-status");

    if (!element || !status) return;

    if (!window.L) {
        status.textContent = "Библиотека карты не загрузилась.";
        return;
    }

const map = L.map(element, {
    scrollWheelZoom: false,
    zoomControl: true,
    attributionControl: true
}).setView([54.99, 73.37], 10);

// Как на основной карте
map.attributionControl.setPrefix(false);

// По умолчанию прокручивается страница
map.dragging.disable();
map.scrollWheelZoom.disable();

const mapToggle = document.getElementById(
    "home-map-interaction-toggle"
);

let mapInteractive = false;

function applyMapInteractionMode() {
    if (mapInteractive) {
        map.dragging.enable();
        element.classList.add("map-interactive");
        mapToggle.classList.add("active");
    } else {
        map.dragging.disable();
        element.classList.remove("map-interactive");
        mapToggle.classList.remove("active");
    }

    mapToggle.setAttribute(
        "aria-pressed",
        String(mapInteractive)
    );

    mapToggle.setAttribute(
        "aria-label",
        mapInteractive
            ? "Выключить управление картой"
            : "Включить управление картой"
    );
}

if (mapToggle) {
    mapToggle.addEventListener("click", () => {
        mapInteractive = !mapInteractive;
        applyMapInteractionMode();
    });

    applyMapInteractionMode();
}

    L.tileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    const markers = L.featureGroup().addTo(map);
    // Цвета точно как на основной карте
const industryColors = {
    "Нефтепереработка": "#f59e0b",
    "Химическая промышленность": "#a78bfa",
    "Теплоэнергетика": "#ef4444",
    "Машиностроение": "#38bdf8",
    "Шинная промышленность": "#eab308"
};

function getIndustryColor(industry) {
    return industryColors[industry] ?? "#94a3b8";
}

    function offsetCoordinate(lat, lon, east, north) {
        const radius = 6371000;

        const newLat = lat +
            (north / radius) * 180 / Math.PI;

        const newLon = lon +
            (east / (
                radius * Math.cos(lat * Math.PI / 180)
            )) * 180 / Math.PI;

        return [newLat, newLon];
    }

    function drawWindSector(source, direction) {
        const radians = (
            (direction + 180) % 360
        ) * Math.PI / 180;

        const left = [];
        const right = [];

        for (let distance = 300; distance <= 10000;
             distance += 400) {

            const width = 0.15 * distance;

            for (const [side, collection] of [
                [-1, left],
                [1, right]
            ]) {
                const lateral = side * width;

                const east =
                    distance * Math.sin(radians) +
                    lateral * Math.cos(radians);

                const north =
                    distance * Math.cos(radians) -
                    lateral * Math.sin(radians);

                collection.push(
                    offsetCoordinate(
                        source.latitude,
                        source.longitude,
                        east,
                        north
                    )
                );
            }
        }

        L.polygon(
            [
                [source.latitude, source.longitude],
                ...left,
                ...right.reverse()
            ],
{
    color: getIndustryColor(source.industry),
    fillColor: getIndustryColor(source.industry),
    fillOpacity: 0.10,
    opacity: 0.45,
    weight: 1,
    interactive: false
}
        ).addTo(markers);
    }

/* ===== ВЫВОД О НАПРАВЛЕНИИ ВЕТРА ===== */

function renderWindConclusion(sources, wind) {
    const conclusion = document.getElementById(
        "home-wind-conclusion"
    );

    const list = document.getElementById(
        "home-wind-sources"
    );

    const showMore = document.getElementById(
        "home-wind-show-more"
    );

    if (!conclusion || !list || !showMore) return;

    list.replaceChildren();
    showMore.hidden = true;
    showMore.setAttribute("aria-expanded", "false");

    // Нельзя определять направление без данных о ветре.
    if (
        !wind ||
        wind.direction == null ||
        wind.speed == null ||
        !Number.isFinite(Number(wind.direction)) ||
        !Number.isFinite(Number(wind.speed))
    ) {
        conclusion.textContent = "Нет данных о ветре";
        return;
    }

    if (Number(wind.speed) < 0.5) {
        conclusion.textContent = "Ветер слишком слабый";
        return;
    }

    if (!Array.isArray(sources)) {
        conclusion.textContent = "Нет данных о предприятиях";
        return;
    }

    const analyzed = sources.filter(source =>
        source.wind_analysis?.position_code
    );

    if (analyzed.length === 0) {
        conclusion.textContent =
            "Выбери дом на карте для анализа ветра";
        return;
    }

    const downwind = analyzed.filter(source =>
        source.wind_analysis.position_code === "downwind"
    );

    const edge = analyzed.filter(source =>
        source.wind_analysis.position_code === "edge"
    );

    if (downwind.length > 0) {
        conclusion.textContent =
            `Ветер в сторону дома от ${downwind.length} предприятий`;
    } else if (edge.length > 0) {
        conclusion.textContent =
            `Возможен перенос от ${edge.length} предприятий`;
    } else {
        conclusion.textContent =
            "Ветер от известных предприятий не направлен к дому";
    }

    const relevant = [...downwind, ...edge].sort((a, b) => {
        const aDistance = Number(a.distance_km);
        const bDistance = Number(b.distance_km);

        return (
            (Number.isFinite(aDistance) ? aDistance : Infinity) -
            (Number.isFinite(bDistance) ? bDistance : Infinity)
        );
    });

    const rows = [];

    for (const source of relevant) {
        const card = document.createElement("div");
        card.className = "home-wind-source";

        const name = document.createElement("span");
        name.className = "home-wind-source-name";

        const isEdge =
            source.wind_analysis.position_code === "edge";

        name.textContent =
            (isEdge ? "Вблизи направления: " : "") +
            (source.name || "Предприятие");

        const distance = document.createElement("span");
        distance.className = "home-wind-source-distance";

        const km = Number(source.distance_km);

        distance.textContent =
            source.distance_km != null &&
            Number.isFinite(km)
                ? `${km.toLocaleString("ru-RU", {
                    maximumFractionDigits: 1
                  })} км`
                : "—";

        card.append(name, distance);
        list.appendChild(card);

        rows.push(card);
    }

    if (rows.length <= 2) return;

    // По умолчанию видны только два предприятия.
    rows.forEach((row, index) => {
        row.hidden = index >= 2;
    });

    showMore.hidden = false;
    showMore.textContent = `Показать все (${rows.length})`;

    showMore.onclick = () => {
        const expanded =
            showMore.getAttribute("aria-expanded") === "true";

        rows.forEach((row, index) => {
            row.hidden = expanded && index >= 2;
        });

        showMore.setAttribute(
            "aria-expanded",
            String(!expanded)
        );

        showMore.textContent = expanded
            ? `Показать все (${rows.length})`
            : "Свернуть";
    };
}

    async function loadMapData() {
        status.textContent = "Обновляем направление ветра...";

        try {
            const [industryResponse, airResponse] =
                await Promise.all([
                    fetch("/api/industry", {
                        cache: "no-store"
                    }),
                    fetch("/api/air-quality", {
                        cache: "no-store"
                    })
                ]);

            const industry = await industryResponse.json();
            const air = await airResponse.json();

            if (!industryResponse.ok) {
                throw new Error(
                    industry.error ||
                    "Не удалось загрузить предприятия."
                );
            }

            markers.clearLayers();

            const sources = Array.isArray(industry.sources)
                ? industry.sources
                : [];

            const wind = industry.wind;
renderWindConclusion(sources, wind);
            const validWind = wind &&
                Number.isFinite(Number(wind.direction)) &&
                Number.isFinite(Number(wind.speed)) &&
                Number(wind.speed) >= 0.5;

            for (const source of sources) {
                if (
                    !Number.isFinite(Number(source.latitude)) ||
                    !Number.isFinite(Number(source.longitude))
                ) {
                    continue;
                }

L.circleMarker(
    [
        Number(source.latitude),
        Number(source.longitude)
    ],
    {
        radius: 7,
        color: "#ffffff",
        weight: 1.5,
        fillColor: getIndustryColor(source.industry),
        fillOpacity: 0.9
    }
)
                .bindPopup(
                    document.createTextNode(
                        source.name || "Промышленный объект"
                    )
                )
                .addTo(markers);

                if (validWind) {
                    drawWindSector(
                        source,
                        Number(wind.direction)
                    );
                }
            }

            const homeLat = Number(air.latitude);
            const homeLon = Number(air.longitude);

            if (
                airResponse.ok &&
                Number.isFinite(homeLat) &&
                Number.isFinite(homeLon)
            ) {
                L.circleMarker(
                    [homeLat, homeLon],
                    {
                        radius: 8,
                        color: "#fff",
                        fillColor: "#79d9a0",
                        fillOpacity: 1,
                        weight: 2
                    }
                )
                .bindPopup("Точка оценки наружного воздуха")
                .addTo(markers);
            }

            if (markers.getLayers().length) {
                map.fitBounds(markers.getBounds(), {
                    padding: [20, 20],
                    maxZoom: 11
                });
            }

            if (validWind) {
                const toward =
                    (Number(wind.direction) + 180) % 360;

                status.textContent =
                    `Ветер ${Number(wind.speed)} м/с. ` +
                    `Перенос в направлении ${Math.round(toward)}°. ` +
                    "Сектора схематичны, концентрации " +
                    "загрязнителей не рассчитаны.";
            } else {
                status.textContent =
                    "Направление переноса сейчас недоступно. " +
                    "Показаны только предприятия.";
            }

        } catch (error) {
        document.getElementById(
    "home-wind-conclusion"
).textContent =
    "Не удалось получить данные для анализа ветра.";

document.getElementById(
    "home-wind-sources"
).replaceChildren();
            status.textContent =
                error.message || "Не удалось загрузить карту.";
            console.error("Home air map:", error);
        }

        setTimeout(() => map.invalidateSize(), 100);
    }

    await loadMapData();

    setInterval(() => {
        if (!document.hidden) {
            loadMapData();
        }
    }, 600000);

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            map.invalidateSize();
            loadMapData();
        }
    });
});
