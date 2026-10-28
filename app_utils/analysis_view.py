"""Word, phrase, and repetition analysis sections."""

import streamlit as st

import metrics.book_metrics as book_metrics
from models.repetitions.ngrams import most_frequent_ngrams
from models.repetitions.word_frequency import (
    most_frequent_words,
    name_frequency,
    word_outliers_by_chapter,
    word_outliers_by_page,
    word_frequency_by_chapter,
)


def render_consecutive_repetition_alert(repetitions, page_texts):
    """Show repeated-word and word-outlier alerts in a toggleable panel."""
    page_cache_key = "book_stats_word_outliers"
    chapter_cache_key = "book_stats_chapter_word_outliers"
    if page_cache_key not in st.session_state:
        st.session_state[page_cache_key] = word_outliers_by_page(page_texts)
    if chapter_cache_key not in st.session_state:
        st.session_state[chapter_cache_key] = word_outliers_by_chapter(page_texts)
    outlier_count = len(st.session_state[page_cache_key]) + len(
        st.session_state[chapter_cache_key]
    )

    button_label = (
        f"⚠️ Alerts ({len(repetitions)} repeated, {outlier_count} outliers) — show/hide"
    )
    if st.button(button_label, key="book_stats_repetition_alert_toggle"):
        st.session_state["book_stats_repetition_alert_open"] = not st.session_state.get(
            "book_stats_repetition_alert_open", False
        )

    if not st.session_state.get("book_stats_repetition_alert_open", False):
        return

    repetition_tab, outlier_tab = st.tabs(["⚠️ Repeated word alerts", "Word outlier"])
    with repetition_tab:
        number_words = {
            2: "twice",
            3: "three times",
            4: "four times",
            5: "five times",
            6: "six times",
            7: "seven times",
            8: "eight times",
            9: "nine times",
            10: "ten times",
        }
        for repetition in repetitions:
            count = repetition["count"]
            count_text = number_words.get(count, f"{count} times")
            st.write(
                f'This word "{repetition["word"]}" is repeated {count_text} '
                f"in page {repetition['page']}."
            )
    with outlier_tab:
        render_word_outliers(page_texts)


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


def render_word_outliers(page_texts):
    """Show page and chapter word counts above the three-sigma threshold."""
    page_cache_key = "book_stats_word_outliers"
    chapter_cache_key = "book_stats_chapter_word_outliers"
    if page_cache_key not in st.session_state:
        with st.spinner("Checking word counts across pages..."):
            st.session_state[page_cache_key] = word_outliers_by_page(page_texts)
    if chapter_cache_key not in st.session_state:
        with st.spinner("Checking word counts across chapters..."):
            st.session_state[chapter_cache_key] = word_outliers_by_chapter(page_texts)

    page_results = st.session_state.get(page_cache_key)
    chapter_results = st.session_state.get(chapter_cache_key)
    st.caption(
        "A word is flagged when its count is greater than its mean count per "
        "page or chapter plus three population standard deviations."
    )
    st.subheader("By page")
    if page_results:
        st.dataframe(page_results, hide_index=True, width="stretch")
    else:
        st.info("No word outliers were found by page.")

    st.subheader("By chapter")
    if chapter_results:
        st.dataframe(chapter_results, hide_index=True, width="stretch")
    else:
        st.info("No word outliers were found by chapter.")
