import importlib.util
import itertools
import unittest

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

import pm4py
from pm4py.algo.concept_drift import _timeseries
from pm4py.algo.concept_drift.variants import conformance, indicators

START = pd.Timestamp("2024-01-01", tz="UTC")
HAS_RIVER = importlib.util.find_spec("river") is not None


def _log(regimes, *, cases_per_day=1):
    rows = []
    for day, (activities, resources) in enumerate(regimes):
        for case in range(cases_per_day):
            for hour, (activity, resource) in enumerate(zip(activities, resources)):
                rows.append(
                    {
                        "case:concept:name": f"{day}-{case}",
                        "concept:name": activity,
                        "time:timestamp": START + pd.Timedelta(days=day, hours=hour),
                        "org:resource": resource,
                    }
                )
    return pd.DataFrame(rows)


def _objective(values, cuts, minimum, penalty, kernel):
    cost = penalty * len(cuts)
    for start, end in itertools.pairwise([0, *cuts, len(values)]):
        segment = values[start:end]
        if len(segment) < minimum:
            return np.inf
        if kernel:
            gram = np.exp(-kernel * cdist(segment, segment, metric="sqeuclidean"))
            cost += len(segment) - gram.sum() / len(segment)
        else:
            cost += ((segment - segment.mean(axis=0)) ** 2).sum()
    return cost


