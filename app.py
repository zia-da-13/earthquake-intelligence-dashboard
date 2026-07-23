"""Interactive dashboard for live and historical earthquake data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics import (
    get_daily_activity,
    get_deepest_earthquakes,
    get_hourly_activity,
    get_largest_earthquakes,
    get_top_locations,
)
from src.charts import (
    create_activity_timeline,
    create_depth_scatter,
    create_earthquake_map,
    create_magnitude_histogram,
    create_severity_chart,
)
from src.data_cleaning import classify_magnitude, create_earthquake_dataframe
from src.database import (
    DATABASE_PATH,
    get_database_record_count,
    load_earthquakes_from_database,
)
from src.earthquake_api import fetch_earthquake_data
from src.filters import apply_filters, display_sidebar_filters
from src.statistics import calculate_summary_statistics


st.set_page_config(
    page_title="Earthquake Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_live_earthquake_data() -> pd.DataFrame:
    """Retrieve and clean the current USGS earthquake feed."""
    raw_earthquake_data = fetch_earthquake_data()
    return create_earthquake_dataframe(raw_earthquake_data)


@st.cache_data(ttl=60)
def load_historical_earthquake_data() -> pd.DataFrame:
    """Load accumulated earthquake records from SQLite."""
    return load_earthquakes_from_database()


def prepare_dashboard_data(
    earthquake_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and prepare earthquake records for the dashboard."""
    if earthquake_dataframe.empty:
        return earthquake_dataframe.copy()

    prepared_dataframe = earthquake_dataframe.copy()

    numeric_columns = [
        "magnitude",
        "depth_km",
        "latitude",
        "longitude",
        "tsunami_alert",
    ]

    for column in numeric_columns:
        if column not in prepared_dataframe.columns:
            prepared_dataframe[column] = pd.NA

        prepared_dataframe[column] = pd.to_numeric(
            prepared_dataframe[column],
            errors="coerce",
        )

    if "event_time" not in prepared_dataframe.columns:
        prepared_dataframe["event_time"] = pd.NaT

    prepared_dataframe["event_time"] = pd.to_datetime(
        prepared_dataframe["event_time"],
        utc=True,
        errors="coerce",
    )

    prepared_dataframe = prepared_dataframe.dropna(
        subset=[
            "magnitude",
            "depth_km",
            "latitude",
            "longitude",
            "event_time",
        ]
    ).copy()

    if "place" not in prepared_dataframe.columns:
        prepared_dataframe["place"] = "Unknown location"

    prepared_dataframe["place"] = (
        prepared_dataframe["place"]
        .fillna("Unknown location")
        .astype(str)
    )

    if "severity" not in prepared_dataframe.columns:
        prepared_dataframe["severity"] = prepared_dataframe[
            "magnitude"
        ].apply(classify_magnitude)
    else:
        prepared_dataframe["severity"] = (
            prepared_dataframe["severity"]
            .fillna("")
            .astype(str)
        )

        missing_severity = (
            prepared_dataframe["severity"]
            .str.strip()
            .eq("")
        )

        prepared_dataframe.loc[
            missing_severity,
            "severity",
        ] = prepared_dataframe.loc[
            missing_severity,
            "magnitude",
        ].apply(classify_magnitude)

    prepared_dataframe["tsunami_alert"] = (
        prepared_dataframe["tsunami_alert"]
        .fillna(0)
        .astype(int)
    )

    for column in ["status", "details_url", "earthquake_id"]:
        if column not in prepared_dataframe.columns:
            prepared_dataframe[column] = ""

        prepared_dataframe[column] = (
            prepared_dataframe[column]
            .fillna("")
            .astype(str)
        )

    return (
        prepared_dataframe.sort_values(
            by="event_time",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def display_summary_metrics(
    earthquake_dataframe: pd.DataFrame,
) -> None:
    """Display headline earthquake metrics."""
    summary = calculate_summary_statistics(earthquake_dataframe)
    metric_columns = st.columns(5)

    metric_columns[0].metric(
        "Total Earthquakes",
        f"{summary['total_earthquakes']:,}",
    )
    metric_columns[1].metric(
        "Largest Magnitude",
        f"{summary['largest_magnitude']:.1f}",
    )
    metric_columns[2].metric(
        "Average Magnitude",
        f"{summary['average_magnitude']:.2f}",
    )
    metric_columns[3].metric(
        "Average Depth",
        f"{summary['average_depth']:.1f} km",
    )
    metric_columns[4].metric(
        "Tsunami Alerts",
        f"{summary['tsunami_alerts']:,}",
    )


def display_earthquake_table(
    earthquake_dataframe: pd.DataFrame,
) -> None:
    """Display a formatted table of earthquake records."""
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

    available_columns = [
        column
        for column in display_columns
        if column in earthquake_dataframe.columns
    ]

    st.dataframe(
        earthquake_dataframe[available_columns].copy(),
        use_container_width=True,
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
            "status": "Status",
            "details_url": st.column_config.LinkColumn(
                "USGS Details",
                display_text="Open event",
            ),
        },
    )


def display_ranked_table(
    earthquake_dataframe: pd.DataFrame,
    columns: list[str],
) -> None:
    """Display a compact ranked earthquake table."""
    st.dataframe(
        earthquake_dataframe[columns],
        use_container_width=True,
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
        },
    )


