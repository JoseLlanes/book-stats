import unittest

import matplotlib.pyplot as plt

from metrics.book_metrics import prepare_metric_data
from visualization.plots import plot_metric


class ExplorerDataTests(unittest.TestCase):
    def test_page_data_matches_page_metrics(self):
        data = prepare_metric_data(["One two.", "Three."], "num_words", "Pages")
        self.assertEqual(
            data.to_dict("records"),
            [{"Pages": 1, "value": 2.0}, {"Pages": 2, "value": 1.0}],
        )

    def test_chapter_additive_metrics_are_summed(self):
        data = prepare_metric_data(
            ["CHAPTER 1\nOne two.", "Three four."], "num_words", "Chapters"
        )
        # The existing tokenizer includes the two words in the chapter heading.
        self.assertEqual(data.iloc[0]["value"], 5)

    def test_chapter_average_is_recomputed_from_text(self):
        data = prepare_metric_data(
            ["CHAPTER 1\nA. B C D."], "avg_sentence_length", "Chapters"
        )
        self.assertAlmostEqual(data.iloc[0]["value"], 2.5)

    def test_unique_words_recomputed_and_unheaded_pages_excluded(self):
        data = prepare_metric_data(
            ["before", "CHAPTER I\nEcho echo.", "Echo."], "num_unique_words", "Chapters"
        )
        # Heading words are part of the PDF page text and existing analysis metrics.
        self.assertEqual(data.iloc[0]["value"], 3)
        self.assertEqual(len(data), 1)

    def test_empty_and_missing_values(self):
        self.assertTrue(prepare_metric_data([], "num_words", "Pages").empty)
        data = prepare_metric_data(["", ""], "avg_sentence_length", "Pages")
        self.assertTrue(data.empty)

    def test_invalid_metric_and_axis_raise(self):
        with self.assertRaises(ValueError):
            prepare_metric_data(["word"], "unknown", "Pages")
        with self.assertRaises(ValueError):
            prepare_metric_data(["word"], "num_words", "Sentences")


class ExplorerChartTests(unittest.TestCase):
    def test_all_chart_types_generate_figures(self):
        import pandas as pd

        data = pd.DataFrame({"Pages": [1, 2], "value": [2, 3]})
        for chart_type in ("Line", "Bar", "Scatter"):
            with self.subTest(chart_type=chart_type):
                fig = plot_metric(data, "Pages", "Number of words", chart_type)
                self.assertIsNotNone(fig)
                plt.close(fig)

    def test_empty_data_returns_no_figure_and_invalid_chart_rejected(self):
        import pandas as pd

        self.assertIsNone(
            plot_metric(
                pd.DataFrame(columns=["Pages", "value"]), "Pages", "Words", "Line"
            )
        )
        with self.assertRaises(ValueError):
            plot_metric(
                pd.DataFrame({"Pages": [1], "value": [2]}), "Pages", "Words", "Pie"
            )


if __name__ == "__main__":
    unittest.main()
