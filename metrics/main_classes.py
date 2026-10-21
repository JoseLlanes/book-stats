from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    aggregation: Literal["sum", "recompute"]
    axes: tuple[Literal["Pages", "Chapters"], ...] = ("Pages", "Chapters")


# Add metrics here and to _page_metric_values; chart rendering stays generic.
METRICS = (
    Metric("num_pages", "Number of pages", "sum", axes=("Chapters",)),
    Metric("num_words", "Number of words", "sum"),
    Metric("num_unique_words", "Number of unique words", "recompute"),
    Metric("num_sentences", "Number of sentences", "sum"),
    Metric("avg_sentence_length", "Average sentence length (words)", "recompute"),
    Metric("mean_word_length", "Average word length (characters)", "recompute"),
    Metric("ttr", "Type-token ratio", "recompute"),
)
