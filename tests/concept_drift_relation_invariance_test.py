"""Structural relation stability checks."""

import unittest
from collections import Counter
from itertools import groupby, pairwise, product

import pandas as pd

from pm4py.algo.concept_drift.variants import relation_invariance
from pm4py.objects.log.obj import Event, EventLog, Trace

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


class RelationInvarianceTest(unittest.TestCase):
    def test_eventually_follows_detects_order_change_without_dfg_change(self):
        before, after = "ABACA", "ACABA"
        self.assertEqual(Counter(pairwise(before)), Counter(pairwise(after)))
        log = _event_log([before] * 15 + [after] * 15).iloc[::-1]
        parameters = {"min_stable_traces": 5}
        result = relation_invariance.apply(log, parameters)
        self.assertEqual([change.index for change in result.changes], [15])
        change = result.changes[0]
        self.assertEqual(change.details["appeared"], {("eventually_follows", "C", "B")})
        self.assertEqual(
            change.details["disappeared"], {("eventually_follows", "B", "C")}
        )
        self.assertEqual(change.timestamp, _ORIGIN + pd.Timedelta(seconds=150))
        self.assertEqual(change.available_at, log["time:timestamp"].max())
        self.assertIsNone(change.p_value)
        self.assertEqual(result.metadata["trace_order"], "start")
        self.assertEqual(
            [score.index for score in result.scores if score.score > 0], [15]
        )

        only_direct = relation_invariance.apply(
            log, {**parameters, "relation_type": "directly_follows"}
        )
        self.assertFalse(only_direct.changes)
        self.assertTrue(all(score.score == 0 for score in only_direct.scores))

    def test_cluster_combines_staggered_relation_changes_at_weighted_centroid(self):
        log = _event_log(["ABC"] * 10 + ["AC"] * 2 + ["ACD"] * 8)
        parameters = {"min_stable_traces": 3, "radius": 2}
        result = relation_invariance.apply(log, parameters)
        (change,) = result.changes
        self.assertEqual(change.details["candidates"], (10, 12))
        self.assertEqual(change.index, 11)
        self.assertEqual(change.score, 8)
        self.assertIn(("directly_follows", "A", "C"), change.details["appeared"])
        self.assertIn(("eventually_follows", "A", "D"), change.details["appeared"])
        self.assertIn(("directly_follows", "A", "B"), change.details["disappeared"])
        self.assertEqual(
            [(score.index, score.score) for score in result.scores if score.score],
            [(10, 5), (12, 3)],
        )
        split = relation_invariance.apply(
            log, {**parameters, "radius": 0, "min_separation": 2}
        )
        self.assertEqual([point.index for point in split.changes], [10, 12])

    def test_separation_favors_stronger_cluster_away_from_log_edges(self):
        log = _event_log(["ABC"] * 10 + ["AXC"] * 4 + ["AXCD"] * 15 + ["AXCDF"])
        result = relation_invariance.apply(
            log, {"min_stable_traces": 3, "radius": 0, "min_separation": 6}
        )
        self.assertEqual([change.index for change in result.changes], [10])
        self.assertEqual(
            [score.index for score in result.scores if score.score], [10, 14, 29]
        )

    def test_sparse_stability_matches_boolean_reference(self):
        for length in range(8):
            for sequence in product((False, True), repeat=length):
                occurrences = [
                    index for index, present in enumerate(sequence) if present
                ]
                for minimum in range(1, 5):
                    expected = set()
                    start = 0
                    for _, run in groupby(sequence):
                        end = start + len(list(run))
                        if end - start >= minimum:
                            expected.update((start, end))
                        start = end
                    expected.difference_update((0, length))
                    observed = relation_invariance._stable_boundaries(
                        occurrences, length, minimum
                    )
                    self.assertEqual(observed, expected)

    def test_case_start_order_on_overlapping_traces_and_custom_keys(self):
        log = _event_log(["AB"] * 2 + ["AC"] * 2).rename(
            columns={
                "case:concept:name": "identifier",
                "concept:name": "label",
                "time:timestamp": "time",
            }
        )
        # A long-running pre-drift case still precedes the replacement regime.
        log.loc[1, "time"] = _ORIGIN + pd.Timedelta(minutes=10)
        legacy = EventLog(
            [
                Trace([Event(row) for row in group.to_dict("records")][::-1])
                for _, group in log.groupby("identifier")
            ][::-1]
        )
        parameters = {
            "min_stable_traces": 2,
            "radius": 0,
            "relation_type": "directly_follows",
            "activity_key": "label",
            "timestamp_key": "time",
            "case_id_key": "identifier",
        }
        result = relation_invariance.apply(log, parameters)
        self.assertEqual(result, relation_invariance.apply(legacy, parameters))
        self.assertEqual([point.index for point in result.changes], [2])
        self.assertEqual(result.changes[0].available_at, log["time"].max())
        self.assertEqual(
            result.changes[0].timestamp, _ORIGIN + pd.Timedelta(seconds=20)
        )

    def test_empty_constant_and_frequently_varying_signals(self):
        parameters = {relation_invariance.Parameters.MIN_STABLE_TRACES: 4}
        for variants in ([], ["AB"] * 10, ["AB", "AC"] * 8, ["A"] * 10 + ["B"] * 10):
            with self.subTest(variants=variants):
                result = relation_invariance.apply(_event_log(variants), parameters)
                self.assertFalse(result.changes)
                self.assertTrue(all(score.score == 0 for score in result.scores))

    def test_invalid_parameters(self):
        for key, value in (
            ("min_stable_traces", 0),
            ("radius", -1),
            ("min_separation", True),
            ("relation_type", "invalid"),
        ):
            with self.subTest(parameter=key), self.assertRaisesRegex(ValueError, key):
                relation_invariance.apply(pd.DataFrame(), {key: value})
