'''
PM4Py – A Process Mining Library for Python
Copyright (C) 2026 Process Intelligence Solutions GmbH

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see this software project's root or
visit <https://www.gnu.org/licenses/>.

Website: https://processintelligence.solutions
Contact: contact@processintelligence.solutions
'''
"""Stochastic-language EMD curves, optionally using activity-specific time bins.

The timed descriptor and weighted edit operations follow Brockhoff, Uysal,
and van der Aalst (https://www.vdaalst.com/publications/p1146.pdf).
"""

from collections import Counter, defaultdict
from dataclasses import replace
from enum import Enum
from functools import lru_cache, partial
from numbers import Real

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from pm4py.algo.concept_drift import _common
from pm4py.util import constants, exec_utils, string_distance, xes_constants


class Parameters(Enum):
    WINDOW_SIZE = "window_size"
    STEP = "step"
    THRESHOLD = "threshold"
    PERSISTENCE = "persistence"
    MIN_SEPARATION = "min_separation"
    TIME_FEATURE = "time_feature"
    PERCENTILES = "percentiles"
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY


def _timed_descriptors(observations, feature, percentiles, start_key):
    timed = []
    samples = defaultdict(list)
    for trace in observations:
        previous = trace.start
        descriptor = []
        for activity, event, end in zip(
            trace.activities, trace.events, trace.timestamps
        ):
            start = previous
            if feature == "service":
                if start_key not in event or pd.isna(event[start_key]):
                    raise ValueError(
                        f"service time requires event attribute {start_key!r}"
                    )
                start = pd.to_datetime(event[start_key], utc=True)
                if pd.isna(start):
                    raise ValueError(
                        f"service time requires event attribute {start_key!r}"
                    )
            elapsed = (end - start) / pd.Timedelta(seconds=1)
            if elapsed < 0:
                raise ValueError("timings must be nonnegative")
            samples[activity].append(elapsed)
            descriptor.append((activity, elapsed))
            previous = end
        timed.append(descriptor)

    boundaries = {}
    for activity, durations in samples.items():
        cutoffs = np.unique(np.percentile(durations, percentiles))
        boundaries[activity] = cutoffs[cutoffs < max(durations)]
    return [
        tuple(
            (activity, int(boundaries[activity].searchsorted(elapsed, side="left")))
            for activity, elapsed in trace
        )
        for trace in timed
    ]


def _edit_distance(first, second, timed):
    size = max(len(first), len(second))
    if not size or first == second:
        return 0.0
    if not timed:
        return string_distance.levenshtein_distance(first, second) / size

    previous = np.cumsum([0] + [1 + time_bin for _, time_bin in second]).tolist()
    for first_activity, first_bin in first:
        deletion = 1 + first_bin
        row = [previous[0] + deletion]
        for index, (second_activity, second_bin) in enumerate(second):
            insertion = 1 + second_bin
            rename = (first_activity != second_activity) + abs(first_bin - second_bin)
            row.append(
                min(
                    previous[index + 1] + deletion,
                    row[index] + insertion,
                    previous[index] + rename,
                )
            )
        previous = row
    return previous[-1] / size


