"""Behavioral and numerical checks for structural and execution drift."""

import unittest
from functools import partial

import pandas as pd
from scipy.stats import chi2

from pm4py.algo.concept_drift.variants import earth_mover, lcdd, run_distribution
from pm4py.objects.log.obj import Event, EventLog, Trace


def _event_log(variants, gaps=None, service=None):
    origin = pd.Timestamp("2026-01-01", tz="UTC")
    rows = []
    for index, activities in enumerate(variants):
        start = origin + pd.Timedelta(minutes=index)
        gap = 1 if gaps is None else gaps[index]
        duration = 1 if service is None else service[index]
        for position, activity in enumerate(activities):
            end = start + pd.Timedelta(seconds=position * gap)
            rows.append(
                {
                    "case:concept:name": f"case-{index}",
                    "concept:name": activity,
                    "time:timestamp": end,
                    "start_timestamp": end - pd.Timedelta(seconds=duration),
                }
            )
    return pd.DataFrame(rows)


class StructuralDriftTest(unittest.TestCase):
    def test_removal_and_reappearance_have_different_confirmation_delays(self):
        log = _event_log(["ABC"] * 20 + ["A"] * 20 + ["ABC"] * 10)
        result = lcdd.apply(
            log,
            {lcdd.Parameters.COMPLETE_WINDOW_SIZE: 5, "detection_window_size": 4},
        )
        self.assertEqual([20, 40], [change.index for change in result.changes])
        removal, introduction = result.changes
        edges = {("A", "B"), ("B", "C")}
        self.assertEqual(edges, removal.details["missing"])
        self.assertEqual(edges, introduction.details["added"])
        self.assertEqual(
            pd.Timedelta(minutes=3), removal.available_at - removal.timestamp
        )
        self.assertEqual(introduction.timestamp, introduction.available_at)
        self.assertEqual(
            [*range(5, 24), *range(25, 41), *range(45, 50)],
            [sample.index for sample in result.scores],
        )
        self.assertIsNone(removal.p_value)

    def test_missing_edge_must_be_absent_from_a_full_window(self):
        variants = ["AB"] * 5 + ["A", "A", "AB"] + ["A"] * 3
        params = {"complete_window_size": 5, "detection_window_size": 3}
        self.assertEqual([], lcdd.apply(_event_log(variants), params).changes)
        params["min_disappeared"] = 1
        self.assertEqual([], lcdd.apply(_event_log(variants[:-1]), params).changes)
        result = lcdd.apply(_event_log(variants), params)
        self.assertEqual([8], [change.index for change in result.changes])
        self.assertEqual({("A", "B")}, result.changes[0].details["missing"])
        self.assertEqual(result.scores[-1].timestamp, result.changes[0].available_at)

    def test_stability_period_consolidates_nearby_disappearances(self):
        log = _event_log(["ABCDE"] * 10 + ["CDE"] * 2 + ["E"] * 8)
        params = {"complete_window_size": 5, "detection_window_size": 5}
        early = lcdd.apply(log, {**params, "stable_period": 1}).changes[0]
        grouped = lcdd.apply(log, {**params, "stable_period": 2}).changes[0]
        self.assertEqual(10, early.index)
        self.assertEqual(12, grouped.index)
        self.assertEqual(4, len(grouped.details["missing"]))
        self.assertEqual(early.available_at, grouped.available_at)

    def test_frequency_shift_with_stable_support_does_not_raise_an_alarm(self):
        log = _event_log(["AB", "AC"] * 15 + (["AB"] * 8 + ["AC"]) * 6)
        result = lcdd.apply(
            log,
            {
                "complete_window_size": 10,
                "detection_window_size": 12,
                "min_disappeared": 1,
            },
        )
        self.assertEqual([], result.changes)
        self.assertTrue(all(sample.score == 0 for sample in result.scores))


