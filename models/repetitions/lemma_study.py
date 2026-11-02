"""Part-of-speech and lemma counts for page- or chapter-level study."""

from functools import lru_cache

import pandas as pd
import spacy

from models.lemma_constants import POS_LABELS
from models.repetitions.repetitions_utils import chapter_texts_by_name


@lru_cache(maxsize=1)
def _load_nlp():
    """Load the Spanish medium model once, on first use."""
    return spacy.load("es_core_news_md")


def build_token_info_dataframe(docs: dict) -> pd.DataFrame:
    """Convert spaCy docs keyed by page/chapter label into token-level rows."""
    records = []
    for group, doc in docs.items():
        for token in doc:
            records.append(
                {
                    "group": group,
                    "token": token.text,
                    "lemma": token.lemma_.lower(),
                    "pos": token.pos_,
                    "is_stop": token.is_stop,
                    "is_punct": token.is_punct,
                    "is_alpha": token.is_alpha,
                    "token_index": token.i,
                }
            )

    return pd.DataFrame(
        records,
        columns=[
            "group",
            "token",
            "lemma",
            "pos",
            "is_stop",
            "is_punct",
            "is_alpha",
            "token_index",
        ],
    )


def token_info_by_page(page_texts: list[str]) -> pd.DataFrame:
    """Return token annotations for each page (page numbers start at 1)."""
    nlp = _load_nlp()
    page_labels = [f"Page {number}" for number in range(1, len(page_texts) + 1)]
    docs = dict(zip(page_labels, nlp.pipe(text or "" for text in page_texts)))
    result = build_token_info_dataframe(docs)

    return result.rename(columns={"group": "page"})


def token_info_by_chapter(page_texts: list[str]) -> pd.DataFrame:
    """Return token annotations grouped by detected chapter."""
    nlp = _load_nlp()
    chapter_texts = chapter_texts_by_name(page_texts)
    docs = dict(zip(chapter_texts, nlp.pipe(chapter_texts.values())))
    result = build_token_info_dataframe(docs)

    return result.rename(columns={"group": "chapter"})


def lemma_repetition(
    token_info: pd.DataFrame,
    group_by: str,
    pos: str | None = None,
    include_stop_words: bool = False,
    min_length: int = 1,
    excluded_words: set[str] | None = None,
) -> pd.DataFrame:
    """Count lemma occurrences per page/chapter, optionally filtered by POS.

    ``group_by`` names the scope column (``page`` or ``chapter``). Punctuation
    and non-alphabetic tokens are omitted; optional filters match the word
    frequency analysis.
    """
    if group_by not in token_info.columns:
        raise ValueError(f"Unknown grouping column: {group_by}")
    filtered = token_info[token_info["is_alpha"] & ~token_info["is_punct"]]
    if min_length > 1:
        filtered = filtered[filtered["token"].str.len() >= min_length]
    if excluded_words:
        filtered = filtered[~filtered["token"].str.casefold().isin(excluded_words)]
    if not include_stop_words:
        filtered = filtered[~filtered["is_stop"]]
    if pos:
        filtered = filtered[filtered["pos"] == pos.upper()]

    return (
        filtered.groupby([group_by, "pos", "lemma"], as_index=False)
        .size()
        .rename(columns={"size": "frequency"})
        .sort_values([group_by, "frequency", "lemma"], ascending=[True, False, True])
        .reset_index(drop=True)
    )


def lemma_frequency(
    page_texts: list[str], limit: int | None = None, min_frequency: int = 11
) -> list[dict]:
    """Return book-wide lemma counts, regardless of page or chapter.

    All alphabetic tokens are counted. The frequency threshold is applied
    after aggregation over the whole book; percentages use all alphabetic
    tokens as their denominator.
    """
    token_info = token_info_by_page(page_texts)
    eligible_tokens = token_info[token_info["is_alpha"] & ~token_info["is_punct"]]
    totals = (
        eligible_tokens.groupby(["pos", "lemma"], as_index=False)
        .size()
        .rename(columns={"size": "frequency"})
        .sort_values(["frequency", "lemma"], ascending=[False, True])
    )
    total_tokens = len(eligible_tokens)
    totals = totals[totals["frequency"] >= min_frequency]
    if limit is not None:
        totals = totals.head(limit)
    if not total_tokens or totals.empty:
        return []

    return [
        {
            "Lemma": row.lemma,
            "Type": POS_LABELS.get(row.pos, row.pos),
            "Frequency": int(row.frequency),
            "Frequency percentage": round(100 * row.frequency / total_tokens, 2),
        }
        for row in totals.head(limit).itertuples(index=False)
    ]