def _transport(first, second, distance):
    left = Counter(first)
    right = Counter(second)
    if left == right:
        return 0.0

    costs = np.array([[distance(a, b) for b in right] for a in left])
    supply = np.array(list(left.values()), dtype=float) / len(first)
    demand = np.array(list(right.values()), dtype=float) / len(second)
    if len(left) == 1 or len(right) == 1:
        return float(supply @ costs @ demand)

    # One flow variable per pair, constrained by its source and destination.
    flows = np.arange(costs.size)
    constraints = coo_matrix(
        (
            np.ones(2 * costs.size),
            (
                np.concatenate((flows // len(right), len(left) + flows % len(right))),
                np.tile(flows, 2),
            ),
        ),
        shape=(len(left) + len(right), costs.size),
    ).tocsr()
    solution = linprog(
        costs.ravel(),
        A_eq=constraints,
        b_eq=np.concatenate((supply, demand)),
        method="highs",
    )
    if not solution.success:
        raise RuntimeError(
            f"Earth Mover's Distance optimization failed: {solution.message}"
        )
    return float(solution.fun)


def apply(log, parameters=None):
    """Compare adjacent windows of completed traces using Earth Mover's Distance.

    ``window_size`` (default 50) and ``step`` (default 1) are in traces. The
    default control-flow descriptor is the trace's activity sequence, with
    normalized Levenshtein edit cost. Set ``time_feature`` to ``"inter_event"``
    for successive event-completion gaps (first event zero), or ``"service"``
    for event completion minus the configured start timestamp. Timed variants
    fit per-activity bins over the complete log using ``percentiles`` (default
    50, 80, 95), then compare activity and time-bin sequences with weighted
    edit cost. Time-aware scores may exceed 1.

    The alarm rule is retrospective and selects the strongest score in each
    excursion at or above ``threshold`` (default 0.25). Set it to ``None`` to
    return only the distance curve. ``persistence`` counts consecutive window
    scores (default 1), and ``min_separation`` is measured in traces (default 0).
    """
    parameters = parameters or {}
    window = _common.integer(
        exec_utils.get_param_value(Parameters.WINDOW_SIZE, parameters, 50),
        "window_size",
    )
    step = _common.integer(
        exec_utils.get_param_value(Parameters.STEP, parameters, 1), "step"
    )
    threshold = exec_utils.get_param_value(Parameters.THRESHOLD, parameters, 0.25)
    persistence = _common.integer(
        exec_utils.get_param_value(Parameters.PERSISTENCE, parameters, 1), "persistence"
    )
    min_separation = _common.integer(
        exec_utils.get_param_value(Parameters.MIN_SEPARATION, parameters, 0),
        "min_separation",
        minimum=0,
    )
    feature = exec_utils.get_param_value(Parameters.TIME_FEATURE, parameters, None)
    if feature not in (None, "inter_event", "service"):
        raise ValueError("time_feature must be None, 'inter_event', or 'service'")
    if threshold is not None and (
        isinstance(threshold, bool)
        or not isinstance(threshold, Real)
        or not np.isfinite(threshold)
        or threshold <= 0
    ):
        raise ValueError("threshold must be None or a positive finite number")

    observations = _common.completed_traces(log, parameters)
    percentiles = None
    if feature is None:
        descriptors = [trace.activities for trace in observations]
    else:
        try:
            percentiles = tuple(
                exec_utils.get_param_value(
                    Parameters.PERCENTILES, parameters, (50, 80, 95)
                )
            )
        except TypeError as exc:
            raise ValueError(
                "percentiles must be a sequence of numbers in (0, 100)"
            ) from exc
        if not percentiles or any(
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not 0 < value < 100
            for value in percentiles
        ):
            raise ValueError("percentiles must be a sequence of numbers in (0, 100)")
        start_key = _common.attribute_key(
            parameters, "start_timestamp_key", xes_constants.DEFAULT_START_TIMESTAMP_KEY
        )
        descriptors = _timed_descriptors(observations, feature, percentiles, start_key)

    distance = lru_cache(maxsize=8192)(
        partial(_edit_distance, timed=feature is not None)
    )
    scores = []
    for start, boundary, stop in _common.adjacent_windows(
        len(observations), window, step
    ):
        score = _transport(
            descriptors[start:boundary], descriptors[boundary:stop], distance
        )
        available_at = observations[-1 if feature else stop - 1].end
        scores.append(
            _common.WindowScore(
                boundary, score, observations[boundary].end, available_at
            )
        )

    changes = []
    if threshold is not None:
        changes = [
            replace(change, available_at=observations[-1].end)
            for change in _common.consolidate(
                scores,
                lambda sample: sample.score >= threshold,
                persistence=persistence,
                min_separation=min_separation,
                retrospective=True,
            )
        ]
    return _common.DriftResult(
        observation_unit="trace",
        scores=scores,
        changes=changes,
        metadata={
            "window_size": window,
            "step": step,
            "time_feature": feature,
            "percentiles": percentiles,
            "threshold": threshold,
            "persistence": persistence,
            "min_separation": min_separation,
            "representation": "stochastic language of trace descriptors",
            "mode": "retrospective",
        },
    )
