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
"""Chi-square monitoring of partially ordered execution runs.

This variant follows the run representation and sliding-window test of
Maaradji, Dumas, La Rosa, and Ostovar, with bounded adaptive windows and an
optional retrospective mixture check (https://doi.org/10.1109/TKDE.2017.2720601).
"""

from collections import Counter
from enum import Enum
from functools import lru_cache
from itertools import pairwise

import networkx as nx
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import chi2, chi2_contingency

from pm4py.algo.concept_drift import _common


class Parameters(Enum):
    WINDOW_SIZE = "window_size"
    STEP = "step"
    ALPHA = "alpha"
    PERSISTENCE = "persistence"
    MIN_SEPARATION = "min_separation"
    ADAPTIVE = "adaptive"
    MIN_WINDOW_SIZE = "min_window_size"
    MAX_WINDOW_SIZE = "max_window_size"
    GRADUAL = "gradual"


def _concurrency(relations):
    return frozenset((a, b) for a, b in relations if a != b and (b, a) in relations)


def _run(activities, concurrent):
    # Within a run, occurrences of the same activity always keep their order.
    counts = Counter()
    occurrences = []
    for activity in activities:
        counts[activity] += 1
        occurrences.append((activity, counts[activity]))

    order = nx.DiGraph()
    order.add_nodes_from(occurrences)
    for position, first in enumerate(occurrences):
        for second in occurrences[position + 1 :]:
            if (first[0], second[0]) not in concurrent:
                order.add_edge(first, second)
    return frozenset(occurrences), frozenset(nx.transitive_reduction(order).edges)


def _histogram(variants, relations, run_descriptor):
    concurrent = _concurrency(relations)
    histogram = Counter()
    for variant, count in variants.items():
        activities = set(variant)
        relevant = frozenset(
            (a, b) for a, b in concurrent if a in activities and b in activities
        )
        histogram[run_descriptor(variant, relevant)] += count
    return histogram


def _window_histogram(traces, relations, run_descriptor):
    pairs = set().union(*relations)
    return _histogram(Counter(traces), pairs, run_descriptor)


def _mixture(before, during, after, alpha):
    """Fit a convex mixture and compare it with the observed middle interval."""
    _, counts = _common.count_vectors((before, during, after))
    reference, observed, replacement = counts
    if np.any((observed > 0) & (reference + replacement == 0)):
        return None
    reference /= reference.sum()
    replacement /= replacement.sum()
    if np.allclose(reference, replacement):
        return None

    def loss(weight):
        expected = observed.sum() * ((1 - weight) * reference + weight * replacement)
        positive = expected > 0
        if np.any((observed > 0) & ~positive):
            return np.inf
        return np.sum(
            (observed[positive] - expected[positive]) ** 2 / expected[positive]
        )

    fit = minimize_scalar(loss, bounds=(0, 1), method="bounded")
    if not fit.success:
        return None
    weight = float(fit.x)
    critical = chi2.isf(alpha, len(observed) - 1)
    if loss(0) <= critical or loss(1) <= critical or fit.fun > critical:
        return None
    return {"later_weight": weight, "pearson_statistic": float(fit.fun)}


