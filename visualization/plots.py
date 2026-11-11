"""Matplotlib chart builder for the interactive Book Stats explorer."""

import matplotlib.pyplot as plt
import pandas as pd


def _configure_axes(ax, x_column: str) -> None:
    """Apply the shared axis styling used by Book Stats charts."""
    ax.grid(axis="y", alpha=0.3)
    if x_column == "Chapter":
        ax.tick_params(axis="x", rotation=45, labelsize=9)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")


def plot_metric(
    data: pd.DataFrame,
    x_column: str,
    metric_label: str,
    chart_type: str,
) -> plt.Figure | None:
    """Build a metric chart from prepared explorer data."""
    if chart_type not in {"Line", "Bar", "Scatter"}:
        raise ValueError(f"Unavailable chart type: {chart_type}")
    if x_column not in data.columns or "value" not in data.columns:
        raise ValueError(
            "Chart data must contain the selected x-axis and value columns"
        )
    if data.empty:
        return None

    # Keep the in-app chart compact; the PNG export is rendered separately at
    # higher DPI from this same figure.
    figure_size = (11, 4) if x_column == "Chapter" else (8, 3.2)
    fig, ax = plt.subplots(figsize=figure_size, constrained_layout=True)
    x, y = data[x_column], data["value"]
    if chart_type == "Line":
        ax.plot(x, y, marker="o", markersize=4, linewidth=1.5)
    elif chart_type == "Bar":
        ax.bar(x, y, color="#4c78a8")
    else:
        ax.scatter(x, y, color="#4c78a8")
    ax.set_xlabel(x_column)
    ax.set_ylabel(metric_label)
    ax.set_title(f"{metric_label} by {x_column.lower()}")
    _configure_axes(ax, x_column)
    return fig


def plot_metrics(
    data: pd.DataFrame,
    x_column: str,
    metric_columns: list[str],
    chart_title: str,
    y_label: str,
    chart_type: str,
) -> plt.Figure | None:
    """Build a chart with multiple metrics sharing the same x-axis."""
    if chart_type not in {"Line", "Bar", "Scatter"}:
        raise ValueError(f"Unavailable chart type: {chart_type}")
    if x_column not in data.columns or any(
        column not in data.columns for column in metric_columns
    ):
        raise ValueError("Chart data must contain the x-axis and metric columns")
    if data.empty or not metric_columns:
        return None

    figure_size = (11, 4) if x_column == "Chapter" else (8, 3.2)
    fig, ax = plt.subplots(figsize=figure_size, constrained_layout=True)
    labels = data[x_column].astype(str)
    positions = (
        pd.to_numeric(data[x_column]).tolist()
        if x_column == "Pages"
        else list(range(len(data)))
    )
    if chart_type == "Bar":
        width = 0.8 / len(metric_columns)
        for index, column in enumerate(metric_columns):
            offsets = [
                position - 0.4 + width * (index + 0.5)
                for position in positions
            ]
            ax.bar(offsets, data[column], width=width, label=column.capitalize())
        if x_column == "Chapter":
            ax.set_xticks(positions, labels)
    else:
        for column in metric_columns:
            if chart_type == "Line":
                ax.plot(
                    positions,
                    data[column],
                    marker="o",
                    markersize=4,
                    linewidth=1.5,
                    label=column.capitalize(),
                )
            else:
                ax.scatter(positions, data[column], label=column.capitalize())
        if x_column == "Chapter":
            ax.set_xticks(positions, labels)

    ax.set_xlabel(x_column)
    ax.set_ylabel(y_label)
    ax.set_title(chart_title)
    _configure_axes(ax, x_column)
    ax.legend()
    return fig
