"""Checks for drift detection over process graph topology."""

import unittest

import pandas as pd

from pm4py.algo.concept_drift.variants import graph_metrics

_ORIGIN = pd.Timestamp("2026-01-01", tz="UTC")


def _event_log(variants):
    return pd.DataFrame(
        [
            {
                "case:concept:name": index,
                "concept:name": label,
                "time:timestamp": _ORIGIN + pd.Timedelta(seconds=10 * index + offset),
            }
            for index, variant in enumerate(variants)
            for offset, label in enumerate(variant)
        ]
    )


class GraphMetricsTest(unittest.TestCase):
    def test_graph_ratios_and_isolated_activities(self):
        log = _event_log(["AA", "AB", "BA", "C"])
        parameters = {"window_size": 4}
        result = graph_metrics.apply(log, parameters)
        metrics = result.scores[0].details["metrics"]
        self.assertEqual(
            metrics,
            {
                "activity_count": 3,
                "edge_density": 1 / 3,
                "branching_fraction": 0,
                "merging_fraction": 0,
                "weak_component_count": 2,
                "cyclic_activity_fraction": 2 / 3,
                "self_loop_fraction": 1 / 3,
            },
        )
        filtered = graph_metrics.apply(log, {**parameters, "min_edge_count": 2})
        after = filtered.scores[0].details["metrics"]
        self.assertEqual(after["activity_count"], 3)
        self.assertEqual(after["weak_component_count"], 3)
        for ratio in ("edge_density", "cyclic_activity_fraction", "self_loop_fraction"):
            self.assertEqual(after[ratio], 0)

    def test_incoming_and_outgoing_degree_are_different_signals(self):
        log = _event_log(["AB", "AC", "AD"])
        result = graph_metrics.apply(log, {"window_size": 3})
        metrics = result.scores[0].details["metrics"]
        self.assertEqual(metrics["branching_fraction"], 1 / 4)
        self.assertEqual(metrics["merging_fraction"], 0)
        reverse = graph_metrics.apply(
            _event_log(["BA", "CA", "DA"]), {"window_size": 3}
        )
        other_metrics = reverse.scores[0].details["metrics"]
        self.assertEqual(other_metrics["branching_fraction"], 0)
        self.assertEqual(other_metrics["merging_fraction"], 1 / 4)

    def test_drift_in_connectivity_and_cycles_with_stable_density(self):
        before, after = ["ABC", "C"] * 20, ["ABA", "C"] * 20
        log = _event_log(before + after + ["ZX"])
        parameters = {graph_metrics.Parameters.WINDOW_SIZE: 4}
        result = graph_metrics.apply(log.iloc[::-1], parameters)
        self.assertEqual([change.index for change in result.changes], [40])
        self.assertEqual(
            [score.index for score in result.scores], list(range(0, 80, 4))
        )
        self.assertTrue(
            all(
                score.details["metrics"]["edge_density"] == 1 / 3
                for score in result.scores
            )
        )
        change = result.changes[0]
        self.assertEqual(
            set(change.details["metric_changes"]),
            {
                "weak_component_count",
                "cyclic_activity_fraction",
            },
        )
        self.assertAlmostEqual(
            change.details["metric_changes"]["cyclic_activity_fraction"], 2 / 3
        )
        self.assertEqual(change.details["metric_changes"]["weak_component_count"], 1)
        self.assertGreater(change.score, 10)
        self.assertEqual(change.timestamp, _ORIGIN + pd.Timedelta(seconds=402))
        self.assertEqual(change.available_at, log["time:timestamp"].max())
        self.assertIsNone(change.p_value)

    def test_label_renaming_preserves_topology_and_scores(self):
        log = _event_log(["ABC"] * 16 + ["DEE"] * 16)
        shifted = graph_metrics.apply(log, {"window_size": 4, "penalty": 2})
        self.assertEqual([change.index for change in shifted.changes], [16])
        renamed = graph_metrics.apply(
            _event_log(["ABC"] * 16 + ["DEF"] * 16), {"window_size": 4, "penalty": 2}
        )
        self.assertFalse(renamed.changes)
        self.assertTrue(all(score.score == 0 for score in renamed.scores))

    def test_selected_metrics_custom_activity_and_no_standardization(self):
        log = _event_log(["AA"] * 4 + ["A"] * 4).rename(
            columns={"concept:name": "task"}
        )
        result = graph_metrics.apply(
            log,
            {
                "window_size": 2,
                "activity_key": "task",
                "metrics": ["edge_count", "edge_count"],
                "standardize": False,
                "penalty": 0.5,
            },
        )
        self.assertEqual(result.metadata["metrics"], ("edge_count",))
        self.assertEqual([score.score for score in result.scores], [0, 0, 1, 0])
        (change,) = result.changes
        self.assertEqual(change.index, 4)
        self.assertEqual(change.score, 1)
        self.assertEqual(change.details["metric_changes"], {"edge_count": -1})

    def test_empty_short_and_invalid_input(self):
        for log in (pd.DataFrame(), _event_log(["A"] * 5)):
            self.assertFalse(graph_metrics.apply(log).scores)
        for key, value in (
            ("window_size", 0),
            ("min_edge_count", -1),
            ("metrics", ["unknown"]),
            ("min_size", False),
            ("penalty", 0),
        ):
            with self.subTest(parameter=key), self.assertRaisesRegex(ValueError, key):
                graph_metrics.apply(pd.DataFrame(), {key: value})
