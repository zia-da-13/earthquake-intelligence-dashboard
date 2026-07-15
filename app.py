"""Interactive dashboard for live USGS earthquake data."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_cleaning import create_earthquake_dataframe
from src.earthquake_api import fetch_earthquake_data
from src.statistics import calculate_summary_statistics


st.set_page_config(
    page_title="Earthquake Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_earthquake_data() -> pd.DataFrame:
    """
    Retrieve live earthquake data from USGS and return a clean DataFrame.
    """
    earthquake_data = fetch_earthquake_data()
    return create_earthquake_dataframe(earthquake_data)


def classify_magnitude(magnitude: float) -> str:
    """
    Return a readable severity category for an earthquake magnitude.
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


st.title("🌍 Global Earthquake Intelligence Dashboard")

st.caption(
    "Live global earthquake activity from the USGS past-day feed."
)


try:
    earthquake_dataframe = load_earthquake_data()

except Exception as error:
    st.error(f"Unable to retrieve earthquake data: {error}")
    st.stop()


if earthquake_dataframe.empty:
    st.warning("No earthquake records are currently available.")
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


if earthquake_dataframe.empty:
    st.warning("No valid earthquake records are available.")
    st.stop()


if "severity" not in earthquake_dataframe.columns:
    earthquake_dataframe["severity"] = (
        earthquake_dataframe["magnitude"].apply(
            classify_magnitude
        )
    )


earthquake_dataframe["event_time"] = pd.to_datetime(
    earthquake_dataframe["event_time"],
    utc=True,
    errors="coerce",
)


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


severity_order = [
    "Micro",
    "Minor",
    "Light",
    "Moderate",
    "Strong",
    "Major",
    "Great",
    "Unknown",
]


