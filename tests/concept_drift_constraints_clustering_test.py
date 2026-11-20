import importlib.util
import unittest
from collections import Counter
from itertools import pairwise

import pandas as pd

from pm4py.algo.concept_drift.variants import declare_profiles, version_clustering
from pm4py.objects.log.obj import Event, EventLog, Trace

_ORIGIN = pd.Timestamp("2025-01-01", tz="UTC")


def _log(variants):
    return pd.DataFrame(
        [
            {
                "case:concept:name": case,
                "concept:name": activity,
                "time:timestamp": _ORIGIN + pd.Timedelta(seconds=10 * case + index),
            }
            for case, trace in enumerate(variants)
            for index, activity in enumerate(trace)
        ]
    )


class DeclareProfilesTest(unittest.TestCase):
    def test_detects_long_range_change_with_identical_dfgs(self):
        before, after = tuple("ABACA"), tuple("ACABA")
        self.assertEqual(Counter(pairwise(before)), Counter(pairwise(after)))
        log = _log([before] * 16 + [after] * 16).iloc[::-1]
        response = ("response", "B", "C")
        precedence = ("precedence", "C", "B")
        result = declare_profiles.apply(
            log,
            {"window_size": 4, "penalty": 0.6, "constraints": [response, precedence]},
        )

        self.assertEqual(
            [score.index for score in result.scores], list(range(0, 32, 4))
        )
        self.assertEqual(
            result.scores[0].details["profile"], {response: 1, precedence: 0}
        )
        self.assertEqual(
            result.scores[-1].details["profile"], {response: 0, precedence: 1}
        )
        self.assertEqual([alarm.index for alarm in result.changes], [16])
        change = result.changes[0]
        self.assertEqual(
            change.details["constraint_deltas"], {response: -1, precedence: 1}
        )
        self.assertIsNone(change.p_value)
        self.assertGreater(change.score, 0.6)
        self.assertEqual(change.timestamp, _ORIGIN + pd.Timedelta(seconds=164))
        self.assertEqual(change.available_at, log["time:timestamp"].max())

    def test_activation_semantics_for_three_statistics(self):
        rules = [
            ("response", "A", "B"),
            ("precedence", "A", "B"),
            ("existence", "A"),
            ("coexistence", "A", "B"),
            ("noncoexistence", "A", "B"),
            ("response", "Z", "A"),
        ]
        log = _log(["ACAB", "BA", "B", "C"])
        for statistic, expected in (
            ("confidence", [1 / 4, 1 / 4, 2 / 4, 2 / 4, 1 / 4, 0]),
            ("support", [1 / 2, 1 / 3, 2 / 4, 2 / 3, 1 / 3, 0]),
            ("violation_rate", [1 / 2, 2 / 3, 2 / 4, 1 / 3, 2 / 3, 0]),
        ):
            with self.subTest(statistic=statistic):
                result = declare_profiles.apply(
                    log,
                    {"window_size": 4, "constraints": rules, "statistic": statistic},
                )
                self.assertEqual(
                    result.scores[0].details["profile"], dict(zip(rules, expected))
                )
                self.assertEqual(result.changes, [])

    def test_event_log_custom_keys_and_window_step(self):
        log = EventLog(
            [
                Trace(
                    [
                        Event(
                            {
                                "task": "B",
                                "clock": _ORIGIN + pd.Timedelta(minutes=2 * i + 1),
                            }
                        ),
                        Event(
                            {
                                "task": "A",
                                "clock": _ORIGIN + pd.Timedelta(minutes=2 * i),
                            }
                        ),
                    ]
                )
                for i in reversed(range(11))
            ]
        )
        result = declare_profiles.apply(
            log,
            {
                "activity_key": "task",
                "timestamp_key": "clock",
                "window_size": 4,
                "step": 3,
                "constraints": [("chainresponse", "A", "B")],
            },
        )
        self.assertEqual([score.index for score in result.scores], [0, 3, 6])
        self.assertTrue(
            all(
                score.details["profile"] == {("chainresponse", "A", "B"): 1}
                for score in result.scores
            )
        )
        self.assertEqual(result.changes, [])

    def test_empty_and_invalid_parameters(self):
        self.assertEqual(declare_profiles.apply(pd.DataFrame()).scores, [])
        no_rules = declare_profiles.apply(
            _log(["AB"] * 4), {"window_size": 1, "constraints": []}
        )
        self.assertEqual(
            [score.details["profile"] for score in no_rules.scores], [{}] * 4
        )
        self.assertEqual(no_rules.changes, [])
        for parameters, message in (
            ({"window_size": 0}, "window_size"),
            ({"window_size": 4, "step": 5}, "step"),
            ({"constraints": [("response", "A", "A")]}, "distinct"),
            ({"constraints": [("precedence", "A")]}, "activities"),
            ({"statistic": "accuracy"}, "statistic"),
            ({"penalty": 0}, "penalty"),
            ({"gamma": -1}, "gamma"),
            ({"gamma": False}, "gamma"),
        ):
            with (
                self.subTest(parameters=parameters),
                self.assertRaisesRegex(ValueError, message),
            ):
                declare_profiles.apply(_log(["AB"]), parameters)