class RunDistributionTest(unittest.TestCase):
    def test_run_identity_is_invariant_under_concurrent_reordering(self):
        concurrent = frozenset({("B", "C"), ("C", "B")})
        run = run_distribution._run
        self.assertEqual(
            run(tuple("ABBCD"), concurrent), run(tuple("ACBBD"), concurrent)
        )
        self.assertNotEqual(
            run(tuple("ABCD"), concurrent), run(tuple("ABBCD"), concurrent)
        )
        self.assertNotEqual(run(("A",), concurrent), run(("B",), concurrent))
        # A->B->C implies A->C even when the oracle declares A and C concurrent.
        indirect = frozenset({("A", "C"), ("C", "A")})
        self.assertEqual(run(tuple("ABC"), indirect), run(tuple("ABC"), frozenset()))

    def test_concurrent_interleavings_share_a_distribution(self):
        log = _event_log((["ABCD"] * 9 + ["ACBD"]) * 4 + (["ACBD"] * 9 + ["ABCD"]) * 4)
        result = run_distribution.apply(log, {"window_size": 25, "persistence": 1})
        self.assertEqual([], result.changes)
        self.assertTrue(
            all(sample.score == 0 and sample.p_value == 1 for sample in result.scores)
        )

    def test_chi_square_test_detects_the_execution_shift(self):
        log = _event_log(["ABC"] * 30 + ["ADC"] * 30)
        result = run_distribution.apply(log, {"window_size": 10, "persistence": 3})
        self.assertEqual(1, len(result.changes))
        alarm = result.changes[0]
        self.assertLess(abs(alarm.index - 30), 10)
        self.assertGreater(alarm.available_at, alarm.timestamp)
        self.assertLess(alarm.p_value, 0.05)
        sample = next(score for score in result.scores if score.index == 30)
        self.assertAlmostEqual(20, sample.score)
        self.assertAlmostEqual(chi2.sf(20, 1), sample.p_value)
        self.assertEqual(0, sample.details["fraction_expected_below_five"])

    def test_adaptive_windows_use_only_observed_executions(self):
        variants = ["ABC"] * 20 + ["ADC"] * 20 + ["AEC", "AFC"] * 12
        parameters = {"window_size": 8, "persistence": 2, "adaptive": True}
        prefix = run_distribution.apply(_event_log(variants[:36]), parameters)
        full = run_distribution.apply(_event_log(variants), parameters)
        self.assertEqual(prefix.scores, full.scores[: len(prefix.scores)])
        self.assertEqual(prefix.changes, full.changes[: len(prefix.changes)])
        self.assertGreater(
            len({score.details["window_size"] for score in full.scores}), 1
        )
        self.assertEqual(
            sorted(score.available_at for score in full.scores),
            [score.available_at for score in full.scores],
        )

    def test_labelled_intervals_require_a_compatible_mixture(self):
        first, last = ["AB"] * 40, ["AC"] * 40
        parameters = {"window_size": 12, "persistence": 3, "gradual": True}
        blend = _event_log(first + ["AB", "AC"] * 20 + last)
        other = _event_log(first + ["AB", "AE", "AC"] * 20 + last)
        blended = run_distribution.apply(blend, parameters)
        self.assertEqual(1, len(blended.intervals))
        interval = blended.intervals[0]
        self.assertEqual(blended.changes[0].index, interval.start_index)
        self.assertEqual(blended.changes[1].index - 1, interval.end_index)
        self.assertEqual(blend["time:timestamp"].max(), interval.available_at)
        self.assertAlmostEqual(0.5, interval.details["later_weight"], delta=0.1)
        abrupt = run_distribution.apply(other, parameters)
        self.assertEqual(2, len(abrupt.changes))
        self.assertEqual([], abrupt.intervals)


