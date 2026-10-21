import unittest

from metrics.book_metrics import calculate_metrics


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


if __name__ == "__main__":
    unittest.main()
