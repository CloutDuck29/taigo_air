
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById(
        "outdoor-forecast-cards"
    );

    if (!container) return;

    const directions = [
        "С", "СВ", "В", "ЮВ",
        "Ю", "ЮЗ", "З", "СЗ"
    ];

    function formatNumber(value, digits = 0) {
        if (value == null || !Number.isFinite(Number(value))) {
            return "—";
        }

        return Number(value).toLocaleString("ru-RU", {
            maximumFractionDigits: digits
        });
    }

    function directionName(degrees) {
        if (degrees == null || !Number.isFinite(Number(degrees))) {
            return "—";
        }

        const normalized = ((Number(degrees) % 360) + 360) % 360;
        return directions[Math.round(normalized / 45) % 8];
    }

    function getAirQuality(aqi) {
        if (aqi == null || !Number.isFinite(Number(aqi))) {
            return { label: "Нет данных", level: "unknown" };
        }

        if (aqi <= 20) return { label: "Хорошее", level: "good" };
        if (aqi <= 40) return { label: "Умеренное", level: "fair" };
        if (aqi <= 60) return { label: "Среднее", level: "moderate" };
        if (aqi <= 80) return { label: "Плохое", level: "poor" };
        if (aqi <= 100) return { label: "Очень плохое", level: "poor" };

        return { label: "Крайне плохое", level: "poor" };
    }

    function getIndustryCount(sources, windDirection, windSpeed) {
        if (
            !Array.isArray(sources) ||
            windDirection == null ||
            windSpeed == null ||
            !Number.isFinite(Number(windDirection)) ||
            !Number.isFinite(Number(windSpeed))
        ) return null;

        if (Number(windSpeed) < 0.5) return 0;

        const toward = (Number(windDirection) + 180) % 360;
        let count = 0;
        let hasBearing = false;

        for (const source of sources) {
            const bearing = source.wind_analysis?.bearing;

            if (bearing == null || !Number.isFinite(Number(bearing))) {
                continue;
            }

            hasBearing = true;

            const difference = Math.abs(
                ((Number(bearing) - toward + 540) % 360) - 180
            );

            if (difference <= 60) {
                count++;
            }
        }

        return hasBearing ? count : null;
    }

    function addText(parent, tag, className, value) {
        const element = document.createElement(tag);
        element.className = className;
        element.textContent = value;
        parent.appendChild(element);
        return element;
    }

    function addMetric(parent, label, value, unit = "") {
        const metric = document.createElement("div");
        metric.className = "outdoor-metric";

        addText(metric, "span", "outdoor-metric-label", label);
        addText(metric, "strong", "outdoor-metric-value", value);

        if (unit) {
            addText(metric, "span", "outdoor-metric-unit", unit);
        }

        parent.appendChild(metric);
    }

    function renderForecast(results, sources) {
        container.replaceChildren();

        for (const item of results) {
            const quality = getAirQuality(item.european_aqi);
            const count = getIndustryCount(
                sources,
                item.wind_direction,
                item.wind_speed
            );

            const card = document.createElement("article");
            card.className =
                `outdoor-forecast-card outdoor-level-${quality.level}`;

            const top = document.createElement("div");
            top.className = "outdoor-card-top";

            const when = document.createElement("div");
            when.className = "outdoor-card-when";

            const time = typeof item.time === "string"
                ? item.time.slice(11, 16)
                : "—";

            addText(
                when, "span", "outdoor-card-period",
                `+${item.hours_ahead} ч`
            );

            addText(when, "strong", "outdoor-card-time", time);

            addText(top, "span", "outdoor-quality", quality.label);
            top.prepend(when);
            card.appendChild(top);

            const metrics = document.createElement("div");
            metrics.className = "outdoor-card-metrics";

            addMetric(
                metrics,
                "PM2.5",
                formatNumber(item.pm25, 1),
                "мкг/м³"
            );

            addMetric(
                metrics,
                "EU AQI",
                formatNumber(item.european_aqi)
            );

            const wind = document.createElement("div");
            wind.className = "outdoor-metric";

            addText(wind, "span", "outdoor-metric-label", "Ветер");
            addText(
                wind,
                "strong",
                "outdoor-metric-wind",
                `${formatNumber(item.wind_speed, 1)} м/с`
            );
            addText(
                wind,
                "span",
                "outdoor-metric-unit",
                `с ${directionName(item.wind_direction)}`
            );
            metrics.appendChild(wind);

            card.appendChild(metrics);

            if (
                item.european_aqi != null &&
                Number.isFinite(Number(item.european_aqi))
            ) {
                const track = document.createElement("div");
                track.className = "outdoor-aqi-track";

                const fill = document.createElement("div");
                fill.className = "outdoor-aqi-fill";
                fill.style.width =
                    `${Math.min(100, Math.max(0, Number(item.european_aqi)))}%`;

                track.appendChild(fill);
                card.appendChild(track);
            }

            const industry = document.createElement("div");
            industry.className = "outdoor-industry-summary";

            const symbol = document.createElement("span");
            symbol.className = "outdoor-industry-symbol";
            symbol.textContent = "◈";

            const industryText = document.createElement("span");

            if (count === null) {
                industryText.textContent =
                    "Нет данных для анализа промышленного переноса";
            } else if (count === 0) {
                industryText.textContent =
                    "По ветру значимых предприятий не выявлено";
            } else {
                industryText.textContent =
                    `Возможен перенос от ${count} предприятий`;
            }

            industry.append(symbol, industryText);
            card.appendChild(industry);

            container.appendChild(card);
        }

        if (!results.length) {
            container.textContent = "Прогноз пока недоступен";
        }
    }

    async function loadOutdoorForecast() {
        try {
            const [forecastResponse, industryResponse] =
                await Promise.all([
                    fetch("/api/outdoor-forecast", {
                        cache: "no-store"
                    }),
                    fetch("/api/industry", {
                        cache: "no-store"
                    })
                ]);

            if (!forecastResponse.ok) {
                throw new Error("Прогноз недоступен");
            }

            const forecast = await forecastResponse.json();

            if (
                forecast.status !== "ok" ||
                !Array.isArray(forecast.results)
            ) {
                throw new Error("Нет данных прогноза");
            }

            let sources = null;

            if (industryResponse.ok) {
                const industry = await industryResponse.json();

                if (Array.isArray(industry.sources)) {
                    sources = industry.sources;
                }
            }

            renderForecast(forecast.results, sources);

        } catch (error) {
            console.warn("Outdoor forecast:", error);
            container.textContent =
                "Не удалось загрузить прогноз наружного воздуха";
        }
    }

    loadOutdoorForecast();

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            loadOutdoorForecast();
        }
    });
});
