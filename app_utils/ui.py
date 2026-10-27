"""Small reusable helpers for the Streamlit interface."""

import csv
import io

import streamlit as st


def metrics_csv(metrics):
    """Serialize the book summary metrics as a downloadable CSV file."""
    fields = [
        ("Pages", "num_pages"),
        ("Total words", "num_words"),
        ("Unique words", "num_unique_words"),
        ("Type-Token Ratio", "ttr"),
        ("Mean word length", "mean_word_length"),
        ("Word length standard deviation", "std_word_length"),
        ("Longest word", "longest_word"),
        ("Longest word length", "longest_word_length"),
        ("Mean words per page", "mean_words_per_page"),
        ("Words per page standard deviation", "std_words_per_page"),
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    writer.writerows((label, metrics[key]) for label, key in fields)
    return output.getvalue().encode("utf-8-sig")


def analysis_button(label, result_key, widget_key):
    """Show an analysis action and a close button while results are visible."""
    if st.session_state.get(result_key) is None:
        return st.button(label, key=f"{widget_key}_action")

    action_col, close_col = st.columns([1, 0.16], vertical_alignment="center")
    action_clicked = action_col.button(label, key=f"{widget_key}_action")
    close_clicked = close_col.button(
        "×", key=f"{widget_key}_close", help="Close results"
    )
    if close_clicked:
        st.session_state.pop(result_key, None)
        return False
    return action_clicked
