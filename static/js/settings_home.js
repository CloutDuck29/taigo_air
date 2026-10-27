
"use strict";
function formatHomeAddress(fullAddress) {
  if (!fullAddress) return "Дом не выбран";

  const parts = fullAddress
    .split(",")
    .map(part => part.trim())
    .filter(Boolean);

  const district = parts.find(part =>
    /административный округ|округ/i.test(part) &&
    !/федеральный/i.test(part)
  );

  const streetIndex = parts.findIndex(part =>
    /улица|проспект|просп\.|переулок|бульвар|проезд|набережная|шоссе/i.test(part)
  );

  let street = "";

  if (streetIndex !== -1) {
    street = parts.slice(streetIndex, streetIndex + 3).join(", ");
  }

  if (!street) {
    return fullAddress
      .replace(/\b\d{6},?\s*/g, "")
      .replace(/Россия,?\s*/gi, "")
      .replace(/Омская область,?\s*/gi, "")
      .replace(/Сибирский федеральный округ,?\s*/gi, "")
      .trim();
  }

  const shortDistrict = district
    ? district.replace(/административный округ/i, "округ")
    : "";

  return [shortDistrict, street]
    .filter(Boolean)
    .join(", ");
}
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("home-map-toggle");
  const wrap = document.getElementById("home-map-wrap");
  const coordinates = document.getElementById("home-coordinates");
  const address = document.getElementById("home-address-text");
  if (address && address.textContent.trim() !== "Дом не выбран") {
  address.textContent = formatHomeAddress(address.textContent.trim());
}
  const mapStatus = document.getElementById("home-map-status");
  const form = document.getElementById("home-form");
  const saveButton = document.getElementById("home-save");
  const saveStatus = document.getElementById("home-save-status");

  if (!toggle || !wrap || !coordinates || !form) return;

  const savedLat = coordinates.dataset.latitude;
  const savedLon = coordinates.dataset.longitude;

  let latitude = savedLat === "" ? null : Number(savedLat);
  let longitude = savedLon === "" ? null : Number(savedLon);

  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    latitude = null;
    longitude = null;
  }

  let map = null;
  let marker = null;
  let requestId = 0;
  let dirty = false;

  function markChanged() {
    dirty = true;
    saveStatus.textContent = "Есть несохранённые изменения.";
  }

  function initMap() {
    if (map) {
      map.invalidateSize();
      return;
    }

    if (typeof L === "undefined") {
      mapStatus.textContent = "Не удалось загрузить карту.";
      return;
    }

    map = L.map("home-map", {
      zoomControl: true,
      attributionControl: true
    }).setView(
      latitude !== null && longitude !== null
        ? [latitude, longitude]
        : [54.99, 73.37],
      latitude !== null ? 15 : 11
    );

    map.attributionControl.setPrefix(false);

    L.tileLayer(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
      }
    ).addTo(map);

    // Прокрутка страницы не должна приближать карту.
map.scrollWheelZoom.disable();
map.dragging.disable();

const interactionButton = document.getElementById(
  "home-map-interaction"
);

const mapElement = document.getElementById("home-map");

let interactive = false;

function applyInteractionMode() {
  if (interactive) {
    map.dragging.enable();
    map.touchZoom.enable();
  } else {
    map.dragging.disable();
    map.touchZoom.disable();
  }

  mapElement.classList.toggle("map-interactive", interactive);
  interactionButton.classList.toggle("active", interactive);

  interactionButton.setAttribute(
    "aria-pressed",
    String(interactive)
  );

  interactionButton.setAttribute(
    "aria-label",
    interactive
      ? "Выключить управление картой"
      : "Включить управление картой"
  );
}

interactionButton.addEventListener("click", () => {
  interactive = !interactive;
  applyInteractionMode();
});

applyInteractionMode();

    if (latitude !== null && longitude !== null) {
      marker = L.marker([latitude, longitude]).addTo(map);
    }

    map.on("click", async event => {
      latitude = event.latlng.lat;
      longitude = event.latlng.lng;

      if (marker) {
        marker.setLatLng([latitude, longitude]);
      } else {
        marker = L.marker([latitude, longitude]).addTo(map);
      }

      markChanged();

      const currentRequest = ++requestId;

      address.textContent = "Определяем адрес...";
      mapStatus.textContent = "Получаем адрес выбранной точки...";

      try {
        const params = new URLSearchParams({
          lat: String(latitude),
          lon: String(longitude)
        });

        const response = await fetch(
          `/api/map/address?${params}`,
          { cache: "no-store" }
        );

        const data = await response.json();

        if (currentRequest !== requestId) return;

        if (!response.ok) {
          throw new Error(data.error || "Адрес недоступен");
        }

        address.textContent = formatHomeAddress(data.address);
        mapStatus.textContent =
          "Дом выбран. Нажми «Сохранить дом».";

      } catch (error) {
        if (currentRequest !== requestId) return;

        address.textContent =
          `Точка: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

        mapStatus.textContent =
          "Не удалось определить адрес. Точку можно сохранить.";
      }
    });
  }

  toggle.addEventListener("click", () => {
    const open = wrap.hidden;

    wrap.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));

    if (open) {
      requestAnimationFrame(() => {
        initMap();
        map?.invalidateSize();
      });
    }
  });

  form.addEventListener("input", markChanged);
  form.addEventListener("change", markChanged);

  form.addEventListener("submit", async event => {
    event.preventDefault();

    if (latitude === null || longitude === null) {
      saveStatus.textContent =
        "Сначала выбери дом на карте.";

      if (wrap.hidden) toggle.click();
      return;
    }

    const data = {
      latitude,
      longitude,
      floor: Number(document.getElementById("home-floor").value),
      window_direction:
        document.getElementById("home-direction").value,
      room_area: Number(document.getElementById("home-area").value),
      ceiling_height:
        Number(document.getElementById("home-height").value)
    };

    saveButton.disabled = true;
    saveStatus.textContent = "Сохранение...";

    try {
      const response = await fetch("/api/map/apartment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || "Не удалось сохранить дом");
      }

      address.textContent = formatHomeAddress(result.address);
      coordinates.dataset.latitude = String(latitude);
      coordinates.dataset.longitude = String(longitude);

      dirty = false;
      saveStatus.textContent = "Дом успешно сохранён.";
      mapStatus.textContent = "Расположение сохранено.";

      wrap.hidden = true;
      toggle.setAttribute("aria-expanded", "false");

    } catch (error) {
      saveStatus.textContent = error.message;
    } finally {
      saveButton.disabled = false;
    }
  });
});
