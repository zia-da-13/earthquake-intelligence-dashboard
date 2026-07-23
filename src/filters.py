"""Create and apply Streamlit sidebar filters."""

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st


SEVERITY_ORDER = [
    "Micro",
    "Minor",
    "Light",
    "Moderate",
    "Strong",
    "Major",
    "Great",
    "Unknown",
]


def display_sidebar_filters(
    earthquake_dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Display all dashboard filters in the Streamlit sidebar.

    Args:
        earthquake_dataframe: Complete cleaned earthquake dataset.

    Returns:
        Dictionary containing the selected filter values.
    """
    st.sidebar.divider()
    st.sidebar.header("Dashboard Filters")

    minimum_magnitude = float(
        earthquake_dataframe["magnitude"].min()
    )

    maximum_magnitude = float(
        earthquake_dataframe["magnitude"].max()
    )

    selected_magnitude_range = st.sidebar.slider(
        "Magnitude range",
        min_value=minimum_magnitude,
        max_value=maximum_magnitude,
        value=(
            minimum_magnitude,
            maximum_magnitude,
        ),
        step=0.1,
    )

    minimum_depth = float(
        earthquake_dataframe["depth_km"].min()
    )

    maximum_depth = float(
        earthquake_dataframe["depth_km"].max()
    )

    selected_depth_range = st.sidebar.slider(
        "Depth range in kilometers",
        min_value=minimum_depth,
        max_value=maximum_depth,
        value=(
            minimum_depth,
            maximum_depth,
        ),
        step=1.0,
    )

    available_severities = [
        severity
        for severity in SEVERITY_ORDER
        if severity
        in earthquake_dataframe["severity"]
        .dropna()
        .unique()
    ]

    selected_severities = st.sidebar.multiselect(
        "Severity categories",
        options=available_severities,
        default=available_severities,
    )

    search_location = st.sidebar.text_input(
        "Search location",
        placeholder="Example: California",
    )

    tsunami_only = st.sidebar.checkbox(
        "Show tsunami alerts only",
        value=False,
    )

    st.sidebar.divider()
    st.sidebar.subheader("Event Date Range")

    valid_event_times = earthquake_dataframe[
        "event_time"
    ].dropna()

    if valid_event_times.empty:
        minimum_event_date = date.today()
        maximum_event_date = date.today()

    else:
        minimum_event_date = (
            valid_event_times.min().date()
        )

        maximum_event_date = (
            valid_event_times.max().date()
        )

    selected_date_range = st.sidebar.date_input(
        "Select event dates",
        value=(
            minimum_event_date,
            maximum_event_date,
        ),
        min_value=minimum_event_date,
        max_value=maximum_event_date,
    )

    if isinstance(selected_date_range, tuple):
        if len(selected_date_range) == 2:
            selected_start_date = selected_date_range[0]
            selected_end_date = selected_date_range[1]

        elif len(selected_date_range) == 1:
            selected_start_date = selected_date_range[0]
            selected_end_date = selected_date_range[0]

        else:
            selected_start_date = minimum_event_date
            selected_end_date = maximum_event_date

    else:
        selected_start_date = selected_date_range
        selected_end_date = selected_date_range

    return {
        "magnitude_range": selected_magnitude_range,
        "depth_range": selected_depth_range,
        "severities": selected_severities,
        "search_location": search_location,
        "tsunami_only": tsunami_only,
        "start_date": selected_start_date,
        "end_date": selected_end_date,
    }


def apply_filters(
    earthquake_dataframe: pd.DataFrame,
    selected_filters: dict[str, Any],
) -> pd.DataFrame:
    """
    Apply sidebar filter values to earthquake data.

    Args:
        earthquake_dataframe: Complete earthquake dataset.
        selected_filters: Values selected in the sidebar.

    Returns:
        Filtered earthquake dataset.
    """
    magnitude_range = selected_filters[
        "magnitude_range"
    ]

    depth_range = selected_filters[
        "depth_range"
    ]

    selected_severities = selected_filters[
        "severities"
    ]

    search_location = selected_filters[
        "search_location"
    ]

    tsunami_only = selected_filters[
        "tsunami_only"
    ]

    selected_start_date = selected_filters[
        "start_date"
    ]

    selected_end_date = selected_filters[
        "end_date"
    ]

    filtered_dataframe = earthquake_dataframe[
        earthquake_dataframe["magnitude"].between(
            magnitude_range[0],
            magnitude_range[1],
        )
        & earthquake_dataframe["depth_km"].between(
            depth_range[0],
            depth_range[1],
        )
        & earthquake_dataframe["severity"].isin(
            selected_severities
        )
    ].copy()

    if selected_start_date and selected_end_date:
        start_timestamp = pd.Timestamp(
            selected_start_date,
            tz="UTC",
        )

        end_timestamp = (
            pd.Timestamp(
                selected_end_date,
                tz="UTC",
            )
            + pd.Timedelta(days=1)
            - pd.Timedelta(microseconds=1)
        )

        filtered_dataframe = filtered_dataframe[
            filtered_dataframe["event_time"].between(
                start_timestamp,
                end_timestamp,
            )
        ]

    if search_location:
        filtered_dataframe = filtered_dataframe[
            filtered_dataframe["place"]
            .fillna("")
            .str.contains(
                search_location,
                case=False,
                na=False,
            )
        ]

    if tsunami_only:
        filtered_dataframe = filtered_dataframe[
            filtered_dataframe["tsunami_alert"]
            .fillna(0)
            .astype(int)
            .eq(1)
        ]

    return (
        filtered_dataframe.sort_values(
            by="event_time",
            ascending=False,
        )
        .reset_index(drop=True)
    )