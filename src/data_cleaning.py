"""Clean and transform raw USGS earthquake data."""

from typing import Any

import pandas as pd


def classify_magnitude(magnitude: float) -> str:
    """
    Assign a readable severity category based on magnitude.

    Args:
        magnitude: Earthquake magnitude.

    Returns:
        Earthquake severity category.
    """
    if pd.isna(magnitude):
        return "Unknown"

    if magnitude < 2.0:
        return "Micro"

    if magnitude < 4.0:
        return "Minor"

    if magnitude < 5.0:
        return "Light"

    if magnitude < 6.0:
        return "Moderate"

    if magnitude < 7.0:
        return "Strong"

    if magnitude < 8.0:
        return "Major"

    return "Great"


def create_earthquake_dataframe(
    earthquake_data: dict[str, Any],
) -> pd.DataFrame:
    """
    Convert raw USGS GeoJSON data into a cleaned DataFrame.

    Args:
        earthquake_data: Complete USGS GeoJSON response.

    Returns:
        Cleaned earthquake DataFrame.
    """
    earthquake_records: list[dict[str, Any]] = []

    for feature in earthquake_data.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []

        if len(coordinates) < 3:
            continue

        earthquake_records.append(
            {
                "earthquake_id": feature.get("id"),
                "place": properties.get("place"),
                "magnitude": properties.get("mag"),
                "longitude": coordinates[0],
                "latitude": coordinates[1],
                "depth_km": coordinates[2],
                "event_time": properties.get("time"),
                "updated_time": properties.get("updated"),
                "status": properties.get("status"),
                "event_type": properties.get("type"),
                "felt_reports": properties.get("felt"),
                "significance": properties.get("sig"),
                "tsunami_alert": properties.get("tsunami"),
                "details_url": properties.get("url"),
            }
        )

    earthquake_dataframe = pd.DataFrame(
        earthquake_records
    )

    if earthquake_dataframe.empty:
        return earthquake_dataframe

    numeric_columns = [
        "magnitude",
        "longitude",
        "latitude",
        "depth_km",
        "felt_reports",
        "significance",
        "tsunami_alert",
    ]

    for column in numeric_columns:
        earthquake_dataframe[column] = pd.to_numeric(
            earthquake_dataframe[column],
            errors="coerce",
        )

    earthquake_dataframe["event_time"] = pd.to_datetime(
        earthquake_dataframe["event_time"],
        unit="ms",
        utc=True,
        errors="coerce",
    )

    earthquake_dataframe["updated_time"] = pd.to_datetime(
        earthquake_dataframe["updated_time"],
        unit="ms",
        utc=True,
        errors="coerce",
    )

    earthquake_dataframe["severity"] = (
        earthquake_dataframe["magnitude"].apply(
            classify_magnitude
        )
    )

    earthquake_dataframe["place"] = (
        earthquake_dataframe["place"]
        .fillna("Unknown location")
        .astype(str)
    )

    earthquake_dataframe["status"] = (
        earthquake_dataframe["status"]
        .fillna("unknown")
        .astype(str)
    )

    earthquake_dataframe = earthquake_dataframe.dropna(
        subset=[
            "magnitude",
            "latitude",
            "longitude",
            "depth_km",
            "event_time",
        ]
    )

    earthquake_dataframe = (
        earthquake_dataframe.sort_values(
            by="event_time",
            ascending=False,
        )
        .drop_duplicates(
            subset=["earthquake_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return earthquake_dataframe