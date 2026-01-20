"""
Chart components for the Aadhaar Analytics Dashboard.
Uses Plotly for interactive visualizations.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Optional, Any
from .theme import TIER_COLORS, PLOTLY_COLOR_SEQUENCE, DEFAULT_COLOR, get_tier_color


def create_horizontal_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    top_n: int = 10,
    height: int = 400
) -> go.Figure:
    """
    Create a horizontal bar chart for ranking data.

    Args:
        df: DataFrame with the data
        x_col: Column for x-axis (values)
        y_col: Column for y-axis (categories)
        color_col: Optional column for color coding
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        top_n: Number of top items to show
        height: Chart height in pixels
    """
    # Sort and get top N
    df_sorted = df.nlargest(top_n, x_col).sort_values(x_col, ascending=True)

    if color_col and color_col in df_sorted.columns:
        # Map colors based on tier/level
        df_sorted["_color"] = df_sorted[color_col].apply(get_tier_color)

        fig = go.Figure(go.Bar(
            x=df_sorted[x_col],
            y=df_sorted[y_col],
            orientation='h',
            marker_color=df_sorted["_color"],
            text=df_sorted[x_col].round(2),
            textposition='outside',
            hovertemplate=f"<b>%{{y}}</b><br>{x_label}: %{{x:.2f}}<br>{color_col}: %{{customdata}}<extra></extra>",
            customdata=df_sorted[color_col]
        ))
    else:
        fig = px.bar(
            df_sorted,
            x=x_col,
            y=y_col,
            orientation='h',
            text=x_col,
            color_discrete_sequence=PLOTLY_COLOR_SEQUENCE
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')

    fig.update_layout(
        title=title,
        xaxis_title=x_label or x_col,
        yaxis_title=y_label or y_col,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )

    return fig


def create_pie_donut_chart(
    df: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str = "",
    hole: float = 0.4,
    height: int = 350,
    color_map: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Create a pie/donut chart for distribution data.

    Args:
        df: DataFrame with aggregated data
        values_col: Column containing values
        names_col: Column containing category names
        title: Chart title
        hole: Size of donut hole (0 for pie, >0 for donut)
        height: Chart height
        color_map: Optional mapping of category names to colors
    """
    # Aggregate if needed
    agg_df = df.groupby(names_col)[values_col].sum().reset_index()

    colors = None
    if color_map:
        colors = [color_map.get(name, DEFAULT_COLOR) for name in agg_df[names_col]]

    fig = go.Figure(go.Pie(
        labels=agg_df[names_col],
        values=agg_df[values_col],
        hole=hole,
        marker_colors=colors,
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
    ))

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    return fig


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    hover_name: Optional[str] = None,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    height: int = 400,
    marker_style: str = "circle"
) -> go.Figure:
    """
    Create an interactive scatter plot.

    Args:
        df: DataFrame with the data
        x_col: Column for x-axis
        y_col: Column for y-axis
        color_col: Column for color coding
        size_col: Column for marker size
        hover_name: Column for hover label
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        height: Chart height
        marker_style: Marker symbol ('circle', 'diamond', 'cross', etc.)
    """
    # Prepare color mapping
    color_discrete_map = None
    if color_col:
        unique_colors = df[color_col].unique()
        color_discrete_map = {c: get_tier_color(c) for c in unique_colors}

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col,
        hover_name=hover_name or y_col,
        color_discrete_map=color_discrete_map,
        title=title
    )

    # Apply marker style
    symbol_map = {
        "circle": "circle",
        "diamond": "diamond",
        "cross": "cross",
        "square": "square",
        "dot": "circle-open-dot"
    }
    fig.update_traces(marker=dict(symbol=symbol_map.get(marker_style, "circle")))

    fig.update_layout(
        xaxis_title=x_label or x_col,
        yaxis_title=y_label or y_col,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig


def create_histogram(
    df: pd.DataFrame,
    x_col: str,
    title: str = "",
    x_label: str = "",
    nbins: int = 20,
    height: int = 350
) -> go.Figure:
    """
    Create a histogram.

    Args:
        df: DataFrame with the data
        x_col: Column for histogram values
        title: Chart title
        x_label: X-axis label
        nbins: Number of bins
        height: Chart height
    """
    fig = px.histogram(
        df,
        x=x_col,
        nbins=nbins,
        title=title,
        color_discrete_sequence=PLOTLY_COLOR_SEQUENCE
    )

    fig.update_layout(
        xaxis_title=x_label or x_col,
        yaxis_title="Count",
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        bargap=0.1
    )

    return fig


def create_comparison_bar_chart(
    df: pd.DataFrame,
    category_col: str,
    value_cols: List[str],
    title: str = "",
    height: int = 400,
    top_n: int = 10
) -> go.Figure:
    """
    Create a grouped bar chart for comparing multiple values.

    Args:
        df: DataFrame with the data
        category_col: Column for categories (x-axis)
        value_cols: List of columns to compare
        title: Chart title
        height: Chart height
        top_n: Number of top items to show
    """
    # Get top N by first value column
    df_sorted = df.nlargest(top_n, value_cols[0])

    fig = go.Figure()

    for i, col in enumerate(value_cols):
        fig.add_trace(go.Bar(
            name=col,
            x=df_sorted[category_col],
            y=df_sorted[col],
            marker_color=PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)]
        ))

    fig.update_layout(
        title=title,
        barmode='group',
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_kpi_indicator(
    value: float,
    title: str,
    reference: Optional[float] = None,
    suffix: str = "",
    mode: str = "number+delta"
) -> go.Figure:
    """
    Create a KPI indicator gauge.

    Args:
        value: Current value
        title: KPI title
        reference: Reference value for delta
        suffix: Value suffix (e.g., "%")
        mode: Indicator mode
    """
    fig = go.Figure(go.Indicator(
        mode=mode if reference else "number",
        value=value,
        number={'suffix': suffix},
        delta={'reference': reference} if reference else None,
        title={'text': title},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        height=150,
        margin=dict(l=20, r=20, t=30, b=20)
    )

    return fig


def create_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    height: int = 400,
    markers: bool = True
) -> go.Figure:
    """
    Create a line chart with optional markers.

    Args:
        df: DataFrame with the data
        x_col: Column for x-axis
        y_col: Column for y-axis
        color_col: Column for color grouping
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        height: Chart height
        markers: Whether to show markers
    """
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        markers=markers,
        color_discrete_sequence=PLOTLY_COLOR_SEQUENCE
    )

    fig.update_layout(
        xaxis_title=x_label or x_col,
        yaxis_title=y_label or y_col,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

