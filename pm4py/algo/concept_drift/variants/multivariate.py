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
"""Permutation tests on joint process features using MMD or energy distance."""

from collections import Counter
from collections.abc import Callable
from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from pm4py.algo.concept_drift import _common, _statistics


def apply(log, parameters=None):
    """Test completed-trace features with an RBF kernel or energy distance.

    Set ``features`` to a sequence drawn from ``activity``, ``dfg``, ``resource``,
    ``activity_resource``, ``duration``, ``mean_gap``, or pairs of the form
    ``("case_numeric", attribute)`` and ``("case_category", attribute)``.
    The default is activity proportions and case duration. Activity-resource
    proportions retain the association even when the marginals are unchanged.
    A callable can supply a mapping of feature names to numeric values for each
    completed trace. For precomputed observations, use :func:`apply_features`.
    """
    traces = _common.completed_traces(log, parameters)
    features = _common.parameter(parameters, "features", ("activity", "duration"))
    if callable(features):
        rows = [features(trace) for trace in traces]
        numeric = lambda name: True
        feature_spec = "custom"
    else:
        feature_spec = tuple(features) if not isinstance(features, str) else (features,)
        _validate_features(feature_spec)
        resource_key = _common.attribute_key(parameters, "resource_key", "org:resource")
        rows = [_trace_features(trace, feature_spec, resource_key) for trace in traces]
        numeric = _numeric_trace_feature
    matrix = lambda start, stop: _common.count_vectors(rows[start:stop])
    timestamps = [trace.end for trace in traces]
    return _detect(
        len(traces),
        matrix,
        numeric,
        timestamps,
        timestamps,
        "trace",
        parameters,
        feature_spec,
    )


