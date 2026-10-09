import re
import numpy as np
import matplotlib.pyplot as plt

import regex_utils as reut


def plot_mean_len_per_page(doc):
    # Mean word length per page
    mean_word_length_per_page = []

    for page in doc:
        page_text = page.get_text()
        page_words = re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", page_text)

        if page_words:
            word_lengths = [len(word) for word in page_words]
            mean_word_length_per_page.append(np.mean(word_lengths))
        else:
            mean_word_length_per_page.append(0)

    # Plot
    plt.figure(figsize=(12, 5))

    plt.plot(
        range(1, len(mean_word_length_per_page) + 1),
        mean_word_length_per_page,
        marker="o",
        markersize=3,
    )

    plt.xlabel("Page")
    plt.ylabel("Mean Word Length")
    plt.title("Mean Word Length Throughout La Carontina")

    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_pages_per_chapter(doc):
    """
    Detects chapter headings such as 'Chapter I' or 'CHAPTER II'
    and plots the estimated number of pages per chapter.
    """

    chapter_pages = {}
    current_chapter = "Unidentified"

    for _, page in enumerate(doc, start=1):
        page_text = page.get_text()

        # Find chapter headings in the page text
        matches = list(reut.chapter_pattern.finditer(page_text))

        # Assign the page to the first chapter heading found
        if matches:
            current_chapter = matches[0].group(1).upper()

        chapter_pages.setdefault(current_chapter, 0)
        chapter_pages[current_chapter] += 1

    # Exclude pages before the first identified chapter
    chapter_pages.pop("Unidentified", None)

    if not chapter_pages:
        print("No chapter headings were detected.")
        return

    chapters = list(chapter_pages.keys())
    pages = list(chapter_pages.values())

    plt.figure(figsize=(12, 5))

    plt.bar(chapters, pages)

    plt.xlabel("Chapter")
    plt.ylabel("Number of Pages")
    plt.title("Number of Pages per Chapter")

    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()
