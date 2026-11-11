import unittest

import pandas as pd

from models.lemma_constants import INITAL_LEMMA_TO_COUNT, POS_LABELS
from models.repetitions.lemma_study import pos_counts_by_group


class POSCountTests(unittest.TestCase):
    def test_selected_pos_percentages_do_not_exceed_100_percent(self):
        token_info = pd.DataFrame(
            [
                # One phrase: three selected POS tokens and one other word.
                {"page": "Page 1", "pos": "ADJ", "is_alpha": True, "is_punct": False},
                {"page": "Page 1", "pos": "NOUN", "is_alpha": True, "is_punct": False},
                {"page": "Page 1", "pos": "VERB", "is_alpha": True, "is_punct": False},
                {"page": "Page 1", "pos": "ADP", "is_alpha": True, "is_punct": False},
                {"page": "Page 1", "pos": "PUNCT", "is_alpha": False, "is_punct": True},
                # Several phrases: six selected POS tokens and one determiner.
                {"page": "Page 2", "pos": "DET", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "NOUN", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "ADV", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "VERB", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "ADJ", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "NOUN", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "VERB", "is_alpha": True, "is_punct": False},
                {"page": "Page 2", "pos": "PUNCT", "is_alpha": False, "is_punct": True},
            ]
        )

        result = pos_counts_by_group(token_info, "page")
        percentage_columns = [
            f"{POS_LABELS[pos]}_percentage" for pos in INITAL_LEMMA_TO_COUNT
        ]
        percentage_totals = result[percentage_columns].sum(axis=1)

        self.assertTrue((percentage_totals <= 100 + 1e-10).all())
        self.assertAlmostEqual(percentage_totals.iloc[0], 75.0)
        self.assertAlmostEqual(percentage_totals.iloc[1], 85.7142857, places=6)


if __name__ == "__main__":
    unittest.main()
