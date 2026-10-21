import re


def split_sentences(text: str) -> list[str]:
    """Split text into sentences while normalizing PDF line breaks."""
    normalized_text = re.sub(r"\s*\n\s*", " ", text or "")
    sentences = re.split(r"(?<=[.!?])\s+", normalized_text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]
