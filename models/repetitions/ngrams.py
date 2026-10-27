"""Count the most common two-word and three-word sequences."""

from collections import Counter

from models.repetitions.repetitions_utils import analysis_words


def most_frequent_ngrams(
    page_texts: list[str], n: int, limit: int = 20
) -> list[dict]:
    """Return the most common n-grams, without joining words across pages."""
    if n not in (2, 3):
        raise ValueError("Only bigrams (2) and trigrams (3) are supported.")

    ngrams = []
    for page_text in page_texts:
        words = analysis_words(page_text)
        ngrams.extend(
            " ".join(words[index : index + n])
            for index in range(len(words) - n + 1)
        )

    total = len(ngrams)
    return [
        {
            "N-gram": phrase,
            "Frequency": count,
            "Frequency percentage": round(100 * count / total, 2),
        }
        for phrase, count in Counter(ngrams).most_common(limit)
    ]
