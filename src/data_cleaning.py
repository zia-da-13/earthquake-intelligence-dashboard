"""
Convert raw USGS earthquake data into a clean pandas DataFrame.
"""

import pandas as pd


def create_earthquake_dataframe(earthquake_data):
    records = []

    for feature in earthquake_data.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])

        if len(coordinates) < 3:
            continue

        records.append(
            {
                "earthquake_id": feature.get("id"),
                "place": properties.get("place"),
                "magnitude": properties.get("mag"),
                "longitude": coordinates[0],
                "latitude": coordinates[1],
                "depth_km": coordinates[2],
                "event_time": properties.get("time"),
                "status": properties.get("status"),
                "tsunami_alert": properties.get("tsunami"),
                "details_url": properties.get("url"),
            }
        )

    dataframe = pd.DataFrame(records)

    if dataframe.empty:
        return dataframe

    dataframe["event_time"] = pd.to_datetime(
        dataframe["event_time"],
        unit="ms",
        utc=True,
        errors="coerce",
    )

    dataframe["magnitude"] = pd.to_numeric(
        dataframe["magnitude"],
        errors="coerce",
    )

    dataframe["depth_km"] = pd.to_numeric(
        dataframe["depth_km"],
        errors="coerce",
    )

    dataframe = dataframe.sort_values(
        by="event_time",
        ascending=False,
    ).reset_index(drop=True)

    return dataframe