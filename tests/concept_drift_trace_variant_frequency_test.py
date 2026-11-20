"""Checks for exact sequence drift with categorical permutation calibration."""

import unittest

import pandas as pd

from pm4py.algo.concept_drift.variants import (
    dfg_frequency,
    run_distribution,
    trace_variant_frequency,
)
from tests.concept_drift_statistics_test import make_log


class TraceVariantFrequencyTest(unittest.TestCase):
    def test_equal_dfgs_can_hide_exact_sequence_drift(self):
        before, after = "ABACA", "ACABA"
        log = make_log([before] * 40 + [after] * 40)
        settings = {"window_size": 20, "step": 20, "permutation_block_size": 2}
        control = dfg_frequency.apply(log, settings)
        self.assertFalse(control.changes)
        self.assertTrue(all(point.score == 0.0 for point in control.scores))

        result = trace_variant_frequency.apply(log, settings)
        self.assertEqual([alarm.index for alarm in result.changes], [40])
        alarm = result.changes[0]
        self.assertEqual(alarm.score, 1.0)
        self.assertLessEqual(alarm.p_value, 0.05)
        self.assertEqual(
            alarm.details["changed_variants"], {tuple(before): -1.0, tuple(after): 1.0}
        )
        self.assertEqual(alarm.timestamp, log["time:timestamp"].iloc[40 * 5 + 4])
        self.assertEqual(alarm.available_at, log["time:timestamp"].iloc[-1])
        comparison = result.scores[1]
        self.assertEqual(
            comparison.available_at, log["time:timestamp"].iloc[60 * 5 - 1]
        )
        self.assertLess(comparison.available_at, alarm.available_at)

    def test_detects_changes_in_order_frequencies_that_runs_pool(self):
        left = ["ABC"] * 8 + ["ACB"] * 2
        right = ["ACB"] * 8 + ["ABC"] * 2
        log = make_log(left * 4 + right * 4)
        settings = {"window_size": 40, "persistence": 1}
        result = trace_variant_frequency.apply(log, settings)
        self.assertEqual([alarm.index for alarm in result.changes], [40])
        self.assertAlmostEqual(
            result.changes[0].details["changed_variants"][tuple("ACB")], 0.6
        )

        run_result = run_distribution.apply(log, settings)
        self.assertEqual(run_result.scores[0].score, 0)
        self.assertFalse(run_result.changes)

    def test_sequential_confirmation_is_unchanged_when_appending_cases(self):
        log = make_log(["ABACA"] * 30 + ["ACABA"] * 20 + ["ABACA"] * 25)
        settings = {
            "window_size": 10,
            "step": 2,
            "persistence": 2,
            "retrospective": False,
            "alpha": 0.1,
        }
        result = trace_variant_frequency.apply(log, settings)
        self.assertEqual(len(result.changes), 2)
        first = result.changes[0]
        confirmation = next(
            point for point in result.scores if point.index == first.index + 2
        )
        self.assertEqual(first.available_at, confirmation.available_at)
        endpoint = log["time:timestamp"] <= first.available_at
        prefix = trace_variant_frequency.apply(log[endpoint], settings)
        unconfirmed = trace_variant_frequency.apply(
            log[
                endpoint
                & (
                    log["case:concept:name"]
                    != log[endpoint].iloc[-1]["case:concept:name"]
                )
            ],
            settings,
        )
        self.assertEqual(prefix.scores, result.scores[: len(prefix.scores)])
        self.assertEqual(prefix.changes, [first])
        self.assertFalse(unconfirmed.changes)

    def test_stationary_empty_and_invalid_inputs(self):
        result = trace_variant_frequency.apply(
            make_log(["AB", "AC"] * 20),
            {"window_size": 10},
        )
        self.assertTrue(result.scores)
        self.assertFalse(result.changes)
        self.assertTrue(all(point.p_value == 1.0 for point in result.scores))
        self.assertFalse(trace_variant_frequency.apply(pd.DataFrame()).scores)
        for settings in (
            {"window_size": 0},
            {"step": 0},
            {"permutation_block_size": 3},
            {"alpha": 1.1},
            {"min_effect": -1},
        ):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                trace_variant_frequency.apply(pd.DataFrame(), settings)
        with self.assertRaisesRegex(TypeError, "retrospective"):
            trace_variant_frequency.apply(pd.DataFrame(), {"retrospective": "false"})
