"""Create reusable Plotly charts for the earthquake dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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


def create_earthquake_map(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create an interactive global earthquake map.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly map figure.
    """
    map_dataframe = earthquake_dataframe.copy()

    map_dataframe["marker_size"] = (
        map_dataframe["magnitude"]
        .fillna(0.1)
        .clip(lower=0.1)
    )

    map_figure = px.scatter_map(
        map_dataframe,
        lat="latitude",
        lon="longitude",
        size="marker_size",
        color="severity",
        hover_name="place",
        hover_data={
            "magnitude": ":.1f",
            "depth_km": ":.1f",
            "event_time": True,
            "latitude": ":.3f",
            "longitude": ":.3f",
            "marker_size": False,
        },
        size_max=25,
        zoom=1,
        height=650,
        map_style="carto-positron",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        labels={
            "magnitude": "Magnitude",
            "depth_km": "Depth (km)",
            "event_time": "Event Time",
            "severity": "Severity",
        },
    )

    map_figure.update_layout(
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0,
        },
        legend_title_text="Severity",
    )

    return map_figure


def create_activity_timeline(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create an hourly earthquake activity timeline.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly line figure.
    """
    timeline_dataframe = earthquake_dataframe.dropna(
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
                "size": "earthquake_count",
            }
        )
        .sort_values("event_hour")
    )

    timeline_figure = px.line(
        hourly_activity,
        x="event_hour",
        y="earthquake_count",
        markers=True,
        title="Earthquakes Recorded by Hour",
        labels={
            "event_hour": "Event Time",
            "earthquake_count": "Earthquake Count",
        },
    )

    timeline_figure.update_layout(
        xaxis_title="Event Time",
        yaxis_title="Earthquake Count",
        hovermode="x unified",
    )

    return timeline_figure


def create_magnitude_histogram(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a magnitude distribution histogram.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly histogram figure.
    """
    magnitude_figure = px.histogram(
        earthquake_dataframe,
        x="magnitude",
        nbins=20,
        title="Distribution of Earthquake Magnitudes",
        labels={
            "magnitude": "Magnitude",
            "count": "Earthquake Count",
        },
    )

    magnitude_figure.update_layout(
        xaxis_title="Magnitude",
        yaxis_title="Earthquake Count",
        bargap=0.05,
    )

    return magnitude_figure


def create_severity_chart(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a bar chart showing earthquakes by severity.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly bar figure.
    """
    severity_summary = (
        earthquake_dataframe.groupby(
            "severity",
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "earthquake_count",
            }
        )
    )

    severity_figure = px.bar(
        severity_summary,
        x="severity",
        y="earthquake_count",
        title="Earthquakes by Severity",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        labels={
            "severity": "Severity",
            "earthquake_count": "Earthquake Count",
        },
    )

    severity_figure.update_layout(
        xaxis_title="Severity",
        yaxis_title="Earthquake Count",
    )

    return severity_figure


def create_depth_scatter(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a magnitude-versus-depth scatter plot.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly scatter figure.
    """
    depth_figure = px.scatter(
        earthquake_dataframe,
        x="depth_km",
        y="magnitude",
        color="severity",
        size="magnitude",
        hover_name="place",
        hover_data={
            "event_time": True,
            "latitude": ":.3f",
            "longitude": ":.3f",
            "depth_km": ":.1f",
            "magnitude": ":.1f",
        },
        size_max=18,
        title="Earthquake Magnitude Compared with Depth",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        labels={
            "depth_km": "Depth (km)",
            "magnitude": "Magnitude",
            "severity": "Severity",
        },
    )

    depth_figure.update_layout(
        xaxis_title="Depth in Kilometers",
        yaxis_title="Magnitude",
    )

    return depth_figure