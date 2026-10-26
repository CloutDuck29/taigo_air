
const industryMarkers = L.layerGroup().addTo(map);

async function loadIndustry() {
    const status = document.getElementById("industry-status");
    const table = document.getElementById("industry-table");
    const windInfo = document.getElementById("industry-wind");

    status.textContent = "Загрузка предприятий...";
    windInfo.textContent = "Получаем данные о ветре...";

    table.replaceChildren();
    industryMarkers.clearLayers();

    try {
        // Получаем предприятия и анализ ветра от Flask
        const response = await fetch("/api/industry");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Ошибка получения данных"
            );
        }

        status.textContent =
            `Найдено объектов: ${data.count}`;

        // Отображаем направление и скорость ветра
        if (data.wind) {
            const windTo =
                (data.wind.direction + 180) % 360;

            windInfo.textContent =
                `Ветер: ${data.wind.speed} м/с. ` +
                `Дует с ${data.wind.direction}° ` +
                `в сторону ${windTo}°. ` +
                `Время данных: ${data.wind.time ?? "неизвестно"}`;
        } else {
            windInfo.textContent =
                "Данные о ветре недоступны.";
        }

        // Перебираем предприятия
        for (const source of data.sources) {
            const analysis = source.wind_analysis;

            // Маркер предприятия на карте
            const marker = L.circleMarker(
                [source.latitude, source.longitude],
                {
                    radius: 7,
                    color: "#b45309",
                    fillColor: "#f59e0b",
                    fillOpacity: 0.8
                }
            ).addTo(industryMarkers);

            // Информация при нажатии на маркер
            const popup = document.createElement("div");

            const popupTitle = document.createElement("strong");
            popupTitle.textContent = source.name;

            const popupInfo = document.createElement("p");
            popupInfo.textContent =
                `Расстояние: ${source.distance_km} км. ` +
                `Положение: ${analysis?.position ?? "Нет данных"}`;

            popup.append(popupTitle, popupInfo);
            marker.bindPopup(popup);


// Создаём карточку предприятия
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
    ? `${analysis.bearing}° (${analysis.bearing_name})`
    : "Направление: нет данных",
  analysis?.position ?? "Ветер: нет данных"
];

values.forEach(value => {
  const tag = document.createElement("span");
  tag.className = "industry-tag";
  tag.textContent = value;
  meta.appendChild(tag);
});

card.append(title, meta);

// При нажатии показываем предприятие на карте
card.addEventListener("click", () => {
  map.setView(
    [source.latitude, source.longitude],
    14
  );

  marker.openPopup();

  document.getElementById("map-container")
    ?.scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
});

table.appendChild(card);

        }

    } catch (error) {
        status.textContent =
            "Ошибка загрузки предприятий: " + error.message;

        windInfo.textContent = "Анализ ветра недоступен.";

        console.error(error);
    }
}


const industryButton = document.getElementById("load-industry");

// Кнопку оставляем для ручного обновления при необходимости
if (industryButton) {
    industryButton.textContent = "Обновить данные";

    industryButton.addEventListener(
        "click",
        loadIndustry
    );
}

// Автоматическая загрузка после открытия страницы
loadIndustry();
