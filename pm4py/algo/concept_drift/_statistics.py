"""Permutation calibration shared by two-sample drift detectors."""

import numpy as np

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
