"""Count the most common words in a collection of page texts."""

from collections import Counter

from core.name_detector import detect_names
from models.tokenizer import tokenize


def most_frequent_words(page_texts: list[str], limit: int = 20) -> list[dict]:
    """Return up to ``limit`` words with at least five characters."""
    names = detect_names(page_texts)
    words = (
        word.lower()
        for page_text in page_texts
        for word in tokenize(page_text)
        if len(word) >= 5 and word.casefold() not in names
    )
    return [
        {"Word": word, "Frequency": count}
        for word, count in Counter(words).most_common(limit)
    ]
