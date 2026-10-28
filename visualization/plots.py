"""Matplotlib chart builder for the interactive Book Stats explorer."""

import matplotlib.pyplot as plt


def plot_metric(data, x_column, metric_label, chart_type):
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
    ax.grid(axis="y", alpha=0.3)
    if x_column == "Chapter":
        ax.tick_params(axis="x", rotation=45, labelsize=9)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    return fig
