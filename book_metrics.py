"""Metric calculations for PDF book analysis."""

import re
from typing import Iterable

import fitz
import numpy as np
import pandas as pd


WORD_PATTERN = re.compile(r"\b[^\W\d_]+(?:['’\-][^\W\d_]+)*\b", re.UNICODE)


def extract_page_texts(pdf_bytes: bytes) -> list[str]:
    """Extract page text from an in-memory PDF and always close the document."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        return [page.get_text() for page in document]


def tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall(text or "")


def calculate_metrics(page_texts: Iterable[str]) -> dict:
    """Calculate book-wide and per-page metrics from extracted page text."""
    pages = list(page_texts)
    words_by_page = [tokenize(text) for text in pages]
    words = [word for page_words in words_by_page for word in page_words]
    lengths = [len(word) for word in words]
    unique_words = {word.casefold() for word in words}

    mean_words_per_page = (
        float(np.mean([len(words) for words in words_by_page])) if pages else 0.0
    )
    std_words_per_page = (
        float(np.std([len(words) for words in words_by_page])) if pages else 0.0
    )

    mean_word_length_per_page = [
        float(np.mean([len(word) for word in page_words])) if page_words else 0.0
        for page_words in words_by_page
    ]

    return {
        "num_pages": len(pages),
        "num_words": len(words),
        "num_unique_words": len(unique_words),
        "ttr": len(unique_words) / len(words) if words else 0.0,
        "mean_word_length": float(np.mean(lengths)) if lengths else 0.0,
        "std_word_length": float(np.std(lengths)) if lengths else 0.0,
        "longest_word": max(words, key=len) if words else "—",
        "longest_word_length": max(lengths, default=0),
        "mean_words_per_page": mean_words_per_page,
        "std_words_per_page": std_words_per_page,
        "mean_word_length_per_page": mean_word_length_per_page,
    }


def analyze_pdf(pdf_bytes: bytes) -> tuple[dict, list[str]]:
    pages = extract_page_texts(pdf_bytes)
    return calculate_metrics(pages), pages


def split_sentences(text: str) -> list[str]:
    """Split text into sentences while normalizing PDF line breaks."""
    # Replace line breaks with spaces
    text = re.sub(r"\s*\n\s*", " ", text)

    # Split after sentence-ending punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)

    return [sentence.strip() for sentence in sentences if sentence.strip()]


def get_repeated_words(sentences: list[str], big_word_th: int = 5):
    """Find long words shared by each pair of consecutive sentences.

    Matching is case-insensitive and ignores punctuation, so e.g. ``story,``
    and ``Story`` count as the same word.
    """
    save_data_list = []
    for i, (first, second) in enumerate(zip(sentences, sentences[1:]), start=1):
        words_1 = {word.casefold() for word in tokenize(first)}
        words_2 = {word.casefold() for word in tokenize(second)}
        common_words = sorted(words_1 & words_2)
        big_words = [word for word in common_words if len(word) >= big_word_th]

        save_data_list.append(
            {
                "lines": f"{i}-{i + 1}",
                "common_words": common_words,
                "num_common_words": len(common_words),
                "big_words_repeated": big_words,
                "num_big_words_repeated": len(big_words),
            }
        )

    return pd.DataFrame(
        save_data_list,
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
    """Return one row per long word repeated across adjacent sentences per page."""
    rows = []
    for page_number, text in enumerate(page_texts, start=1):
        sentence_results = get_repeated_words(split_sentences(text), big_word_th)
        for result in sentence_results.itertuples(index=False):
            # Ignore sentence pairs with no repeated long words.
            if result.num_big_words_repeated == 0:
                continue
            for word in result.big_words_repeated:
                rows.append(
                    {
                        "Page": page_number,
                        "Sentence pair": result.lines,
                        "Repeated word": word,
                    }
                )
    return pd.DataFrame(rows, columns=["Page", "Sentence pair", "Repeated word"])
