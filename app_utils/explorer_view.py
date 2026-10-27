"""Controls and chart output for the literary metrics explorer."""

import io

import matplotlib.pyplot as plt
import streamlit as st

import metrics.book_metrics as book_metrics
import visualization.plots as plots
from metrics.main_classes import METRICS
from app_utils.ui import analysis_button, metrics_csv


def render_explorer(page_texts, metrics):
    """Render metric selection, chart output, and the CSV download."""
    st.header("Literary Metrics Visualizer")
    control_cols = st.columns(3)
    with control_cols[0]:
        axis = st.selectbox("X-axis", ["Pages", "Chapters"], key="explorer_axis")

    metrics_by_label = {item.label: item for item in METRICS if axis in item.axes}
    options = list(metrics_by_label)
    metric_key = "explorer_metric"
    if st.session_state.get(metric_key) not in metrics_by_label:
        st.session_state[metric_key] = options[0]

    with control_cols[1]:
        selected_label = st.selectbox("Metric", options, key=metric_key)
    with control_cols[2]:
        chart_type = st.selectbox(
            "Chart type", ["Line", "Bar", "Scatter"], key="explorer_chart_type"
        )

    if analysis_button("Plot", "book_stats_explorer", "explorer_plot"):
        selected = metrics_by_label[selected_label]
        chart_data = book_metrics.prepare_metric_data(page_texts, selected.key, axis)
        x_column = "Pages" if axis == "Pages" else "Chapter"
        st.session_state["book_stats_explorer"] = (
            chart_data,
            x_column,
            selected.label,
            chart_type,
        )
        st.rerun()

    explorer = st.session_state.get("book_stats_explorer")
    if explorer:
        chart_data, x_column, metric_label, plotted_type = explorer
        figure = plots.plot_metric(chart_data, x_column, metric_label, plotted_type)
        if figure is None:
            st.info("No valid values are available for this selection.")
        else:
            st.pyplot(figure, width="content")
            buffer = io.BytesIO()
            figure.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
            plt.close(figure)
            st.download_button(
                "Download chart as PNG",
                buffer.getvalue(),
                "literary_metrics.png",
                "image/png",
            )

    st.download_button(
        "Download metrics as CSV",
        data=metrics_csv(metrics),
        file_name="book_stats_metrics.csv",
        mime="text/csv",
    )
