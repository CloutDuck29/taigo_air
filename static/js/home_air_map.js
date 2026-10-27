
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

    const plumes = L.layerGroup().addTo(map);
const markers = L.featureGroup().addTo(map);
let mapViewInitialized = false;
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
    const lat = Number(source.latitude);
    const lon = Number(source.longitude);
    const distanceKm = Number(source.distance_km);

    if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lon) ||
        !Number.isFinite(distanceKm) ||
        distanceKm <= 0
    ) return;

    const angle = ((Number(direction) + 180) % 360)
        * Math.PI / 180;

    // Длина только для наглядности: до расстояния до дома.
    const length = distanceKm * 1000 * 1.1;

    const left = [];
    const right = [];

    for (let step = 1; step <= 20; step++) {
        const distance = length * step / 20;

        // Узкий коридор вместо огромного треугольника.
        const width = Math.min(550, 80 + distance * 0.09);

        for (const [side, points] of [
            [-1, left],
            [1, right]
        ]) {
            const lateral = side * width;

            const east =
                distance * Math.sin(angle) +
                lateral * Math.cos(angle);

            const north =
                distance * Math.cos(angle) -
                lateral * Math.sin(angle);

            points.push(
                offsetCoordinate(lat, lon, east, north)
            );
        }
    }

    const edge =
        source.wind_analysis?.position_code === "edge";

L.polygon(
    [
        [lat, lon],
        ...left,
        ...right.reverse()
    ],
{
    stroke: false,
    fillColor: "#FFC247",
    fillOpacity: edge ? 0.16 : 0.30,
    interactive: false
}
).addTo(plumes);
}


/* ===== ВЫВОД О НАПРАВЛЕНИИ ВЕТРА ===== */

function renderWindConclusion(sources, wind, plumeResults = []) {
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

const relevantCount = downwind.length + edge.length;

conclusion.textContent = relevantCount > 0
    ? `Возможен перенос от ${relevantCount} предприятий`
    : "Ветер от известных предприятий не направлен к дому";

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

name.textContent = source.name || "Предприятие";

const info = source.pollutants;
const textBlock = document.createElement("div");
textBlock.className = "home-industry-text";

textBlock.appendChild(name);



if (info) {
    const substances = document.createElement("span");
    substances.className = "home-industry-substances";
    substances.textContent = info.substances;
    textBlock.appendChild(substances);

    if (info.verified === false) {
        const warning = document.createElement("span");
        warning.className = "home-industry-unverified";
        warning.textContent =
            "Перечень веществ предварительный";

        textBlock.appendChild(warning);
    }
}

const plume = plumeResults.find(
    item => item.source_id === source.id
);

if (plume) {
    const plumeInfo = document.createElement("span");
    plumeInfo.className = "home-industry-plume";

    if (plume.within_plume === true) {
        plumeInfo.textContent =
            "Внутри условной полосы шлейфа";
        plumeInfo.classList.add("plume-inside");

    } else if (plume.within_plume === false) {
        plumeInfo.textContent =
            "Вне условной полосы шлейфа";
        plumeInfo.classList.add("plume-outside");

    } else {
        plumeInfo.textContent =
            "Модельный шлейф не рассчитан";
    }

    textBlock.appendChild(plumeInfo);
}

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

        card.append(textBlock, distance);
        list.appendChild(card);


        rows.push(card);
    }

    const health = document.getElementById("home-wind-health");

    if (health) {
const substances = relevant
    .map(source => {
        const info = source.pollutants;

        if (!info || info.verified !== true) {
            return "";
        }

        return info.substances || "";
    })
    .join(" ");

        const effects = [];

        if (/NO₂|SO₂|NOₓ|SOₓ/.test(substances)) {
            effects.push(
                "NO₂ и SO₂ — могут раздражать дыхательные пути"
            );
        }

        if (/пыль|зола/i.test(substances)) {
            effects.push(
                "Пыль и зола — частицы могут оседать на поверхностях и попадать в лёгкие"
            );
        }

        if (/бензол/i.test(substances)) {
            effects.push(
                "Бензол — канцероген; опасность зависит от уровня и длительности воздействия"
            );
        }

        if (/формальдегид/i.test(substances)) {
            effects.push(
                "Формальдегид — может раздражать глаза и дыхательные пути"
            );
        }

        if (/фенол/i.test(substances)) {
            effects.push(
                "Фенол — при достаточном воздействии раздражает глаза и дыхательные пути"
            );
        }

        health.replaceChildren();

        if (!effects.length) {
            health.textContent =
                "Для оценки воздействия недостаточно подтверждённых данных.";
        } else {
            const title = document.createElement("strong");
            title.textContent = "Возможное воздействие";
            health.appendChild(title);

            for (const effect of effects) {
                const row = document.createElement("div");
                row.className = "home-health-row";
                row.textContent = effect;
                health.appendChild(row);
            }
        }
    }
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

let plumeResults = [];

