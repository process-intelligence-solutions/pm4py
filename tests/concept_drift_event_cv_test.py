import unittest
from typing import ClassVar

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift.variants import cv_indicators, event_relations
from pm4py.objects.log.obj import EventStream
from tests.concept_drift_timeseries_test import _log


def _stream(after_change="CD"):
    log = pd.DataFrame(
        [
            (str(case), ("AB" if round_ < 8 else after_change)[round_ % 2])
            for round_ in range(16)
            for case in range(8)
        ],
        columns=["case:concept:name", "concept:name"],
    )
    log["time:timestamp"] = pd.date_range(
        "2025-01-01", periods=len(log), freq="s", tz="UTC"
    )
    return log


class EventRelationTest(unittest.TestCase):
    settings: ClassVar = {
        "window_size": 32,
        "adaptive": False,
        "step": 8,
        "persistence": 2,
        "min_effect": 0.7,
    }

    def test_change_before_any_case_completes(self):
        log = _stream()
        result = event_relations.apply(log, self.settings)
        self.assertEqual(result.observation_unit, "event")
        (alarm,) = result.changes
        self.assertEqual(alarm.index, 71)
        self.assertEqual(alarm.details["window_boundary_index"], 40)
        self.assertEqual(alarm.details["confirmed_at_index"], 79)
        self.assertEqual(alarm.available_at, log["time:timestamp"].iloc[79])
        first_completion = (
            log.groupby("case:concept:name")["time:timestamp"].max().min()
        )
        self.assertLess(alarm.available_at, first_completion)
        self.assertLess(alarm.p_value, 0.05)
        self.assertIn("g_statistic", alarm.details)
        self.assertFalse(event_relations.apply(_stream("AB"), self.settings).changes)

    def test_adaptive_incremental_replay_is_prefix_invariant(self):
        log = _stream()
        settings = {**self.settings, "adaptive": True, "max_window_size": 45}
        detector = event_relations.EventStreamDetector(settings)
        replay = event_relations.apply(log.iloc[::-1], settings)
        first = event_relations.apply(log.iloc[:96], settings)
        self.assertEqual(first.scores, replay.scores[: len(first.scores)])
        self.assertLess(
            len({point.details["window_size"] for point in first.scores}), 8
        )
        self.assertGreater(
            len({point.details["window_size"] for point in first.scores}), 1
        )
        self.assertEqual(first.changes, replay.changes)
        incremental = [detector.update(event) for event in log.to_dict("records")]
        self.assertEqual(
            [score for score, _ in incremental if score is not None], replay.scores
        )
        self.assertEqual(
            [alarm for _, alarm in incremental if alarm is not None], replay.changes
        )
        self.assertLessEqual(len(detector._buffer), 2 * settings["max_window_size"])
        with self.assertRaisesRegex(ValueError, "timestamp order"):
            detector.update(log.iloc[0].to_dict())

    def test_relation_categories_and_case_boundaries(self):
        # Interleave the three cases to check relations use case-local order.
        events = [
            (1, "A", None),
            (2, "C", None),
            (3, "B", None),
            (1, "B", None),
            (2, "C", None),
            (3, "A", None),
            (1, "A", None),
            (3, "B", None),
        ]
        counts = event_relations._relation_counts(events, include_conflicts=True)
        self.assertEqual(counts["loop_one", "C"], 1)
        self.assertEqual(counts["loop_two", ("A", "B")], 1)
        self.assertEqual(counts["loop_two", ("B", "A")], 1)
        self.assertEqual(counts["causal", ("A", "B")], 2)
        self.assertEqual(counts["causal", ("B", "A")], 2)
        self.assertEqual(counts["conflict", frozenset(("A", "C"))], 5)
        parallel = event_relations._relation_counts(
            [(1, "A", None), (2, "B", None), (1, "B", None), (2, "A", None)],
            include_conflicts=False,
        )
        self.assertEqual(dict(parallel), {("parallel", frozenset(("A", "B"))): 1})

    def test_event_stream_input_keys_and_sparse_evidence(self):
        log = _stream().rename(
            columns={
                "case:concept:name": "i",
                "concept:name": "a",
                "time:timestamp": "t",
            }
        )
        params = {
            **self.settings,
            "case_id_key": "i",
            "activity_key": "a",
            "timestamp_key": "t",
        }
        self.assertEqual(
            event_relations.apply(log, params),
            event_relations.apply(EventStream(log.to_dict("records")), params),
        )
        result = event_relations.apply(
            log, {**params, "window_size": 1, "include_conflicts": False}
        )
        self.assertTrue(result.scores)
        self.assertTrue(all(score.p_value is None for score in result.scores))
        self.assertFalse(result.changes)
        with self.assertRaisesRegex(ValueError, "Missing event log columns"):
            event_relations.apply(log, self.settings)


class CvIndicatorTest(unittest.TestCase):
    def test_window_width_selection_and_workload_shift(self):
        log = _log([("A", ["r1"])] * 80, cases_per_day=4)
        log = log[
            (log["time:timestamp"].dt.dayofyear > 40)
            | log["case:concept:name"].str.endswith("-0")
        ]
        feature = ("activity_frequency", "A")
        result = cv_indicators.apply(log, {"features": ["arrivals", feature]})
        self.assertEqual(
            result.metadata["selected_windows"], {"arrivals": 3, feature: 1}
        )
        self.assertEqual(
            set(result.metadata["cv_curves"]["arrivals"]), {1, 3, 5, 9, 17}
        )
        (alarm,) = result.changes
        self.assertEqual(alarm.index, 40)
        self.assertEqual(set(alarm.details["changed_features"]), {"arrivals"})
        self.assertEqual(
            alarm.available_at, result.scores[-1].timestamp + pd.Timedelta(days=1)
        )

    def test_rolling_median_keeps_missing_calendar_indices(self):
        series = pd.Series([1.0, 3.0, np.nan, 9.0, 9.0])
        width, curve, smoothed = cv_indicators._select_width(series, [3], "median", 2)
        self.assertEqual(width, 3)
        self.assertGreater(curve[3], 0)
        np.testing.assert_allclose(smoothed, [2, 2, np.nan, 9, 9])
        self.assertFalse(cv_indicators.apply(pd.DataFrame()).changes)
        self.assertEqual(
            cv_indicators._select_width(series, [9], "mean", 2), (None, {}, None)
        )
        with self.assertRaisesRegex(ValueError, "candidate_windows"):
            cv_indicators.apply(pd.DataFrame(), {"candidate_windows": []})

    def test_large_case_values_do_not_hide_a_finite_mean_shift(self):
        log = _log([("A", ["r1"])] * 80, cases_per_day=2)
        log["case:amount"] = np.where(
            log["time:timestamp"].dt.dayofyear > 40, 1.7e308, 0.0
        )
        feature = ("case_value", "amount")
        result = cv_indicators.apply(
            log, {"features": [feature], "candidate_windows": [1]}
        )
        self.assertEqual(result.scores[-1].details["values"][feature], 1.7e308)
        self.assertEqual([alarm.index for alarm in result.changes], [40])
        width, _, smoothed = cv_indicators._select_width(
            pd.Series([1.0, np.inf, 3.0]), [1], "mean", 2
        )
        self.assertEqual(width, 1)
        np.testing.assert_allclose(smoothed, [1.0, np.nan, 3.0])
