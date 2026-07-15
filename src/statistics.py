"""Calculate summary statistics for earthquake data."""

from typing import Any

import pandas as pd


def calculate_summary_statistics(
    earthquake_dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Calculate dashboard summary statistics.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        A dictionary containing dashboard metrics.
    """
    if earthquake_dataframe.empty:
        return {
            "total_earthquakes": 0,
            "largest_magnitude": 0.0,
            "average_magnitude": 0.0,
            "average_depth": 0.0,
            "tsunami_alerts": 0,
        }

    total_earthquakes = len(earthquake_dataframe)

    largest_magnitude = float(
        earthquake_dataframe["magnitude"].max()
    )

    average_magnitude = float(
        earthquake_dataframe["magnitude"].mean()
    )

    average_depth = float(
        earthquake_dataframe["depth_km"].mean()
    )

    tsunami_alerts = int(
        earthquake_dataframe["tsunami_alert"]
        .fillna(0)
        .sum()
    )

    return {
        "total_earthquakes": total_earthquakes,
        "largest_magnitude": largest_magnitude,
        "average_magnitude": average_magnitude,
        "average_depth": average_depth,
        "tsunami_alerts": tsunami_alerts,
    }