def apply(log, parameters=None):
    """Detect shifts in the distribution of completed execution runs.

    Each window independently infers alpha concurrency from directly-follows
    edges observed in both directions. Linearizations of the same labeled
    partial order share a run. A Pearson chi-square test compares adjacent
    run histograms. Sparse expected counts are reported in score details.

    ``window_size`` defaults to 50 traces and ``step`` defaults to 1. Alarms
    require ``persistence`` consecutive p-values below ``alpha`` (default
    0.05). Persistence defaults to a third of the initial window size,
    rounded down to a minimum of one test. ``min_separation`` is measured in
    traces (default 0).

    Set ``adaptive=True`` to adjust the window width in proportion to changes
    in the number of distinct runs, within ``min_window_size`` and
    ``max_window_size`` (defaults half and four times the initial width).
    Adaptive scores follow the order of confirmation and their estimated
    boundaries can move backwards when windows grow.

    Set ``gradual=True`` to retrospectively label intervals between adjacent
    alarms whose run distribution is compatible at the nominal Pearson
    cutoff with a mixture of its neighbors. Both single-regime fits must be
    rejected. The interval check uses the complete log and reports a fit
    statistic rather than a calibrated p-value.
    """
    initial = _common.integer(
        _common.parameter(parameters, Parameters.WINDOW_SIZE, 50), "window_size"
    )
    step = _common.integer(_common.parameter(parameters, Parameters.STEP, 1), "step")
    alpha = _common.real(
        _common.parameter(parameters, Parameters.ALPHA, 0.05), "alpha", 0, 1
    )
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    persistence = _common.integer(
        _common.parameter(parameters, Parameters.PERSISTENCE, max(1, initial // 3)),
        "persistence",
    )
    separation = _common.integer(
        _common.parameter(parameters, Parameters.MIN_SEPARATION, 0),
        "min_separation",
        minimum=0,
    )
    adaptive = _common.parameter(parameters, Parameters.ADAPTIVE, False)
    gradual = _common.parameter(parameters, Parameters.GRADUAL, False)
    if not isinstance(adaptive, bool) or not isinstance(gradual, bool):
        raise TypeError("adaptive and gradual must be booleans")
    minimum = _common.integer(
        _common.parameter(parameters, Parameters.MIN_WINDOW_SIZE, max(1, initial // 2)),
        "min_window_size",
    )
    maximum = _common.integer(
        _common.parameter(parameters, Parameters.MAX_WINDOW_SIZE, initial * 4),
        "max_window_size",
    )
    if not minimum <= initial <= maximum:
        raise ValueError(
            "window_size must be between min_window_size and max_window_size"
        )

    observations = _common.completed_traces(log, parameters)
    traces = [trace.activities for trace in observations]
    relations = [set(_common.directly_follows(trace)) for trace in traces]
    run_descriptor = lru_cache(maxsize=8192)(_run)
    scores = []

    def histogram(start, stop):
        return _window_histogram(
            traces[start:stop], relations[start:stop], run_descriptor
        )

    width = initial
    previous_diversity = None
    for stop in range(2 * initial, len(traces) + 1, step):
        boundary = stop - width
        left = histogram(boundary - width, boundary)
        right = histogram(boundary, stop)
        diversity = len(left.keys() | right.keys())
        if adaptive and previous_diversity is not None:
            target = round(width * diversity / previous_diversity)
            target = min(maximum, stop // 2, max(minimum, target))
            if target != width:
                width = target
                boundary = stop - width
                left = histogram(boundary - width, boundary)
                right = histogram(boundary, stop)
                diversity = len(left.keys() | right.keys())
        previous_diversity = diversity

        _, table = _common.count_vectors((left, right))
        statistic, p_value, _, expected = chi2_contingency(table, correction=False)
        scores.append(
            _common.WindowScore(
                boundary,
                float(statistic),
                observations[boundary].end,
                observations[stop - 1].end,
                p_value=float(p_value),
                details={
                    "window_size": width,
                    "distinct_runs": diversity,
                    "fraction_expected_below_five": float(np.mean(expected < 5)),
                },
            )
        )

    changes = _common.consolidate(
        scores,
        lambda sample: sample.p_value < alpha,
        persistence=persistence,
        min_separation=max(1, separation),
    )
    intervals = []
    if gradual and len(changes) >= 2:
        boundaries = [0] + [alarm.index for alarm in changes] + [len(traces)]
        segments = [histogram(a, b) for a, b in pairwise(boundaries)]
        for index, (before, during, after) in enumerate(
            zip(segments, segments[1:], segments[2:]), start=1
        ):
            details = _mixture(before, during, after, alpha)
            if details is not None:
                start, stop = boundaries[index : index + 2]
                intervals.append(
                    _common.DriftInterval(
                        start,
                        stop - 1,
                        observations[start].end,
                        observations[stop - 1].end,
                        observations[-1].end,
                        details=details,
                    )
                )
    return _common.DriftResult(
        observation_unit="trace",
        scores=scores,
        changes=changes,
        intervals=intervals,
        metadata={
            "representation": "partially ordered runs with window-local alpha concurrency",
            "mode": "sequential with retrospective intervals"
            if gradual
            else "sequential",
            "window_size": initial,
            "step": step,
            "alpha": alpha,
            "persistence": persistence,
            "min_separation": separation,
            "adaptive": adaptive,
            "min_window_size": minimum,
            "max_window_size": maximum,
            "gradual": gradual,
        },
    )
