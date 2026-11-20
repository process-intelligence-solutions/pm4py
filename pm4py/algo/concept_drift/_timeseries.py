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
"""Reusable change-point detectors for numeric observations."""

from enum import Enum
from numbers import Integral, Real

import numpy as np
from scipy.spatial.distance import pdist, squareform

from pm4py.util import exec_utils


class Parameters(Enum):
    PH_MIN_INSTANCES = "page_hinkley_min_instances"
    PH_DELTA = "page_hinkley_delta"
    PH_THRESHOLD = "page_hinkley_threshold"
    PH_DIRECTION = "page_hinkley_direction"
    ADWIN_DELTA = "adwin_delta"
    ADWIN_CLOCK = "adwin_clock"
    ADWIN_MIN_WINDOW_LENGTH = "adwin_min_window_length"
    ADWIN_GRACE_PERIOD = "adwin_grace_period"


def _matrix(values):
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("observations must be a finite numeric vector or matrix")
    return values


def segment_cost(values, *, kernel=False):
    """Return a segment cost for half-open intervals ``[start, end)``.

    The cost is the sum of squared deviations from the segment mean. With
    ``kernel=True`` the deviations are measured in an RBF feature space using
    the inverse median nonzero squared distance as gamma. A positive numeric
    ``kernel`` value sets gamma directly. ``start`` can be an array of indices.
    """
    values = _matrix(values)
    if kernel is not False:
        distances = pdist(values, metric="sqeuclidean")
        if kernel is True:
            positive = distances[distances > 0]
            gamma = 1 / np.median(positive) if len(positive) else 1.0
        else:
            gamma = kernel
        if not isinstance(gamma, Real) or not np.isfinite(gamma) or gamma <= 0:
            raise ValueError("RBF gamma must be positive and finite")
        gram = (
            squareform(np.exp(-gamma * distances)) if len(values) else np.empty((0, 0))
        )
        np.fill_diagonal(gram, 1)
        prefix = np.pad(gram.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))

        def cost(start, end):
            total = (
                prefix[end, end]
                - prefix[start, end]
                - prefix[end, start]
                + prefix[start, start]
            )
            size = end - start
            return np.maximum(0.0, size - total / size)

        return cost

    # Centering improves accuracy when the values have a large common offset.
    if len(values):
        values = values - values[0]
    sums = np.pad(values.cumsum(axis=0), ((1, 0), (0, 0)))
    squares = np.r_[0.0, np.sum(values * values, axis=1).cumsum()]

    def cost(start, end):
        total = sums[end] - sums[start]
        mean_cost = np.sum(total * total, axis=-1) / (end - start)
        return np.maximum(0.0, squares[end] - squares[start] - mean_cost)

    return cost


def pelt(values, penalty, min_size=2, *, kernel=False, cost=None):
    """Return interior change points minimizing segment cost plus per-cut penalty.

    This implements the PELT recurrence of Killick, Fearnhead and Eckley
    (2012) using squared-error or RBF segment costs. Each segment contains at
    least ``min_size`` observations. An optional precomputed ``segment_cost``
    callable avoids fitting the cost again when scoring the resulting cuts.
    """
    if not isinstance(penalty, Real) or not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("penalty must be positive and finite")
    _positive_integer(min_size, "min_size")
    if cost is None:
        cost = segment_cost(values, kernel=kernel)
    length = len(values)
    if length < 2 * min_size:
        return []

    objective = np.full(length + 1, np.inf)
    objective[0] = -penalty
    previous = np.zeros(length + 1, dtype=int)
    candidates = np.empty(0, dtype=int)
    expires = np.empty(0, dtype=int)

    for end in range(min_size, length + 1):
        eligible = expires > end
        candidates, expires = candidates[eligible], expires[eligible]
        start = end - min_size
        if np.isfinite(objective[start]):
            candidates = np.append(candidates, start)
            expires = np.append(expires, length + 1)

        totals = objective[candidates] + cost(candidates, end)
        best = np.argmin(totals)
        objective[end] = totals[best] + penalty
        previous[end] = candidates[best]

        # A replacement cut at end becomes admissible only after min_size more observations.
        tolerance = 1e-12 * (1 + abs(objective[end]))
        prune = totals > objective[end] + tolerance
        expires[prune] = np.minimum(expires[prune], end + min_size)

    changes = []
    end = previous[length]
    while end:
        changes.append(int(end))
        end = previous[end]
    return changes[::-1]


