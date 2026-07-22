"""Interactive dashboard for live USGS earthquake data."""

import pandas as pd
import streamlit as st

from src.charts import (
    create_activity_timeline,
    create_depth_scatter,
    create_earthquake_map,
    create_magnitude_histogram,
    create_severity_chart,
)
from src.data_cleaning import create_earthquake_dataframe
from src.earthquake_api import fetch_earthquake_data
from src.filters import apply_filters, display_sidebar_filters
from src.statistics import calculate_summary_statistics


st.set_page_config(
    page_title="Earthquake Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_earthquake_data() -> pd.DataFrame:
    """
    Retrieve live earthquake data and return a clean DataFrame.
    """
    earthquake_data = fetch_earthquake_data()
    return create_earthquake_dataframe(earthquake_data)


def display_summary_metrics(
    earthquake_dataframe: pd.DataFrame,
) -> None:
    """
    Display summary metric cards.

    Args:
        earthquake_dataframe: Filtered earthquake records.
    """
    statistics = calculate_summary_statistics(
        earthquake_dataframe
    )

    metric_columns = st.columns(5)

    metric_columns[0].metric(
        label="Total Earthquakes",
        value=f"{statistics['total_earthquakes']:,}",
    )

    metric_columns[1].metric(
        label="Largest Magnitude",
        value=f"{statistics['largest_magnitude']:.1f}",
    )

    metric_columns[2].metric(
        label="Average Magnitude",
        value=f"{statistics['average_magnitude']:.2f}",
    )

    metric_columns[3].metric(
        label="Average Depth",
        value=f"{statistics['average_depth']:.1f} km",
    )

    metric_columns[4].metric(
        label="Tsunami Alerts",
        value=f"{statistics['tsunami_alerts']:,}",
    )


st.title("🌍 Global Earthquake Intelligence Dashboard")

st.caption(
    "Live global earthquake activity from the "
    "USGS past-day earthquake feed."
)


try:
    earthquake_dataframe = load_earthquake_data()

except Exception as error:
    st.error(
        f"Unable to retrieve earthquake data: {error}"
    )
    st.stop()


if earthquake_dataframe.empty:
    st.warning(
        "No earthquake records are currently available."
    )
    st.stop()


required_numeric_columns = [
    "magnitude",
    "depth_km",
    "latitude",
    "longitude",
]


for column in required_numeric_columns:
    earthquake_dataframe[column] = pd.to_numeric(
        earthquake_dataframe[column],
        errors="coerce",
    )


earthquake_dataframe = earthquake_dataframe.dropna(
    subset=required_numeric_columns
).copy()


earthquake_dataframe["event_time"] = pd.to_datetime(
    earthquake_dataframe["event_time"],
    utc=True,
    errors="coerce",
)


if earthquake_dataframe.empty:
    st.warning(
        "No valid earthquake records are available."
    )
    st.stop()


selected_filters = display_sidebar_filters(
    earthquake_dataframe
)


if st.sidebar.button(
    "Refresh earthquake data",
    type="primary",
):
    st.cache_data.clear()
    st.rerun()


filtered_dataframe = apply_filters(
    earthquake_dataframe,
    selected_filters,
)


display_summary_metrics(
    filtered_dataframe
)


st.divider()


if filtered_dataframe.empty:
    st.warning(
        "No earthquakes match the selected filters."
    )
    st.stop()


map_tab, analysis_tab, records_tab = st.tabs(
    [
        "🌍 Earthquake Map",
        "📊 Activity Analysis",
        "📋 Earthquake Records",
    ]
)


with map_tab:
    st.subheader("Interactive Earthquake Map")

    earthquake_map = create_earthquake_map(
        filtered_dataframe
    )

    st.plotly_chart(
        earthquake_map,
        width="stretch",
    )

    st.info(
        "Marker size represents magnitude. "
        "Marker categories represent earthquake severity."
    )


with analysis_tab:
    st.subheader("Earthquake Activity Over Time")

    activity_timeline = create_activity_timeline(
        filtered_dataframe
    )

    st.plotly_chart(
        activity_timeline,
        width="stretch",
    )

    chart_column_1, chart_column_2 = st.columns(2)

    with chart_column_1:
        magnitude_histogram = (
            create_magnitude_histogram(
                filtered_dataframe
            )
        )

        st.plotly_chart(
            magnitude_histogram,
            width="stretch",
        )

    with chart_column_2:
        severity_chart = create_severity_chart(
            filtered_dataframe
        )

        st.plotly_chart(
            severity_chart,
            width="stretch",
        )

    depth_scatter = create_depth_scatter(
        filtered_dataframe
    )

    st.plotly_chart(
        depth_scatter,
        width="stretch",
    )

    st.subheader("Strongest Earthquakes")

    strongest_earthquakes = (
        filtered_dataframe.sort_values(
            by="magnitude",
            ascending=False,
        )
        .head(10)
    )

    strongest_columns = [
        "event_time",
        "place",
        "magnitude",
        "severity",
        "depth_km",
        "tsunami_alert",
    ]

    st.dataframe(
        strongest_earthquakes[
            strongest_columns
        ],
        width="stretch",
        hide_index=True,
    )


with records_tab:
    st.subheader("Filtered Earthquake Records")

    display_columns = [
        "event_time",
        "place",
        "magnitude",
        "severity",
        "depth_km",
        "latitude",
        "longitude",
        "tsunami_alert",
        "status",
        "details_url",
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in filtered_dataframe.columns
    ]

    records_dataframe = filtered_dataframe[
        available_display_columns
    ].copy()

    st.dataframe(
        records_dataframe,
        width="stretch",
        hide_index=True,
        column_config={
            "event_time": st.column_config.DatetimeColumn(
                "Event Time",
                format="YYYY-MM-DD HH:mm:ss",
            ),
            "place": "Location",
            "magnitude": st.column_config.NumberColumn(
                "Magnitude",
                format="%.1f",
            ),
            "depth_km": st.column_config.NumberColumn(
                "Depth (km)",
                format="%.1f",
            ),
            "latitude": st.column_config.NumberColumn(
                "Latitude",
                format="%.3f",
            ),
            "longitude": st.column_config.NumberColumn(
                "Longitude",
                format="%.3f",
            ),
            "tsunami_alert": st.column_config.CheckboxColumn(
                "Tsunami Alert",
            ),
            "details_url": st.column_config.LinkColumn(
                "USGS Details",
                display_text="Open event",
            ),
        },
    )

    csv_data = records_dataframe.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_earthquakes.csv",
        mime="text/csv",
        type="primary",
    )


st.divider()

st.caption(
    "Data source: United States Geological Survey "
    "Earthquake Hazards Program."
)