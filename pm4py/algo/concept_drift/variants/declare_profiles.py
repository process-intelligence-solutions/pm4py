"""Retrospective segmentation of fixed Declare constraint profiles.

This adaptation of Visual Drift Detection (Yeshchenko et al., 2019,
https://arxiv.org/abs/1907.06386) tracks trace-level statistics for a fixed bank
of constraints and segments the joint profile with an RBF kernel cost.
"""

from collections import Counter
from enum import Enum
from itertools import combinations, permutations

import numpy as np

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.algo.concept_drift._common import DriftAlarm, DriftResult, WindowScore
from pm4py.algo.conformance.declare.variants.classic import apply_list
from pm4py.algo.discovery.declare import templates
from pm4py.util import exec_utils


class Parameters(Enum):
    CONSTRAINTS = "constraints"
    WINDOW_SIZE = "window_size"
    STEP = "step"
    STATISTIC = "statistic"
    PENALTY = "penalty"
    MIN_SIZE = "min_size"
    GAMMA = "gamma"


_UNARY = {templates.EXISTENCE, templates.ABSENCE, templates.EXACTLY_ONE, templates.INIT}
_FIRST = {
    templates.RESPONDED_EXISTENCE,
    templates.RESPONSE,
    templates.ALTRESPONSE,
    templates.CHAINRESPONSE,
}
_SECOND = {templates.PRECEDENCE, templates.ALTPRECEDENCE, templates.CHAINPRECEDENCE}
_EITHER = {templates.COEXISTENCE, templates.NONCOEXISTENCE}


def _constraint_bank(observations, constraints):
    if constraints is None:
        activities = list(
            dict.fromkeys(
                activity for trace in observations for activity in trace.activities
            )
        )
        bank = [(templates.EXISTENCE, activity) for activity in activities]
        for a, b in permutations(activities, 2):
            bank.extend([(templates.RESPONSE, a, b), (templates.PRECEDENCE, a, b)])
        for a, b in combinations(activities, 2):
            bank.extend(
                [(templates.COEXISTENCE, a, b), (templates.NONCOEXISTENCE, a, b)]
            )
        return bank

    bank = []
    for rule in constraints:
        if (
            not isinstance(rule, (tuple, list))
            or not rule
            or not isinstance(rule[0], str)
        ):
            raise ValueError(
                "Each constraint must be a tuple of a template and its activities"
            )
        kind, *activities = rule
        if kind in _UNARY:
            if len(activities) != 1:
                raise ValueError(f"{kind} needs one activity")
        elif kind in _FIRST | _SECOND | _EITHER:
            if len(activities) != 2 or activities[0] == activities[1]:
                raise ValueError(f"{kind} needs two distinct activities")
        else:
            raise ValueError(f"Unsupported Declare template {kind!r}")
        bank.append(tuple(rule))
    return list(dict.fromkeys(bank))


def _trace_profiles(observations, bank):
    model = {}
    for kind, *activities in bank:
        key = activities[0] if len(activities) == 1 else tuple(activities)
        model.setdefault(kind, {})[key] = {}

    variants = dict.fromkeys(trace.activities for trace in observations)
    profiles = {}
    for variant in variants:
        result = apply_list([variant], model)[0]
        present = set(variant)
        deviations = {tuple(deviation) for deviation in result["deviations"]}
        profile = np.zeros(len(bank), dtype=np.int8)
        for index, (kind, *activities) in enumerate(bank):
            if kind in _UNARY:
                active = True
                key = activities[0]
            else:
                key = tuple(activities)
                first, second = key
                if kind in _FIRST:
                    active = first in present
                elif kind in _SECOND:
                    active = second in present
                else:
                    active = first in present or second in present
            if active:
                profile[index] = -1 if (kind, key) in deviations else 1
        profiles[variant] = profile
    return profiles


def _window_profile(observations, trace_profiles, statistic, count):
    satisfied = np.zeros(count, dtype=int)
    violated = np.zeros(count, dtype=int)
    for variant, frequency in Counter(
        trace.activities for trace in observations
    ).items():
        profile = trace_profiles[variant]
        satisfied += frequency * (profile == 1)
        violated += frequency * (profile == -1)
    if statistic == "confidence":
        return satisfied / len(observations)
    activated = satisfied + violated
    numerator = satisfied if statistic == "support" else violated
    return np.divide(numerator, activated, out=np.zeros(count), where=activated > 0)


