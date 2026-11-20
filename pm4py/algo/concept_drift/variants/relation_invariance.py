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
"""Retrospective structural drift detection from invariant activity relations.

This adaptation of Zheng, Wen, and Wang's RINV method groups candidate
boundaries of invariant relation periods. See
https://doi.org/10.1007/978-3-319-69462-7_33.
"""

from bisect import bisect_left
from collections import defaultdict
from enum import Enum

from pm4py.algo.concept_drift import _common
from pm4py.algo.concept_drift.variants.bose import compute_follows_relation


class Parameters(Enum):
    MIN_STABLE_TRACES = "min_stable_traces"
    RADIUS = "radius"
    MIN_SEPARATION = "min_separation"
    RELATION_TYPE = "relation_type"


def _relations(activities, relation_type):
    if relation_type != "eventually_follows":
        yield from (
            ("directly_follows", *pair) for pair in _common.directly_follows(activities)
        )
    if relation_type != "directly_follows":
        yield from (
            ("eventually_follows", *pair)
            for pair in compute_follows_relation(activities, set(activities))
        )


def _presence_runs(occurrences):
    if not occurrences:
        return
    start = stop = occurrences[0]
    for index in occurrences:
        if index > stop:
            yield start, stop
            start = index
        stop = index + 1
    yield start, stop


def _stable_boundaries(occurrences, length, minimum):
    """Compute edges of stable presence and absence runs from sparse positions."""
    boundaries = set()
    previous_stop = 0
    for start, stop in _presence_runs(occurrences):
        if start - previous_stop >= minimum:
            boundaries.update((previous_stop, start))
        if stop - start >= minimum:
            boundaries.update((start, stop))
        previous_stop = stop
    if length - previous_stop >= minimum:
        boundaries.add(previous_stop)
    boundaries.discard(0)
    boundaries.discard(length)
    return boundaries


def _clusters(candidates, radius):
    """Yield one-dimensional DBSCAN clusters with minimum density one."""
    cluster = []
    for index in sorted(candidates):
        if cluster and index - cluster[-1] > radius:
            yield cluster
            cluster = []
        cluster.append(index)
    if cluster:
        yield cluster


def _rank_clusters(candidates, radius, length, separation):
    ranked = []
    for indices in _clusters(candidates, radius):
        votes = sum(len(candidates[index]) for index in indices)
        weighted_index = sum(index * len(candidates[index]) for index in indices)
        # Round the weighted centroid to the nearest trace, with half ties up.
        center = (2 * weighted_index + votes) // (2 * votes)
        ranked.append((votes, center, indices))
    kept = [0, length]
    for votes, center, indices in sorted(ranked, key=lambda item: (-item[0], item[1])):
        slot = bisect_left(kept, center)
        if min(center - kept[slot - 1], kept[slot] - center) >= separation:
            kept.insert(slot, center)
            yield center, votes, indices


def _present(occurrences, index):
    position = bisect_left(occurrences, index)
    return position < len(occurrences) and occurrences[position] == index


def apply(log, parameters=None):
    """Find clustered changes in directly- and eventually-follows relations.

    A trace contributes a Boolean value for each relation. A run of at
    least ``min_stable_traces`` consecutive cases (default 100) with constant
    presence or absence contributes its interior edges as candidates.
    Set ``relation_type`` to ``"both"`` (default), ``"directly_follows"``, or
    ``"eventually_follows"``. Eventually-follows includes adjacent activities.

    Candidate boundaries separated by at most ``radius`` traces (default 10)
    belong to the same cluster. Each relation votes at most once per
    boundary. The rounded vote-weighted centroid estimates the change point.
    In decreasing order of votes, retain changes with at least
    ``min_separation`` traces (default ``min_stable_traces``) between them and
    the other retained changes or either log boundary.

    Zero-based indices follow case start order, with ties ordered by
    completion time and then input case order. Both the scores and alarms
    use the full log and become available at its latest case completion.
    Each boundary score is its raw vote count. An alarm records the total
    votes and the net appearance or disappearance of supporting relations
    from just before its first candidate through its last candidate.
    """
    get = _common.parameter
    minimum = _common.integer(
        get(parameters, Parameters.MIN_STABLE_TRACES, 100), "min_stable_traces"
    )
    radius = _common.integer(
        get(parameters, Parameters.RADIUS, 10), "radius", minimum=0
    )
    separation = _common.integer(
        get(parameters, Parameters.MIN_SEPARATION, minimum), "min_separation"
    )
    relation_type = get(parameters, Parameters.RELATION_TYPE, "both")
    if relation_type not in ("both", "directly_follows", "eventually_follows"):
        raise ValueError(
            "relation_type must be 'both', 'directly_follows', or 'eventually_follows'"
        )

    traces = _common.completed_traces(log, parameters)
    available_at = traces[-1].end if traces else None
    traces.sort(key=lambda trace: trace.start)
    length = len(traces)
    positions = defaultdict(list)
    for index, trace in enumerate(traces):
        for relation in _relations(trace.activities, relation_type):
            positions[relation].append(index)

    candidates = defaultdict(set)
    for relation, occurrences in positions.items():
        for index in _stable_boundaries(occurrences, length, minimum):
            candidates[index].add(relation)

    scores = []
    for index in range(1, length):
        supporting = frozenset(candidates.get(index, ()))
        scores.append(
            _common.WindowScore(
                index,
                float(len(supporting)),
                traces[index].start,
                available_at,
                details={"supporting_relations": supporting},
            )
        )
    changes = []
    for center, votes, indices in _rank_clusters(
        candidates, radius, length, separation
    ):
        supporting = set().union(*(candidates[index] for index in indices))
        appeared = set()
        disappeared = set()
        for relation in supporting:
            previously = _present(positions[relation], indices[0] - 1)
            now = _present(positions[relation], indices[-1])
            if previously != now:
                (appeared if now else disappeared).add(relation)
        changes.append(
            _common.DriftAlarm(
                center,
                traces[center].start,
                available_at,
                float(votes),
                details={
                    "candidates": tuple(indices),
                    "supporting_relations": frozenset(supporting),
                    "appeared": frozenset(appeared),
                    "disappeared": frozenset(disappeared),
                },
            )
        )

    return _common.DriftResult(
        "trace",
        scores=scores,
        changes=sorted(changes, key=lambda change: change.index),
        metadata={
            "mode": "retrospective",
            "trace_order": "start",
            "relation_type": relation_type,
            "min_stable_traces": minimum,
            "radius": radius,
            "min_separation": separation,
        },
    )
