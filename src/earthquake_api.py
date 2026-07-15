"""
Retrieve live earthquake information from the USGS API.
"""

import requests

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


def fetch_earthquake_data():
    """
    Fetch live earthquake data from the USGS feed.

    Returns:
        dict: JSON response from the API.
    """
    response = requests.get(USGS_URL, timeout=30)
    response.raise_for_status()
    return response.json()