class EarthMoverDriftTest(unittest.TestCase):
    def test_earth_mover_transports_multivariant_probabilities(self):
        first = [("A",)] * 4 + [("B",)] * 2
        second = [("A",)] * 2 + [("B",)] + [("X",)] * 3
        distance = partial(earth_mover._edit_distance, timed=False)
        self.assertAlmostEqual(0.5, earth_mover._transport(first, second, distance))
        self.assertAlmostEqual(0.5, earth_mover._transport(second, first, distance))
        self.assertEqual(0.0, earth_mover._transport(second, second[::-1], distance))

    def test_earth_mover_selects_the_peak_and_can_return_only_scores(self):
        log = _event_log(["ABC"] * 10 + ["AXC"] * 10)
        result = earth_mover.apply(log, {"window_size": 5})
        self.assertEqual([10], [change.index for change in result.changes])
        self.assertAlmostEqual(1 / 3, result.changes[0].score)
        self.assertEqual(11, len(result.scores))
        self.assertEqual(log["time:timestamp"].max(), result.changes[0].available_at)
        curve = earth_mover.apply(log, {"window_size": 5, "threshold": None})
        self.assertEqual(result.scores, curve.scores)
        self.assertEqual([], curve.changes)

    def test_inter_event_timing_exposes_a_pure_performance_shift(self):
        log = _event_log(["AB"] * 20, gaps=[1] * 10 + [10] * 10)
        result = earth_mover.apply(
            log, {"window_size": 5, "time_feature": "inter_event"}
        )
        self.assertEqual([10], [change.index for change in result.changes])
        self.assertAlmostEqual(0.5, result.changes[0].score)
        self.assertTrue(
            all(
                sample.available_at == log["time:timestamp"].max()
                for sample in result.scores
            )
        )
        self.assertTrue(all(sample.p_value is None for sample in result.scores))
        control_flow = earth_mover.apply(log, {"window_size": 5})
        self.assertEqual([], control_flow.changes)
        self.assertTrue(all(sample.score == 0 for sample in control_flow.scores))

    def test_service_and_inter_event_times_are_distinct(self):
        log = _event_log(["AB"] * 20, service=[1] * 10 + [10] * 10)
        log["begun"] = log.pop("start_timestamp").dt.tz_localize(None)
        log = log.rename(columns={"time:timestamp": "finished"})
        parameters = {"window_size": 5, "timestamp_key": "finished"}
        service = earth_mover.apply(
            log,
            {**parameters, "time_feature": "service", "start_timestamp_key": "begun"},
        )
        self.assertEqual([10], [change.index for change in service.changes])
        self.assertAlmostEqual(1.0, service.changes[0].score)
        gap = earth_mover.apply(log, {**parameters, "time_feature": "inter_event"})
        self.assertEqual([], gap.changes)
        self.assertTrue(all(sample.score == 0 for sample in gap.scores))
        with self.assertRaisesRegex(
            ValueError, "service time requires event attribute"
        ):
            earth_mover.apply(log, {**parameters, "time_feature": "service"})
        log["begun"] = log["finished"] + pd.Timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError, "timings must be nonnegative"):
            earth_mover.apply(
                log,
                {
                    **parameters,
                    "time_feature": "service",
                    "start_timestamp_key": "begun",
                },
            )

    def test_weighted_trace_distance_charges_for_time_and_control_flow(self):
        distance = partial(earth_mover._edit_distance, timed=True)
        first = (("A", 1), ("B", 2))
        second = (("A", 0), ("C", 2))
        self.assertEqual(1.0, distance(first, second))
        self.assertEqual(distance(first, second), distance(second, first))
        self.assertEqual(2.5, distance(first, ()))
        self.assertEqual(0, distance(first, first))


class ExecutionInputTest(unittest.TestCase):
    def test_dataframe_and_reversed_event_log_have_the_same_results(self):
        dataframe = _event_log(["ABC"] * 10 + ["AXC"] * 10)
        event_log = EventLog(
            [
                Trace([Event(row) for row in rows.iloc[::-1].to_dict("records")])
                for _, rows in dataframe.groupby("case:concept:name")
            ][::-1]
        )
        for variant, params in (
            (earth_mover, {"window_size": 5, "time_feature": "service"}),
            (lcdd, {"complete_window_size": 5, "detection_window_size": 5}),
            (run_distribution, {"window_size": 5, "persistence": 1}),
        ):
            with self.subTest(variant=variant.__name__):
                self.assertEqual(
                    variant.apply(dataframe, params), variant.apply(event_log, params)
                )
                self.assertEqual([], variant.apply(EventLog(), params).scores)

    def test_configuration_validation(self):
        for variant, params in (
            (earth_mover, {"threshold": float("nan")}),
            (earth_mover, {"time_feature": "unknown"}),
            (earth_mover, {"time_feature": "service", "percentiles": (50, 100)}),
            (lcdd, {"detection_window_size": 0}),
            (run_distribution, {"alpha": 0}),
            (run_distribution, {"window_size": 5, "min_window_size": 6}),
        ):
            with (
                self.subTest(variant=variant.__name__, params=params),
                self.assertRaises(ValueError),
            ):
                variant.apply(EventLog(), params)
