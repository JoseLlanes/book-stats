import unittest

from book_metrics import calculate_metrics
from visualization import get_chapter_pages


class MetricsTests(unittest.TestCase):
    def test_metrics_include_unicode_words_and_empty_pages(self):
        text = "Hola mundo"
        text += " " + chr(0x00A1) + "Mundo! caf" + chr(0x00E9)
        result = calculate_metrics([text])
        self.assertEqual(result["num_pages"], 1)
        self.assertEqual(result["num_words"], 4)
        self.assertEqual(result["num_unique_words"], 3)
        self.assertEqual(result["ttr"], 0.75)
        self.assertEqual(result["longest_word"], "mundo")

    def test_empty_document_has_zero_metrics(self):
        result = calculate_metrics([])
        self.assertEqual(result["num_pages"], 0)
        self.assertEqual(result["num_words"], 0)
        self.assertEqual(result["mean_word_length"], 0)


class ChapterDetectionTests(unittest.TestCase):
    def test_detects_spanish_english_roman_and_arabic_headings(self):
        spanish_heading = "CAP" + chr(0x00CD) + "TULO I\ntext"
        pages = ["Preface", spanish_heading, "CHAPTER 2\ntext", "CAPITULO III"]
        self.assertEqual(get_chapter_pages(pages), {"I": 1, "2": 1, "III": 1})

    def test_no_headings_returns_empty_mapping(self):
        self.assertEqual(get_chapter_pages(["Just prose", "More prose"]), {})


if __name__ == "__main__":
    unittest.main()
