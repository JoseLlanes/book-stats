import re

WORD_PATTERN = re.compile(r"\b[^\W\d_]+(?:['â€™\-][^\W\d_]+)*\b", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Return the words in text using the application's Unicode-aware pattern."""
    return WORD_PATTERN.findall(text or "")
