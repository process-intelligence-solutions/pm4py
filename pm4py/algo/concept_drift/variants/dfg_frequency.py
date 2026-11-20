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
"""Two-sample detection of directly-follows frequency changes."""

from collections import Counter

import numpy as np
from scipy.stats import chi2_contingency

from pm4py.algo.concept_drift import _common, _statistics
from pm4py.algo.discovery.dfg.variants import native


def apply(log, parameters=None):
    """Compare directly-follows frequencies in adjacent completed-trace windows.

    ``window_size`` counts traces per side (default 100), with ``step`` traces
    between evaluations (default 1). The score is Jensen–Shannon distance in
    [0, 1]. The default ``test="permutation"`` resamples completed traces or
    contiguous groups of ``permutation_block_size`` traces. Alternatively,
    ``test="g_test"`` uses the asymptotic likelihood-ratio test on edge counts.

    An alarm needs distance > 0, distance >= ``min_effect`` (default 0), and
    p <= ``alpha`` (default 0.05). By default retrospective consolidation selects
    the strongest boundary. Set ``retrospective=False`` for sequential alarms
    and use ``persistence`` to require multiple consecutive positive windows.
    """
    get = _common.parameter
    size = _common.integer(get(parameters, "window_size", 100), "window_size")
    step = _common.integer(get(parameters, "step", 1), "step")
    alpha = _common.real(get(parameters, "alpha", 0.05), "alpha", maximum=1)
    min_effect = _common.real(
        get(parameters, "min_effect", 0.0), "min_effect", maximum=1
    )
    test = get(parameters, "test", "permutation")
    if test not in ("permutation", "g_test"):
        raise ValueError("test must be 'permutation' or 'g_test'")
    retrospective = get(parameters, "retrospective", True)
    persistence = get(parameters, "persistence", 1)
    min_separation = get(parameters, "min_separation", size)
    permutation_metadata = {}
    if test == "permutation":
        permutations, block_size, random_state = _statistics.permutation_settings(
            parameters, size
        )
        rng = np.random.default_rng(random_state)
        permutation_metadata.update(
            permutations=permutations,
            permutation_block_size=block_size,
            random_state=random_state,
        )

    traces = _common.completed_traces(log, parameters)
    activity = _common.attribute_key(parameters, "activity_key", "concept:name")
    counts = [
        native.apply([trace.events], {native.Parameters.ACTIVITY_KEY: activity})
        for trace in traces
    ]
    scores = []
    for start, boundary, stop in _common.adjacent_windows(len(traces), size, step):
        rows = counts[start:stop]
        left_counts = sum(rows[:size], Counter())
        right_counts = sum(rows[size:], Counter())
        keys, table = _common.count_vectors([left_counts, right_counts])
        distance = _statistics.frequency_distance(*table)
        p_value = 1.0
        if distance > 0:
            if test == "g_test":
                p_value = float(
                    chi2_contingency(
                        table, correction=False, lambda_="log-likelihood"
                    ).pvalue
                )
            else:
                _, vectors = _common.count_vectors(rows)

                def statistic(left, right, vectors=vectors):
                    return _statistics.frequency_distance(
                        vectors[left].sum(axis=0), vectors[right].sum(axis=0)
                    )

                p_value = _statistics.permutation_p_value(
                    statistic, distance, size, permutations, block_size, rng
                )
        scores.append(
            _common.WindowScore(
                index=boundary,
                score=distance,
                timestamp=traces[boundary].end,
                available_at=traces[-1 if retrospective else stop - 1].end,
                p_value=p_value,
                details={
                    "changed_relations": _statistics.changed_proportions(keys, table)
                },
            )
        )
    changes = _common.consolidate(
        scores,
        lambda point: 0 < point.score >= min_effect and point.p_value <= alpha,
        persistence,
        min_separation,
        retrospective,
    )
    return _common.DriftResult(
        "trace",
        scores,
        changes,
        metadata={
            "representation": "directly_follows_frequency",
            "method": "dfg_frequency",
            "test": test,
            "retrospective": retrospective,
            "window_size": size,
            "step": step,
            "alpha": alpha,
            "min_effect": min_effect,
            "persistence": persistence,
            "min_separation": min_separation,
            **permutation_metadata,
        },
    )
