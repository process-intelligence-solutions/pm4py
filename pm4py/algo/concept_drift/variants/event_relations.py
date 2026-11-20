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
"""Event-level alpha-plus relation monitoring inspired by Ostovar et al."""

from collections import Counter, defaultdict, deque
from itertools import combinations, islice
from math import ceil

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from pm4py.algo.concept_drift import _common, _statistics
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.util import constants, xes_constants


def apply(log, parameters=None):
    """Replay a DataFrame, EventLog, or EventStream in event timestamp order.

    The detector uses adjacent windows of events, including events of
    unfinished cases. See :class:`EventStreamDetector` for the settings and
    incremental use. Events with equal timestamps retain input order.
    An EventLog uses its trace identities as the case identifiers.
    """
    detector = EventStreamDetector(parameters)
    events = sorted(_observations(log, detector.keys), key=lambda event: event[2])
    result = _common.DriftResult("event", metadata=detector.metadata)
    for event in events:
        score, alarm = detector._observe(event)
        if score is not None:
            result.scores.append(score)
        if alarm is not None:
            result.changes.append(alarm)
    return result


class EventStreamDetector:
    """Monitor alpha-plus relations across adjacent windows of ordered events.

    ``window_size`` is the initial width in events on each side (default 100).
    By default, ``adaptive=True`` uses five times the square of the largest
    number of activity labels in either current window as the next width.
    The width is bounded by the available history, ``min_window_size``
    (default half the initial width), and ``max_window_size`` (default four
    times the initial width). Fixed windows use ``adaptive=False``.
    ``step`` defaults to one new event per test.

    Groups of events from the same case within each window supply the
    relations. Counts include one- and two-step loops, causality, parallelism
    and, by default, conflict. Set ``include_conflicts=False`` to omit the
    conflict features. The score is Jensen–Shannon distance and p-values
    come from an asymptotic G-test. The fraction of expected counts below
    five is reported for judging sparsity.

    A positive test has p <= ``alpha`` (default 0.05), and a nonzero score
    of at least ``min_effect`` (default 0). The same run of positive tests
    must persist for ``persistence`` evaluations. Its default corresponds
    to about half the first positive window width in events.
    ``min_separation`` sets the minimum distance between alarms in events
    (default 1). An alarm is located at the event that produced the first
    positive test and is available at the confirming event. Its details
    include the boundary between the two windows of the first positive test.

    Call :meth:`update` with one event mapping at a time. The monitor stores
    at most twice the maximum window size in observed events.
    """

    def __init__(self, parameters=None):
        get = _common.parameter
        size = _common.integer(get(parameters, "window_size", 100), "window_size")
        adaptive = get(parameters, "adaptive", True)
        conflicts = get(parameters, "include_conflicts", True)
        if not isinstance(adaptive, bool) or not isinstance(conflicts, bool):
            raise TypeError("adaptive and include_conflicts must be booleans")
        minimum = _common.integer(
            get(parameters, "min_window_size", max(1, size // 2)), "min_window_size"
        )
        maximum = _common.integer(
            get(parameters, "max_window_size", size * 4), "max_window_size"
        )
        if not minimum <= size <= maximum:
            raise ValueError(
                "window_size must be between min_window_size and max_window_size"
            )
        persistence = get(parameters, "persistence", None)
        if persistence is not None:
            persistence = _common.integer(persistence, "persistence")
        self.metadata = {
            "method": "event_relations",
            "mode": "sequential",
            "representation": "alpha_plus_event_relations",
            "window_size": size,
            "adaptive": adaptive,
            "min_window_size": minimum if adaptive else size,
            "max_window_size": maximum if adaptive else size,
            "include_conflicts": conflicts,
            "step": _common.integer(get(parameters, "step", 1), "step"),
            "alpha": _common.real(get(parameters, "alpha", 0.05), "alpha", maximum=1),
            "min_effect": _common.real(
                get(parameters, "min_effect", 0), "min_effect", maximum=1
            ),
            "min_separation": _common.integer(
                get(parameters, "min_separation", 1), "min_separation", minimum=0
            ),
            "persistence": persistence,
        }
        self.keys = (
            _common.attribute_key(
                parameters, "case_id_key", constants.CASE_CONCEPT_NAME
            ),
            _common.attribute_key(
                parameters, "activity_key", xes_constants.DEFAULT_NAME_KEY
            ),
            _common.attribute_key(
                parameters, "timestamp_key", xes_constants.DEFAULT_TIMESTAMP_KEY
            ),
        )
        self._buffer = deque(maxlen=2 * self.metadata["max_window_size"])
        self._width = size
        self._seen = 0
        self._positive = None
        self._count = 0
        self._last_change = -1

    def update(self, event):
        """Return a pair of optional score and alarm for the latest event.

        Supply case ID, activity, and timestamp using the configured keys.
        Events must arrive in nondecreasing timestamp order.
        """
        return self._observe(_read_event(event, self.keys))

    def _windows(self):
        width = self._width
        start = len(self._buffer) - 2 * width
        left = list(islice(self._buffer, start, start + width))
        right = list(islice(self._buffer, start + width, None))
        return left, right

    def _observe(self, event):
        settings = self.metadata
        timestamp = event[2]
        if self._buffer and timestamp < self._buffer[-1][2]:
            raise ValueError("Stream events must be supplied in timestamp order")
        self._buffer.append(event)
        self._seen += 1
        offset = self._seen - 2 * settings["window_size"]
        if offset < 0 or offset % settings["step"]:
            return None, None

        left, right = self._windows()
        if settings["adaptive"]:
            labels = max(len({event[1] for event in side}) for side in (left, right))
            target = min(
                len(self._buffer) // 2,
                settings["max_window_size"],
                max(settings["min_window_size"], 5 * labels**2),
            )
            if target != self._width:
                self._width = target
                left, right = self._windows()
        width = self._width
        relations, table = _common.count_vectors(
            [
                _relation_counts(side, settings["include_conflicts"])
                for side in (left, right)
            ]
        )
        distance = _statistics.frequency_distance(*table)
        p_value = None
        statistic = None
        sparse = None
        if table.shape[1] and table.sum(axis=1).all():
            test = chi2_contingency(table, correction=False, lambda_="log-likelihood")
            statistic, p_value = float(test.statistic), float(test.pvalue)
            sparse = float(np.mean(test.expected_freq < 5))

        score = _common.WindowScore(
            self._seen - width,
            distance,
            right[0][2],
            timestamp,
            p_value=p_value,
            details={
                "window_size": width,
                "test_event_index": self._seen - 1,
                "g_statistic": statistic,
                "fraction_expected_below_five": sparse,
                "changed_relations": _statistics.changed_proportions(relations, table),
            },
        )
        return score, self._confirm(score)

    def _confirm(self, score):
        settings = self.metadata
        positive = (
            score.p_value is not None
            and score.p_value <= settings["alpha"]
            and 0 < score.score >= settings["min_effect"]
        )
        if not positive:
            self._positive = None
            self._count = 0
            return None
        if self._positive is None:
            self._positive = score
        self._count += 1
        first = self._positive
        required = settings["persistence"] or ceil(
            first.details["window_size"] / (2 * settings["step"])
        )
        if self._count != required:
            return None
        index = first.details["test_event_index"]
        if (
            self._last_change >= 0
            and index - self._last_change < settings["min_separation"]
        ):
            return None
        self._last_change = index
        return _common.DriftAlarm(
            index,
            first.available_at,
            score.available_at,
            first.score,
            first.p_value,
            {
                **first.details,
                "window_boundary_index": first.index,
                "window_boundary_timestamp": first.timestamp,
                "confirmed_at_index": score.details["test_event_index"],
                "persistence": required,
            },
        )


def _read_event(event, keys):
    try:
        case, activity, timestamp = (event[key] for key in keys)
    except KeyError as error:
        raise ValueError(f"Missing event attribute {error.args[0]!r}") from error
    return _prepare_event(case, activity, timestamp)


def _prepare_event(case, activity, timestamp):
    timestamp = pd.to_datetime(timestamp, utc=True)
    if timestamp is None or timestamp is pd.NaT:
        raise ValueError("Event timestamps must be present")
    if not isinstance(timestamp, pd.Timestamp):
        raise TypeError("Event timestamps must be scalar")
    for value in (case, activity):
        if pd.api.types.is_scalar(value) and pd.isna(value):
            raise ValueError("Event case identifiers and activities must be present")
        hash(value)
    return case, activity, timestamp


def _observations(log, keys):
    if isinstance(log, pd.DataFrame):
        if log.empty:
            return
        missing = [key for key in keys if key not in log]
        if missing:
            raise ValueError(f"Missing event log columns: {missing}")
        for row in log.loc[:, list(keys)].itertuples(index=False, name=None):
            yield _prepare_event(*row)
    elif isinstance(log, EventLog):
        _, activity_key, time_key = keys
        for case, trace in enumerate(log):
            for event in trace:
                try:
                    values = event[activity_key], event[time_key]
                except KeyError as error:
                    raise ValueError(
                        f"Missing event attribute {error.args[0]!r}"
                    ) from error
                yield _prepare_event(case, *values)
    elif isinstance(log, EventStream):
        yield from (_read_event(event, keys) for event in log)
    else:
        raise TypeError("Expected a pandas DataFrame, EventLog, or EventStream")


def _relation_counts(events, include_conflicts):
    cases = defaultdict(list)
    activity_counts = Counter()
    for case, activity, _ in events:
        cases[case].append(activity)
        activity_counts[activity] += 1
    frequencies = Counter()
    loops = Counter()
    for activities in cases.values():
        frequencies.update(_common.directly_follows(activities))
        loops.update(
            (a, b)
            for a, b, c in zip(activities, activities[1:], activities[2:])
            if a == c and a != b
        )
    relations = Counter({("loop_two", edge): count for edge, count in loops.items()})
    for (a, b), count in frequencies.items():
        if a == b:
            relations["loop_one", a] = count
            continue
        reverse = frequencies[b, a]
        if not reverse or (loops[a, b] and loops[b, a]):
            relations["causal", (a, b)] = count
        else:
            relations["parallel", frozenset((a, b))] = min(count, reverse)
    if include_conflicts:
        for a, b in combinations(activity_counts, 2):
            if (a, b) not in frequencies and (b, a) not in frequencies:
                relations["conflict", frozenset((a, b))] = (
                    activity_counts[a] + activity_counts[b]
                )
    return relations
