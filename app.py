"""Streamlit entry point for Book Stats: Literary Analytics."""

import streamlit as st

from app_utils.analysis_view import (
    render_chapter_word_frequency,
    render_name_frequency,
    render_ngrams,
    render_repetitions,
    render_word_frequency,
)
from app_utils.book_view import render_overview, render_upload
from app_utils.explorer_view import render_explorer


def main():
    """Build the page and connect each section to the analyzed book."""
    st.set_page_config(
        page_title="Book Stats: Literary Analytics",
        page_icon="📚",
        layout="wide",
    )
    st.title("Book Stats: Literary Analytics")
    st.write(
        "Explore the vocabulary, word lengths, and chapter structure of a PDF book."
    )

    render_upload()

    metrics = st.session_state.get("book_stats_metrics")
    page_texts = st.session_state.get("book_stats_pages")
    if not metrics or page_texts is None:
        return

    render_overview(metrics)
    render_explorer(page_texts, metrics)

    st.header("Text Analysis")
    word_tab, chapter_tab, name_tab, ngram_tab, repetition_tab = st.tabs(
        [
            "Word frequency",
            "Frequency by chapter",
            "Name frequency",
            "N-grams",
            "Repeated words",
        ],
        key="book_stats_analysis_tabs",
        on_change="rerun",
    )
    if word_tab.open:
        render_word_frequency(page_texts)
    if chapter_tab.open:
        render_chapter_word_frequency(page_texts)
    if name_tab.open:
        render_name_frequency(page_texts)
    if ngram_tab.open:
        render_ngrams(page_texts)
    if repetition_tab.open:
        render_repetitions(page_texts)


main()
