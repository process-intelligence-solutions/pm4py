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
"""Retrospective Version Clustering on directly-follows similarity profiles.

The detector follows the three stages of Abarca Zúñiga et al. (2026),
https://doi.org/10.1007/978-3-032-28110-4_4.
"""

from enum import Enum

import numpy as np

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.algo.concept_drift._common import (
    DriftAlarm,
    DriftResult,
    VersionAssignment,
    WindowScore,
)
from pm4py.util import exec_utils


class Parameters(Enum):
    NUM_WINDOWS = "num_windows"
    MIN_CLUSTER_SIZE = "min_cluster_size"
    MEMBERSHIP_THRESHOLD = "membership_threshold"
    PENALTY = "penalty"
    MIN_SIZE = "min_size"
    GAMMA = "gamma"


def _soft_memberships(similarities, min_cluster_size):
    try:
        from hdbscan import HDBSCAN, all_points_membership_vectors
    except ImportError as exc:
        raise ImportError(
            "Version Clustering requires hdbscan. Install it with pip install 'pm4py[drift]'."
        ) from exc

    if len(similarities) < 2 * min_cluster_size:
        return np.zeros((len(similarities), 0))
    clusterer = HDBSCAN(min_cluster_size=min_cluster_size, prediction_data=True).fit(
        similarities
    )
    if np.all(clusterer.labels_ < 0):
        return np.zeros((len(similarities), 0))
    # Identical windows can give 0/0 in HDBSCAN's probability calculation.
    # Recover the fitted assignment and its strength only for those rows.
    with np.errstate(divide="ignore", invalid="ignore"):
        memberships = all_points_membership_vectors(clusterer)
    invalid = ~np.isfinite(memberships).all(axis=1)
    memberships[invalid] = 0.0
    assigned = np.flatnonzero(invalid & (clusterer.labels_ >= 0))
    memberships[assigned, clusterer.labels_[assigned]] = clusterer.probabilities_[
        assigned
    ]
    return np.clip(memberships, 0.0, 1.0)


def apply(log, parameters=None):
    """Identify recurring behavioral versions and the boundaries between them.

    Completed traces are sorted by first-event timestamp and partitioned into
    ``num_windows`` balanced contiguous blocks (default 100). In short logs
    there is at most one block per trace. HDBSCAN clusters the rows of the DFG
    cosine-similarity matrix. ``min_cluster_size`` defaults to 5. The most
    likely membership assigns a version unless its probability falls below
    ``membership_threshold`` (default 0.75). Version 0 marks unknown windows.

    Penalized RBF-kernel segmentation uses the unthresholded probability
    vectors. ``penalty`` defaults to 3, ``min_size`` to two windows, and
    ``gamma`` optionally fixes the RBF coefficient. Changing the membership
    threshold affects the assignments alone. There are no change points if
    no clusters are found. Change and assignment indices identify the first
    trace of a block in first-event order. Ties in start time are ordered by
    completion. Results use the entire log.
    """
    num_windows = _common.integer(
        exec_utils.get_param_value(Parameters.NUM_WINDOWS, parameters, 100),
        "num_windows",
    )
    min_cluster_size = _common.integer(
        exec_utils.get_param_value(Parameters.MIN_CLUSTER_SIZE, parameters, 5),
        "min_cluster_size",
        minimum=2,
    )
    membership_threshold = _common.real(
        exec_utils.get_param_value(Parameters.MEMBERSHIP_THRESHOLD, parameters, 0.75),
        "membership_threshold",
        maximum=1,
    )
    penalty = exec_utils.get_param_value(Parameters.PENALTY, parameters, 3.0)
    min_size = exec_utils.get_param_value(Parameters.MIN_SIZE, parameters, 2)
    gamma = exec_utils.get_param_value(Parameters.GAMMA, parameters, None)
    if gamma is not None:
        gamma = _common.real(gamma, "gamma")
    observations = sorted(
        _common.completed_traces(log, parameters), key=lambda trace: trace.start
    )
    windows = _common.window_partition(len(observations), num_windows)
    similarities = _common.dfg_window_similarities(observations, windows)
    probabilities = _soft_memberships(similarities, min_cluster_size)
    cost = _timeseries.segment_cost(
        probabilities, kernel=True if gamma is None else gamma
    )
    boundaries = _timeseries.pelt(probabilities, penalty, min_size, cost=cost)

    available_at = max((trace.end for trace in observations), default=None)
    versions = []
    scores = []
    for i, (start, stop) in enumerate(windows):
        row = probabilities[i]
        confidence = float(row.max()) if len(row) else 0.0
        label = (
            int(row.argmax()) + 1
            if confidence > 0 and confidence >= membership_threshold
            else 0
        )
        timestamp = observations[start].start
        details = {"probabilities": tuple(row.tolist()), "window_stop": stop}
        versions.append(VersionAssignment(start, label, timestamp, confidence, details))
        scores.append(
            WindowScore(
                index=start,
                score=float(np.linalg.norm(row - probabilities[i - 1])) if i else 0.0,
                timestamp=timestamp,
                available_at=available_at,
                details=details,
            )
        )

    changes = []
    for left, cut, right in zip(
        [0] + boundaries, boundaries, boundaries[1:] + [len(windows)]
    ):
        gain = cost(left, right) - cost(left, cut) - cost(cut, right)
        changes.append(
            DriftAlarm(
                index=versions[cut].index,
                timestamp=versions[cut].timestamp,
                available_at=available_at,
                score=float(gain),
                details={
                    "before_version": versions[cut - 1].label,
                    "after_version": versions[cut].label,
                },
            )
        )

    return DriftResult(
        observation_unit="trace",
        scores=scores,
        changes=changes,
        versions=versions,
        metadata={
            "method": "version_clustering",
            "mode": "retrospective",
            "trace_order": "start",
            "num_windows": num_windows,
            "actual_windows": len(windows),
            "min_cluster_size": min_cluster_size,
            "membership_threshold": membership_threshold,
            "penalty": penalty,
            "min_size": min_size,
            "gamma": gamma,
        },
    )