def apply(log, parameters=None):
    """Detect changes in Declare profiles over trace-count windows.

    ``constraints`` is an iterable of tuples such as ``("response", "A", "B")``.
    The bank defaults to existence, response, precedence, coexistence, and
    noncoexistence over the log's observed activities. Explicit banks also
    support absence, exactly_one, init, responded_existence, and the alternate
    and chain forms of response and precedence.

    ``statistic`` selects confidence (activated and satisfied divided by all
    traces, the default), support (satisfied divided by activated traces), or
    violation_rate (violated divided by activated traces). Each trace counts
    once, even with multiple activations. Unactivated rules contribute zero
    and globally unactivated window statistics are zero. Unary rules activate
    on every trace. Response activates on the first activity, precedence on
    the second, and coexistence/noncoexistence on either.

    Traces are ordered by completion. ``window_size`` defaults to 50 and
    ``step`` defaults to the window size. Only full windows are used. Detected
    changes refer to the first trace of the first window in a new segment.
    ``penalty`` defaults to 3, ``min_size`` is the minimum segment length in
    windows (default 2), and ``gamma`` optionally fixes the RBF coefficient.
    The score series contains distances between successive profiles. Change
    scores give the reduction in kernel cost from splitting adjacent segments.
    """
    window_size = _common.integer(
        exec_utils.get_param_value(Parameters.WINDOW_SIZE, parameters, 50),
        "window_size",
    )
    step = _common.integer(
        exec_utils.get_param_value(Parameters.STEP, parameters, window_size), "step"
    )
    statistic = exec_utils.get_param_value(
        Parameters.STATISTIC, parameters, "confidence"
    )
    penalty = exec_utils.get_param_value(Parameters.PENALTY, parameters, 3.0)
    min_size = exec_utils.get_param_value(Parameters.MIN_SIZE, parameters, 2)
    gamma = exec_utils.get_param_value(Parameters.GAMMA, parameters, None)
    if gamma is not None:
        gamma = _common.real(gamma, "gamma")
    if step > window_size:
        raise ValueError("step cannot be larger than window_size")
    if statistic not in {"confidence", "support", "violation_rate"}:
        raise ValueError(
            "statistic must be 'confidence', 'support', or 'violation_rate'"
        )

    observations = _common.completed_traces(log, parameters)
    bank = _constraint_bank(
        observations,
        exec_utils.get_param_value(Parameters.CONSTRAINTS, parameters, None),
    )
    trace_profiles = _trace_profiles(observations, bank)
    starts = list(range(0, len(observations) - window_size + 1, step))
    values = np.array(
        [
            _window_profile(
                observations[start : start + window_size],
                trace_profiles,
                statistic,
                len(bank),
            )
            for start in starts
        ]
    ).reshape(len(starts), len(bank))
    cost = _timeseries.segment_cost(values, kernel=True if gamma is None else gamma)
    boundaries = _timeseries.pelt(values, penalty, min_size, cost=cost)
    available_at = observations[-1].end if observations else None
    scores = [
        WindowScore(
            index=start,
            score=float(np.linalg.norm(values[i] - values[i - 1])) if i else 0.0,
            timestamp=observations[start].end,
            available_at=available_at,
            details={"profile": dict(zip(bank, values[i].tolist()))},
        )
        for i, start in enumerate(starts)
    ]
    changes = []
    for left, cut, right in zip(
        [0] + boundaries, boundaries, boundaries[1:] + [len(values)]
    ):
        before, after = values[left:cut].mean(axis=0), values[cut:right].mean(axis=0)
        deltas = {
            rule: float(delta)
            for rule, delta in zip(bank, after - before)
            if not np.isclose(delta, 0)
        }
        gain = cost(left, right) - cost(left, cut) - cost(cut, right)
        changes.append(
            DriftAlarm(
                index=starts[cut],
                timestamp=observations[starts[cut]].end,
                available_at=available_at,
                score=float(gain),
                details={"constraint_deltas": deltas},
            )
        )

    return DriftResult(
        observation_unit="trace",
        scores=scores,
        changes=changes,
        metadata={
            "method": "declare_profiles",
            "mode": "retrospective",
            "trace_order": "completion",
            "constraints": tuple(bank),
            "statistic": statistic,
            "window_size": window_size,
            "step": step,
            "penalty": penalty,
            "min_size": min_size,
            "gamma": gamma,
        },
    )