class ConceptDriftTimeSeriesTest(unittest.TestCase):
    def test_pelt_matches_exhaustive_segmentations(self):
        rng = np.random.default_rng(123)
        for seed, minimum, kernel in itertools.product(
            range(5), (1, 2, 3), (False, 1.0)
        ):
            values = rng.normal(size=(seed + 5, 2)) + 100
            n = len(values)
            penalty = 0.2 + seed * 0.4

            exhaustive = min(
                _objective(values, cuts, minimum, penalty, kernel)
                for size in range(n)
                for cuts in itertools.combinations(range(1, n), size)
            )
            with self.subTest(n=n, minimum=minimum, kernel=kernel):
                selected = _timeseries.pelt(values, penalty, minimum, kernel=kernel)
                self.assertAlmostEqual(
                    _objective(values, selected, minimum, penalty, kernel),
                    exhaustive,
                    places=9,
                )

    def test_pelt_cost_variants_and_validation(self):
        values = np.r_[np.tile([1.0, -1.0], 30), np.tile([3.0, -3.0], 30)]
        self.assertEqual(_timeseries.pelt(values, 10, 10), [])
        cost = _timeseries.segment_cost(values, kernel=True)
        self.assertEqual(_timeseries.pelt(values, 10, 10, cost=cost), [60])
        self.assertEqual(_timeseries.pelt([2, 2, 2], 1), [])
        self.assertEqual(_timeseries.pelt([], 1, kernel=True), [])
        for values, penalty, minimum in (([1, np.nan], 2, 1), ([1], 0, 1), ([1], 2, 0)):
            with self.assertRaises(ValueError):
                _timeseries.pelt(values, penalty, minimum)

    def test_page_hinkley_directions_and_reset(self):
        for direction, signals in (("up", [25]), ("down", [50]), ("both", [25, 50])):
            detector = _timeseries.make_detector(
                "page_hinkley",
                {
                    "page_hinkley_threshold": 1,
                    "page_hinkley_direction": direction,
                },
            )
            values = np.repeat([0.0, 1.0, 0.0], 25)
            observed = []
            for index, value in enumerate(values):
                score, lag = detector.update(value)
                if lag is not None:
                    self.assertGreater(score, 1)
                    observed.append(index - lag)
            self.assertEqual(observed, signals)

    def test_calendar_features_with_gaps_and_custom_columns(self):
        case = pd.DataFrame(
            {
                "id": [123, 123, 456, 789],
                "activity": ["B", "A", "A", "B"],
                "time": [
                    START + pd.Timedelta(days=2),
                    START + pd.Timedelta(hours=12),
                    START + pd.Timedelta(days=2, hours=6),
                    START + pd.Timedelta(days=2, hours=8),
                ],
                "start": [START + pd.Timedelta(days=1, hours=23), None, None, None],
                "resource": ["r2", "r1", "r2", None],
                "case:type": ["special", "special", "normal", None],
                "case:amount": [42, 42, 10, None],
            }
        )
        features = [
            *indicators.DEFAULT_FEATURES,
            "active_resources",
            ("activity_count", "B"),
            ("activity_frequency", "B"),
            ("inter_event_gap", "B"),
            ("service_time", "B"),
            ("resource_assignment", "B", "r2"),
            ("resource_handover", "r1", "r2"),
            ("case_type", "type", "special"),
            ("case_value", "amount"),
        ]
        parameters = {
            "case_id_key": "id",
            "activity_key": "activity",
            "timestamp_key": "time",
            "resource_key": "resource",
            "start_timestamp_key": "start",
            "features": features,
        }
        frame = indicators.extract_features(case, parameters)
        self.assertEqual(list(frame.columns), features)
        self.assertEqual(
            frame.index.tolist(), pd.date_range(START, periods=3, freq="D").tolist()
        )
        self.assertEqual(frame["arrivals"].tolist(), [1, 0, 2])
        self.assertEqual(frame["completions"].tolist(), [0, 0, 3])
        self.assertEqual(frame["work_in_progress"].tolist(), [1, 1, 0])
        self.assertEqual(frame["events"].tolist(), [1, 0, 3])
        self.assertEqual(frame["active_resources"].tolist(), [1, 0, 1])
        self.assertEqual(frame[("activity_count", "B")].tolist(), [0, 0, 2])
        self.assertTrue(np.isnan(frame[("activity_frequency", "B")].iloc[1]))
        self.assertAlmostEqual(frame[("activity_frequency", "B")].iloc[2], 2 / 3)
        self.assertEqual(frame["case_duration"].iloc[2], 36 * 3600 / 3)
        self.assertEqual(frame[("inter_event_gap", "B")].iloc[2], 36 * 3600)
        self.assertEqual(frame[("service_time", "B")].iloc[2], 3600)
        self.assertEqual(frame[("resource_assignment", "B", "r2")].iloc[2], 1)
        self.assertEqual(frame[("resource_handover", "r1", "r2")].tolist(), [0, 0, 1])
        self.assertEqual(frame[("case_type", "type", "special")].iloc[2], 0.5)
        self.assertEqual(frame[("case_value", "amount")].iloc[2], 26)

        legacy = pm4py.convert_to_event_log(
            case.assign(id=case["id"].astype(str)), case_id_key="id"
        )
        pd.testing.assert_frame_equal(
            indicators.extract_features(legacy, parameters), frame
        )

    def test_calendar_multi_month_bins_keep_a_common_origin(self):
        log = _log([("A", ["r"]), ("B", ["r"]), ("B", ["r"])])
        log["time:timestamp"] = pd.to_datetime(
            ["2024-01-05", "2024-02-10", "2024-05-05"], utc=True
        )
        frame = indicators.extract_features(
            log, {"bin_size": "2MS", "features": ["arrivals", ("activity_count", "B")]}
        )
        self.assertEqual(frame["arrivals"].tolist(), [2, 0, 1])
        self.assertEqual(frame[("activity_count", "B")].tolist(), [1, 0, 1])

    def test_pelt_detects_workload_and_conditional_resource_drift(self):
        model = ("AB", ["r1", "r2"])
        changed = ("AB", ["r2", "r1"])
        reassign = _log([model] * 20 + [changed] * 20)
        features = [
            "active_resources",
            ("activity_frequency", "A"),
            ("resource_assignment", "A", "r1"),
        ]
        result = indicators.apply(reassign, {"features": features, "penalty": 5})
        self.assertEqual([alarm.index for alarm in result.changes], [20])
        alarm = result.changes[0]
        self.assertEqual(set(alarm.details["changed_features"]), {features[-1]})
        self.assertEqual(alarm.available_at, START + pd.Timedelta(days=40))
        self.assertEqual(result.scores[20].score, 1)
        self.assertIsNone(alarm.p_value)

        more_cases = _log([model] * 40, cases_per_day=2)
        log = more_cases[
            (more_cases["time:timestamp"] >= START + pd.Timedelta(days=20))
            | more_cases["case:concept:name"].str.endswith("-0")
        ]
        result = indicators.apply(
            log, {"features": ["arrivals", ("activity_frequency", "A")], "penalty": 5}
        )
        self.assertEqual([alarm.index for alarm in result.changes], [20])
        self.assertEqual(
            set(result.changes[0].details["changed_features"]), {"arrivals"}
        )

    def test_pelt_standardizes_case_values_across_finite_scales(self):
        log = _log([("A", ["r1"])] * 20)
        for scale in (1.0, 1e-200, 1e200):
            with self.subTest(scale=scale):
                log["case:amount"] = [0] * 10 + [scale] * 10
                result = indicators.apply(
                    log, {"features": [("case_value", "amount")], "penalty": 4}
                )
                self.assertEqual([alarm.index for alarm in result.changes], [10])

    def test_sequential_calendar_alarm_delays_and_prefix_stability(self):
        old = ("AB", ["r1", "r2"])
        new = ("AB", ["r2", "r1"])
        log = _log([old] * 20 + [new] * 20)
        feature = ("resource_assignment", "A", "r1")
        parameters = {
            "method": "page_hinkley",
            "features": [feature],
            "page_hinkley_threshold": 1,
        }
        result = indicators.apply(log, parameters)
        self.assertEqual([alarm.index for alarm in result.changes], [20])
        alarm = result.changes[0]
        self.assertEqual(alarm.timestamp, START + pd.Timedelta(days=20))
        self.assertGreater(alarm.available_at, alarm.timestamp)
        prior = indicators.apply(
            log[log["time:timestamp"] < alarm.available_at],
            {**parameters, "observation_end": alarm.available_at},
        )
        self.assertEqual(prior.changes, result.changes)
        self.assertEqual(prior.scores, result.scores[: len(prior.scores)])

    def test_sequential_ignores_open_bin_and_monitors_recorded_empty_bins(self):
        log = _log([("A", ["r1"])] * 20, cases_per_day=10)
        last_day = START + pd.Timedelta(days=20)
        next_event = log.iloc[[-1]].copy()
        next_event["case:concept:name"] = "next"
        next_event["time:timestamp"] = last_day + pd.Timedelta(hours=1)
        early_snapshot = pd.concat([log, next_event], ignore_index=True)
        parameters = {
            "method": "page_hinkley",
            "features": ["arrivals"],
            "page_hinkley_direction": "down",
            "page_hinkley_threshold": 5,
        }

        replay = indicators.apply(early_snapshot, parameters)
        self.assertEqual(len(replay.scores), 20)
        self.assertFalse(replay.changes)
        closed = indicators.apply(
            early_snapshot,
            {**parameters, "observation_end": last_day + pd.Timedelta(days=2)},
        )
        self.assertEqual([alarm.index for alarm in closed.changes], [20])
        self.assertEqual(
            closed.changes[0].available_at, last_day + pd.Timedelta(days=1)
        )
        self.assertEqual(closed.scores[-1].details["values"]["arrivals"], 0)
        with self.assertRaisesRegex(ValueError, "precedes the last input event"):
            indicators.apply(
                early_snapshot, {**parameters, "observation_end": last_day}
            )

    @unittest.skipUnless(HAS_RIVER, "optional River ADWIN dependency is missing")
    def test_adwin_indicators_and_adaptive_reference(self):
        old = ("AB", ["r1", "r2"])
        new = ("CD", ["r1", "r2"])
        log = _log([old] * 70 + [new] * 100)
        result = indicators.apply(
            log, {"method": "adwin", "features": [("activity_frequency", "A")]}
        )
        self.assertEqual(len(result.changes), 1)
        alarm = result.changes[0]
        self.assertGreater(alarm.available_at, START + pd.Timedelta(days=70))
        self.assertLess(alarm.available_at, START + pd.Timedelta(days=140))
        self.assertLess(alarm.timestamp, alarm.available_at)
        result = conformance.apply(
            log, {"method": "adwin", "model_policy": "on_alarm", "update_window": 8}
        )
        self.assertEqual(len(result.changes), 1)
        self.assertEqual(result.scores[-1].score, 1)
        self.assertEqual(result.versions[-1].label, 1)

    @unittest.skipIf(HAS_RIVER, "River is available in this environment")
    def test_adwin_missing_dependency(self):
        with self.assertRaisesRegex(ImportError, r"pm4py\[drift\]"):
            _timeseries.make_detector("adwin")

    def test_conformance_detects_and_adapts_to_recurring_regime(self):
        old, new = ("AB", ["r1", "r2"]), ("CD", ["r1", "r2"])
        log = _log([old] * 30 + [new] * 30 + [old] * 30).sample(frac=1, random_state=2)
        parameters = {"reference_size": 15, "page_hinkley_threshold": 1}
        fixed = conformance.apply(log, parameters)
        adaptive = conformance.apply(log, {**parameters, "model_policy": "on_alarm"})
        self.assertEqual([alarm.index for alarm in adaptive.changes], [30, 60])
        self.assertEqual(fixed.scores[55].score, 0)
        self.assertEqual(adaptive.scores[55].score, 1)
        self.assertEqual(fixed.versions[-1].label, 0)
        self.assertEqual(adaptive.versions[-1].label, 2)
        self.assertEqual(adaptive.scores[0].available_at, adaptive.scores[14].timestamp)
        for version, alarm in enumerate(adaptive.changes, 1):
            start, end = adaptive.metadata["reference_models"][version][
                "training_range"
            ]
            self.assertEqual(start, alarm.index)
            self.assertEqual(adaptive.scores[end - 1].available_at, alarm.available_at)
            self.assertEqual(adaptive.versions[end - 1].label, version - 1)
            self.assertEqual(adaptive.versions[end].label, version)

    def test_conformance_external_model_and_short_log(self):
        old, new = ("AB", ["r1", "r2"]), ("AC", ["r1", "r2"])
        trainer = _log([old] * 10)
        model = pm4py.discover_petri_net_inductive(trainer)
        query = _log([old] * 3 + [new] * 4).rename(columns={"concept:name": "step"})
        self.assertEqual(conformance.apply(query, {"activity_key": "step"}).scores, [])
        result = conformance.apply(
            query, {"activity_key": "step", "reference_model": model}
        )
        self.assertEqual([item.score for item in result.scores], [1] * 3 + [0.5] * 4)
        self.assertEqual(result.changes, [])
        self.assertEqual(result.scores[0].available_at, result.scores[0].timestamp)
        self.assertIsNone(result.metadata["reference_models"][0]["training_range"])

    def test_empty_inputs_and_invalid_options(self):
        empty = pd.DataFrame()
        self.assertEqual(indicators.apply(empty).changes, [])
        self.assertEqual(conformance.apply(empty).changes, [])
        for parameters in (
            {"features": []},
            {"features": [("activity_count",)]},
            {"bin_size": "-1h"},
            {"penalty": 0},
            {"method": "other"},
        ):
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                indicators.apply(empty, parameters)
        for parameters in (
            {"reference_model": (None, None, None)},
            {"model_policy": "other"},
            {"reference_size": 0},
            {"update_window": -1},
            {"page_hinkley_delta": np.nan},
        ):
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                conformance.apply(empty, parameters)
