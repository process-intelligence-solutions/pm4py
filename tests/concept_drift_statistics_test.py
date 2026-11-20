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
                    available_at=pd.Series(closes, index=range(90, 130)),
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

    def test_standardizing_handles_large_and_small_finite_scales(self):
        from pm4py.algo.concept_drift.variants import multivariate

        reference = np.r_[np.zeros(20), np.ones(20)]
        scores = [
            multivariate.apply_features(reference * scale, {"window_size": 20}).scores[
                0
            ]
            for scale in (1.0, 1e-200, 1e200)
        ]
        self.assertGreater(scores[0].score, 0.0)
        self.assertEqual([score.score for score in scores], [scores[0].score] * 3)
        self.assertEqual([score.p_value for score in scores], [scores[0].p_value] * 3)


class DriftDispatchTest(unittest.TestCase):
    def test_bose_default_preserves_legacy_return(self):
        log = make_log(["AB"] * 10)
        parameters = {"sub_log_size": 5, "window_size": 2}
        sublogs, timestamps, p_values = algorithm.apply(log, parameters=parameters)
        self.assertGreater(len(sublogs), 0)
        self.assertEqual((timestamps, p_values), ([], []))

    def test_bose_orders_cases_by_time_and_preserves_the_original_segments(self):
        case_ids = np.random.default_rng(5).permutation(61)
        situations = [("A,B", "C")] * 30 + [("A,B", "D")] * 31
        log = make_log(situations).rename(
            columns={
                "case:concept:name": "case",
                "concept:name": "activity",
                "time:timestamp": "when",
            }
        )
        log["case"] = [f"{case_ids[i // 2]:03}" for i in range(len(log))]
        log["weight"] = np.arange(len(log))
        parameters = {
            "case_id_key": "case",
            "activity_key": "activity",
            "timestamp_key": "when",
            "sub_log_size": 5,
            "window_size": 4,
            "num_permutations": 999,
            "thresh_p_value": 0.05,
            "random_state": 8,
        }

        segments, timestamps, p_values = algorithm.apply(
            log.sample(frac=1, random_state=9), parameters=parameters
        )
        self.assertEqual(timestamps, [log.loc[60, "when"].timestamp()])
        self.assertEqual(len(p_values), 1)
        self.assertTrue(0 < p_values[0] < 0.05)
        self.assertEqual([len(segment) for segment in segments], [60, 62])
        pd.testing.assert_frame_equal(pd.concat(segments, ignore_index=True), log)

        legacy = EventLog(
            [
                Trace(
                    [Event(row) for row in group.to_dict("records")],
                    attributes={"concept:name": identifier},
                )
                for identifier, group in log.groupby("case")
            ]
        )
        _, legacy_timestamps, legacy_p_values = algorithm.apply(
            legacy, parameters=parameters
        )
        self.assertEqual((legacy_timestamps, legacy_p_values), (timestamps, p_values))

    def test_bose_does_not_permute_a_partial_sublog(self):
        from unittest.mock import patch

        from pm4py.algo.concept_drift.variants import bose

        with patch.object(bose, "permutation_test", return_value=0.01) as test:
            sublogs, changes = bose.detect_concept_drift(
                ["AB"] * 19, sub_log_size=5, window_size=2
            )
        test.assert_not_called()
        self.assertEqual([len(sublog) for sublog in sublogs], [5, 5, 5, 4])
        self.assertEqual(changes, [])

    def test_all_new_variants_return_shared_result_on_empty_input(self):
        from importlib.util import find_spec

        cases = {
            variant: {}
            for variant in algorithm.Variants
            if variant is not algorithm.Variants.BOSE
        }
        cases[algorithm.Variants.SUPERVISED_SIMILARITY] = {"predictor": lambda _: []}
        if not find_spec("hdbscan"):
            del cases[algorithm.Variants.VERSION_CLUSTERING]
        for variant, parameters in cases.items():
            with self.subTest(variant=variant.name):
                result = algorithm.apply(pd.DataFrame(), variant, parameters)
                self.assertIsInstance(result, DriftResult)
                self.assertFalse(
                    result.scores
                    or result.changes
                    or result.versions
                    or result.intervals
                )
                self.assertIn("pm4py_version", result.metadata)
