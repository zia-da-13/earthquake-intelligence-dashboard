"""Analytics functions for the Earthquake Intelligence Dashboard."""

import pandas as pd


def get_top_locations(
    earthquake_dataframe: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the locations with the most earthquakes.

    Args:
        earthquake_dataframe: Earthquake records.
        top_n: Number of locations to return.

    Returns:
        DataFrame of earthquake counts by location.
    """
    top_locations = (
        earthquake_dataframe.groupby("place")
        .size()
        .reset_index(name="earthquake_count")
        .sort_values(
            by="earthquake_count",
            ascending=False,
        )
        .head(top_n)
    )

    return top_locations


def get_largest_earthquakes(
    earthquake_dataframe: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the strongest earthquakes.

    Args:
        earthquake_dataframe: Earthquake records.
        top_n: Number of earthquakes.

    Returns:
        Largest earthquakes.
    """
    return (
        earthquake_dataframe.sort_values(
            by="magnitude",
            ascending=False,
        )
        .head(top_n)
    )


def get_deepest_earthquakes(
    earthquake_dataframe: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the deepest earthquakes.

    Args:
        earthquake_dataframe: Earthquake records.
        top_n: Number of earthquakes.

    Returns:
        Deepest earthquakes.
    """
    return (
        earthquake_dataframe.sort_values(
            by="depth_km",
            ascending=False,
        )
        .head(top_n)
    )


def get_hourly_activity(
    earthquake_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count earthquakes by hour of day.

    Args:
        earthquake_dataframe: Earthquake records.

    Returns:
        Hourly activity.
    """
    hourly_dataframe = earthquake_dataframe.copy()

    hourly_dataframe["hour"] = (
        hourly_dataframe["event_time"].dt.hour
    )

    return (
        hourly_dataframe.groupby("hour")
        .size()
        .reset_index(name="earthquake_count")
        .sort_values("hour")
    )


def get_daily_activity(
    earthquake_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count earthquakes by day.

    Args:
        earthquake_dataframe: Earthquake records.

    Returns:
        Daily activity.
    """
    daily_dataframe = earthquake_dataframe.copy()

    daily_dataframe["date"] = (
        hourly_dataframe := daily_dataframe["event_time"].dt.date
    )

    return (
        daily_dataframe.groupby("date")
        .size()
        .reset_index(name="earthquake_count")
        .sort_values("date")
    )


def get_summary_statistics(
    earthquake_dataframe: pd.DataFrame,
) -> dict:
    """
    Return additional analytics.

    Args:
        earthquake_dataframe: Earthquake records.

    Returns:
        Dictionary of analytics.
    """
    return {
        "average_magnitude": round(
            earthquake_dataframe["magnitude"].mean(),
            2,
        ),
        "largest_magnitude": round(
            earthquake_dataframe["magnitude"].max(),
            2,
        ),
        "deepest_earthquake": round(
            earthquake_dataframe["depth_km"].max(),
            1,
        ),
        "average_depth": round(
            earthquake_dataframe["depth_km"].mean(),
            1,
        ),
        "tsunami_alerts": int(
            earthquake_dataframe[
                "tsunami_alert"
            ].sum()
        ),
    }