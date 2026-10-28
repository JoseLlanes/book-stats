"""Detect identical words repeated consecutively in text."""

from models.tokenizer import tokenize


def find_consecutive_repetitions_by_page(page_texts: list[str]) -> list[dict]:
    """Find runs of identical consecutive words and their page numbers."""
    repetitions = []
    for page_number, text in enumerate(page_texts, start=1):
        words = tokenize(text)
        index = 0
        while index < len(words) - 1:
            end = index + 1
            while end < len(words) and words[end].casefold() == words[index].casefold():
                end += 1
            if end - index >= 2:
                repetitions.append(
                    {
                        "word": words[index],
                        "count": end - index,
                        "page": page_number,
                    }
                )
            index = end
    return repetitions


def has_consecutive_repeated_words(text: str) -> bool:
    """Return whether any word is immediately repeated in the token sequence."""
    words = tokenize(text)
    return any(
        first.casefold() == second.casefold() for first, second in zip(words, words[1:])
    )
