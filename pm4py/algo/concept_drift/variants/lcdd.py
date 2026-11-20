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
"""Structural drift detection using the fixed-window form of LCDD.

Based on Lin et al., *LCDD: Detecting Business Process Drifts Based on
Local Completeness* (https://doi.org/10.1109/TSC.2020.3032787).
"""

from enum import Enum

from pm4py.algo.concept_drift import _common
from pm4py.util import exec_utils


class Parameters(Enum):
    COMPLETE_WINDOW_SIZE = "complete_window_size"
    DETECTION_WINDOW_SIZE = "detection_window_size"
    STABLE_PERIOD = "stable_period"
    MIN_DISAPPEARED = "min_disappeared"


def _localize_disappearance(last_seen, boundary, stop, stable_period, minimum):
    """Consolidate nearby groups of stable disappearances within the window."""
    disappeared = {edge for edge, index in last_seen.items() if index < boundary}
    candidates = {}
    for edge, index in last_seen.items():
        if index >= boundary:
            candidates.setdefault(index + 1, set()).add(edge)

    newly_missing = set()
    for index, edges in sorted(candidates.items()):
        if index >= stop or index - boundary > stable_period:
            break
        newly_missing.update(edges)
        if len(newly_missing) >= minimum:
            boundary = index
            disappeared.update(newly_missing)
            newly_missing.clear()
    return boundary, disappeared


def apply(log, parameters=None):
    """Find additions and stable disappearances of directly-follows relations.

    The first ``complete_window_size`` traces (default 200) of each regime
    are assumed locally complete. An unseen relation is reported immediately.
    A disappearance requires at least ``min_disappeared`` relations (default
    2) absent from a full ``detection_window_size`` window (default 200).
    ``stable_period`` (default 10) groups nearby disappearances inside that
    window and can move the estimated boundary towards the later ones.

    After an alarm the reference is forgotten and rebuilt from the estimated
    boundary. Availability is the completion time at confirmation, including
    the preceding alarm if the reference is being rebuilt from older traces.
    Scores count added relations and, once the detection window is full,
    absent reference relations. They are indexed by the trace inspected.
    """
    parameters = parameters or {}
    settings = {}
    for key, default in (
        (Parameters.COMPLETE_WINDOW_SIZE, 200),
        (Parameters.DETECTION_WINDOW_SIZE, 200),
        (Parameters.STABLE_PERIOD, 10),
        (Parameters.MIN_DISAPPEARED, 2),
    ):
        settings[key.value] = _common.integer(
            exec_utils.get_param_value(key, parameters, default), key.value
        )

    reference_size = settings["complete_window_size"]
    detection_size = settings["detection_window_size"]
    stable_period = settings["stable_period"]
    minimum = settings["min_disappeared"]

    observations = _common.completed_traces(log, parameters)
    relations = [
        set(_common.directly_follows(trace.activities)) for trace in observations
    ]
    result = _common.DriftResult(
        observation_unit="trace",
        scores=[],
        changes=[],
        metadata={
            **settings,
            "representation": "directly-follows relation support",
            "reference_update": "rebuild from the estimated boundary",
            "mode": "sequential",
        },
    )

    regime_start = 0
    last_confirmation = 0
    while regime_start + reference_size < len(relations):
        detection_start = regime_start + reference_size
        last_seen = {
            edge: index
            for index in range(regime_start, detection_start)
            for edge in relations[index]
        }
        for index in range(detection_start, len(relations)):
            added = relations[index].difference(last_seen)
            for edge in relations[index].intersection(last_seen):
                last_seen[edge] = index

            boundary = index
            left = index + 1 - detection_size
            missing = (
                {edge for edge, last in last_seen.items() if last < left}
                if left >= detection_start
                else set()
            )
            if not added and len(missing) >= minimum:
                boundary, missing = _localize_disappearance(
                    last_seen, left, index + 1, stable_period, minimum
                )

            details = {"added": frozenset(added), "missing": frozenset(missing)}
            score = float(len(added) + len(missing))
            timestamp = observations[index].end
            if not result.scores or index > result.scores[-1].index:
                result.scores.append(
                    _common.WindowScore(
                        index, score, timestamp, timestamp, details=details
                    )
                )
            if added or len(missing) >= minimum:
                last_confirmation = max(last_confirmation, index)
                result.changes.append(
                    _common.DriftAlarm(
                        boundary,
                        timestamp=observations[boundary].end,
                        available_at=observations[last_confirmation].end,
                        score=score,
                        details=details,
                    )
                )
                regime_start = boundary
                break
        else:
            break

    return result
