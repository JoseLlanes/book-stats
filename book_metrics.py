"""Metric calculations for PDF book analysis."""

import re
from typing import Iterable

import fitz
import numpy as np


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

    return {
        "num_pages": len(pages),
        "num_words": len(words),
        "num_unique_words": len(unique_words),
        "ttr": len(unique_words) / len(words) if words else 0.0,
        "mean_word_length": float(np.mean(lengths)) if lengths else 0.0,
        "std_word_length": float(np.std(lengths)) if lengths else 0.0,
        "longest_word": max(words, key=len) if words else "—",
        "longest_word_length": max(lengths, default=0),
        "shortest_word": min(words, key=len) if words else "—",
        "shortest_word_length": min(lengths, default=0),
        "mean_words_per_page": float(np.mean([len(words) for words in words_by_page])) if pages else 0.0,
        "std_words_per_page": float(np.std([len(words) for words in words_by_page])) if pages else 0.0,
        "mean_word_length_per_page": [
            float(np.mean([len(word) for word in page_words])) if page_words else 0.0
            for page_words in words_by_page
        ],
    }


def analyze_pdf(pdf_bytes: bytes) -> tuple[dict, list[str]]:
    pages = extract_page_texts(pdf_bytes)
    return calculate_metrics(pages), pages
