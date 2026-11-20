import importlib.util
import unittest
from collections import Counter
from itertools import pairwise

import pandas as pd

from pm4py.algo.concept_drift.variants import cluster_frequency, declare_profiles
from tests.concept_drift_constraints_clustering_test import _log


class SequentialDeclareProfilesTest(unittest.TestCase):
    def test_page_hinkley_localizes_and_combines_rule_changes(self):
        rules = [("response", "A", "B"), ("precedence", "A", "B")]
        log = _log(["AB"] * 24 + ["BA"] * 24 + ["AB"] * 24)
        parameters = {
            "method": "page_hinkley",
            "constraints": rules,
            "window_size": 4,
            "page_hinkley_min_instances": 3,
            "page_hinkley_threshold": 1,
        }
        result = declare_profiles.apply(log, parameters)
        self.assertEqual(result.metadata["mode"], "sequential")
        self.assertEqual(result.metadata["detector"], "page_hinkley")
        self.assertEqual([alarm.index for alarm in result.changes], [24, 48])
        alarm, recurring = result.changes
        self.assertEqual(alarm.score, 2)
        self.assertEqual(set(alarm.details["constraint_scores"]), set(rules))
        self.assertEqual(alarm.details["signaling_window_start"], 28)
        self.assertEqual(alarm.timestamp, pd.Timestamp("2025-01-01T00:04:01Z"))
        self.assertEqual(alarm.available_at, pd.Timestamp("2025-01-01T00:05:11Z"))
        self.assertEqual(recurring.available_at, pd.Timestamp("2025-01-01T00:09:11Z"))
        self.assertEqual(result.scores[6].details["profile"], dict.fromkeys(rules, 0))

        prefix = log.loc[log["time:timestamp"] <= alarm.available_at]
        early = declare_profiles.apply(prefix, parameters)
        self.assertEqual(early.changes, result.changes[:1])
        self.assertEqual(early.scores, result.scores[: len(early.scores)])

    def test_undefined_conditional_statistics_skip_detector_updates(self):
        log = _log(["AB"] * 20 + ["C"] * 4 + ["AC"] * 20)
        rule = ("response", "A", "B")
        parameters = {
            "method": "page_hinkley",
            "constraints": [rule],
            "window_size": 2,
            "page_hinkley_threshold": 1,
        }
        for statistic, expected in (
            ("support", 24),
            ("violation_rate", 24),
            ("confidence", 20),
        ):
            with self.subTest(statistic=statistic):
                result = declare_profiles.apply(
                    log, {**parameters, "statistic": statistic}
                )
                self.assertEqual([alarm.index for alarm in result.changes], [expected])
                inactive = result.scores[10]
                if statistic == "confidence":
                    self.assertEqual(inactive.details["profile"][rule], 0)
                else:
                    self.assertIsNone(inactive.details["profile"][rule])
                    self.assertEqual(inactive.details["constraint_scores"], {})

    def test_sequential_requires_explicit_nonempty_rules(self):
        log = _log(["AB"] * 6)
        with self.assertRaisesRegex(ValueError, "explicit constraints"):
            declare_profiles.apply(log, {"method": "page_hinkley"})
        with self.assertRaisesRegex(ValueError, "nonempty constraints"):
            declare_profiles.apply(log, {"method": "page_hinkley", "constraints": []})
        with self.assertRaisesRegex(ValueError, "method"):
            declare_profiles.apply(log, {"method": "unknown"})

    @unittest.skipUnless(importlib.util.find_spec("river"), "requires the drift extra")
    def test_adwin_detects_a_rule_shift(self):
        log = _log(["AB"] * 120 + ["BA"] * 120 + ["AB"] * 120)
        parameters = {
            "method": "adwin",
            "constraints": [("response", "A", "B")],
            "window_size": 2,
            "adwin_delta": 0.01,
        }
        result = declare_profiles.apply(log, parameters)
        self.assertEqual(len(result.changes), 2)
        alarm, recurring = result.changes
        signaling_window = alarm.details["signaling_window_start"]
        self.assertGreaterEqual(signaling_window, 120)
        self.assertLess(signaling_window, 180)
        self.assertLessEqual(alarm.index, signaling_window)
        self.assertEqual(
            alarm.available_at, result.scores[signaling_window // 2].available_at
        )
        self.assertLess(alarm.timestamp, alarm.available_at)
        self.assertGreaterEqual(recurring.details["signaling_window_start"], 240)
        self.assertGreater(recurring.available_at, alarm.available_at)
        self.assertEqual(result.metadata["detector_settings"]["delta"], 0.01)
        before_alarm = declare_profiles.apply(
            log.loc[
                log["time:timestamp"] < alarm.available_at - pd.Timedelta(seconds=1)
            ],
            parameters,
        )
        prefix = declare_profiles.apply(
            log.loc[log["time:timestamp"] <= alarm.available_at],
            parameters,
        )
        self.assertEqual(before_alarm.changes, [])
        self.assertEqual(prefix.changes, result.changes[:1])
        self.assertEqual(prefix.scores, result.scores[: len(prefix.scores)])


@unittest.skipUnless(importlib.util.find_spec("sklearn"), "requires the ml extra")
class ClusterFrequencyTest(unittest.TestCase):
    def test_detects_clustering_shift_with_equal_aggregate_dfgs(self):
        mixed = "ABACA"
        training = ["ABABA", "ACACA", mixed] * 4
        before = ["ABABA", "ACACA"] * 10
        after = [mixed] * 20
        self.assertEqual(
            Counter(edge for trace in before for edge in pairwise(trace)),
            Counter(edge for trace in after for edge in pairwise(trace)),
        )
        result = cluster_frequency.apply(
            _log(training + before + after),
            {"training_size": 12, "n_clusters": 3, "window_size": 20},
        )
        self.assertEqual([alarm.index for alarm in result.changes], [32])
        self.assertEqual(result.changes[0].score, 1)
        self.assertEqual(
            sorted(result.changes[0].details["changed_cluster_shares"].values()),
            [-0.5, -0.5, 1],
        )

    def test_population_drift_recurring_clusters_and_prefix_stability(self):
        variants = ["AB", "AC"] * 4 + ["AB"] * 20 + ["AC"] * 20 + ["AB"] * 20
        log = _log(variants)
        parameters = {
            "training_size": 8,
            "n_clusters": 2,
            "window_size": 10,
            "permutation_block_size": 2,
            "alpha": 0.1,
        }
        result = cluster_frequency.apply(log, parameters)
        labels = [version.label for version in result.versions]
        self.assertEqual(set(labels), {1, 2})
        self.assertEqual(labels[:20], labels[40:])
        self.assertEqual(result.metadata["actual_clusters"], 2)
        self.assertEqual([alarm.index for alarm in result.changes], [28, 48])
        first = result.changes[0]
        self.assertEqual(first.score, 1)
        self.assertLessEqual(first.p_value, 0.1)
        self.assertEqual(
            first.details["changed_cluster_shares"], {labels[0]: -1, labels[20]: 1}
        )
        self.assertEqual(first.available_at, pd.Timestamp("2025-01-01T00:06:11Z"))

        prefix = cluster_frequency.apply(
            log.loc[log["time:timestamp"] <= first.available_at], parameters
        )
        self.assertEqual(prefix.changes, result.changes[:1])
        self.assertEqual(prefix.versions, result.versions[: len(prefix.versions)])
        self.assertEqual(prefix.scores, result.scores[: len(prefix.scores)])

    def test_frozen_vocabulary_and_optional_distance_rejection(self):
        log = _log(["AB", "BA"] * 3 + ["AB", "ABA", "AC"])
        result = cluster_frequency.apply(
            log, {"training_size": 6, "outlier_distance": 0.1, "n_clusters": 5}
        )
        self.assertEqual(result.metadata["actual_clusters"], 2)
        valid, distant, novel = result.versions
        self.assertGreater(valid.label, 0)
        self.assertEqual(distant.label, 0)
        self.assertGreater(distant.details["distance"], 0.1)
        self.assertEqual(novel.label, 0)
        self.assertEqual(novel.details["outlier"], "unseen_features")
        self.assertIn(("activity", "C"), novel.details["unseen_features"])
        self.assertEqual(result.scores, [])

    def test_stationary_trace_profiles(self):
        result = cluster_frequency.apply(
            _log(["AB"] * 40), {"training_size": 8, "window_size": 4}
        )
        self.assertEqual(result.metadata["actual_clusters"], 1)
        self.assertTrue(result.scores)
        self.assertEqual({score.score for score in result.scores}, {0})
        self.assertEqual({score.p_value for score in result.scores}, {1})
        self.assertEqual(result.changes, [])


class ClusterFrequencyParametersTest(unittest.TestCase):
    def test_empty_and_invalid_parameters(self):
        self.assertEqual(cluster_frequency.apply(pd.DataFrame()).versions, [])
        for parameters, message in (
            ({"n_clusters": False}, "n_clusters"),
            ({"training_size": 0}, "training_size"),
            ({"outlier_distance": float("inf")}, "outlier_distance"),
            ({"window_size": 3, "permutation_block_size": 2}, "must divide"),
        ):
            with (
                self.subTest(parameters=parameters),
                self.assertRaisesRegex(ValueError, message),
            ):
                cluster_frequency.apply(pd.DataFrame(), parameters)
