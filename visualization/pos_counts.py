"""Charts for part-of-speech counts by page or chapter."""

import matplotlib.pyplot as plt
import streamlit as st

from visualization.plots import plot_metrics


def render_pos_counts_chart(page_texts, count_by_page, count_by_chapter):
    """Render part-of-speech counts across the selected text scope."""
    st.subheader("Parts of speech by page or chapter")
    control_cols = st.columns(3)
    with control_cols[0]:
        value_type = st.selectbox(
            "Measure",
            ["Count", "Percentage"],
            key="lemma_pos_counts_measure",
        )
    with control_cols[1]:
        axis = st.selectbox(
            "Show by",
            ["Pages", "Chapters"],
            key="lemma_pos_counts_axis",
        )
    with control_cols[2]:
        chart_type = st.selectbox(
            "Chart type",
            ["Line", "Bar", "Scatter"],
            key="lemma_pos_counts_chart_type",
        )

    is_page = axis == "Pages"
    scope_column = "page" if is_page else "chapter"
    cache_key = (
        "book_stats_pos_counts_page_v2"
        if is_page
        else "book_stats_pos_counts_chapter_v2"
    )
    count_function = count_by_page if is_page else count_by_chapter
    if cache_key not in st.session_state:
        with st.spinner("Counting parts of speech with spaCy..."):
            st.session_state[cache_key] = count_function(page_texts)

    data = st.session_state[cache_key]
    if data.empty:
        st.info("No part-of-speech data is available to display.")
        return

    percentage_mode = value_type == "Percentage"
    metric_columns = [
        column
        for column in data.columns
        if column != scope_column and column.endswith("_percentage") == percentage_mode
    ]
    if not metric_columns:
        st.info("The calculation returned no part-of-speech categories to display.")
        return

    if percentage_mode:
        source_columns = metric_columns
        metric_columns = [
            column.removesuffix("_percentage") for column in source_columns
        ]
        plot_data = data[[scope_column, *source_columns]].copy()
        plot_data.columns = [scope_column, *metric_columns]
    else:
        plot_data = data[[scope_column, *metric_columns]].copy()

    if is_page:
        x_column = "Pages"
        plot_data[x_column] = (
            plot_data[scope_column]
            .astype(str)
            .map(lambda label: label.removeprefix("Page "))
            .astype(int)
        )
    else:
        x_column = "Chapter"
        plot_data = plot_data[plot_data[scope_column] != "Sin capitulo"].copy()
        plot_data[x_column] = (
            plot_data[scope_column]
            .astype(str)
            .map(lambda label: label.removeprefix("Capitulo "))
        )

    figure = plot_metrics(
        plot_data,
        x_column,
        metric_columns,
        f"Parts of speech by {x_column.lower()}",
        "Percentage (%)" if percentage_mode else "Token count",
        chart_type,
    )
    if figure is None:
        st.info("No part-of-speech data is available to display.")
        return

    st.pyplot(figure, width="stretch")
    plt.close(figure)
