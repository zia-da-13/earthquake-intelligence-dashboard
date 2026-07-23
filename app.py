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
from src.data_cleaning import (
    classify_magnitude,
    create_earthquake_dataframe,
)
from src.database import (
    DATABASE_PATH,
    get_database_record_count,
    load_earthquakes_from_database,
)
from src.earthquake_api import fetch_earthquake_data
from src.filters import (
    apply_filters,
    display_sidebar_filters,
)
from src.statistics import calculate_summary_statistics


st.set_page_config(
    page_title="Earthquake Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_live_earthquake_data() -> pd.DataFrame:
    """Retrieve and clean the current USGS feed."""
    raw_earthquake_data = fetch_earthquake_data()

    return create_earthquake_dataframe(
        raw_earthquake_data
    )


@st.cache_data(ttl=60)
def load_historical_earthquake_data() -> pd.DataFrame:
    """Load accumulated earthquake records from SQLite."""
    return load_earthquakes_from_database()


def prepare_dashboard_data(
    earthquake_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate and prepare data for filters and visualizations.

    Args:
        earthquake_dataframe: Data from USGS or SQLite.

    Returns:
        Validated earthquake records.
    """
    if earthquake_dataframe.empty:
        return earthquake_dataframe

    earthquake_dataframe = (
        earthquake_dataframe.copy()
    )

    numeric_columns = [
        "magnitude",
        "depth_km",
        "latitude",
        "longitude",
        "tsunami_alert",
    ]

    for column in numeric_columns:
        if column not in earthquake_dataframe.columns:
            earthquake_dataframe[column] = pd.NA

        earthquake_dataframe[column] = pd.to_numeric(
            earthquake_dataframe[column],
            errors="coerce",
        )

    if "event_time" not in earthquake_dataframe.columns:
        earthquake_dataframe["event_time"] = pd.NaT

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
        earthquake_dataframe["place"] = (
            "Unknown location"
        )

    earthquake_dataframe["place"] = (
        earthquake_dataframe["place"]
        .fillna("Unknown location")
        .astype(str)
    )

    if "severity" not in earthquake_dataframe.columns:
        earthquake_dataframe["severity"] = (
            earthquake_dataframe[
                "magnitude"
            ].apply(classify_magnitude)
        )

    else:
        missing_severity = (
            earthquake_dataframe["severity"].isna()
            | earthquake_dataframe[
                "severity"
            ].eq("")
        )

        earthquake_dataframe.loc[
            missing_severity,
            "severity",
        ] = earthquake_dataframe.loc[
            missing_severity,
            "magnitude",
        ].apply(classify_magnitude)

    earthquake_dataframe["tsunami_alert"] = (
        earthquake_dataframe["tsunami_alert"]
        .fillna(0)
        .astype(int)
    )

    return (
        earthquake_dataframe.sort_values(
            by="event_time",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def display_summary_metrics(
    earthquake_dataframe: pd.DataFrame,
) -> None:
    """Display earthquake summary metrics."""
    summary = calculate_summary_statistics(
        earthquake_dataframe
    )

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


st.title("🌍 Global Earthquake Intelligence Dashboard")

st.caption(
    "Explore live USGS earthquake activity and "
    "historical records stored in SQLite."
)


st.sidebar.header("Data Source")

selected_data_source = st.sidebar.selectbox(
    "Choose earthquake dataset",
    options=[
        "Live USGS feed",
        "SQLite historical data",
    ],
)


if st.sidebar.button(
    "Refresh selected data",
    type="primary",
    width="stretch",
):
    st.cache_data.clear()
    st.rerun()


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
            "Displaying accumulated earthquake records "
            "from the local SQLite database."
        )

except Exception as error:
    st.error(
        f"Unable to load earthquake data: {error}"
    )
    st.stop()


earthquake_dataframe = prepare_dashboard_data(
    earthquake_dataframe
)


if earthquake_dataframe.empty:
    if selected_data_source == (
        "SQLite historical data"
    ):
        st.warning(
            "The SQLite database does not contain usable "
            "earthquake records."
        )

        st.code(
            "python main.py",
            language="powershell",
        )

    else:
        st.warning(
            "The live USGS feed did not return usable data."
        )

    st.stop()


source_column, record_column = st.columns(
    [3, 1]
)


with source_column:
    st.info(source_description)


with record_column:
    if selected_data_source == (
        "SQLite historical data"
    ):
        st.metric(
            "Database Records",
            f"{get_database_record_count():,}",
        )

    else:
        st.metric(
            "Live Feed Records",
            f"{len(earthquake_dataframe):,}",
        )


selected_filters = display_sidebar_filters(
    earthquake_dataframe
)


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


map_tab, analysis_tab, records_tab, information_tab = (
    st.tabs(
        [
            "🌍 Earthquake Map",
            "📊 Activity Analysis",
            "📋 Earthquake Records",
            "🗄️ Data Information",
        ]
    )
)


with map_tab:
    st.subheader("Interactive Earthquake Map")

    st.plotly_chart(
        create_earthquake_map(
            filtered_dataframe
        ),
        width="stretch",
    )

    st.info(
        "Marker size represents magnitude. "
        "Marker categories represent severity."
    )


with analysis_tab:
    st.subheader("Earthquake Activity Over Time")

    st.plotly_chart(
        create_activity_timeline(
            filtered_dataframe
        ),
        width="stretch",
    )

    chart_column_1, chart_column_2 = st.columns(2)

    with chart_column_1:
        st.plotly_chart(
            create_magnitude_histogram(
                filtered_dataframe
            ),
            width="stretch",
        )

    with chart_column_2:
        st.plotly_chart(
            create_severity_chart(
                filtered_dataframe
            ),
            width="stretch",
        )

    st.plotly_chart(
        create_depth_scatter(
            filtered_dataframe
        ),
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

    available_columns = [
        column
        for column in display_columns
        if column in filtered_dataframe.columns
    ]

    records_dataframe = filtered_dataframe[
        available_columns
    ].copy()

    st.dataframe(
        records_dataframe,
        width="stretch",
        hide_index=True,
        column_config={
            "event_time": (
                st.column_config.DatetimeColumn(
                    "Event Time",
                    format="YYYY-MM-DD HH:mm:ss",
                )
            ),
            "place": "Location",
            "magnitude": (
                st.column_config.NumberColumn(
                    "Magnitude",
                    format="%.1f",
                )
            ),
            "depth_km": (
                st.column_config.NumberColumn(
                    "Depth (km)",
                    format="%.1f",
                )
            ),
            "latitude": (
                st.column_config.NumberColumn(
                    "Latitude",
                    format="%.3f",
                )
            ),
            "longitude": (
                st.column_config.NumberColumn(
                    "Longitude",
                    format="%.3f",
                )
            ),
            "tsunami_alert": (
                st.column_config.CheckboxColumn(
                    "Tsunami Alert",
                )
            ),
            "details_url": (
                st.column_config.LinkColumn(
                    "USGS Details",
                    display_text="Open event",
                )
            ),
        },
    )

    csv_data = records_dataframe.to_csv(
        index=False
    ).encode("utf-8")

    filename_prefix = (
        "live"
        if selected_data_source == "Live USGS feed"
        else "historical"
    )

    st.download_button(
        "Download Filtered Data as CSV",
        data=csv_data,
        file_name=(
            f"{filename_prefix}_earthquakes.csv"
        ),
        mime="text/csv",
        type="primary",
    )


with information_tab:
    st.subheader("Data Source Information")

    information_column_1, information_column_2 = (
        st.columns(2)
    )

    with information_column_1:
        st.markdown("#### Selected dataset")

        st.write(selected_data_source)

        st.metric(
            "Loaded Records",
            f"{len(earthquake_dataframe):,}",
        )

        st.metric(
            "Filtered Records",
            f"{len(filtered_dataframe):,}",
        )

    with information_column_2:
        st.markdown("#### SQLite database")

        st.write(
            f"Database path: `{DATABASE_PATH}`"
        )

        st.write(
            "Database status: "
            + (
                "Available"
                if DATABASE_PATH.exists()
                else "Not created"
            )
        )

        st.metric(
            "Stored Database Records",
            f"{get_database_record_count():,}",
        )

    st.markdown("#### Update historical records")

    st.write(
        "Run this command periodically to retrieve "
        "new earthquake records:"
    )

    st.code(
        "python main.py",
        language="powershell",
    )


st.divider()

st.caption(
    "Data source: United States Geological Survey "
    "Earthquake Hazards Program."
)