st.title("🌍 Global Earthquake Intelligence Dashboard")
st.caption(
    "Explore live USGS earthquake activity and historical "
    "records accumulated in SQLite."
)

st.sidebar.header("Data Source")
selected_data_source = st.sidebar.selectbox(
    "Choose earthquake dataset",
    options=[
        "Live USGS feed",
        "SQLite historical data",
    ],
    index=0,
)

if st.sidebar.button(
    "Refresh selected data",
    type="primary",
    use_container_width=True,
):
    st.cache_data.clear()
    st.rerun()

try:
    if selected_data_source == "Live USGS feed":
        earthquake_dataframe = load_live_earthquake_data()
        source_description = (
            "Displaying records from the current USGS "
            "past-day earthquake feed."
        )
    else:
        earthquake_dataframe = load_historical_earthquake_data()
        source_description = (
            "Displaying accumulated records from the local "
            "SQLite earthquake database."
        )
except Exception as error:
    st.error(f"Unable to load earthquake data: {error}")
    st.stop()

earthquake_dataframe = prepare_dashboard_data(earthquake_dataframe)

if earthquake_dataframe.empty:
    if selected_data_source == "SQLite historical data":
        st.warning(
            "The SQLite database does not contain usable "
            "earthquake records."
        )
        st.write(
            "Run this command in the VS Code terminal to "
            "populate the database:"
        )
        st.code("python main.py", language="powershell")
    else:
        st.warning(
            "The live USGS feed did not return usable "
            "earthquake records."
        )
    st.stop()

source_column, record_column = st.columns([3, 1])
with source_column:
    st.info(source_description)
with record_column:
    if selected_data_source == "SQLite historical data":
        st.metric(
            "Database Records",
            f"{get_database_record_count():,}",
        )
    else:
        st.metric(
            "Live Feed Records",
            f"{len(earthquake_dataframe):,}",
        )

selected_filters = display_sidebar_filters(earthquake_dataframe)
filtered_dataframe = apply_filters(
    earthquake_dataframe,
    selected_filters,
)

if filtered_dataframe.empty:
    st.warning("No earthquakes match the selected filters.")
    st.stop()

display_summary_metrics(filtered_dataframe)
st.divider()

earliest_event = filtered_dataframe["event_time"].min()
latest_event = filtered_dataframe["event_time"].max()

date_column_1, date_column_2 = st.columns(2)
date_column_1.caption(
    "Earliest displayed event: "
    f"{earliest_event:%Y-%m-%d %H:%M UTC}"
)
date_column_2.caption(
    "Latest displayed event: "
    f"{latest_event:%Y-%m-%d %H:%M UTC}"
)

(
    map_tab,
    analysis_tab,
    insights_tab,
    records_tab,
    information_tab,
) = st.tabs(
    [
        "🌍 Earthquake Map",
        "📊 Activity Analysis",
        "📈 Insights",
        "📋 Earthquake Records",
        "🗄️ Data Information",
    ]
)

with map_tab:
    st.subheader("Interactive Earthquake Map")
    st.plotly_chart(
        create_earthquake_map(filtered_dataframe),
        use_container_width=True,
    )
    st.info(
        "Marker size represents magnitude. Marker category "
        "represents earthquake severity."
    )

