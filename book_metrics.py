import re
import numpy as np
import fitz

import visualization as vis


PDF_PATH = "data/La Carontina.pdf"

# Open PDF
doc = fitz.open(PDF_PATH)

# Number of pages
num_pages = len(doc)

# Extract all text
text = "\n".join(page.get_text() for page in doc)

# Extract words
words = re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", text)
num_words = len(words)

# Word lengths
word_lengths = [len(word) for word in words]

# Unique words
unique_words = set(word.lower() for word in words)
num_unique_words = len(unique_words)

# Words per page
words_per_page = [
    re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", page.get_text()) for page in doc
]

# Discard the first page because it contains the title
words_per_page = words_per_page[1:]

# Count the number of words on each page
num_words_per_page = [len(page_words) for page_words in words_per_page]


# Print document metrics
print(f"Pages: {num_pages}")
print(f"Words: {num_words}")
print(f"Unique words: {num_unique_words}")

if num_words > 0:
    lexical_richness = num_unique_words / num_words
    print(f"Type-Token Ratio (TTR): {lexical_richness * 100:.2f} %")

    print(
        f"Mean word length: {np.mean(word_lengths):.2f} +/- {np.std(word_lengths):.2f}"
    )

    max_word_index = np.argmax(word_lengths)
    print(
        f"Maximum word length: {word_lengths[max_word_index]} ({words[max_word_index]})"
    )

    print(f"Minimum word length: {np.min(word_lengths)}")

if num_words_per_page:
    mean_words_per_page = np.mean(num_words_per_page)
    std_words_per_page = np.std(num_words_per_page)

    print(
        f"Mean words per page: {mean_words_per_page:.2f} +/- {std_words_per_page:.2f}"
    )


# Generate visualizations
vis.plot_mean_len_per_page(doc)
vis.plot_pages_per_chapter(doc)

# Close PDF
doc.close()
