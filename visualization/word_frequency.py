"""Word frequency chart components for the Streamlit interface."""

import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from models.repetitions.word_frequency import (
    word_count_by_chapter,
    word_count_by_page,
)
from visualization.plots import plot_metric


def render_word_frequency_chart(page_texts):
    """Render a selectable word's occurrence count across pages or chapters."""
    st.subheader("Word frequency by page or chapter")
    control_cols = st.columns(3)
    with control_cols[0]:
        word = st.text_input("Word to track", key="chapter_word_chart_word").strip()
    with control_cols[1]:
        axis = st.selectbox(
            "Show frequency by",
            ["Pages", "Chapters"],
            key="word_frequency_chart_axis",
        )
    with control_cols[2]:
        chart_type = st.selectbox(
            "Chart type",
            ["Line", "Bar", "Scatter"],
            key="chapter_word_chart_type",
        )

    if not word:
        st.info("Enter a word to see how often it appears on each page or chapter.")
        return

    if axis == "Pages":
        x_column = "Pages"
        data = word_count_by_page(page_texts, word)
    else:
        x_column = "Chapter"
        data = word_count_by_chapter(page_texts, word)
    chart_data = pd.DataFrame(data, columns=[x_column, "value"])
    figure = plot_metric(chart_data, x_column, f'Occurrences of "{word}"', chart_type)
    if figure is None:
        st.info("No data is available for this selection.")
        return

    average = chart_data["value"].mean()
    axis_object = figure.axes[0]
    average_label = "Mean per page" if axis == "Pages" else "Mean per chapter"
    axis_object.axhline(
        average,
        color="red",
        linestyle="--",
        alpha=0.6,
        label=f"{average_label}: {average:.2f}",
    )
    axis_object.legend()

    st.pyplot(figure, width="content")
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    plt.close(figure)
    st.download_button(
        "Download chart as PNG",
        buffer.getvalue(),
        "word_frequency.png",
        "image/png",
        key="chapter_word_chart_download",
    )
