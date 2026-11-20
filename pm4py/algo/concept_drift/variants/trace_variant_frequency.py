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
"""Two-sample detection of changes in exact trace-variant frequencies."""

from dataclasses import replace

import numpy as np

from pm4py.algo.concept_drift import _common, _statistics
from pm4py.algo.concept_drift.result import DriftResult, WindowScore


def apply(log, parameters=None):
    """Compare distributions of complete activity sequences.

    Each completed trace contributes one categorical observation. Consecutive
    windows have ``window_size`` traces each (default 100) and advance by
    ``step`` traces (default 1). The score is the Jensen–Shannon distance.
    Permutations exchange whole traces or contiguous groups of
    ``permutation_block_size`` traces. Set ``permutations`` (default 199)
    and ``random_state`` (default 0) to control this calibration.

    Alarms require positive distance, distance at least ``min_effect``
    (default 0), and a p-value at most ``alpha`` (default 0.05).
    ``persistence`` counts consecutive positive comparisons (default 1),
    and ``min_separation`` defaults to the window size. Each score belongs
    to the first trace of the right window and is available when that
    window completes. Retrospective alarms (the default) choose the
    strongest boundary in each excursion and become available at log end.
    With ``retrospective=False`` the first positive boundary is reported
    once the persistence requirement has been met.
    """
    get = _common.parameter
    size = _common.integer(get(parameters, "window_size", 100), "window_size")
    step = _common.integer(get(parameters, "step", 1), "step")
    alpha = _common.real(get(parameters, "alpha", 0.05), "alpha", maximum=1)
    min_effect = _common.real(
        get(parameters, "min_effect", 0.0), "min_effect", maximum=1
    )
    persistence = _common.integer(get(parameters, "persistence", 1), "persistence")
    min_separation = _common.integer(
        get(parameters, "min_separation", size), "min_separation", minimum=0
    )
    retrospective = get(parameters, "retrospective", True)
    if not isinstance(retrospective, bool):
        raise TypeError("retrospective must be a boolean")
    permutations, block_size, random_state = _statistics.permutation_settings(
        parameters, size
    )
    rng = np.random.default_rng(random_state)
    traces = _common.completed_traces(log, parameters)
    labels = [trace.activities for trace in traces]

    scores = []
    for start, boundary, stop in _common.adjacent_windows(len(labels), size, step):
        distance, p_value, changed = _statistics.categorical_window_test(
            labels[start:stop], size, permutations, block_size, rng
        )
        scores.append(
            WindowScore(
                index=boundary,
                score=distance,
                timestamp=traces[boundary].end,
                available_at=traces[stop - 1].end,
                p_value=p_value,
                details={"changed_variants": changed},
            )
        )
    changes = _common.consolidate(
        scores,
        lambda point: 0 < point.score >= min_effect and point.p_value <= alpha,
        persistence,
        min_separation,
        retrospective,
    )
    if retrospective:
        changes = [replace(alarm, available_at=traces[-1].end) for alarm in changes]

    return DriftResult(
        "trace",
        scores=scores,
        changes=changes,
        metadata={
            "method": "trace_variant_frequency",
            "representation": "exact_activity_sequences",
            "window_size": size,
            "step": step,
            "alpha": alpha,
            "min_effect": min_effect,
            "persistence": persistence,
            "min_separation": min_separation,
            "retrospective": retrospective,
            "permutations": permutations,
            "permutation_block_size": block_size,
            "random_state": random_state,
        },
    )
