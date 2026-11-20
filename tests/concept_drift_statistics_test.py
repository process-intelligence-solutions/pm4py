import unittest

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift import _common, algorithm
from pm4py.algo.concept_drift.result import DriftResult, WindowScore
from pm4py.algo.concept_drift.variants import dfg_frequency
from pm4py.objects.log.obj import Event, EventLog, Trace


def make_log(variants):
    origin = pd.Timestamp("2025-01-01", tz="UTC")
    return pd.DataFrame(
        [
            {
                "case:concept:name": f"case-{i}",
                "concept:name": activity,
                "time:timestamp": origin + pd.Timedelta(seconds=10 * i + j),
            }
            for i, trace in enumerate(variants)
            for j, activity in enumerate(trace)
        ]
    )


class DriftCommonTest(unittest.TestCase):
    def test_completed_trace_order_custom_keys_and_ties(self):
        rows = pd.DataFrame(
            {
                "identifier": ["later", "first", "first", "later", "tie"],
                "label": ["D", "B", "A", "C", "E"],
                "when": pd.to_datetime(
                    [
                        "2025-01-03",
                        "2025-01-02",
                        "2025-01-02",
                        "2025-01-01",
                        "2025-01-02",
                    ]
                ),
                "case:category": ["later_end", "first", "first", "later_start", "tie"],
            }
        )
        result = _common.completed_traces(
            rows,
            {
                "case_id_key": "identifier",
                "label": "unused",
                "activity_key": "label",
                "pm4py:param:timestamp_key": "when",
            },
        )
        self.assertEqual(
            [trace.activities for trace in result], [("B", "A"), ("E",), ("C", "D")]
        )
        self.assertEqual(result[2].attributes["category"], "later_start")
        self.assertEqual(result[2].end, pd.Timestamp("2025-01-03", tz="UTC"))
        legacy = EventLog(
            [Trace(), Trace([Event({"label": "E", "when": rows.when[4]})])]
        )
        self.assertEqual(
            _common.completed_traces(
                legacy, {"activity_key": "label", "timestamp_key": "when"}
            )[0].activities,
            ("E",),
        )
        with self.assertRaisesRegex(ValueError, "Missing event log columns"):
            _common.completed_traces(rows)

    def test_partitions_and_similarity_of_empty_graphs(self):
        self.assertEqual(
            list(_common.adjacent_windows(9, 3, 2)), [(0, 3, 6), (2, 5, 8)]
        )
        self.assertEqual(_common.window_partition(8, 3), [(0, 3), (3, 6), (6, 8)])
        np.testing.assert_array_equal(
            _common.cosine_similarity([{}, {}, {("A", "B"): 2}]),
            [[1, 1, 0], [1, 1, 0], [0, 0, 1]],
        )

    def test_alarm_persistence_and_separation(self):
        scores = [
            WindowScore(
                i,
                value,
                available_at=pd.Timestamp("2025-01-01", tz="UTC")
                + pd.Timedelta(days=i),
            )
            for i, value in enumerate([1, 2, 0, 3, 4, 0, 5])
        ]
        sequential = _common.consolidate(scores, lambda point: point.score > 0, 2, 4)
        self.assertEqual([alarm.index for alarm in sequential], [0])
        self.assertEqual(sequential[0].available_at, scores[1].available_at)
        retrospective = _common.consolidate(
            scores, lambda point: point.score > 0, 2, 4, True
        )
        self.assertEqual([alarm.index for alarm in retrospective], [4])