try {
    const plumeResponse = await fetch("/api/plume", {
        cache: "no-store"
    });

    if (plumeResponse.ok) {
        const plumeData = await plumeResponse.json();

        if (Array.isArray(plumeData.results)) {
            plumeResults = plumeData.results;
        }
    }
} catch (error) {
    console.warn(
        "TaigoPlume недоступен:",
        error
    );
}

            if (!industryResponse.ok) {
                throw new Error(
                    industry.error ||
                    "Не удалось загрузить предприятия."
                );
            }

            markers.clearLayers();
plumes.clearLayers();

            const sources = Array.isArray(industry.sources)
                ? industry.sources
                : [];

            const wind = industry.wind;
renderWindConclusion(sources, wind, plumeResults);
            const validWind = wind &&
                Number.isFinite(Number(wind.direction)) &&
                Number.isFinite(Number(wind.speed)) &&
                Number(wind.speed) >= 0.5;
const arrow = document.getElementById("home-wind-arrow");
const arrowIcon = document.getElementById("home-wind-arrow-icon");
const arrowSpeed = document.getElementById("home-wind-arrow-speed");

if (arrow && arrowIcon && arrowSpeed) {
    arrow.hidden = !validWind;

    if (validWind) {
        const toward = (Number(wind.direction) + 180) % 360;

        arrowIcon.style.transform = `rotate(${toward}deg)`;

        arrowSpeed.textContent =
            `${Number(wind.speed).toFixed(1)} м/с`;
    }
}
for (const source of sources) {
    if (
        source.latitude == null ||
        source.longitude == null ||
        !Number.isFinite(Number(source.latitude)) ||
        !Number.isFinite(Number(source.longitude))
    ) {
        continue;
    }

    const position = source.wind_analysis?.position_code;

    const relevant =
        validWind &&
        (position === "downwind" || position === "edge");

    L.circleMarker(
    [
        Number(source.latitude),
        Number(source.longitude)
    ],
    {
radius: relevant ? 7 : 4,
color: relevant ? "#ffffff" : "#9ca3af",
weight: relevant ? 1.5 : 1,
fillColor: relevant
    ? getIndustryColor(source.industry)
    : "#94a3b8",
fillOpacity: relevant ? 0.95 : 0.35
    }
)
                .bindPopup(
                    document.createTextNode(
                        source.name || "Промышленный объект"
                    )
                )
                .addTo(markers);


if (
    validWind &&
    (position === "downwind" || position === "edge")
) {
    drawWindSector(
        source,
        Number(wind.direction)
    );
}
            }

const homeLocation = document.getElementById("home-location");

const rawLat = homeLocation?.dataset.latitude ?? "";
const rawLon = homeLocation?.dataset.longitude ?? "";

const homeLat = rawLat === "" ? NaN : Number(rawLat);
const homeLon = rawLon === "" ? NaN : Number(rawLon);

if (
    Number.isFinite(homeLat) &&
    Number.isFinite(homeLon) &&
    homeLat >= -90 && homeLat <= 90 &&
    homeLon >= -180 && homeLon <= 180
) {
    const homeIcon = L.divIcon({
        className: "taigo-home-marker",
        html: `
          <div class="taigo-home-pin">
            <svg viewBox="0 0 24 24"
                 width="23"
                 height="23"
                 fill="none"
                 stroke="currentColor"
                 stroke-width="2.2"
                 stroke-linecap="round"
                 stroke-linejoin="round">
              <path d="m3 10 9-7 9 7"/>
              <path d="M5 9v12h14V9"/>
              <path d="M9 21v-8h6v8"/>
            </svg>
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        popupAnchor: [0, -22]
    });

    L.marker([homeLat, homeLon], {
        icon: homeIcon,
        zIndexOffset: 1000
    })
        .bindPopup("Мой дом")
        .addTo(markers);
}


const focusPoints = [];

if (
    Number.isFinite(homeLat) &&
    Number.isFinite(homeLon)
) {
    focusPoints.push([homeLat, homeLon]);
}

for (const source of sources) {
    const position = source.wind_analysis?.position_code;

    if (
        position !== "downwind" &&
        position !== "edge"
    ) {
        continue;
    }

    const lat = Number(source.latitude);
    const lon = Number(source.longitude);

    if (
        source.latitude != null &&
        source.longitude != null &&
        Number.isFinite(lat) &&
        Number.isFinite(lon)
    ) {
        focusPoints.push([lat, lon]);
    }
}

if (!mapViewInitialized) {
    if (focusPoints.length > 1) {
        map.fitBounds(L.latLngBounds(focusPoints), {
            padding: [50, 50],
            maxZoom: 11,
            animate: false
        });
    } else if (focusPoints.length === 1) {
        map.setView(focusPoints[0], 11);
    } else if (markers.getLayers().length) {
        map.fitBounds(markers.getBounds(), {
            padding: [40, 40],
            maxZoom: 10,
            animate: false
        });
    }

    if (focusPoints.length || markers.getLayers().length) {
        mapViewInitialized = true;
    }
}


            if (validWind) {
                const toward =
                    (Number(wind.direction) + 180) % 360;

                status.textContent =
                    `Ветер ${Number(wind.speed)} м/с. `;
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
