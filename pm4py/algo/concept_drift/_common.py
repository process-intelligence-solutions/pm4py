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
"""Observation construction, windows, and alarm handling for drift detectors."""

from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import groupby, pairwise
from numbers import Integral, Real

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift.result import (
    DriftAlarm,
    DriftInterval,
    DriftResult,
    VersionAssignment,
    WindowScore,
)
from pm4py.objects.log.obj import EventLog
from pm4py.util import constants, exec_utils, xes_constants

__all__ = [
    "DriftAlarm",
    "DriftInterval",
    "DriftResult",
    "VersionAssignment",
    "WindowScore",
]


@dataclass
class TraceObservation:
    """A completed case, with stable ordering of simultaneous events."""

    events: tuple[Mapping, ...]
    activities: tuple
    timestamps: tuple[pd.Timestamp, ...]
    attributes: Mapping

    @property
    def start(self):
        return self.timestamps[0]

    @property
    def end(self):
        return self.timestamps[-1]


def parameter(parameters, name, default):
    return exec_utils.get_param_value(name, parameters, default)


def attribute_key(parameters, name, default):
    return parameter(
        parameters, f"pm4py:param:{name}", parameter(parameters, name, default)
    )


def integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def real(value, name, minimum=0.0, maximum=np.inf):
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not np.isfinite(value)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be a finite number in [{minimum}, {maximum}]")
    return float(value)


def completed_traces(log, parameters=None) -> list[TraceObservation]:
    """Group and stably order cases by completion time and events by timestamp.

    Timestamps are normalized to UTC. Naive timestamps are interpreted as UTC.
    Empty legacy traces are skipped. DataFrame case attributes use the PM4Py
    ``case:`` prefix and the first chronological event's value.
    """
    activity = attribute_key(parameters, "activity_key", xes_constants.DEFAULT_NAME_KEY)
    timestamp = attribute_key(
        parameters, "timestamp_key", xes_constants.DEFAULT_TIMESTAMP_KEY
    )
    case_id = attribute_key(parameters, "case_id_key", constants.CASE_CONCEPT_NAME)
    observations = []
    if isinstance(log, pd.DataFrame):
        if log.empty:
            return observations
        missing = [
            column for column in (case_id, activity, timestamp) if column not in log
        ]
        if missing:
            raise ValueError(f"Missing event log columns: {missing}")
        if log[case_id].isna().any():
            raise ValueError(f"Case identifier {case_id!r} contains missing values")
        if log[activity].isna().any():
            raise ValueError(f"Activity {activity!r} contains missing values")
        case_columns = {
            column: column.removeprefix(constants.CASE_ATTRIBUTE_PREFIX)
            for column in log.columns
            if isinstance(column, str)
            and column.startswith(constants.CASE_ATTRIBUTE_PREFIX)
        }
        for identifier, events in log.groupby(case_id, sort=False, observed=True):
            observation = _observation(
                events.to_dict("records"), {}, activity, timestamp
            )
            attributes = {
                name: observation.events[0][column]
                for column, name in case_columns.items()
            }
            attributes.setdefault(xes_constants.DEFAULT_TRACEID_KEY, identifier)
            observation.attributes = attributes
            observations.append(observation)
    elif isinstance(log, EventLog):
        observations = [
            _observation(trace, trace.attributes, activity, timestamp)
            for trace in log
            if trace
        ]
    else:
        raise TypeError("Expected a pandas DataFrame or an EventLog")
    observations.sort(key=lambda trace: trace.end)
    return observations


def _observation(events, attributes, activity, timestamp):
    try:
        times = pd.to_datetime([event[timestamp] for event in events], utc=True)
        order = np.argsort(times, kind="stable")
        ordered_events = tuple(events[i] for i in order)
        activities = tuple(event[activity] for event in ordered_events)
    except KeyError as error:
        raise ValueError(f"Missing event attribute: {error.args[0]!r}") from error
    if times.isna().any() or any(
        pd.api.types.is_scalar(label) and pd.isna(label) for label in activities
    ):
        raise ValueError("Event timestamps and activities must be present")
    return TraceObservation(ordered_events, activities, tuple(times[order]), attributes)


