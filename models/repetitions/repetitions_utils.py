"""Shared text preparation for lexical analyses."""

from collections import Counter

from core.chapter_detector import chapter_pattern
from models.tokenizer import tokenize


def analysis_words(
    text: str,
    min_length: int = 1,
    excluded_words: set[str] | None = None,
) -> list[str]:
    """Return case-insensitive words after applying shared lexical filters."""
    excluded_words = excluded_words or set()
    return [
        word.casefold()
        for word in tokenize(text)
        if len(word) >= min_length and word.casefold() not in excluded_words
    ]


def word_counts_by_chapter(
    page_texts: list[str],
    min_length: int = 1,
    included_words: set[str] | None = None,
    excluded_words: set[str] | None = None,
) -> dict[str, Counter]:
    """Count filtered words per detected chapter, omitting chapter headings."""
    counts_by_chapter = {}
    for chapter, chapter_text in chapter_texts_by_name(page_texts).items():
        words = analysis_words(
            chapter_text,
            min_length=min_length,
            excluded_words=excluded_words,
        )
        if included_words is not None:
            words = [word for word in words if word in included_words]
        counts_by_chapter[chapter] = Counter(words)
    return counts_by_chapter


def chapter_texts_by_name(page_texts: list[str]) -> dict[str, str]:
    """Collect page fragments under detected chapter names, omitting headings."""
    chapters = {}
    current_chapter = "Sin capitulo"

    for page_text in page_texts:
        text = page_text or ""
        start = 0
        for heading in chapter_pattern.finditer(text):
            fragment = text[start : heading.start()]
            if fragment.strip():
                chapters.setdefault(current_chapter, []).append(fragment)
            current_chapter = f"Capitulo {heading.group(1).upper()}"
            chapters.setdefault(current_chapter, [])
            start = heading.end()

        fragment = text[start:]
        if fragment.strip():
            chapters.setdefault(current_chapter, []).append(fragment)

    return {chapter: "\n".join(fragments) for chapter, fragments in chapters.items()}
