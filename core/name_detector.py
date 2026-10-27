"""Heuristics for finding likely proper names in book text."""

from models.tokenizer import WORD_PATTERN


def detect_names(texts: list[str]) -> set[str]:
    """Return normalized words used with internal title capitalization.

    A capitalized word is considered a likely name only when it does not start
    a sentence. This avoids classifying ordinary sentence-initial words as
    names while still finding names such as ``Hades`` in running prose.
    """
    names = set()
    for text in texts:
        main_line = (text or "").splitlines() or [text or ""]
        for line in main_line:
            for match in WORD_PATTERN.finditer(line):
                word = match.group()
                if not word[:1].isupper():
                    continue
                prefix = line[: match.start()]
                # Sentence boundaries after the prior token mark this as a
                # sentence-initial capital, rather than evidence of a name.
                prior = prefix.rstrip()
                if prior and prior[-1] not in ".!?…":
                    names.add(word.casefold())
    return names
