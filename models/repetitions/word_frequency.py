"""Count frequent words across a book and within each chapter."""

from collections import Counter

from core.name_detector import detect_names
from models.repetitions.repetitions_utils import analysis_words, word_counts_by_chapter


def most_frequent_words(page_texts: list[str], limit: int = 20) -> list[dict]:
    """Return up to ``limit`` words with at least five characters."""
    names = detect_names(page_texts)
    words = [
        word
        for page_text in page_texts
        for word in analysis_words(page_text, min_length=5, excluded_words=names)
    ]

    total_words = len(words)
    result = []
    for word, count in Counter(words).most_common(limit):
        percentage = round(100 * count / total_words, 2)
        result.append(
            {"Word": word, "Frequency": count, "Frequency percentage": percentage}
        )
    return result


def word_frequency_by_chapter(page_texts: list[str]) -> list[dict]:
    """Count long, non-name words by chapter and add book-wide statistics.

    The mean is calculated across all detected chapters, including chapters
    where a word does not occur. Text before the first heading is grouped under
    ``Sin capitulo``. Chapter headings themselves are omitted.
    """
    names = detect_names(page_texts)
    counts_by_chapter = word_counts_by_chapter(
        page_texts, min_length=5, excluded_words=names
    )

    chapter_count = len(counts_by_chapter)
    total_by_word = Counter()
    for chapter_counts in counts_by_chapter.values():
        total_by_word.update(chapter_counts)

    results = []
    for chapter, word_counts in counts_by_chapter.items():
        for word, count in word_counts.items():
            if count <= 10:
                continue

            mean_per_chapter = total_by_word[word] / chapter_count
            results.append(
                {
                    "Chapter": chapter,
                    "Word": word,
                    "Frequency": count,
                    "Mean per chapter": round(mean_per_chapter, 2),
                    "Document total": total_by_word[word],
                    "ratio_appearance": round(count / mean_per_chapter, 2),
                }
            )

    return sorted(results, key=lambda row: row["ratio_appearance"], reverse=True)


def name_frequency(page_texts: list[str], limit: int = 20) -> list[dict]:
    """Return the most frequent likely names and their chapter distribution."""
    names = detect_names(page_texts)
    counts_by_chapter = word_counts_by_chapter(
        page_texts, min_length=5, included_words=names
    )

    chapter_count = len(counts_by_chapter)
    if not chapter_count:
        return []

    total_by_name = Counter()
    for chapter_counts in counts_by_chapter.values():
        total_by_name.update(chapter_counts)

    results = []
    for name, total in total_by_name.most_common(limit):
        chapter, _ = max(counts_by_chapter.items(), key=lambda item: item[1][name])
        chapter_total = counts_by_chapter[chapter].get(name, 0)
        results.append(
            {
                "Name": name,
                "Total appearances": total,
                "Most frequent chapter": chapter,
                "Appearances in chapter": chapter_total,
                "Mean per chapter": round(total / chapter_count, 2),
            }
        )
    return results
