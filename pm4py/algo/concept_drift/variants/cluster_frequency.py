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
"""Monitor populations of trace clusters fitted on an initial reference period."""

from collections import Counter

import numpy as np

from pm4py.algo.concept_drift import _common, _statistics
from pm4py.util import ml_utils


def _trace_profile(activities):
    edges = _common.directly_follows(activities)
    profile = {
        ("activity", activity): count / len(activities)
        for activity, count in Counter(activities).items()
    }
    profile.update(
        {
            ("directly_follows", source, target): count / (len(activities) - 1)
            for (source, target), count in edges.items()
        }
    )
    return profile


def _kmeans_input(matrix):
    # K-means requires 32-bit CSR indices even when the encoder returns int64.
    if max(*matrix.shape, matrix.nnz) <= np.iinfo(np.int32).max:
        matrix.indices = matrix.indices.astype(np.int32, copy=False)
        matrix.indptr = matrix.indptr.astype(np.int32, copy=False)
    return matrix


def _classify(observations, training_size, n_clusters, seed, outlier_distance):
    try:
        from sklearn.feature_extraction import DictVectorizer
    except ModuleNotFoundError as exc:
        if exc.name != "sklearn":
            raise
        raise ImportError(
            "Cluster frequency monitoring requires scikit-learn. Install pm4py[ml]."
        ) from exc

    training = [
        _trace_profile(trace.activities) for trace in observations[:training_size]
    ]
    n_distinct = len({frozenset(profile.items()) for profile in training})
    clusters = min(n_clusters, n_distinct)
    encoder = DictVectorizer(sort=False)
    model = ml_utils.KMeans(n_clusters=clusters, random_state=seed, n_init=10).fit(
        _kmeans_input(encoder.fit_transform(training))
    )
    monitoring = [
        _trace_profile(trace.activities) for trace in observations[training_size:]
    ]
    distances = model.transform(_kmeans_input(encoder.transform(monitoring)))
    closest = distances.argmin(axis=1)
    versions = []
    for offset, (profile, cluster) in enumerate(zip(monitoring, closest)):
        index = training_size + offset
        unfamiliar = tuple(key for key in profile if key not in encoder.vocabulary_)
        distance = float(distances[offset, cluster])
        if unfamiliar:
            label = 0
            details = {"outlier": "unseen_features", "unseen_features": unfamiliar}
        elif outlier_distance is not None and distance > outlier_distance:
            label = 0
            details = {"outlier": "distance", "distance": distance}
        else:
            label = int(cluster) + 1
            details = {"distance": distance}
        versions.append(
            _common.VersionAssignment(
                index, label, observations[index].end, details=details
            )
        )
    return versions, clusters


def apply(log, parameters=None):
    """Detect changes in stable trace-cluster populations after training.

    Train a K-means model on the first ``training_size`` completed traces
    (default 200), using activity and directly-follows relative frequencies.
    The vocabulary and model stay fixed throughout monitoring. The requested
    ``n_clusters`` (default 4) is capped at the number of distinct training
    profiles. ``cluster_random_state`` defaults to 0.

    After training, cases are assigned to the closest cluster. Label 0
    pools traces with unseen features or whose Euclidean distance to the
    closest center exceeds ``outlier_distance`` (optional, disabled by default).
    Positive labels represent clusters and stay comparable within a run.

    Compare adjacent ``window_size`` windows (default 100 traces per side),
    advancing ``step`` traces (default the window size). Both windows follow
    the training period. Jensen–Shannon distance is calibrated using whole
    traces or contiguous blocks of ``permutation_block_size`` traces.
    ``permutations`` defaults to 199 and ``random_state`` to 0. An alarm needs
    positive distance, distance at least ``min_effect`` (default 0), and a
    p-value at most ``alpha`` (default 0.05). ``persistence`` counts consecutive
    positive comparisons, and ``min_separation`` defaults to the window size.
    Alarm availability is the completion time of the confirming trace.
    """
    get = _common.parameter
    training_size = _common.integer(
        get(parameters, "training_size", 200), "training_size"
    )
    n_clusters = _common.integer(get(parameters, "n_clusters", 4), "n_clusters")
    seed = _common.integer(
        get(parameters, "cluster_random_state", 0), "cluster_random_state", minimum=0
    )
    outlier_distance = get(parameters, "outlier_distance", None)
    if outlier_distance is not None:
        outlier_distance = _common.real(outlier_distance, "outlier_distance")
    size = _common.integer(get(parameters, "window_size", 100), "window_size")
    step = _common.integer(get(parameters, "step", size), "step")
    alpha = _common.real(get(parameters, "alpha", 0.05), "alpha", maximum=1)
    min_effect = _common.real(
        get(parameters, "min_effect", 0.0), "min_effect", maximum=1
    )
    persistence = _common.integer(get(parameters, "persistence", 1), "persistence")
    min_separation = _common.integer(
        get(parameters, "min_separation", size), "min_separation", minimum=0
    )
    permutations, block_size, random_state = _statistics.permutation_settings(
        parameters, size
    )
    rng = np.random.default_rng(random_state)

    result = _common.DriftResult(
        "trace",
        metadata={
            "method": "cluster_frequency",
            "representation": "fixed_kmeans_activity_and_directly_follows_profiles",
            "mode": "sequential",
            "training_size": training_size,
            "n_clusters": n_clusters,
            "actual_clusters": 0,
            "cluster_random_state": seed,
            "outlier_distance": outlier_distance,
            "window_size": size,
            "step": step,
            "alpha": alpha,
            "min_effect": min_effect,
            "persistence": persistence,
            "min_separation": min_separation,
            "permutations": permutations,
            "permutation_block_size": block_size,
            "random_state": random_state,
        },
    )
    observations = _common.completed_traces(log, parameters)
    if len(observations) <= training_size:
        return result
    result.versions, result.metadata["actual_clusters"] = _classify(
        observations, training_size, n_clusters, seed, outlier_distance
    )
    labels = [version.label for version in result.versions]
    for start, boundary, stop in _common.adjacent_windows(len(labels), size, step):
        distance, p_value, changes = _statistics.categorical_window_test(
            labels[start:stop], size, permutations, block_size, rng
        )
        index = training_size + boundary
        result.scores.append(
            _common.WindowScore(
                index,
                distance,
                observations[index].end,
                observations[training_size + stop - 1].end,
                p_value,
                details={"changed_cluster_shares": changes},
            )
        )
    result.changes = _common.consolidate(
        result.scores,
        lambda point: 0 < point.score >= min_effect and point.p_value <= alpha,
        persistence,
        min_separation,
    )
    return result