def _positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


class _PageHinkley:
    def __init__(self, min_instances, delta, threshold, direction):
        self.min_instances = min_instances
        self.delta = delta
        self.threshold = threshold
        self.direction = direction
        self._reset()

    def _reset(self):
        self.count = 0
        self.mean = 0.0
        self.up = self.down = 0.0
        self.up_start = self.down_start = 0

    def update(self, value):
        index = self.count
        self.count += 1
        deviation = value - self.mean
        self.mean += deviation / self.count
        deviation = value - self.mean
        if self.up == 0:
            self.up_start = index
        if self.down == 0:
            self.down_start = index
        self.up = max(0.0, self.up + deviation - self.delta)
        self.down = max(0.0, self.down - deviation - self.delta)

        score, start = self.up, self.up_start
        if self.direction == "down" or (
            self.direction == "both" and self.down > self.up
        ):
            score, start = self.down, self.down_start
        if self.count >= self.min_instances and score > self.threshold:
            self._reset()
            return score, index - start
        return score, None


class _ADWIN:
    def __init__(self, **kwargs):
        try:
            from river.drift import ADWIN
        except ModuleNotFoundError as exc:
            if exc.name != "river":
                raise
            raise ImportError(
                "The ADWIN method requires River. Install pm4py[drift]."
            ) from exc

        self.detector = ADWIN(**kwargs)

    def update(self, value):
        self.detector.update(value)
        lag = None
        if self.detector.drift_detected:
            lag = max(0, int(self.detector.width) - 1)
        return float(self.detector.estimation), lag


def detector_settings(method, parameters=None):
    """Validate and return scalar detector settings, with PM4Py defaults."""
    parameters = parameters or {}
    get = exec_utils.get_param_value
    if method == "page_hinkley":
        min_instances = get(Parameters.PH_MIN_INSTANCES, parameters, 10)
        delta = get(Parameters.PH_DELTA, parameters, 0.005)
        threshold = get(Parameters.PH_THRESHOLD, parameters, 5.0)
        direction = get(Parameters.PH_DIRECTION, parameters, "both")
        _positive_integer(min_instances, Parameters.PH_MIN_INSTANCES.value)
        if not isinstance(delta, Real) or not np.isfinite(delta) or delta < 0:
            raise ValueError("page_hinkley_delta must be finite and nonnegative")
        if (
            not isinstance(threshold, Real)
            or not np.isfinite(threshold)
            or threshold <= 0
        ):
            raise ValueError("page_hinkley_threshold must be positive and finite")
        if direction not in ("up", "down", "both"):
            raise ValueError("page_hinkley_direction must be 'up', 'down' or 'both'")
        return {
            "min_instances": min_instances,
            "delta": delta,
            "threshold": threshold,
            "direction": direction,
        }

    if method == "adwin":
        delta = get(Parameters.ADWIN_DELTA, parameters, 0.002)
        clock = get(Parameters.ADWIN_CLOCK, parameters, 1)
        min_window_length = get(Parameters.ADWIN_MIN_WINDOW_LENGTH, parameters, 5)
        grace_period = get(Parameters.ADWIN_GRACE_PERIOD, parameters, 10)
        if not isinstance(delta, Real) or not 0 < delta < 1:
            raise ValueError("adwin_delta must be between 0 and 1")
        _positive_integer(clock, Parameters.ADWIN_CLOCK.value)
        _positive_integer(min_window_length, Parameters.ADWIN_MIN_WINDOW_LENGTH.value)
        _positive_integer(grace_period, Parameters.ADWIN_GRACE_PERIOD.value)
        return {
            "delta": delta,
            "clock": clock,
            "min_window_length": min_window_length,
            "grace_period": grace_period,
        }

    raise ValueError("method must be 'page_hinkley' or 'adwin'")


def make_detector(method, parameters=None):
    """Create a scalar detector with ``update(value) -> (score, lag_or_none)``.

    On an alarm, the lag estimates the boundary relative to the latest value.
    Page–Hinkley's score is the cumulative evidence in the strongest enabled
    direction. ADWIN's score is its current estimated mean and its lag reflects
    the beginning of the retained adaptive window.
    """
    settings = detector_settings(method, parameters)
    detector = _PageHinkley if method == "page_hinkley" else _ADWIN
    return detector(**settings)
