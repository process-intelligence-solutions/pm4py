import importlib.util
import unittest

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift import algorithm
from pm4py.algo.concept_drift.variants import supervised_similarity as supervised
from tests.concept_drift_statistics_test import make_log


class SupervisedSimilarityTest(unittest.TestCase):
    def test_similarity_image_uses_balanced_start_order_windows(self):
        log = make_log(["AB"] * 3 + ["AC"] * 3)
        # First trace spans into the second regime but still belongs to window 0.
        log.loc[1, "time:timestamp"] += pd.Timedelta(hours=1)
        image = supervised.similarity_image(log, {"num_windows": 2})
        self.assertEqual(image.windows, [(0, 3), (3, 6)])
        self.assertEqual(image.pixels.dtype, np.uint8)
        np.testing.assert_array_equal(image.pixels, [[255, 0], [0, 255]])
        identical = supervised.similarity_image(
            make_log(["AB"] * 4), {"num_windows": 8}
        )
        np.testing.assert_array_equal(identical.pixels, np.full((4, 4), 255))
        empty = supervised.similarity_image(pd.DataFrame())
        self.assertEqual(empty.pixels.shape, (0, 0))

    def test_external_predictor_and_interval_mapping(self):
        log = make_log(["AB"] * 4 + ["AC"] * 4 + ["AB"] * 4)
        predictions = [
            supervised.Region(1, 3, "sudden", 0.8),
            supervised.Region(2, 4, "recurring", 0.9),
            supervised.Region(5, 5, "incremental", 0.2),
        ]

        def predictor(pixels):
            self.assertEqual(pixels.shape, (6, 6))
            return predictions

        result = algorithm.apply(
            log,
            algorithm.Variants.SUPERVISED_SIMILARITY,
            {"predictor": predictor, "num_windows": 6},
        )
        self.assertEqual([score.score for score in result.scores], [0.8, 0.9, 0.2])
        self.assertEqual([alarm.index for alarm in result.changes], [4, 4])
        (interval,) = result.intervals
        self.assertEqual((interval.start_index, interval.end_index), (4, 9))
        self.assertEqual(interval.details["type"], "recurring")
        self.assertEqual(interval.available_at, log["time:timestamp"].max())
        with self.assertRaisesRegex(ValueError, "outside"):
            supervised.apply(
                log, {"predictor": lambda _: [supervised.Region(99, 99, "sudden")]}
            )
        with self.assertRaisesRegex(TypeError, "predictor"):
            supervised.apply(log)

    @unittest.skipUnless(importlib.util.find_spec("sklearn"), "requires the ml extra")
    def test_fit_predicts_held_out_drift_and_passes_stationary_control(self):
        parameters = {"num_windows": 8}
        stable = make_log(["AB"] * 24)
        shifted = make_log(["AB"] * 12 + ["AC"] * 12)
        shifted_early = make_log(["AC"] * 9 + ["AB"] * 15)
        model = supervised.fit(
            [
                (stable, []),
                (shifted, [supervised.Region(4, 4, "sudden")]),
                (shifted_early, [supervised.Region(3, 3, "sudden")]),
            ],
            parameters,
        )
        held_out = make_log(["XY"] * 15 + ["XZ"] * 9)
        configured = {**parameters, "predictor": model}
        self.assertEqual(
            [alarm.index for alarm in supervised.apply(held_out, configured).changes],
            [15],
        )
        self.assertFalse(supervised.apply(stable, configured).changes)
        with self.assertRaisesRegex(ValueError, "stable and drift"):
            supervised.fit([(stable, [])], parameters)
