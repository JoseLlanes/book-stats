"""Matplotlib chart builders for Book Stats."""

import matplotlib.pyplot as plt

import regex_utils as reut


def plot_mean_len_per_page(mean_word_length_per_page):
    """Return a figure showing average token length on every page."""
    fig, ax = plt.subplots(figsize=(10, 4))
    pages = range(1, len(mean_word_length_per_page) + 1)
    ax.plot(pages, mean_word_length_per_page, marker="o", markersize=3, linewidth=1.5)
    ax.set_xlabel("Page")
    ax.set_ylabel("Mean word length (characters)")
    ax.set_title("Mean Word Length per Page")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def get_chapter_pages(page_texts):
    """Estimate chapter lengths by assigning pages from each heading onward."""
    chapter_pages = {}
    current_chapter = None
    for page_text in page_texts:
        matches = list(reut.chapter_pattern.finditer(page_text or ""))
        if matches:
            current_chapter = matches[0].group(1).upper()
            chapter_pages.setdefault(current_chapter, 0)
        if current_chapter is not None:
            chapter_pages[current_chapter] += 1
    return chapter_pages


def plot_pages_per_chapter(page_texts):
    """Return (figure, chapter counts), or (None, {}) when no headings exist."""
    chapter_pages = get_chapter_pages(page_texts)
    if not chapter_pages:
        return None, chapter_pages

    fig, ax = plt.subplots(figsize=(10, 4))
    chapters = list(chapter_pages)
    ax.bar(chapters, list(chapter_pages.values()), color="#4c78a8")
    ax.set_xlabel("Chapter")
    ax.set_ylabel("Estimated pages")
    ax.set_title("Estimated Pages per Chapter")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig, chapter_pages