with analysis_tab:
    st.subheader("Earthquake Activity Over Time")
    st.plotly_chart(
        create_activity_timeline(filtered_dataframe),
        use_container_width=True,
    )

    chart_column_1, chart_column_2 = st.columns(2)
    with chart_column_1:
        st.plotly_chart(
            create_magnitude_histogram(filtered_dataframe),
            use_container_width=True,
        )
    with chart_column_2:
        st.plotly_chart(
            create_severity_chart(filtered_dataframe),
            use_container_width=True,
        )

    st.plotly_chart(
        create_depth_scatter(filtered_dataframe),
        use_container_width=True,
    )

    st.subheader("Strongest Earthquakes")
    strongest_earthquakes = (
        filtered_dataframe.sort_values(
            by="magnitude",
            ascending=False,
        )
        .head(10)
    )

    st.dataframe(
        strongest_earthquakes[
            [
                "event_time",
                "place",
                "magnitude",
                "severity",
                "depth_km",
                "tsunami_alert",
            ]
        ],
        use_container_width=True,
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

with insights_tab:
    st.subheader("Earthquake Insights")
    insight_summary = calculate_summary_statistics(
        filtered_dataframe
    )

    insight_column_1, insight_column_2, insight_column_3 = st.columns(3)
    insight_column_1.metric(
        "Largest Magnitude",
        f"{insight_summary['largest_magnitude']:.1f}",
    )
    insight_column_2.metric(
        "Average Depth",
        f"{insight_summary['average_depth']:.1f} km",
    )
    insight_column_3.metric(
        "Tsunami Alerts",
        f"{insight_summary['tsunami_alerts']:,}",
    )

    st.divider()
    ranked_column_1, ranked_column_2 = st.columns(2)

    with ranked_column_1:
        st.markdown("### Strongest Earthquakes")
        largest_earthquakes = get_largest_earthquakes(
            filtered_dataframe,
            top_n=10,
        )
        display_ranked_table(
            largest_earthquakes,
            [
                "event_time",
                "place",
                "magnitude",
                "depth_km",
            ],
        )

    with ranked_column_2:
        st.markdown("### Deepest Earthquakes")
        deepest_earthquakes = get_deepest_earthquakes(
            filtered_dataframe,
            top_n=10,
        )
        display_ranked_table(
            deepest_earthquakes,
            [
                "event_time",
                "place",
                "depth_km",
                "magnitude",
            ],
        )

    st.markdown("### Most Active Locations")
    top_locations = get_top_locations(
        filtered_dataframe,
        top_n=10,
    )
    st.dataframe(
        top_locations,
        use_container_width=True,
        hide_index=True,
        column_config={
            "place": "Location",
            "earthquake_count": st.column_config.NumberColumn(
                "Earthquake Count",
                format="%d",
            ),
        },
    )

    activity_column_1, activity_column_2 = st.columns(2)
    with activity_column_1:
        st.markdown("### Earthquakes by Hour")
        hourly_activity = get_hourly_activity(filtered_dataframe)
        st.bar_chart(
            hourly_activity.set_index("hour"),
            use_container_width=True,
        )

    with activity_column_2:
        st.markdown("### Earthquakes by Day")
        daily_activity = get_daily_activity(filtered_dataframe)
        st.line_chart(
            daily_activity.set_index("date"),
            use_container_width=True,
        )

with records_tab:
    st.subheader("Filtered Earthquake Records")
    display_earthquake_table(filtered_dataframe)

    download_columns = [
        "earthquake_id",
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

    available_download_columns = [
        column
        for column in download_columns
        if column in filtered_dataframe.columns
    ]

    csv_data = filtered_dataframe[
        available_download_columns
    ].to_csv(index=False).encode("utf-8")

    filename_prefix = (
        "live"
        if selected_data_source == "Live USGS feed"
        else "historical"
    )

    st.download_button(
        "Download Filtered Data as CSV",
        data=csv_data,
        file_name=(
            f"{filename_prefix}_filtered_earthquakes.csv"
        ),
        mime="text/csv",
        type="primary",
    )

with information_tab:
    st.subheader("Data Source Information")
    information_column_1, information_column_2 = st.columns(2)

    with information_column_1:
        st.markdown("### Selected Dataset")
        st.write(selected_data_source)
        st.metric(
            "Loaded Records",
            f"{len(earthquake_dataframe):,}",
        )
        st.metric(
            "Filtered Records",
            f"{len(filtered_dataframe):,}",
        )

        dataset_start = earthquake_dataframe["event_time"].min()
        dataset_end = earthquake_dataframe["event_time"].max()

        st.write(
            "Dataset start: "
            f"{dataset_start:%Y-%m-%d %H:%M UTC}"
        )
        st.write(
            "Dataset end: "
            f"{dataset_end:%Y-%m-%d %H:%M UTC}"
        )

    with information_column_2:
        st.markdown("### SQLite Database")
        st.write(f"Database path: `{DATABASE_PATH}`")

        database_status = (
            "Available"
            if DATABASE_PATH.exists()
            else "Not created"
        )

        st.write(f"Database status: {database_status}")
        st.metric(
            "Stored Database Records",
            f"{get_database_record_count():,}",
        )

    st.markdown("### Update Historical Records")
    st.write(
        "Run the following command periodically to retrieve "
        "the current USGS feed and add new records to SQLite:"
    )
    st.code("python main.py", language="powershell")
    st.write(
        "The USGS earthquake ID is used as the database "
        "primary key, preventing duplicate records."
    )

st.divider()
st.caption(
    "Data source: United States Geological Survey "
    "Earthquake Hazards Program."
)