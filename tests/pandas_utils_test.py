import unittest

import pandas as pd

from pm4py.util import pandas_utils


class PandasUtilsTest(unittest.TestCase):
    def test_to_dict_uses_keyword_only_orient(self):
        """Tests that pandas to_dict is called with a keyword-only orient."""

        class KeywordOnlyDataFrame:
            def to_dict(self, *, orient):
                return orient

        dataframe = KeywordOnlyDataFrame()

        self.assertEqual(pandas_utils.to_dict_records(dataframe), "records")
        self.assertEqual(pandas_utils.to_dict_index(dataframe), "index")

        dataframe = pd.DataFrame([{"case": "A", "event": "start"}])
        self.assertEqual(
            pandas_utils.to_dict_records(dataframe),
            [{"case": "A", "event": "start"}],
        )
        self.assertEqual(
            pandas_utils.to_dict_index(dataframe),
            {0: {"case": "A", "event": "start"}},
        )


if __name__ == "__main__":
    unittest.main()
