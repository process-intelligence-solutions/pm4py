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
"""Statistics shared by two-sample drift detectors."""

import numpy as np
from scipy.spatial.distance import jensenshannon

from pm4py.algo.concept_drift import _common


def permutation_settings(parameters, window_size):
    permutations = _common.integer(
        _common.parameter(parameters, "permutations", 199), "permutations"
    )
    block_size = _common.integer(
        _common.parameter(parameters, "permutation_block_size", 1),
        "permutation_block_size",
    )
    if window_size % block_size:
        raise ValueError("permutation_block_size must divide window_size")
    random_state = _common.parameter(parameters, "random_state", 0)
    return permutations, block_size, random_state


def permutation_p_value(statistic, observed, size, permutations, block_size, rng):
    """Calibrate a statistic by permuting equal blocks of whole observations."""
    indices = np.arange(2 * size).reshape(-1, block_size)
    extreme = 0
    for _ in range(permutations):
        permutation = rng.permutation(indices).ravel()
        value = statistic(permutation[:size], permutation[size:])
        if value >= observed or np.isclose(value, observed, rtol=1e-12, atol=1e-15):
            extreme += 1
    return (extreme + 1) / (permutations + 1)


def frequency_distance(left, right):
    """Jensen–Shannon distance between nonempty count distributions."""
    if not left.any() or not right.any():
        return 0.0
    return float(jensenshannon(left, right, base=2))


def changed_proportions(keys, table, limit=5):
    """Largest signed changes in category proportions from left to right."""
    totals = table.sum(axis=1)
    if not totals.all():
        return {}
    proportions = table / totals[:, None]
    changes = proportions[1] - proportions[0]
    strongest = np.argsort(-np.abs(changes), kind="stable")[:limit]
    return {keys[i]: float(changes[i]) for i in strongest if changes[i]}


def categorical_window_test(labels, size, permutations, block_size, rng):
    """Compare two windows with one categorical observation per row."""
    categories = {}
    codes = np.array(
        [categories.setdefault(label, len(categories)) for label in labels], dtype=int
    )

    def counts(indices):
        return np.bincount(codes[indices], minlength=len(categories))

    table = np.stack([counts(slice(None, size)), counts(slice(size, None))])
    distance = frequency_distance(*table)
    p_value = 1.0
    if distance > 0:
        p_value = permutation_p_value(
            lambda left, right: frequency_distance(counts(left), counts(right)),
            distance,
            size,
            permutations,
            block_size,
            rng,
        )
    return distance, p_value, changed_proportions(list(categories), table)
