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
"""Retrospective drift detection from windowed fitness and precision."""

from collections import Counter
from enum import Enum
from functools import lru_cache
from itertools import pairwise

import numpy as np

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.algo.concept_drift.result import DriftAlarm, DriftResult, WindowScore
from pm4py.algo.concept_drift.variants import conformance
from pm4py.algo.evaluation.precision import algorithm as precision
from pm4py.objects.log.obj import EventLog


class Parameters(Enum):
    WINDOW_SIZE = "window_size"
    STEP = "step"
    REFERENCE_SIZE = "reference_size"
    REFERENCE_MODEL = "reference_model"
    PENALTY = "penalty"
    MIN_SIZE = "min_size"


def apply(log, parameters=None):
    """Segment the fitness and precision profile of a fixed reference model.

    Supply a sound accepting Petri net as a ``reference_model`` tuple
    ``(net, initial_marking, final_marking)``, or discover one with Inductive
    Miner from the first ``reference_size`` completed traces. The default
    reference size is the ``window_size`` (30 traces), and its training
    traces are excluded from evaluation.

    Evaluate complete windows of ``window_size`` traces, spaced ``step``
    traces apart (default ``window_size``). Each profile contains the mean
    alignment fitness and the PM4Py alignment-automaton escaping-edge
    precision. The precision can decrease when a previously used path
    is absent from a window, even if the remaining traces fit the model.

    Joint PELT minimizes the squared deviations of both metrics within
    segments, plus ``penalty`` per change (default 0.1). ``min_size`` is
    the minimum segment length in evaluated windows (default 2). Score
    values are Euclidean distances between consecutive profiles. Scores
    become available after the last trace of their window. Each alarm
    points to the first trace of its new segment and becomes available
    at the end of the supplied log. Window overlap limits the resolution
    of estimated boundaries.

    This is inspired by CRIER (Gallego-Fontenla et al., 2025,
    https://doi.org/10.1145/3716169). It uses a fixed model, alignment
    metrics and joint segmentation in place of CRIER's model updates,
    directly-follows precision estimator and gradual change classification.
    """
    get = _common.parameter
    window_size = _common.integer(
        get(parameters, Parameters.WINDOW_SIZE, 30), "window_size"
    )
    step = _common.integer(get(parameters, Parameters.STEP, window_size), "step")
    if step > window_size:
        raise ValueError("step cannot be larger than window_size")
    reference_size = _common.integer(
        get(parameters, Parameters.REFERENCE_SIZE, window_size), "reference_size"
    )
    penalty = _common.real(get(parameters, Parameters.PENALTY, 0.1), "penalty")
    if penalty == 0:
        raise ValueError("penalty must be positive")
    min_size = _common.integer(get(parameters, Parameters.MIN_SIZE, 2), "min_size")

    model = conformance._reference_model(parameters)
    traces = _common.completed_traces(log, parameters)
    evaluation_start = reference_size if model is None else 0
    starts = range(evaluation_start, len(traces) - window_size + 1, step)
    result = DriftResult(
        "trace",
        metadata={
            "variant": "conformance_profile",
            "method": "pelt",
            "retrospective": True,
            "window_size": window_size,
            "step": step,
            "penalty": penalty,
            "min_size": min_size,
            "reference_model": model,
            "reference_size": evaluation_start,
        },
    )
    if not starts:
        return result

    if model is None:
        model = conformance._discover(traces[:evaluation_start])
        result.metadata["reference_model"] = model

    @lru_cache(maxsize=128)
    def precision_for_window(counts):
        event_log = EventLog(
            conformance._activity_trace(activities)
            for activities, count in counts
            for _ in range(count)
        )
        return precision.apply(
            event_log,
            *model,
            variant=precision.Variants.AUTOMATON_AFTER_ALIGN,
            parameters={"show_progress_bar": False},
        )

    fitness_cache = {}
    values = []
    for start in starts:
        stop = start + window_size
        counts = Counter(trace.activities for trace in traces[start:stop])
        precision_value = precision_for_window(frozenset(counts.items()))
        weighted_fitness = 0.0
        for activities, count in counts.items():
            if activities not in fitness_cache:
                fitness_cache[activities] = conformance._alignment_fitness(
                    activities, model
                )
            weighted_fitness += fitness_cache[activities] * count
        profile = np.array([weighted_fitness / window_size, precision_value])
        score = float(np.linalg.norm(profile - values[-1])) if values else 0.0
        values.append(profile)
        result.scores.append(
            WindowScore(
                index=start,
                score=score,
                timestamp=traces[start].end,
                available_at=traces[stop - 1].end,
                details={
                    "fitness": float(profile[0]),
                    "precision": float(profile[1]),
                    "window_stop": stop,
                },
            )
        )

    profiles = np.asarray(values)
    cost = _timeseries.segment_cost(profiles)
    cuts = _timeseries.pelt(profiles, penalty, min_size, cost=cost)
    segments = list(pairwise([0, *cuts, len(starts)]))
    for (left, cut), (_, right) in pairwise(segments):
        before = profiles[left:cut].mean(axis=0)
        after = profiles[cut:right].mean(axis=0)
        gain = cost(left, right) - cost(left, cut) - cost(cut, right)
        index = starts[cut]
        result.changes.append(
            DriftAlarm(
                index=index,
                timestamp=traces[index].end,
                available_at=traces[-1].end,
                score=float(gain),
                details={
                    "metric_deltas": {
                        "fitness": float(after[0] - before[0]),
                        "precision": float(after[1] - before[1]),
                    }
                },
            )
        )
    return result
