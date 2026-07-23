"""Interactive dashboard for live and historical earthquake data."""

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
from src.database import (
    DATABASE_PATH,
    get_database_record_count,
    load_earthquakes_from_database,
)
from src.earthquake_api import fetch_earthquake_data
from src.filters import apply_filters, display_sidebar_filters
from src.statistics import calculate_summary_statistics


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Earthquake Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)


# ---------------------------------------------------------
# Data-loading functions
# ---------------------------------------------------------

@st.cache_data(ttl=300)
def load_live_earthquake_data() -> pd.DataFrame:
    """
    Retrieve the latest USGS earthquake feed.

    Returns:
        Cleaned live earthquake records.
    """
    earthquake_data = fetch_earthquake_data()

    return create_earthquake_dataframe(
        earthquake_data
    )


@st.cache_data(ttl=60)
def load_historical_earthquake_data() -> pd.DataFrame:
    """
    Load accumulated earthquake records from SQLite.

    Returns:
        Historical earthquake records.
    """
    return load_earthquakes_from_database()


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def prepare_dashboard_data(
    earthquake_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate and prepare earthquake records for the dashboard.

    Args:
        earthquake_dataframe: Earthquake records from an API
            or SQLite database.

    Returns:
        Validated earthquake records.
    """
    if earthquake_dataframe.empty:
        return earthquake_dataframe

    required_numeric_columns = [
        "magnitude",
        "depth_km",
        "latitude",
        "longitude",
    ]

    for column in required_numeric_columns:
        if column not in earthquake_dataframe.columns:
            earthquake_dataframe[column] = pd.NA

        earthquake_dataframe[column] = pd.to_numeric(
            earthquake_dataframe[column],
            errors="coerce",
        )

    earthquake_dataframe["event_time"] = pd.to_datetime(
        earthquake_dataframe["event_time"],
        utc=True,
        errors="coerce",
    )

    earthquake_dataframe = earthquake_dataframe.dropna(
        subset=[
            "magnitude",
            "depth_km",
            "latitude",
            "longitude",
            "event_time",
        ]
    ).copy()

    if "place" not in earthquake_dataframe.columns:
        earthquake_dataframe["place"] = "Unknown location"

    earthquake_dataframe["place"] = (
        earthquake_dataframe["place"]
        .fillna("Unknown location")
        .astype(str)
    )

    if "severity" not in earthquake_dataframe.columns:
        earthquake_dataframe["severity"] = "Unknown"

    earthquake_dataframe["severity"] = (
        earthquake_dataframe["severity"]
        .fillna("Unknown")
        .astype(str)
    )

    if "tsunami_alert" not in earthquake_dataframe.columns:
        earthquake_dataframe["tsunami_alert"] = 0

    earthquake_dataframe["tsunami_alert"] = (
        pd.to_numeric(
            earthquake_dataframe["tsunami_alert"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    earthquake_dataframe = (
        earthquake_dataframe.sort_values(
            by="event_time",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    return earthquake_dataframe


# ---------------------------------------------------------
# Summary metric cards
# ---------------------------------------------------------

def display_summary_metrics(
    earthquake_dataframe: pd.DataFrame,
) -> None:
    """
    Display summary metric cards.

    Args:
        earthquake_dataframe: Filtered earthquake records.
    """
    summary = calculate_summary_statistics(
        earthquake_dataframe
    )

    metric_columns = st.columns(5)

    metric_columns[0].metric(
        label="Total Earthquakes",
        value=f"{summary['total_earthquakes']:,}",
    )

    metric_columns[1].metric(
        label="Largest Magnitude",
        value=f"{summary['largest_magnitude']:.1f}",
    )

    metric_columns[2].metric(
        label="Average Magnitude",
        value=f"{summary['average_magnitude']:.2f}",
    )

    metric_columns[3].metric(
        label="Average Depth",
        value=f"{summary['average_depth']:.1f} km",
    )

    metric_columns[4].metric(
        label="Tsunami Alerts",
        value=f"{summary['tsunami_alerts']:,}",
    )


# ---------------------------------------------------------
# Dashboard heading
# ---------------------------------------------------------

st.title("🌍 Global Earthquake Intelligence Dashboard")

st.caption(
    "Explore live USGS earthquake activity and locally "
    "accumulated historical records."
)


# ---------------------------------------------------------
# Data-source selection
# ---------------------------------------------------------

st.sidebar.header("Data Source")

selected_data_source = st.sidebar.selectbox(
    "Choose earthquake dataset",
    options=[
        "Live USGS feed",
        "SQLite historical data",
    ],
    index=0,
)


refresh_data = st.sidebar.button(
    "Refresh selected data",
    type="primary",
    width="stretch",
)


if refresh_data:
    st.cache_data.clear()
    st.rerun()


# ---------------------------------------------------------
# Load selected source
# ---------------------------------------------------------

try:
    if selected_data_source == "Live USGS feed":
        earthquake_dataframe = (
            load_live_earthquake_data()
        )

        source_description = (
            "Displaying earthquakes from the current "
            "USGS past-day feed."
        )

    else:
        earthquake_dataframe = (
            load_historical_earthquake_data()
        )

        source_description = (
            "Displaying all earthquake records currently "
            "stored in the local SQLite database."
        )

except Exception as error:
    st.error(
        f"Unable to load earthquake data: {error}"
    )
    st.stop()


earthquake_dataframe = prepare_dashboard_data(
    earthquake_dataframe
)


# ---------------------------------------------------------
# Handle missing database data
# ---------------------------------------------------------

if earthquake_dataframe.empty:
    if selected_data_source == "SQLite historical data":
        st.warning(
            "The SQLite database does not contain any usable "
            "earthquake records."
        )

        st.code(
            "python main.py",
            language="powershell",
        )

        st.info(
            "Run the data pipeline from the VS Code terminal, "
            "then select SQLite historical data again."
        )

    else:
        st.warning(
            "The live USGS feed did not return any usable "
            "earthquake records."
        )

    st.stop()


# ---------------------------------------------------------
# Source information
# ---------------------------------------------------------

source_column, record_column = st.columns(
    [3, 1]
)

with source_column:
    st.info(source_description)

with record_column:
    if selected_data_source == "SQLite historical data":
        stored_record_count = (
            get_database_record_count()
        )

        st.metric(
            label="Database Records",
            value=f"{stored_record_count:,}",
        )

    else:
        st.metric(
            label="Live Feed Records",
            value=f"{len(earthquake_dataframe):,}",
        )


# ---------------------------------------------------------
# Dashboard filters
# ---------------------------------------------------------

selected_filters = display_sidebar_filters(
    earthquake_dataframe
)


filtered_dataframe = apply_filters(
    earthquake_dataframe,
    selected_filters,
)


# ---------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------

display_summary_metrics(
    filtered_dataframe
)

st.divider()


if filtered_dataframe.empty:
    st.warning(
        "No earthquakes match the selected filters."
    )
    st.stop()


# ---------------------------------------------------------
# Dataset date range
# ---------------------------------------------------------

earliest_event = filtered_dataframe[
    "event_time"
].min()

latest_event = filtered_dataframe[
    "event_time"
].max()


date_column_1, date_column_2 = st.columns(2)

date_column_1.caption(
    f"Earliest displayed event: "
    f"{earliest_event:%Y-%m-%d %H:%M UTC}"
)

date_column_2.caption(
    f"Latest displayed event: "
    f"{latest_event:%Y-%m-%d %H:%M UTC}"
)


# ---------------------------------------------------------
# Dashboard tabs
# ---------------------------------------------------------

map_tab, analysis_tab, records_tab, database_tab = st.tabs(
    [
        "🌍 Earthquake Map",
        "📊 Activity Analysis",
        "📋 Earthquake Records",
        "🗄️ Data Information",
    ]
)


# ---------------------------------------------------------
# Map tab
# ---------------------------------------------------------

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
        "Marker size represents earthquake magnitude. "
        "Marker categories represent severity."
    )


# ---------------------------------------------------------
# Analysis tab
# ---------------------------------------------------------

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
            "severity": "Severity",
            "depth_km": st.column_config.NumberColumn(
                "Depth (km)",
                format="%.1f",
            ),
            "tsunami_alert": st.column_config.CheckboxColumn(
                "Tsunami Alert",
            ),
        },
    )


# ---------------------------------------------------------
# Records tab
# ---------------------------------------------------------

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
            "severity": "Severity",
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

    source_filename = (
        "live"
        if selected_data_source == "Live USGS feed"
        else "historical"
    )

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name=(
            f"{source_filename}_filtered_earthquakes.csv"
        ),
        mime="text/csv",
        type="primary",
    )


# ---------------------------------------------------------
# Database information tab
# ---------------------------------------------------------

with database_tab:
    st.subheader("Data Source Information")

    information_column_1, information_column_2 = (
        st.columns(2)
    )

    with information_column_1:
        st.markdown("#### Selected source")

        st.write(selected_data_source)

        st.metric(
            label="Loaded Records",
            value=f"{len(earthquake_dataframe):,}",
        )

        st.metric(
            label="Filtered Records",
            value=f"{len(filtered_dataframe):,}",
        )

    with information_column_2:
        st.markdown("#### SQLite storage")

        database_exists = DATABASE_PATH.exists()

        st.write(
            f"Database path: `{DATABASE_PATH}`"
        )

        st.write(
            "Database status: "
            + (
                "Available"
                if database_exists
                else "Not created"
            )
        )

        st.metric(
            label="Stored Database Records",
            value=f"{get_database_record_count():,}",
        )

    st.markdown("#### Update historical data")

    st.write(
        "Run the following command periodically to retrieve "
        "the current feed and add new records to SQLite:"
    )

    st.code(
        "python main.py",
        language="powershell",
    )

    st.write(
        "The database uses the USGS earthquake ID as its "
        "primary key, preventing duplicate records."
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()

st.caption(
    "Data source: United States Geological Survey "
    "Earthquake Hazards Program."
)