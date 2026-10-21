"""Metric calculations and explorer data preparation for PDF books."""

import re
from typing import Iterable

import fitz
import numpy as np
import pandas as pd

# Own libraries
from core.chapter_detector import chapter_pattern
from core.sentence_segmenter import split_sentences
from metrics.main_classes import METRICS
from models.tokenizer import tokenize


def _word_metrics(words: list[str]) -> dict[str, float | int | str]:
    """Calculate shared word-count, diversity, length, and extrema statistics."""
    lengths = [len(word) for word in words]
    unique_words = {word.casefold() for word in words}
    return {
        "num_words": len(words),
        "num_unique_words": len(unique_words),
        "ttr": len(unique_words) / len(words) if words else 0.0,
        "mean_word_length": float(np.mean(lengths)) if lengths else 0.0,
        "std_word_length": float(np.std(lengths)) if lengths else 0.0,
        "longest_word": max(words, key=len) if words else "â€”",
        "longest_word_length": max(lengths, default=0),
    }


def _page_metric_values(text: str) -> dict[str, float]:
    """Calculate the metrics used by the page and chapter explorer."""
    words = tokenize(text)
    sentences = split_sentences(text)
    word_metrics = _word_metrics(words)
    sentence_word_count = sum(len(tokenize(sentence)) for sentence in sentences)
    sentence_count = len(sentences)
    return {
        "num_pages": 1.0,
        "num_words": float(word_metrics["num_words"]),
        "num_unique_words": float(word_metrics["num_unique_words"]),
        "num_sentences": float(sentence_count),
        "avg_sentence_length": (
            sentence_word_count / sentence_count if sentence_count else float("nan")
        ),
        "mean_word_length": (
            float(word_metrics["mean_word_length"]) if words else float("nan")
        ),
        "ttr": float(word_metrics["ttr"]) if words else float("nan"),
    }


def calculate_metrics(page_texts: Iterable[str]) -> dict:
    """Calculate book-wide and per-page metrics from extracted page text."""
    pages = list(page_texts)
    words_by_page = [tokenize(text) for text in pages]
    words = [word for page_words in words_by_page for word in page_words]
    page_word_counts = [len(page_words) for page_words in words_by_page]
    return {
        "num_pages": len(pages),
        **_word_metrics(words),
        "mean_words_per_page": (float(np.mean(page_word_counts)) if pages else 0.0),
        "std_words_per_page": (float(np.std(page_word_counts)) if pages else 0.0),
    }


def extract_page_texts(pdf_bytes: bytes) -> list[str]:
    """Extract page text from an in-memory PDF and always close the document."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        return [page.get_text() for page in document]


def analyze_pdf(pdf_bytes: bytes) -> tuple[dict, list[str]]:
    """Extract a PDF's pages and calculate its book-level metrics."""
    pages = extract_page_texts(pdf_bytes)
    return calculate_metrics(pages), pages


def _chapter_ids(page_texts: list[str]) -> list[str | None]:
    """Assign pages to the most recently detected chapter heading."""
    current_chapter = None
    chapter_ids = []
    for text in page_texts:
        matches = chapter_pattern.finditer(text or "")
        heading = next(matches, None)
        if heading:
            current_chapter = heading.group(1).upper()
        chapter_ids.append(current_chapter)
    return chapter_ids


def prepare_metric_data(
    page_texts: list[str], metric_key: str, axis: str
) -> pd.DataFrame:
    """Return page or chapter x/value rows, omitting missing observations."""
    metric = next((item for item in METRICS if item.key == metric_key), None)
    if metric is None:
        raise ValueError(f"Unavailable metric: {metric_key}")
    if axis not in {"Pages", "Chapters"}:
        raise ValueError(f"Unavailable x-axis: {axis}")
    if axis not in metric.axes:
        raise ValueError(f"Metric {metric_key} is unavailable for {axis}")

    chapter_ids = _chapter_ids(page_texts)
    rows = []
    for page_number, text in enumerate(page_texts, start=1):
        rows.append(
            {
                "Page": page_number,
                "Chapter": chapter_ids[page_number - 1],
                "Text": text or "",
                **_page_metric_values(text or ""),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        x_column = "Pages" if axis == "Pages" else "Chapter"
        return pd.DataFrame(columns=[x_column, "value"])

    if axis == "Pages":
        return (
            frame[["Page", metric_key]]
            .rename(columns={"Page": "Pages", metric_key: "value"})
            .dropna(subset=["value"])
            .reset_index(drop=True)
        )

    frame = frame.dropna(subset=["Chapter"])
    chapter_values = []
    for chapter, chapter_pages in frame.groupby("Chapter", sort=False):
        if metric.aggregation == "sum":
            value = chapter_pages[metric_key].sum(min_count=1)
        else:
            chapter_text = "\n".join(chapter_pages["Text"])
            value = _page_metric_values(chapter_text)[metric_key]
        if pd.notna(value):
            chapter_values.append({"Chapter": chapter, "value": value})
    return pd.DataFrame(chapter_values, columns=["Chapter", "value"])


def get_repeated_words(sentences: list[str], big_word_th: int = 5) -> pd.DataFrame:
    """Find long words shared by each pair of consecutive sentences."""
    rows = []
    for pair_number, (first, second) in enumerate(
        zip(sentences, sentences[1:]), start=1
    ):
        words_1 = {word.casefold() for word in tokenize(first)}
        words_2 = {word.casefold() for word in tokenize(second)}
        common_words = sorted(words_1 & words_2)
        big_words = [word for word in common_words if len(word) >= big_word_th]
        rows.append(
            {
                "lines": f"{pair_number}-{pair_number + 1}",
                "common_words": common_words,
                "num_common_words": len(common_words),
                "big_words_repeated": big_words,
                "num_big_words_repeated": len(big_words),
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "lines",
            "common_words",
            "num_common_words",
            "big_words_repeated",
            "num_big_words_repeated",
        ],
    )


def calculate_repetitions(
    page_texts: Iterable[str], big_word_th: int = 5
) -> pd.DataFrame:
    """Return repeated long words across consecutive sentences on each page."""
    rows = []
    for page_number, text in enumerate(page_texts, start=1):
        sentence_results = get_repeated_words(split_sentences(text), big_word_th)
        for result in sentence_results.itertuples(index=False):
            for word in result.big_words_repeated:
                rows.append(
                    {
                        "Page": page_number,
                        "Sentence pair": result.lines,
                        "Repeated word": word,
                    }
                )
    return pd.DataFrame(rows, columns=["Page", "Sentence pair", "Repeated word"])