available_severities = [
    severity
    for severity in severity_order
    if severity in earthquake_dataframe["severity"].unique()
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


if st.sidebar.button("Refresh earthquake data"):
    st.cache_data.clear()
    st.rerun()


filtered_dataframe = earthquake_dataframe[
    earthquake_dataframe["magnitude"].between(
        selected_magnitude_range[0],
        selected_magnitude_range[1],
    )
    & earthquake_dataframe["depth_km"].between(
        selected_depth_range[0],
        selected_depth_range[1],
    )
    & earthquake_dataframe["severity"].isin(
        selected_severities
    )
].copy()


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


summary_statistics = calculate_summary_statistics(
    filtered_dataframe
)


total_earthquakes = summary_statistics[
    "total_earthquakes"
]

largest_magnitude = summary_statistics[
    "largest_magnitude"
]

average_magnitude = summary_statistics[
    "average_magnitude"
]

average_depth = summary_statistics[
    "average_depth"
]

tsunami_alerts = summary_statistics[
    "tsunami_alerts"
]


metric_column_1, metric_column_2, metric_column_3, metric_column_4 = (
    st.columns(4)
)


metric_column_1.metric(
    label="Total Earthquakes",
    value=f"{total_earthquakes:,}",
)


metric_column_2.metric(
    label="Largest Magnitude",
    value=f"{largest_magnitude:.1f}",
)


metric_column_3.metric(
    label="Average Magnitude",
    value=f"{average_magnitude:.2f}",
)


metric_column_4.metric(
    label="Average Depth",
    value=f"{average_depth:.1f} km",
)


st.caption(
    f"Tsunami alerts in the filtered dataset: {tsunami_alerts}"
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

    map_dataframe = filtered_dataframe.copy()

    map_dataframe["marker_size"] = (
        map_dataframe["magnitude"].clip(lower=0.1)
    )

    map_figure = px.scatter_mapbox(
        map_dataframe,
        lat="latitude",
        lon="longitude",
        size="marker_size",
        color="severity",
        hover_name="place",
        hover_data={
            "magnitude": True,
            "depth_km": True,
            "event_time": True,
            "latitude": True,
            "longitude": True,
            "marker_size": False,
        },
        size_max=25,
        zoom=1,
        height=650,
        category_orders={
            "severity": severity_order
        },
    )

    map_figure.update_layout(
        mapbox_style="carto-positron",
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0,
        },
        legend_title_text="Severity",
    )

    st.plotly_chart(
        map_figure,
        use_container_width=True,
    )

    st.info(
        "Larger markers represent stronger earthquakes."
    )


with analysis_tab:
    st.subheader("Earthquake Activity Over Time")

    timeline_dataframe = filtered_dataframe.dropna(
        subset=["event_time"]
    ).copy()

    timeline_dataframe["event_hour"] = (
        timeline_dataframe["event_time"].dt.floor("h")
    )

    hourly_activity = (
        timeline_dataframe.groupby(
            "event_hour",
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "earthquake_count"
            }
        )
        .sort_values("event_hour")
    )

    timeline_figure = px.line(
        hourly_activity,
        x="event_hour",
        y="earthquake_count",
        markers=True,
        labels={
            "event_hour": "Time",
            "earthquake_count": "Number of Earthquakes",
        },
        title="Earthquakes Recorded by Hour",
    )

    timeline_figure.update_layout(
        xaxis_title="Event Time",
        yaxis_title="Earthquake Count",
    )

    st.plotly_chart(
        timeline_figure,
        use_container_width=True,
    )

    chart_column_1, chart_column_2 = st.columns(2)

    with chart_column_1:
        st.subheader("Magnitude Distribution")

        magnitude_figure = px.histogram(
            filtered_dataframe,
            x="magnitude",
            nbins=20,
            labels={
                "magnitude": "Magnitude",
                "count": "Number of Earthquakes",
            },
            title="Distribution of Earthquake Magnitudes",
        )

        magnitude_figure.update_layout(
            xaxis_title="Magnitude",
            yaxis_title="Earthquake Count",
        )

        st.plotly_chart(
            magnitude_figure,
            use_container_width=True,
        )

    with chart_column_2:
        st.subheader("Severity Breakdown")

        severity_summary = (
            filtered_dataframe.groupby(
                "severity",
                as_index=False,
            )
            .size()
            .rename(
                columns={
                    "size": "earthquake_count"
                }
            )
        )

        severity_figure = px.bar(
            severity_summary,
            x="severity",
            y="earthquake_count",
            category_orders={
                "severity": severity_order
            },
            labels={
                "severity": "Severity",
                "earthquake_count": "Number of Earthquakes",
            },
            title="Earthquakes by Severity",
        )

        severity_figure.update_layout(
            xaxis_title="Severity",
            yaxis_title="Earthquake Count",
        )

        st.plotly_chart(
            severity_figure,
            use_container_width=True,
        )

    st.subheader("Magnitude Compared with Depth")

    depth_figure = px.scatter(
        filtered_dataframe,
        x="depth_km",
        y="magnitude",
        color="severity",
        hover_name="place",
        hover_data={
            "event_time": True,
            "latitude": True,
            "longitude": True,
        },
        category_orders={
            "severity": severity_order
        },
        labels={
            "depth_km": "Depth in Kilometers",
            "magnitude": "Magnitude",
            "severity": "Severity",
        },
        title="Earthquake Magnitude vs. Depth",
    )

    st.plotly_chart(
        depth_figure,
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

    strongest_columns = [
        "event_time",
        "place",
        "magnitude",
        "severity",
        "depth_km",
    ]

    st.dataframe(
        strongest_earthquakes[
            strongest_columns
        ],
        use_container_width=True,
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
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in filtered_dataframe.columns
    ]

    st.dataframe(
        filtered_dataframe[
            available_display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

    csv_data = filtered_dataframe.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_earthquakes.csv",
        mime="text/csv",
    )


st.divider()

st.caption(
    "Data source: United States Geological Survey "
    "Earthquake Hazards Program."
)