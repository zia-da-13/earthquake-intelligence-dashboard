"""Retrieve live earthquake information from the USGS API."""

from typing import Any

import requests


USGS_EARTHQUAKE_URL = (
    "https://earthquake.usgs.gov/"
    "earthquakes/feed/v1.0/summary/all_day.geojson"
)


def fetch_earthquake_data() -> dict[str, Any]:
    """
    Retrieve earthquakes recorded during the past day.

    Returns:
        Complete USGS GeoJSON response.

    Raises:
        requests.RequestException: If the request fails.
        ValueError: If the response is missing earthquake features.
    """
    response = requests.get(
        USGS_EARTHQUAKE_URL,
        timeout=30,
    )

    response.raise_for_status()

    earthquake_data = response.json()

    if "features" not in earthquake_data:
        raise ValueError(
            "The USGS response does not contain earthquake features."
        )

    return earthquake_data