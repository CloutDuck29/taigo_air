
const plumeLayer = L.featureGroup().addTo(map);

function metersToCoordinates(lat, lon, east, north) {
    const earthRadius = 6371000;

    const newLat = lat + (
        north / earthRadius
    ) * 180 / Math.PI;

    const cosLat = Math.cos(lat * Math.PI / 180);

    const newLon = lon + (
        east / (earthRadius * cosLat)
    ) * 180 / Math.PI;

    return [newLat, newLon];
}

function plumeWidth(x) {
    // Коэффициент поперечного рассеивания
    return 0.08 * x / Math.sqrt(1 + 0.0001 * x);
}

function drawPlume(source, windDirection) {
    plumeLayer.clearLayers();

    // Метеорологический ветер указывает,
    // ОТКУДА дует. Нам нужно КУДА.
    const direction = (
        (windDirection + 180) % 360
    ) * Math.PI / 180;

    const rightSide = [];
    const leftSide = [];

    // Условный сектор длиной 15 км
    for (let x = 100; x <= 15000; x += 250) {
        const width = 2 * plumeWidth(x);

        for (const [side, points] of [
            [-1, leftSide],
            [1, rightSide]
        ]) {
            const y = side * width;

            const east =
                x * Math.sin(direction)
                + y * Math.cos(direction);

            const north =
                x * Math.cos(direction)
                - y * Math.sin(direction);

            points.push(
                metersToCoordinates(
                    source.latitude,
                    source.longitude,
                    east,
                    north
                )
            );
        }
    }

    const polygon = [
        [source.latitude, source.longitude],
        ...leftSide,
        ...rightSide.reverse()
    ];

    // Отображаем условный сектор
    L.polygon(polygon, {
        color: "#2563eb",
        fillColor: "#60a5fa",
        fillOpacity: 0.22,
        weight: 2
    }).addTo(plumeLayer);

    // Центр промышленного объекта
    L.circleMarker(
        [source.latitude, source.longitude],
        {
            radius: 9,
            color: "#b45309",
            fillColor: "#f59e0b",
            fillOpacity: 1
        }
    )
    .bindPopup(source.name)
    .addTo(plumeLayer);

    // Центр линии распространения
    const centerEast = 15000 * Math.sin(direction);
    const centerNorth = 15000 * Math.cos(direction);

    const end = metersToCoordinates(
        source.latitude,
        source.longitude,
        centerEast,
        centerNorth
    );

    L.polyline(
        [
            [source.latitude, source.longitude],
            end
        ],
        {
            color: "#1d4ed8",
            weight: 2,
            dashArray: "6, 6"
        }
    ).addTo(plumeLayer);

    map.fitBounds(plumeLayer.getBounds(), {
        padding: [30, 30]
    });
}

async function calculatePlume() {
    const status = document.getElementById("plume-status");
    const table = document.getElementById("plume-table");
    const button = document.getElementById("calculate-plume");

    const selectedId = document.getElementById(
        "plume-source"
    ).value;

    const emission = Number(
        document.getElementById("plume-emission").value
    );

    const height = Number(
        document.getElementById("plume-height").value
    );

    if (
        !Number.isFinite(emission) ||
        emission < 0.01 ||
        emission > 100 ||
        !Number.isFinite(height) ||
        height < 1 ||
        height > 300
    ) {
        status.textContent =
            "Проверь параметры выброса и высоты.";
        return;
    }

    status.textContent = "Выполняется расчёт...";
    button.disabled = true;

    table.replaceChildren();
    plumeLayer.clearLayers();

    try {
        const params = new URLSearchParams({
            emission: String(emission),
            height: String(height)
        });

        const response = await fetch(
            `/api/plume?${params}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Ошибка расчёта"
            );
        }

        for (const result of data.results) {
            const row = document.createElement("tr");

            const values = [
                result.source_name,
                result.distance_km,
                result.concentration_ug_m3 === null
                    ? "Не рассчитано"
                    : result.concentration_ug_m3,
                result.status
            ];

            for (const value of values) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            }

            table.appendChild(row);
        }

        const source = data.sources.find(
            item => item.id === selectedId
        );

        if (source) {
            drawPlume(
                source,
                data.wind_direction
            );
        }

        status.textContent =
            `Учебный расчёт выполнен. ` +
            `Ветер ${data.wind_speed} м/с, ` +
            `с ${data.wind_direction}°. ` +
            `Выброс ${emission} г/с, ` +
            `высота ${height} м. ` +
            `Время данных: ${data.wind_time ?? "—"}.`;

    } catch (error) {
        status.textContent = error.message;
        console.error(error);
    } finally {
        button.disabled = false;
    }
}

document.getElementById(
    "calculate-plume"
).addEventListener("click", calculatePlume);

document.getElementById(
    "clear-plume"
).addEventListener("click", () => {
    plumeLayer.clearLayers();

    document.getElementById(
        "plume-status"
    ).textContent = "Шлейф убран с карты.";
});
