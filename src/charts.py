"""Reusable Plotly charts for the earthquake dashboard."""

from __future__ import annotations

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


def _prepare_chart_dataframe(
    earthquake_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare earthquake records for Plotly charts.

    Negative earthquake magnitudes are scientifically valid, but Plotly
    does not allow negative marker sizes. Therefore, marker_size is kept
    separate from the original magnitude column.

    Args:
        earthquake_dataframe: Earthquake records.

    Returns:
        A cleaned copy of the earthquake records.
    """
    chart_dataframe = earthquake_dataframe.copy()

    numeric_columns = [
        "magnitude",
        "depth_km",
        "latitude",
        "longitude",
        "tsunami_alert",
    ]

    for column in numeric_columns:
        if column not in chart_dataframe.columns:
            chart_dataframe[column] = pd.NA

        chart_dataframe[column] = pd.to_numeric(
            chart_dataframe[column],
            errors="coerce",
        )

    if "event_time" not in chart_dataframe.columns:
        chart_dataframe["event_time"] = pd.NaT

    chart_dataframe["event_time"] = pd.to_datetime(
        chart_dataframe["event_time"],
        utc=True,
        errors="coerce",
    )

    if "place" not in chart_dataframe.columns:
        chart_dataframe["place"] = "Unknown location"

    chart_dataframe["place"] = (
        chart_dataframe["place"]
        .fillna("Unknown location")
        .astype(str)
    )

    if "severity" not in chart_dataframe.columns:
        chart_dataframe["severity"] = "Unknown"

    chart_dataframe["severity"] = (
        chart_dataframe["severity"]
        .fillna("Unknown")
        .astype(str)
    )

    chart_dataframe["tsunami_alert"] = (
        chart_dataframe["tsunami_alert"]
        .fillna(0)
        .astype(int)
    )

    # Plotly marker sizes must be zero or greater.
    # Adding 1.0 keeps very small and negative magnitudes visible.
    chart_dataframe["marker_size"] = (
        chart_dataframe["magnitude"]
        .fillna(0)
        .clip(lower=0)
        .add(1.0)
    )

    return chart_dataframe


def _empty_figure(
    title: str,
    message: str = "No earthquake data is available.",
) -> go.Figure:
    """
    Create an empty Plotly figure with an explanatory message.

    Args:
        title: Figure title.
        message: Message displayed in the chart area.

    Returns:
        Empty Plotly figure.
    """
    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16},
    )

    figure.update_layout(
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        height=450,
    )

    return figure


def create_earthquake_map(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create an interactive geographic earthquake map.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly geographic scatter figure.
    """
    chart_dataframe = _prepare_chart_dataframe(
        earthquake_dataframe
    )

    chart_dataframe = chart_dataframe.dropna(
        subset=[
            "latitude",
            "longitude",
            "magnitude",
            "depth_km",
        ]
    ).copy()

    if chart_dataframe.empty:
        return _empty_figure(
            "Global Earthquake Map"
        )

    figure = px.scatter_geo(
        chart_dataframe,
        lat="latitude",
        lon="longitude",
        size="marker_size",
        color="severity",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        hover_name="place",
        hover_data={
            "event_time": True,
            "magnitude": ":.2f",
            "depth_km": ":.1f",
            "latitude": ":.3f",
            "longitude": ":.3f",
            "tsunami_alert": True,
            "marker_size": False,
        },
        projection="natural earth",
        title="Global Earthquake Locations",
        size_max=28,
    )

    figure.update_geos(
        showland=True,
        showocean=True,
        showcountries=True,
        showcoastlines=True,
        lataxis_showgrid=True,
        lonaxis_showgrid=True,
    )

    figure.update_layout(
        height=650,
        margin={
            "l": 0,
            "r": 0,
            "t": 60,
            "b": 0,
        },
        legend_title_text="Severity",
    )

    return figure


def create_activity_timeline(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a timeline of earthquake magnitude.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly scatter timeline.
    """
    chart_dataframe = _prepare_chart_dataframe(
        earthquake_dataframe
    )

    chart_dataframe = chart_dataframe.dropna(
        subset=[
            "event_time",
            "magnitude",
            "depth_km",
        ]
    ).copy()

    if chart_dataframe.empty:
        return _empty_figure(
            "Earthquake Activity Over Time"
        )

    chart_dataframe = chart_dataframe.sort_values(
        by="event_time"
    )

    figure = px.scatter(
        chart_dataframe,
        x="event_time",
        y="magnitude",
        size="marker_size",
        color="severity",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        hover_name="place",
        hover_data={
            "depth_km": ":.1f",
            "tsunami_alert": True,
            "marker_size": False,
        },
        title="Earthquake Magnitudes Over Time",
        labels={
            "event_time": "Event Time",
            "magnitude": "Magnitude",
            "severity": "Severity",
            "depth_km": "Depth (km)",
        },
        size_max=22,
    )

    figure.update_layout(
        height=500,
        hovermode="closest",
        legend_title_text="Severity",
    )

    figure.update_xaxes(
        title="Event Time"
    )

    figure.update_yaxes(
        title="Magnitude",
        zeroline=True,
    )

    return figure


def create_magnitude_histogram(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a histogram showing magnitude distribution.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly histogram.
    """
    chart_dataframe = _prepare_chart_dataframe(
        earthquake_dataframe
    )

    chart_dataframe = chart_dataframe.dropna(
        subset=["magnitude"]
    ).copy()

    if chart_dataframe.empty:
        return _empty_figure(
            "Magnitude Distribution"
        )

    figure = px.histogram(
        chart_dataframe,
        x="magnitude",
        nbins=25,
        title="Magnitude Distribution",
        labels={
            "magnitude": "Magnitude",
            "count": "Earthquake Count",
        },
    )

    figure.update_layout(
        height=450,
        bargap=0.05,
        showlegend=False,
    )

    figure.update_xaxes(
        title="Magnitude"
    )

    figure.update_yaxes(
        title="Earthquake Count"
    )

    return figure


def create_severity_chart(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a bar chart showing earthquake severity counts.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly bar chart.
    """
    chart_dataframe = _prepare_chart_dataframe(
        earthquake_dataframe
    )

    if chart_dataframe.empty:
        return _empty_figure(
            "Earthquakes by Severity"
        )

    severity_counts = (
        chart_dataframe["severity"]
        .value_counts()
        .rename_axis("severity")
        .reset_index(name="earthquake_count")
    )

    severity_counts["severity"] = pd.Categorical(
        severity_counts["severity"],
        categories=SEVERITY_ORDER,
        ordered=True,
    )

    severity_counts = severity_counts.sort_values(
        by="severity"
    )

    figure = px.bar(
        severity_counts,
        x="severity",
        y="earthquake_count",
        color="severity",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        title="Earthquakes by Severity",
        labels={
            "severity": "Severity",
            "earthquake_count": "Earthquake Count",
        },
        text_auto=True,
    )

    figure.update_layout(
        height=450,
        showlegend=False,
    )

    figure.update_xaxes(
        title="Severity"
    )

    figure.update_yaxes(
        title="Earthquake Count"
    )

    return figure


def create_depth_scatter(
    earthquake_dataframe: pd.DataFrame,
) -> go.Figure:
    """
    Create a scatter chart comparing magnitude and depth.

    Args:
        earthquake_dataframe: Filtered earthquake records.

    Returns:
        Plotly scatter figure.

    Notes:
        The original magnitude remains on the x-axis. The separate
        marker_size field prevents negative magnitudes from being passed
        to Plotly's marker size property.
    """
    chart_dataframe = _prepare_chart_dataframe(
        earthquake_dataframe
    )

    chart_dataframe = chart_dataframe.dropna(
        subset=[
            "magnitude",
            "depth_km",
        ]
    ).copy()

    if chart_dataframe.empty:
        return _empty_figure(
            "Magnitude and Earthquake Depth"
        )

    figure = px.scatter(
        chart_dataframe,
        x="magnitude",
        y="depth_km",
        size="marker_size",
        color="severity",
        category_orders={
            "severity": SEVERITY_ORDER,
        },
        hover_name="place",
        hover_data={
            "event_time": True,
            "magnitude": ":.2f",
            "depth_km": ":.1f",
            "latitude": ":.3f",
            "longitude": ":.3f",
            "tsunami_alert": True,
            "marker_size": False,
        },
        title="Earthquake Magnitude Compared with Depth",
        labels={
            "magnitude": "Magnitude",
            "depth_km": "Depth (km)",
            "severity": "Severity",
        },
        size_max=24,
    )

    figure.update_layout(
        height=550,
        hovermode="closest",
        legend_title_text="Severity",
    )

    figure.update_xaxes(
        title="Magnitude",
        zeroline=True,
    )

    figure.update_yaxes(
        title="Depth (km)",
        autorange="reversed",
    )

    return figure