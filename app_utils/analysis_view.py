"""Word, phrase, and repetition analysis sections."""

import streamlit as st

import metrics.book_metrics as book_metrics
from models.repetitions.ngrams import most_frequent_ngrams
from models.repetitions.word_frequency import (
    most_frequent_words,
    name_frequency,
    word_frequency_by_chapter,
)


def render_word_frequency(page_texts):
    """Render the most frequent long words table."""
    if "book_stats_word_frequency" not in st.session_state:
        st.session_state["book_stats_word_frequency"] = most_frequent_words(page_texts)

    results = st.session_state.get("book_stats_word_frequency")
    if results is not None:
        st.subheader("Most frequent words (5+ characters)")
        if results:
            st.dataframe(results, hide_index=True, width="stretch")
        else:
            st.info("No words with at least five characters were found.")


def render_chapter_word_frequency(page_texts):
    """Show where filtered words occur unusually often by chapter."""
    if "book_stats_word_frequency_by_chapter" not in st.session_state:
        with st.spinner("Counting words by chapter..."):
            st.session_state["book_stats_word_frequency_by_chapter"] = (
                word_frequency_by_chapter(page_texts)
            )

    results = st.session_state.get("book_stats_word_frequency_by_chapter")
    if results is not None:
        st.caption(
            "A ratio above 1 means the word appears more often in that chapter "
            "than its average across chapters."
        )
        if results:
            st.dataframe(
                results,
                hide_index=True,
                width="stretch",
                column_config={
                    "Mean per chapter": st.column_config.NumberColumn(
                        "Mean per chapter", format="%.2f"
                    ),
                    "ratio_appearance": st.column_config.NumberColumn(
                        "Appearance ratio", format="%.2f"
                    ),
                },
            )
        else:
            st.info("No words of at least five characters were found in chapters.")


def render_name_frequency(page_texts):
    """Render the twenty most frequent likely names in the book."""
    cache_key = "book_stats_name_frequency_v2"
    if cache_key not in st.session_state:
        with st.spinner("Counting names by chapter..."):
            st.session_state[cache_key] = name_frequency(page_texts)

    results = st.session_state.get(cache_key)
    if results is not None:
        st.subheader("Most frequent names")
        if results:
            display_results = [
                {**row, "Name": row["Name"][:1].upper() + row["Name"][1:]}
                for row in results
            ]
            st.dataframe(
                display_results,
                hide_index=True,
                width="stretch",
                column_config={
                    "Appearances per chapter": st.column_config.NumberColumn(
                        "Appearances per chapter", format="%.2f"
                    ),
                },
            )
        else:
            st.info("No likely names were found in the book.")


def render_ngrams(page_texts):
    """Render the top bigrams and trigrams."""
    if "book_stats_ngrams" not in st.session_state:
        with st.spinner("Counting two- and three-word phrases..."):
            st.session_state["book_stats_ngrams"] = {
                n: most_frequent_ngrams(page_texts, n) for n in (2, 3)
            }

    results = st.session_state.get("book_stats_ngrams")
    if results is not None:
        st.subheader("Most frequent word combinations")
        columns = st.columns(2)
        for column, n in zip(columns, (2, 3)):
            with column:
                st.markdown(f"**{'Bigrams' if n == 2 else 'Trigrams'}**")
                if results[n]:
                    st.dataframe(results[n], hide_index=True, width="stretch")
                else:
                    st.info("No phrases of this length were found.")


def render_repetitions(page_texts):
    """Render repeated long words from consecutive sentences."""
    if "book_stats_repetitions" not in st.session_state:
        with st.spinner("Finding long words repeated in consecutive sentences..."):
            st.session_state["book_stats_repetitions"] = (
                book_metrics.calculate_repetitions(page_texts)
            )

    results = st.session_state.get("book_stats_repetitions")
    if results is not None:
        st.subheader("Long words repeated in consecutive sentences")
        if results.empty:
            st.info("No long repeated words were found.")
        else:
            st.dataframe(
                results,
                hide_index=True,
                width="stretch",
                column_config={
                    "Page": st.column_config.NumberColumn("Page", format="%d"),
                    "Sentence pair": st.column_config.TextColumn("Sentence Pair"),
                    "Repeated word": st.column_config.TextColumn("Repeated Word"),
                },
            )
