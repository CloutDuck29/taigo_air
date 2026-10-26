
const industryMarkers = L.layerGroup().addTo(map);

const industryFilter = document.getElementById("industry-filter");
const industryShowMore = document.getElementById("industry-show-more");

let industrySources = [];
let industryVisibleCount = 5;

const windDirections = [
    "севера",
    "северо-востока",
    "востока",
    "юго-востока",
    "юга",
    "юго-запада",
    "запада",
    "северо-запада"
];

const windDestinations = [
    "север",
    "северо-восток",
    "восток",
    "юго-восток",
    "юг",
    "юго-запад",
    "запад",
    "северо-запад"
];

function windDirectionIndex(degrees) {
    return Math.floor(
        (((degrees % 360) + 360) % 360 + 22.5) / 45
    ) % 8;
}

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

function renderIndustries() {
    const table = document.getElementById("industry-table");
    const status = document.getElementById("industry-status");

    table.replaceChildren();
    industryMarkers.clearLayers();

    const selectedIndustry = industryFilter?.value ?? "all";

    const filtered = industrySources.filter(source =>
        selectedIndustry === "all" ||
        source.industry === selectedIndustry
    );

    // Маркеры показываем для всех предприятий выбранной отрасли
    const markers = new Map();

    filtered.forEach(source => {
const color = getIndustryColor(source.industry);

const marker = L.circleMarker(
    [source.latitude, source.longitude],
    {
        radius: 7,
        color: "#ffffff",
        weight: 1.5,
        fillColor: color,
        fillOpacity: 0.9
    }
).addTo(industryMarkers);

        const popup = document.createElement("div");

        const title = document.createElement("strong");
        title.textContent = source.name;

        const description = document.createElement("p");
        description.textContent =
            `Расстояние: ${source.distance_km ?? "—"} км. ` +
            `Положение: ${source.wind_analysis?.position ?? "Нет данных"}`;

        popup.append(title, description);
        marker.bindPopup(popup);

        markers.set(source.id, marker);
    });

    filtered.slice(0, industryVisibleCount).forEach(source => {
        const analysis = source.wind_analysis;

        const card = document.createElement("button");
        card.type = "button";
        card.className = "industry-card";

        const title = document.createElement("div");
        title.className = "industry-name";
        title.textContent = source.name;

        const meta = document.createElement("div");
        meta.className = "industry-meta";

const values = [
    `${source.distance_km ?? "—"} км`,
    source.industry ?? "Тип не указан",
    analysis
        ? `Дом от завода: ${analysis.bearing_name} (${analysis.bearing}°)`
        : "Направление: нет данных",
    analysis?.position ?? "Анализ ветра недоступен"
];

        values.forEach(value => {
            const tag = document.createElement("span");
            tag.className = "industry-tag";
            tag.textContent = value;
            meta.appendChild(tag);
        });

        card.append(title, meta);

        card.addEventListener("click", () => {
            map.setView(
                [source.latitude, source.longitude],
                14
            );

            markers.get(source.id)?.openPopup();

            document.getElementById("map-container")
                ?.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
        });

        table.appendChild(card);
    });

    status.textContent =
        `Показано ${Math.min(filtered.length, industryVisibleCount)} ` +
        `из ${filtered.length} предприятий`;

    if (industryShowMore) {
        industryShowMore.hidden =
            filtered.length <= industryVisibleCount;
    }
}

function populateIndustryFilters() {
    if (!industryFilter) return;

    const currentValue = industryFilter.value;
    const industries = [
        ...new Set(
            industrySources.map(source => source.industry)
                .filter(Boolean)
        )
    ].sort((a, b) => a.localeCompare(b, "ru"));

    industryFilter.replaceChildren(
        new Option("Все отрасли", "all")
    );

    industries.forEach(industry => {
        industryFilter.add(
            new Option(industry, industry)
        );
    });

    industryFilter.value =
        industries.includes(currentValue)
            ? currentValue
            : "all";
}

async function loadIndustry() {
    const status = document.getElementById("industry-status");
    const windInfo = document.getElementById("industry-wind");

    status.textContent = "Загрузка предприятий...";
    windInfo.textContent = "Получаем данные о ветре...";

    try {
        const response = await fetch("/api/industry", {
            cache: "no-store"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Ошибка получения данных"
            );
        }

        industrySources = Array.isArray(data.sources)
            ? data.sources
            : [];

if (
    data.wind &&
    Number.isFinite(Number(data.wind.direction)) &&
    Number.isFinite(Number(data.wind.speed)) &&
    data.wind.direction !== null &&
    data.wind.speed !== null
) {
    const direction = Number(data.wind.direction);
    const speed = Number(data.wind.speed);
    const windTo = (direction + 180) % 360;

    const from = windDirections[windDirectionIndex(direction)];
    const to = windDestinations[windDirectionIndex(windTo)];

    windInfo.textContent = speed < 0.5
        ? `Ветер: ${speed} м/с. Направление при слабом ветре неустойчиво.`
        : `Ветер: ${speed} м/с. С ${from} на ${to}. ` +
          `Данные: ${data.wind.time ?? "время неизвестно"}`;
} else {
    windInfo.textContent = "Данные о ветре недоступны.";
}

        industryVisibleCount = 5;
        populateIndustryFilters();
        renderIndustries();

    } catch (error) {
        status.textContent =
            "Ошибка загрузки предприятий: " + error.message;

        windInfo.textContent = "Анализ ветра недоступен.";
        console.error(error);
    }
}

industryFilter?.addEventListener("change", () => {
    industryVisibleCount = 5;
    renderIndustries();
});

industryShowMore?.addEventListener("click", () => {
    industryVisibleCount += 5;
    renderIndustries();
});

document.getElementById("load-industry")
    ?.addEventListener("click", loadIndustry);

loadIndustry();
