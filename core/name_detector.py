"""Heuristics for finding likely proper names in book text."""

import re
from collections.abc import Iterable
from unicodedata import category

from models.tokenizer import WORD_PATTERN


# Common Spanish words that are frequently capitalized at sentence starts.
NON_NAME_WORDS = {
    "aunque",
    "así",
    "bien",
    "cada",
    "como",
    "cuando",
    "cuanto",
    "donde",
    "entonces",
    "mientras",
    "nada",
    "nadie",
    "ningún",
    "ninguna",
    "pero",
    "porque",
    "pues",
    "quien",
    "quienes",
    "quizá",
    "quizás",
    "siempre",
    "sin",
    "solo",
    "también",
    "tampoco",
    "todavía",
    "todo",
    "todos",
    "tras",
    "una",
    "uno",
    "unos",
    "unas",
    "vez",
}


def detect_names(texts: str | Iterable[str], *additional_texts: str) -> set[str]:
    """Return normalized likely proper names found in running prose.

    Words at sentence beginnings are ignored. Newlines are treated as
    whitespace rather than sentence boundaries.
    """
    candidate_counts: dict[str, int] = {}

    if isinstance(texts, str):
        all_texts = (texts, *additional_texts)
    else:
        all_texts = (*texts, *additional_texts)

    for text in all_texts:
        if not text:
            continue

        # PDF line breaks should not change sentence-level decisions.
        normalized_text = re.sub(r"\s+", " ", text).strip()

        for match in WORD_PATTERN.finditer(normalized_text):
            word = match.group()

            if not word[:1].isupper():
                continue

            normalized_word = word.casefold()

            if normalized_word in NON_NAME_WORDS:
                continue

            prefix = normalized_text[: match.start()].rstrip()

            # Ignore words at the beginning of the text.
            if not prefix:
                continue

            # Require a word before this one in the same phrase. Any
            # punctuation between them breaks the pattern, including commas,
            # dashes, quotation marks, and sentence-ending marks.
            previous_character = prefix[-1]
            if category(previous_character).startswith("P"):
                continue

            candidate_counts[normalized_word] = (
                candidate_counts.get(normalized_word, 0) + 1
            )

    return {word for word, count in candidate_counts.items() if count >= 2}
