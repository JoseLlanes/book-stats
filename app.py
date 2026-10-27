"""Streamlit interface for Book Stats: Literary Analytics."""

import csv
import io

import fitz
import matplotlib.pyplot as plt
import streamlit as st

import visualization.plots as vis
import metrics.book_metrics as mbm
from models.analysis.word_frequency import most_frequent_words
from metrics.main_classes import METRICS


st.set_page_config(
    page_title="Book Stats: Literary Analytics", page_icon="\U0001f4da", layout="wide"
)
st.title("Book Stats: Literary Analytics")
st.write("Explore the vocabulary, word lengths, and chapter structure of a PDF book.")

uploaded_file = st.file_uploader("Upload a PDF book", type=["pdf"])


def metrics_csv(metrics):
    output = io.StringIO()
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
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    writer.writerows((label, metrics[key]) for label, key in fields)
    return output.getvalue().encode("utf-8-sig")


def analysis_button(label, result_key, widget_key):
    """Show an analysis button and a close button while its result is visible."""
    has_result = st.session_state.get(result_key) is not None
    if has_result:
        action_col, close_col = st.columns([1, 0.16], vertical_alignment="center")
        action_clicked = action_col.button(label, key=f"{widget_key}_action")
        close_clicked = close_col.button(
            "\u00d7", key=f"{widget_key}_close", help="Close results"
        )
        if close_clicked:
            st.session_state.pop(result_key, None)
            return False
        return action_clicked

    return st.button(label, key=f"{widget_key}_action")


if st.button("Analyze Book", type="primary", disabled=uploaded_file is None):
    st.session_state.pop("book_stats_metrics", None)
    st.session_state.pop("book_stats_pages", None)
    st.session_state.pop("book_stats_repetitions", None)
    st.session_state.pop("book_stats_explorer", None)
    st.session_state.pop("book_stats_word_frequency", None)
    try:
        with st.spinner("Analyzing your book..."):
            metrics, page_texts = mbm.analyze_pdf(uploaded_file.getvalue())
        if metrics["num_pages"] == 0:
            st.error("This PDF contains no pages to analyze.")
        elif metrics["num_words"] == 0:
            st.warning(
                "No selectable text was found. This may be a scanned PDF; OCR is not currently supported."
            )
        else:
            st.session_state["book_stats_metrics"] = metrics
            st.session_state["book_stats_pages"] = page_texts
    except (fitz.FileDataError, fitz.EmptyFileError, ValueError, RuntimeError) as exc:
        st.error(
            f"We couldn't process this PDF. Please check that it is a valid, readable PDF. ({exc.__class__.__name__})"
        )
    except Exception:
        st.error(
            "We couldn't process this PDF. Please check that it is a valid, readable PDF."
        )


metrics = st.session_state.get("book_stats_metrics")
page_texts = st.session_state.get("book_stats_pages")
word_frequency = st.session_state.get("book_stats_word_frequency")
if metrics and page_texts is not None:
    st.header("Overview")
    cols = st.columns(4)
    cols[0].metric("Pages", f"{metrics['num_pages']:,}")
    cols[1].metric("Total words", f"{metrics['num_words']:,}")
    cols[2].metric("Unique words", f"{metrics['num_unique_words']:,}")
    cols[3].metric("Type-Token Ratio", f"{metrics['ttr']:.1%}")

    st.header("Lexical Analysis")
    cols = st.columns(4)
    cols[0].metric("Mean word length", f"{metrics['mean_word_length']:.2f} characters")
    cols[1].metric(
        "Word length standard deviation", f"{metrics['std_word_length']:.2f}"
    )
    cols[2].metric(
        "Longest word", f"{metrics['longest_word']} ({metrics['longest_word_length']})"
    )

    cols = st.columns(2)
    cols[0].metric(
        "Mean words per page",
        f"{metrics['mean_words_per_page']:.1f} +/- {metrics['std_words_per_page']:.1f}",
    )

    st.header("Literary Metrics Visualizer")
    control_cols = st.columns(3)
    with control_cols[0]:
        explorer_axis = st.selectbox(
            "X-axis", ["Pages", "Chapters"], key="explorer_axis"
        )
    metric_by_label = {
        item.label: item for item in METRICS if explorer_axis in item.axes
    }
    metric_options = list(metric_by_label)
    metric_key = "explorer_metric"
    if st.session_state.get(metric_key) not in metric_by_label:
        st.session_state[metric_key] = metric_options[0]
    with control_cols[1]:
        selected_metric = st.selectbox("Metric", metric_options, key=metric_key)
    with control_cols[2]:
        chart_type = st.selectbox(
            "Chart type", ["Line", "Bar", "Scatter"], key="explorer_chart_type"
        )
    if analysis_button("Plot", "book_stats_explorer", "explorer_plot"):
        selected = metric_by_label[selected_metric]
        prepared = mbm.prepare_metric_data(page_texts, selected.key, explorer_axis)
        x_column = "Pages" if explorer_axis == "Pages" else "Chapter"
        chart_data = prepared.rename(columns={"value": "value"})
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
        fig = vis.plot_metric(chart_data, x_column, metric_label, plotted_type)
        if fig is None:
            st.info("No valid values are available for this selection.")
        else:
            st.pyplot(fig, width="content")
            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
            plt.close(fig)
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

    if analysis_button(
        "Calculate most frequent words",
        "book_stats_word_frequency",
        "word_frequency",
    ):
        st.session_state["book_stats_word_frequency"] = most_frequent_words(page_texts)
        st.rerun()

    word_frequency = st.session_state.get("book_stats_word_frequency")
    if word_frequency is not None:
        st.subheader("Most frequent words (5+ characters)")
        if word_frequency:
            st.dataframe(word_frequency, hide_index=True, width="stretch")
        else:
            st.info("No words with at least five characters were found.")

    if analysis_button(
        "Calculate repeated words", "book_stats_repetitions", "repetitions"
    ):
        with st.spinner("Finding long words repeated in consecutive sentences..."):
            st.session_state["book_stats_repetitions"] = mbm.calculate_repetitions(
                page_texts
            )
        st.rerun()

    repetitions = st.session_state.get("book_stats_repetitions")
    if repetitions is not None:
        st.subheader("Long words repeated in consecutive sentences")
        if repetitions.empty:
            st.info("No long repeated words were found.")
        else:
            st.dataframe(
                repetitions,
                hide_index=True,
                width="stretch",
                column_config={
                    "Page": st.column_config.NumberColumn("Page", format="%d"),
                    "Sentence pair": st.column_config.TextColumn("Sentence Pair"),
                    "Repeated word": st.column_config.TextColumn("Repeated Word"),
                },
            )