def adjacent_windows(length: int, window_size: int, step: int = 1) -> Iterator:
    """Yield the start, boundary, and exclusive end of each full window pair."""
    window_size = integer(window_size, "window_size")
    step = integer(step, "step")
    for boundary in range(window_size, length - window_size + 1, step):
        yield boundary - window_size, boundary, boundary + window_size


def window_partition(length: int, num_windows: int) -> list[tuple[int, int]]:
    """Partition observations into up to num_windows nearly equal windows."""
    count = min(length, integer(num_windows, "num_windows"))
    if count == 0:
        return []
    size, remainder = divmod(length, count)
    starts = [i * size + min(i, remainder) for i in range(count + 1)]
    return list(pairwise(starts))


def directly_follows(activities: Sequence) -> Counter:
    """Count consecutive pairs in one projected trace."""
    return Counter(pairwise(activities))


def standardize(values):
    """Center and scale numeric columns without squaring extreme raw values."""
    if not len(values):
        return values
    magnitudes = np.abs(values).max(axis=0)
    scaled = values / np.where(magnitudes > 0, magnitudes, 1)
    deviations = scaled.std(axis=0)
    return (scaled - scaled.mean(axis=0)) / np.where(deviations > 0, deviations, 1)


def count_vectors(counts: Sequence[Mapping]) -> tuple[list, np.ndarray]:
    """Align count vectors by key in order of first appearance."""
    keys = list(dict.fromkeys(key for row in counts for key in row))
    matrix = np.zeros((len(counts), len(keys)))
    positions = {key: i for i, key in enumerate(keys)}
    for i, row in enumerate(counts):
        for key, value in row.items():
            matrix[i, positions[key]] = value
    return keys, matrix


def cosine_similarity(counts: Sequence[Mapping]) -> np.ndarray:
    """Compare count vectors, treating two empty vectors as identical."""
    _, matrix = count_vectors(counts)
    norms = np.linalg.norm(matrix, axis=1)
    normalized = np.divide(
        matrix, norms[:, None], out=np.zeros_like(matrix), where=norms[:, None] > 0
    )
    similarity = np.clip(normalized @ normalized.T, 0, 1)
    empty = np.flatnonzero(norms == 0)
    similarity[np.ix_(empty, empty)] = 1
    np.fill_diagonal(similarity, 1)
    return similarity


def dfg_window_similarities(traces, windows):
    """Build a cosine-similarity matrix for contiguous trace windows."""
    counts = []
    for start, stop in windows:
        edges = Counter()
        for trace in traces[start:stop]:
            edges.update(directly_follows(trace.activities))
        counts.append(edges)
    return cosine_similarity(counts)


def consolidate(
    scores: Iterable[WindowScore],
    is_signal: Callable[[WindowScore], bool],
    persistence: int = 1,
    min_separation: int = 0,
    retrospective: bool = False,
) -> list[DriftAlarm]:
    """Combine consecutive positive scores and enforce minimum separation.

    A sequential alarm keeps the initial boundary and uses the confirmation
    time. Retrospective consolidation selects the smallest p-value, then
    largest score, per run and ensures the strongest nearby alarms survive.
    """
    persistence = integer(persistence, "persistence")
    min_separation = integer(min_separation, "min_separation", minimum=0)
    alarms = []
    candidates = []
    for positive, group in groupby(scores, key=is_signal):
        if not positive:
            continue
        run = list(group)
        if len(run) < persistence:
            continue
        if retrospective:
            candidates.append(min(run, key=_strength))
        elif not alarms or run[0].index - alarms[-1].index >= min_separation:
            alarms.append(_alarm(run[0], run[persistence - 1].available_at))
    if retrospective:
        for candidate in sorted(candidates, key=_strength):
            if all(
                abs(candidate.index - alarm.index) >= min_separation for alarm in alarms
            ):
                alarms.append(_alarm(candidate, candidate.available_at))
        alarms.sort(key=lambda alarm: alarm.index)
    return alarms


def _strength(score):
    significance = score.p_value if score.p_value is not None else 1
    return significance, -score.score, score.index


def _alarm(score, available_at):
    return DriftAlarm(
        score.index,
        score.timestamp,
        available_at,
        score.score,
        score.p_value,
        score.details,
    )