@unittest.skipUnless(importlib.util.find_spec("hdbscan"), "requires the drift extra")
class VersionClusteringTest(unittest.TestCase):
    def test_recurrent_versions_and_start_order(self):
        log = _log(["SAX"] * 18 + ["SBX"] * 18 + ["SAX"] * 18)
        # The first case starts first and completes last.
        log.loc[2, "time:timestamp"] += pd.Timedelta(hours=2)
        result = version_clustering.apply(
            log.iloc[::-1], {"num_windows": 18, "min_cluster_size": 3, "penalty": 0.5}
        )

        self.assertEqual([change.index for change in result.changes], [18, 36])
        self.assertEqual(
            [version.index for version in result.versions], list(range(0, 54, 3))
        )
        self.assertEqual(
            result.changes[0].timestamp, _ORIGIN + pd.Timedelta(seconds=180)
        )
        self.assertEqual(result.changes[0].available_at, log["time:timestamp"].max())
        labels = [version.label for version in result.versions]
        self.assertEqual(labels[:6], labels[12:])
        self.assertNotEqual(labels[0], labels[6])
        self.assertNotIn(0, labels)
        self.assertEqual({version.confidence for version in result.versions}, {1.0})

    def test_membership_threshold_changes_labels_only(self):
        b_counts = [0, 1, 0, 2, 1, 0, 9, 10, 8, 10, 9, 10]
        variants = [
            variant for n in b_counts for variant in ["SAX"] * (10 - n) + ["SBX"] * n
        ]
        log = _log(variants)
        params = {"num_windows": len(b_counts), "min_cluster_size": 3, "penalty": 1.2}
        low = version_clustering.apply(log, {**params, "membership_threshold": 0})
        high = version_clustering.apply(log, {**params, "membership_threshold": 1})

        self.assertEqual([change.index for change in low.changes], [60])
        self.assertEqual([change.index for change in high.changes], [60])
        self.assertEqual(low.scores, high.scores)
        self.assertTrue(
            any(
                sum(probability > 0 for probability in version.details["probabilities"])
                > 1
                for version in low.versions
            )
        )
        self.assertTrue(
            any(
                a.label != 0 and b.label == 0
                for a, b in zip(low.versions, high.versions)
            )
        )

    def test_empty_short_and_stationary_logs(self):
        result = version_clustering.apply(pd.DataFrame())
        self.assertEqual(result.changes, [])
        self.assertEqual(result.versions, [])
        log = _log(["A"] * 21)
        result = version_clustering.apply(
            log, {"num_windows": 10, "min_cluster_size": 3}
        )
        self.assertEqual(result.changes, [])
        self.assertEqual(result.metadata["actual_windows"], 10)
        self.assertEqual([version.label for version in result.versions], [0] * 10)
        self.assertEqual(
            [version.details["window_stop"] for version in result.versions],
            [3, 5, 7, 9, 11, 13, 15, 17, 19, 21],
        )
        short = version_clustering.apply(log.iloc[:1])
        self.assertEqual(len(short.versions), 1)
        self.assertEqual(short.changes, [])


class VersionClusteringParametersTest(unittest.TestCase):
    def test_validation_does_not_require_optional_dependency(self):
        for parameters, message in (
            ({"num_windows": 0}, "num_windows"),
            ({"min_cluster_size": 1}, "min_cluster_size"),
            ({"membership_threshold": float("nan")}, "membership_threshold"),
        ):
            with (
                self.subTest(parameters=parameters),
                self.assertRaisesRegex(ValueError, message),
            ):
                version_clustering.apply(_log(["AB"]), parameters)

    @unittest.skipIf(importlib.util.find_spec("hdbscan"), "hdbscan is installed")
    def test_missing_dependency_explains_installation_extra(self):
        with self.assertRaisesRegex(ImportError, r"pm4py\[drift\]"):
            version_clustering.apply(_log(["AB"]))
