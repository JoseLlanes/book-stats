"""Book upload and summary sections of the Streamlit app."""

import fitz
import streamlit as st

import metrics.book_metrics as book_metrics


RESULT_KEYS = (
    "book_stats_metrics",
    "book_stats_pages",
    "book_stats_repetitions",
    "book_stats_explorer",
    "book_stats_word_frequency",
    "book_stats_word_frequency_by_chapter",
    "book_stats_word_outliers",
    "book_stats_chapter_word_outliers",
    "book_stats_name_frequency",
    "book_stats_name_frequency_v2",
    "book_stats_ngrams",
    "book_stats_consecutive_repetitions",
    "book_stats_repetition_alert_open",
)


def render_upload():
    """Render the PDF uploader and analyze the selected book on demand."""
    uploaded_file = st.file_uploader("Upload a PDF book", type=["pdf"])
    if not st.button("Analyze Book", type="primary", disabled=uploaded_file is None):
        return

    for key in RESULT_KEYS:
        st.session_state.pop(key, None)

    try:
        with st.spinner("Analyzing your book..."):
            metrics, page_texts = book_metrics.analyze_pdf(uploaded_file.getvalue())
    except (fitz.FileDataError, fitz.EmptyFileError, ValueError, RuntimeError) as exc:
        st.error(
            "We couldn't process this PDF. Please check that it is a valid, "
            f"readable PDF. ({exc.__class__.__name__})"
        )
        return
    except Exception:
        st.error(
            "We couldn't process this PDF. Please check that it is a valid, readable PDF."
        )
        return

    if metrics["num_pages"] == 0:
        st.error("This PDF contains no pages to analyze.")
    elif metrics["num_words"] == 0:
        st.warning(
            "No selectable text was found. This may be a scanned PDF; "
            "OCR is not currently supported."
        )
    else:
        st.session_state["book_stats_metrics"] = metrics
        st.session_state["book_stats_pages"] = page_texts


def render_overview(metrics):
    """Show the compact book and vocabulary summary."""
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
    st.columns(2)[0].metric(
        "Mean words per page",
        f"{metrics['mean_words_per_page']:.1f} +/- {metrics['std_words_per_page']:.1f}",
    )
