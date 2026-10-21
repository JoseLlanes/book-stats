"""Streamlit interface for Book Stats: Literary Analytics."""

import csv
import io

import fitz
import matplotlib.pyplot as plt
import streamlit as st

import visualization as vis
from book_metrics import analyze_pdf, calculate_repetitions


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
        ("Shortest word", "shortest_word"),
        ("Shortest word length", "shortest_word_length"),
        ("Mean words per page", "mean_words_per_page"),
        ("Words per page standard deviation", "std_words_per_page"),
    ]
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    writer.writerows((label, metrics[key]) for label, key in fields)
    return output.getvalue().encode("utf-8-sig")


if st.button("Analyze Book", type="primary", disabled=uploaded_file is None):
    st.session_state.pop("book_stats_metrics", None)
    st.session_state.pop("book_stats_pages", None)
    st.session_state.pop("book_stats_repetitions", None)
    try:
        with st.spinner("Analyzing your book..."):
            metrics, page_texts = analyze_pdf(uploaded_file.getvalue())
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

    st.header("Visualizations")
    left, right = st.columns(2)
    with left:
        fig, chapters = vis.plot_pages_per_chapter(page_texts)
        if fig is None:
            st.info(
                "No chapter headings were detected. Try headings such as CAPITULO I or CHAPTER 1."
            )
        else:
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    with right:
        fig = vis.plot_mean_len_per_page(metrics["mean_word_length_per_page"])
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.download_button(
        "Download metrics as CSV",
        data=metrics_csv(metrics),
        file_name="book_stats_metrics.csv",
        mime="text/csv",
    )

    if st.button("Calculate repeated words"):
        with st.spinner("Finding long words repeated in consecutive sentences..."):
            st.session_state["book_stats_repetitions"] = calculate_repetitions(
                page_texts
            )

    repetitions = st.session_state.get("book_stats_repetitions")
    if repetitions is not None:
        st.subheader("Long words repeated in consecutive sentences")
        if repetitions.empty:
            st.info("No long repeated words were found.")
        else:
            st.dataframe(
                repetitions,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Page": st.column_config.NumberColumn("Page", format="%d"),
                    "Sentence pair": st.column_config.TextColumn("Sentence Pair"),
                    "Repeated word": st.column_config.TextColumn("Repeated Word"),
                },
            )
