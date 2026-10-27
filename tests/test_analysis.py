import unittest

from metrics.book_metrics import calculate_metrics
from models.repetitions.word_frequency import most_frequent_words


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


class WordFrequencyTests(unittest.TestCase):
    def test_likely_names_are_excluded_from_frequency_table(self):
        page_texts = [
            "Vio a Pármaco llegar al puerto. Pármaco habló con Hades. "
            "Hades respondió entonces. "
            "La palabra abundante aparece en el texto."
        ]

        words = most_frequent_words(page_texts)

        displayed_words = {row["Word"] for row in words}
        self.assertNotIn("pármaco", displayed_words)
        self.assertNotIn("hades", displayed_words)
        self.assertIn("abundante", displayed_words)

    def test_sentence_initial_capitalization_alone_is_not_a_name(self):
        words = most_frequent_words(["Palabra común. Palabra común."])

        self.assertEqual(words[0]["Word"], "palabra")


if __name__ == "__main__":
    unittest.main()
