
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def get_address(latitude, longitude):
    """Определяет адрес по координатам."""

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
                "accept-language": "ru",
                "zoom": 18
            },
            headers={
                "User-Agent": "TaigoAir/0.1 (educational project)"
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
        address = data.get("address", {})

        street = (
            address.get("road")
            or address.get("pedestrian")
            or address.get("residential")
        )

        house_number = address.get("house_number")

        if street and house_number:
            return f"Омск, {street}, {house_number}"

        # Если точный адрес определить не удалось,
        # возвращаем описание места, но не старый адрес.
        return data.get("display_name")

    except (requests.RequestException, ValueError):
        return None
