import unittest

from metrics.book_metrics import calculate_metrics
from core.name_detector import detect_names
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
            "Hades respondió entonces. Después vio a Pármaco junto a Hades. "
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

    def test_sentence_initial_words_after_punctuation_are_not_names(self):
        names = detect_names('Hablaron. Cuando llegó, saludó. Entonces se marcharon.')

        self.assertNotIn("cuando", names)
        self.assertNotIn("entonces", names)

    def test_capitalized_words_in_the_middle_of_a_sentence_are_names(self):
        names = detect_names(
            "Vio a Hades y luego a Pármaco. Respondió Hades respondió y luego vio a Hades; "
            "Habló con Pármaco."
        )

        self.assertEqual(names, {"hades", "pármaco"})

    def test_single_mid_sentence_capitalization_is_not_enough(self):
        names = detect_names("Vio a Había y a Hombres.")

        self.assertNotIn("había", names)
        self.assertNotIn("hombres", names)

    def test_capitalization_after_any_punctuation_does_not_count(self):
        names = detect_names("Vio, Hades. Vio, Hades.")

        self.assertNotIn("hades", names)

    def test_newline_does_not_make_mid_sentence_capitalization_a_boundary(self):
        names = detect_names("Vio a\nHades y luego a Hades llegar.")

        self.assertIn("hades", names)

    def test_name_detector_accepts_page_text_list(self):
        names = detect_names(
            [
                "Vio a Hades.",
                "Luego encontró a Hades y a Pármaco; después habló con Pármaco.",
            ]
        )

        self.assertEqual(names, {"hades", "pármaco"})


if __name__ == "__main__":
    unittest.main()
