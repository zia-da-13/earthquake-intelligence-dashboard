"""Interactive dashboard for live USGS earthquake data."""

import plotly.express as px
import streamlit as st

from src.data_cleaning import create_earthquake_dataframe
from src.earthquake_api import fetch_earthquake_data


st.set_page_config(
    page_title="Earthquake Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_earthquake_data():
    """Retrieve and clean live earthquake data."""
    earthquake_data = fetch_earthquake_data()
    return create_earthquake_dataframe(earthquake_data)


st.title("🌍 Global Earthquake Intelligence Dashboard")
st.caption("Live earthquake activity from the USGS past-day feed.")

try:
    earthquake_dataframe = load_earthquake_data()
except Exception as error:
    st.error(f"Unable to retrieve earthquake data: {error}")
    st.stop()

if earthquake_dataframe.empty:
    st.warning("No earthquake data is currently available.")
    st.stop()


# Sidebar filters
st.sidebar.header("Dashboard Filters")

minimum_magnitude = float(
    earthquake_dataframe["magnitude"].min()
)

maximum_magnitude = float(
    earthquake_dataframe["magnitude"].max()
)

selected_magnitude = st.sidebar.slider(
    "Minimum magnitude",
    min_value=minimum_magnitude,
    max_value=maximum_magnitude,
    value=minimum_magnitude,
    step=0.1,
)

maximum_depth = float(
    earthquake_dataframe["depth_km"].max()
)

selected_depth = st.sidebar.slider(
    "Maximum depth in kilometers",
    min_value=0.0,
    max_value=maximum_depth,
    value=maximum_depth,
    step=1.0,
)

search_location = st.sidebar.text_input(
    "Search location",
    placeholder="Example: California",
)

filtered_dataframe = earthquake_dataframe[
    (earthquake_dataframe["magnitude"] >= selected_magnitude)
    & (earthquake_dataframe["depth_km"] <= selected_depth)
].copy()

if search_location:
    filtered_dataframe = filtered_dataframe[
        filtered_dataframe["place"]
        .fillna("")
        .str.contains(search_location, case=False, na=False)
    ]


# Summary metrics
total_earthquakes = len(filtered_dataframe)

if filtered_dataframe.empty:
    largest_magnitude = 0
    average_depth = 0
    tsunami_alerts = 0
else:
    largest_magnitude = filtered_dataframe["magnitude"].max()
    average_depth = filtered_dataframe["depth_km"].mean()
    tsunami_alerts = int(
        filtered_dataframe["tsunami_alert"].fillna(0).sum()
    )

metric_column_1, metric_column_2, metric_column_3, metric_column_4 = (
    st.columns(4)
)

metric_column_1.metric(
    "Total Earthquakes",
    f"{total_earthquakes:,}",
)

metric_column_2.metric(
    "Largest Magnitude",
    f"{largest_magnitude:.1f}",
)

metric_column_3.metric(
    "Average Depth",
    f"{average_depth:.1f} km",
)

metric_column_4.metric(
    "Tsunami Alerts",
    f"{tsunami_alerts:,}",
)


if filtered_dataframe.empty:
    st.warning("No earthquakes match the selected filters.")
    st.stop()


# Interactive map
st.subheader("Interactive Earthquake Map")

map_figure = px.scatter_map(
    filtered_dataframe,
    lat="latitude",
    lon="longitude",
    size="magnitude",
    color="magnitude",
    hover_name="place",
    hover_data={
        "latitude": True,
        "longitude": True,
        "depth_km": True,
        "event_time": True,
        "magnitude": True,
    },
    size_max=25,
    zoom=1,
    height=600,
    map_style="carto-positron",
)

map_figure.update_layout(
    margin={
        "r": 0,
        "t": 0,
        "l": 0,
        "b": 0,
    }
)

st.plotly_chart(
    map_figure,
    use_container_width=True,
)


# Charts
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
    )

    st.plotly_chart(
        magnitude_figure,
        use_container_width=True,
    )

with chart_column_2:
    st.subheader("Magnitude vs. Depth")

    depth_figure = px.scatter(
        filtered_dataframe,
        x="depth_km",
        y="magnitude",
        hover_name="place",
        labels={
            "depth_km": "Depth in Kilometers",
            "magnitude": "Magnitude",
        },
    )

    st.plotly_chart(
        depth_figure,
        use_container_width=True,
    )


# Data table
st.subheader("Earthquake Records")

display_columns = [
    "event_time",
    "place",
    "magnitude",
    "depth_km",
    "latitude",
    "longitude",
    "tsunami_alert",
]

st.dataframe(
    filtered_dataframe[display_columns],
    use_container_width=True,
    hide_index=True,
)


# CSV download
csv_data = filtered_dataframe.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_earthquakes.csv",
    mime="text/csv",
)