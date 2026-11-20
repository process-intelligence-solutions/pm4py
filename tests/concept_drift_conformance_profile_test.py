"""Behavioral checks for windowed conformance drift."""

import unittest

import pandas as pd

import pm4py
from pm4py.algo.concept_drift.variants import conformance, conformance_profile
from pm4py.objects.log.obj import Event, EventLog, Trace
from tests.concept_drift_statistics_test import make_log


def _choice_model():
    return pm4py.convert_to_petri_net(
        pm4py.parse_process_tree("-> ( 'A', X ( 'B', 'C' ) )")
    )


class ConformanceProfileTest(unittest.TestCase):
    def test_branch_removal_is_visible_while_trace_fitness_stays_perfect(self):
        log = make_log(
            [("screen, validate", "B"), ("screen, validate", "C")] * 24
            + [("screen, validate", "B")] * 48
        )
        settings = {"window_size": 12}

        fitness_only = conformance.apply(log, {"reference_size": 12})
        self.assertFalse(fitness_only.changes)
        self.assertTrue(all(sample.score == 1.0 for sample in fitness_only.scores))

        result = conformance_profile.apply(log, settings)
        self.assertEqual([alarm.index for alarm in result.changes], [48])
        alarm = result.changes[0]
        self.assertAlmostEqual(alarm.details["metric_deltas"]["precision"], -1 / 3)
        self.assertEqual(alarm.details["metric_deltas"]["fitness"], 0)
        self.assertGreater(alarm.score, result.metadata["penalty"])
        self.assertIsNone(alarm.p_value)
        self.assertTrue(
            all(sample.details["fitness"] == 1.0 for sample in result.scores)
        )

        self.assertEqual(result.metadata["reference_size"], 12)
        self.assertEqual(result.scores[0].index, 12)
        self.assertEqual(result.scores[0].details["precision"], 1.0)
        first_change_score = next(score for score in result.scores if score.index == 48)
        self.assertAlmostEqual(first_change_score.details["precision"], 2 / 3)
        self.assertAlmostEqual(first_change_score.score, 1 / 3)
        self.assertEqual(alarm.timestamp, log["time:timestamp"].iloc[48 * 2 + 1])
        self.assertEqual(alarm.timestamp, first_change_score.timestamp)
        self.assertEqual(
            first_change_score.available_at, log["time:timestamp"].iloc[60 * 2 - 1]
        )
        self.assertEqual(alarm.available_at, log["time:timestamp"].iloc[-1])
        self.assertLess(first_change_score.available_at, alarm.available_at)

        stable = conformance_profile.apply(log.iloc[:96], settings)
        self.assertFalse(stable.changes)
        self.assertTrue(all(point.score == 0.0 for point in stable.scores))

    def test_external_model_detects_a_new_behavior_through_fitness(self):
        model = _choice_model()
        log = make_log(["AB", "AC"] * 12 + ["AD"] * 24)
        result = conformance_profile.apply(
            log, {"reference_model": model, "window_size": 6}
        )
        self.assertIs(model, result.metadata["reference_model"])
        self.assertEqual(result.metadata["reference_size"], 0)
        self.assertEqual(result.scores[0].index, 0)
        self.assertEqual([alarm.index for alarm in result.changes], [24])
        self.assertAlmostEqual(
            result.changes[0].details["metric_deltas"]["fitness"], -0.5
        )

    def test_branch_recurrence_produces_two_directions_of_precision_change(self):
        prefix = ["AB", "AC"] * 18
        log = make_log(prefix + ["AB"] * 36 + prefix)
        result = conformance_profile.apply(
            log, {"reference_model": _choice_model(), "window_size": 12}
        )
        self.assertEqual([alarm.index for alarm in result.changes], [36, 72])
        self.assertAlmostEqual(
            result.changes[0].details["metric_deltas"]["precision"], -1 / 3
        )
        self.assertAlmostEqual(
            result.changes[1].details["metric_deltas"]["precision"], 1 / 3
        )
        self.assertTrue(
            all(
                alarm.available_at == log["time:timestamp"].max()
                for alarm in result.changes
            )
        )

    def test_overlapping_windows_have_stable_order_and_omit_partial_tail(self):
        log = make_log(["AB", "AC", "AB", "AC", "AB", "AC"]).rename(
            columns={
                "case:concept:name": "case_id",
                "concept:name": "activity",
                "time:timestamp": "when",
            },
        )
        legacy = EventLog(
            Trace(
                Event({"activity": row.activity, "when": row.when})
                for row in case.itertuples()
            )
            for _, case in log.iloc[::-1].groupby("case_id", sort=False)
        )
        settings = {
            conformance_profile.Parameters.REFERENCE_MODEL: _choice_model(),
            conformance_profile.Parameters.WINDOW_SIZE: 3,
            conformance_profile.Parameters.STEP: 2,
            "case_id_key": "case_id",
            "activity_key": "activity",
            "timestamp_key": "when",
        }
        result = conformance_profile.apply(log.iloc[::-1], settings)
        self.assertEqual(
            result.scores, conformance_profile.apply(legacy, settings).scores
        )
        self.assertEqual([point.index for point in result.scores], [0, 2])
        self.assertEqual(
            [point.details["window_stop"] for point in result.scores], [3, 5]
        )
        self.assertEqual(result.scores[-1].available_at, log["when"].iloc[9])
        self.assertLess(result.scores[-1].available_at, log["when"].iloc[-1])
        self.assertFalse(result.changes)

    def test_empty_short_and_invalid_inputs(self):
        self.assertFalse(conformance_profile.apply(pd.DataFrame()).scores)
        self.assertFalse(
            conformance_profile.apply(
                make_log(["AB"] * 5), {"reference_size": 3, "window_size": 3}
            ).scores
        )
        for parameters in (
            {"window_size": 1, "step": 2},
            {"window_size": 0},
            {"reference_size": -1},
            {"reference_model": ("not a net", None, None)},
            {"penalty": 0},
            {"min_size": True},
        ):
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                conformance_profile.apply(pd.DataFrame(), parameters)