class DfgFrequencyTest(unittest.TestCase):
    def test_frequency_shift_with_equal_support(self):
        left = ["AB"] * 8 + ["AC"] * 2
        right = ["AC"] * 8 + ["AB"] * 2
        log = make_log(left * 5 + right * 5)
        for statistical_test in ("g_test", "permutation"):
            with self.subTest(statistical_test=statistical_test):
                result = algorithm.apply(
                    log,
                    algorithm.Variants.DFG_FREQUENCY,
                    {
                        "window_size": 40,
                        "step": 10,
                        "test": statistical_test,
                        "min_effect": 0.3,
                        "permutation_block_size": 2,
                    },
                )
                self.assertIsInstance(result, DriftResult)
                self.assertEqual([alarm.index for alarm in result.changes], [50])
                self.assertLessEqual(result.changes[0].p_value, 0.05)
                self.assertAlmostEqual(
                    result.changes[0].details["changed_relations"][("A", "B")], -0.6
                )
                self.assertEqual(
                    result.changes[0].available_at, log["time:timestamp"].max()
                )

    def test_sequential_availability_confirmation_and_no_drift(self):
        log = make_log(["AB"] * 12 + ["AC"] * 12)
        result = dfg_frequency.apply(
            log,
            {
                "window_size": 5,
                "test": "g_test",
                "retrospective": False,
                "persistence": 2,
                "min_effect": 0.5,
            },
        )
        first = result.changes[0]
        self.assertEqual(
            first.available_at, result.scores[first.index + 1 - 5].available_at
        )
        self.assertLess(first.available_at, log["time:timestamp"].max())
        for variants in (["AB"] * 10, ["A"] * 10, [], ["A"] * 5 + ["AB"] * 5):
            self.assertFalse(
                dfg_frequency.apply(make_log(variants), {"window_size": 5}).changes
            )
        with self.assertRaisesRegex(ValueError, "must divide"):
            dfg_frequency.apply(log, {"window_size": 5, "permutation_block_size": 2})


class MultivariateTest(unittest.TestCase):
    def test_dependence_shift_with_identical_marginals(self):
        from pm4py.algo.concept_drift.variants import multivariate

        values = pd.DataFrame(
            [(-1, -1), (1, 1)] * 10 + [(-1, 1), (1, -1)] * 10,
            columns=["workload", "delay"],
            index=pd.date_range("2025", periods=40, freq="h", tz="UTC"),
        )
        closes = values.index + pd.Timedelta(hours=1)
        for method in ("mmd", "energy"):
            with self.subTest(method=method):
                result = multivariate.apply_features(
                    values,
                    {"window_size": 20, "method": method},
                    available_at=closes,
                    observation_unit="calendar_bin",
                )
                self.assertEqual(result.observation_unit, "calendar_bin")
                (change,) = result.changes
                self.assertEqual(change.index, 20)
                self.assertEqual(change.timestamp, values.index[20])
                self.assertEqual(change.available_at, closes[-1])
                self.assertEqual(change.details["changed_means"], {})
                self.assertGreater(change.score, 0)
                self.assertLessEqual(change.p_value, 0.05)
                stable = pd.concat([values.iloc[:20]] * 2, ignore_index=True)
                self.assertFalse(
                    multivariate.apply_features(
                        stable, {"window_size": 20, "method": method}
                    ).changes
                )

    def test_joint_resource_assignment_and_marginal_null(self):
        log = make_log(["AB"] * 40)
        log["org:resource"] = ["r1", "r2"] * 20 + ["r2", "r1"] * 20
        for feature_spec, expected in (
            (("activity_resource",), [20]),
            (("resource", "activity", "dfg", "duration"), []),
        ):
            result = algorithm.apply(
                log,
                algorithm.Variants.MULTIVARIATE,
                {"window_size": 20, "features": feature_spec},
            )
            self.assertEqual([alarm.index for alarm in result.changes], expected)

    def test_bad_numeric_input_and_custom_features(self):
        from pm4py.algo.concept_drift.variants import multivariate

        log = make_log(["AB"] * 8 + ["ABCD"] * 8)
        result = multivariate.apply(
            log,
            {"window_size": 8, "features": lambda trace: {"length": len(trace.events)}},
        )
        self.assertEqual([alarm.index for alarm in result.changes], [8])
        with self.assertRaisesRegex(ValueError, "finite"):
            multivariate.apply_features([1, np.nan])
        with self.assertRaisesRegex(ValueError, "chronological"):
            multivariate.apply_features([0, 1], timestamps=["2025-01-02", "2025-01-01"])
        with self.assertRaisesRegex(ValueError, "Unknown trace feature"):
            multivariate.apply(log, {"features": ["unknown"]})