def apply_features(
    features,
    parameters=None,
    *,
    timestamps=None,
    available_at=None,
    observation_unit="observation",
):
    """Test successive groups of precomputed numerical observations.

    Rows are observations in chronological order. Labels come from DataFrame
    columns when supplied. A DatetimeIndex supplies boundary timestamps by
    default. Pass ``available_at`` when a row is usable only later than its
    timestamp, such as a calendar bin labeled by its start.
    """
    columns = None
    if isinstance(features, pd.DataFrame):
        if not features.columns.is_unique:
            raise ValueError("Feature column names must be unique")
        columns = features.columns.tolist()
        if timestamps is None and isinstance(features.index, pd.DatetimeIndex):
            timestamps = features.index
    values = np.asarray(features, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("features must be a finite numeric observation matrix")
    if columns is None:
        columns = list(range(values.shape[1]))
    length = len(values)
    times = _time_axis(timestamps, length, "timestamps")
    availability = (
        times
        if available_at is None
        else _time_axis(available_at, length, "available_at")
    )
    if any(
        timestamp is not None and usable is not None and usable < timestamp
        for timestamp, usable in zip(times, availability)
    ):
        raise ValueError("An observation cannot be available before its timestamp")
    return _detect(
        length,
        lambda start, stop: (columns, values[start:stop]),
        lambda name: True,
        times,
        availability,
        observation_unit,
        parameters,
        columns,
    )


def _validate_features(features):
    if not features:
        raise ValueError("Choose at least one trace feature")
    for feature in features:
        if feature in (
            "activity",
            "dfg",
            "resource",
            "activity_resource",
            "duration",
            "mean_gap",
        ):
            continue
        if (
            isinstance(feature, tuple)
            and len(feature) == 2
            and feature[0] in ("case_numeric", "case_category")
            and isinstance(feature[1], str)
        ):
            continue
        raise ValueError(f"Unknown trace feature {feature!r}")


def _trace_features(trace, features, resource_key):
    row = {}
    if "resource" in features or "activity_resource" in features:
        resources = tuple(event.get(resource_key) for event in trace.events)
        resources = tuple(
            None if pd.api.types.is_scalar(r) and pd.isna(r) else r for r in resources
        )
    for feature in features:
        if feature == "duration":
            row[(feature,)] = (trace.end - trace.start).total_seconds()
        elif feature == "mean_gap":
            gaps = [(b - a).total_seconds() for a, b in pairwise(trace.timestamps)]
            row[(feature,)] = float(np.mean(gaps)) if gaps else 0.0
        elif isinstance(feature, tuple):
            kind, attribute = feature
            value = trace.attributes.get(attribute.removeprefix("case:"))
            if kind == "case_numeric":
                if value is None:
                    raise ValueError(f"Missing numerical case attribute {attribute!r}")
                row[feature] = float(value)
            else:
                if pd.api.types.is_scalar(value) and pd.isna(value):
                    value = None
                row[feature + (value,)] = 1.0
        else:
            if feature == "activity":
                counts = Counter(trace.activities)
            elif feature == "dfg":
                counts = _common.directly_follows(trace.activities)
            elif feature == "resource":
                counts = Counter(resources)
            else:
                counts = Counter(zip(trace.activities, resources))
            total = counts.total()
            row.update({(feature, key): count / total for key, count in counts.items()})
    return row


def _time_axis(values, length, name):
    if values is None:
        return [None] * length
    axis = pd.DatetimeIndex(pd.to_datetime(values, utc=True))
    if len(axis) != length or axis.isna().any() or not axis.is_monotonic_increasing:
        raise ValueError(
            f"{name} must contain one chronological timestamp per observation"
        )
    return axis


def _numeric_trace_feature(name):
    return name[0] in ("duration", "mean_gap", "case_numeric")


def _detect(
    length,
    matrix: Callable,
    numeric: Callable,
    timestamps,
    availability,
    unit,
    parameters,
    features,
):
    get = _common.parameter
    size = _common.integer(get(parameters, "window_size", 50), "window_size", minimum=2)
    step = _common.integer(get(parameters, "step", 1), "step")
    method = get(parameters, "method", "mmd")
    if method not in ("mmd", "energy"):
        raise ValueError("method must be 'mmd' or 'energy'")
    bandwidth = get(parameters, "bandwidth", None)
    if bandwidth is not None:
        bandwidth = _common.real(bandwidth, "bandwidth", minimum=np.finfo(float).tiny)
    standardize = get(parameters, "standardize", True)
    alpha = _common.real(get(parameters, "alpha", 0.05), "alpha", maximum=1)
    min_effect = _common.real(get(parameters, "min_effect", 0), "min_effect")
    retrospective = get(parameters, "retrospective", True)
    persistence = get(parameters, "persistence", 1)
    min_separation = get(parameters, "min_separation", size)
    permutations, block_size, seed = _statistics.permutation_settings(parameters, size)
    rng = np.random.default_rng(seed)
    scores = []
    for start, boundary, stop in _common.adjacent_windows(length, size, step):
        keys, values = matrix(start, stop)
        if not np.isfinite(values).all():
            raise ValueError("features must be finite")
        values = values.copy()
        if standardize:
            selected = [i for i, key in enumerate(keys) if numeric(key)]
            values[:, selected] = _common.standardize(values[:, selected])

        gram, effective_bandwidth = _comparison_matrix(values, method, bandwidth)
        left = np.arange(size)
        right = np.arange(size, 2 * size)
        distance = _mean_difference(gram, left, right)
        p_value = (
            _statistics.permutation_p_value(
                lambda before, after, gram=gram: _mean_difference(gram, before, after),
                distance,
                size,
                permutations,
                block_size,
                rng,
            )
            if distance > 0
            else 1.0
        )
        difference = values[size:].mean(axis=0) - values[:size].mean(axis=0)
        most_changed = np.argsort(-np.abs(difference), kind="stable")[:5]
        details = {
            "changed_means": {
                keys[i]: float(difference[i]) for i in most_changed if difference[i]
            },
        }
        if effective_bandwidth is not None:
            details["bandwidth"] = effective_bandwidth
        scores.append(
            _common.WindowScore(
                boundary,
                distance,
                timestamps[boundary],
                availability[-1 if retrospective else stop - 1],
                p_value,
                details,
            )
        )
    return _common.DriftResult(
        unit,
        scores,
        _common.consolidate(
            scores,
            lambda point: 0 < point.score >= min_effect and point.p_value <= alpha,
            persistence,
            min_separation,
            retrospective,
        ),
        metadata={
            "method": method,
            "representation": features,
            "retrospective": retrospective,
            "standardize": standardize,
            "bandwidth": bandwidth,
            "window_size": size,
            "step": step,
            "alpha": alpha,
            "min_effect": min_effect,
            "persistence": persistence,
            "min_separation": min_separation,
            "permutations": permutations,
            "permutation_block_size": block_size,
            "random_state": seed,
        },
    )


def _comparison_matrix(values, method, bandwidth):
    distances = cdist(values, values, metric="euclidean")
    if method == "energy":
        return -distances, None
    if bandwidth is None:
        positive = distances[distances > 0]
        bandwidth = float(np.median(positive)) if positive.size else 1.0
    return np.exp(-0.5 * (distances / bandwidth) ** 2), bandwidth


def _mean_difference(matrix, left, right):
    within_left = matrix[np.ix_(left, left)].mean()
    within_right = matrix[np.ix_(right, right)].mean()
    cross = matrix[np.ix_(left, right)].mean()
    return float(max(0, within_left + within_right - 2 * cross))
