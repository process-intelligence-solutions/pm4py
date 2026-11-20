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
"""Retrospective drift detection over directly-follows graph metrics.

Inspired by the process graph metrics of Seeliger, Nolle, and Mühlhäuser
(https://doi.org/10.1145/3040565.3040566). This detector segments metrics of
fixed-block directly-follows graphs with squared-error PELT.
"""

from enum import Enum
from itertools import pairwise

import networkx as nx
import numpy as np

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.algo.discovery.dfg.variants import native
from pm4py.objects.dfg.utils.dfg_utils import transform_dfg_to_directed_nx_graph
from pm4py.util.xes_constants import DEFAULT_NAME_KEY


class Parameters(Enum):
    WINDOW_SIZE = "window_size"
    MIN_EDGE_COUNT = "min_edge_count"
    MIN_SIZE = "min_size"
    PENALTY = "penalty"
    STANDARDIZE = "standardize"
    METRICS = "metrics"


_DEFAULT_METRICS = (
    "activity_count",
    "edge_density",
    "branching_fraction",
    "merging_fraction",
    "weak_component_count",
    "cyclic_activity_fraction",
    "self_loop_fraction",
)
_AVAILABLE_METRICS = frozenset((*_DEFAULT_METRICS, "edge_count"))


def _block_metrics(traces, activity_key, min_edge_count):
    activities = {activity for trace in traces for activity in trace.activities}
    dfg = native.apply(
        [trace.events for trace in traces],
        {native.Parameters.ACTIVITY_KEY: activity_key},
    )
    edges = {edge: count for edge, count in dfg.items() if count >= min_edge_count}
    graph = transform_dfg_to_directed_nx_graph(edges.items(), activities)
    self_loops = set(nx.nodes_with_selfloops(graph))
    cyclic = self_loops | {
        node
        for component in nx.strongly_connected_components(graph)
        if len(component) > 1
        for node in component
    }
    total = sum(edges.values())
    size = len(activities)
    nonself_edges = len(edges) - len(self_loops)
    possible = size * (size - 1)
    return {
        "activity_count": size,
        "edge_count": len(edges),
        "edge_density": nonself_edges / possible if possible else 0.0,
        "branching_fraction": sum(
            degree - (node in self_loops) > 1 for node, degree in graph.out_degree
        )
        / size,
        "merging_fraction": sum(
            degree - (node in self_loops) > 1 for node, degree in graph.in_degree
        )
        / size,
        "weak_component_count": nx.number_weakly_connected_components(graph),
        "cyclic_activity_fraction": len(cyclic) / size,
        "self_loop_fraction": sum(edges[node, node] for node in self_loops) / total
        if total
        else 0.0,
    }


def apply(log, parameters=None):
    """Find changes in graph topology and loop frequency across completed traces.

    Build a directly-follows graph per complete, nonoverlapping block of
    ``window_size`` traces (default 50). Ignore edges with fewer than
    ``min_edge_count`` occurrences (default 1). All observed activities,
    including isolated vertices, remain in each graph.

    By default ``metrics`` includes activity count, directed edge density,
    branching and merging fractions, weak component count, cyclic activity
    fraction, and self-loop fraction. Edge density and the branching and
    merging fractions ignore self-loops. Branching (merging) is the fraction
    of activities with more than one outgoing (incoming) neighbor. An activity
    in a directed cycle or with a self-loop is cyclic. Self-loop fraction
    divides retained self-loop occurrences by all retained edge occurrences.
    These ratios are zero for zero denominators. An explicit metric list can
    also include ``"edge_count"``, which counts self-loops. Metric keys are
    listed in the result metadata.

    Squared-error PELT fits the metric series jointly, with ``penalty``
    (default 10) and ``min_size`` (default 2 blocks per segment). Each metric
    is standardized using the full series by default. Pass
    ``standardize=False`` to use the original units in the cost function.
    Scores report the distance between successive metric vectors alongside
    the raw metrics. Alarms contain the cost reduction and the changes in
    adjacent segments' raw mean metrics. Indices refer to the first case
    in a block, in completion order. The full log is required to report
    results. These metrics are invariant to renaming activities.
    """
    get = _common.parameter
    size = _common.integer(get(parameters, Parameters.WINDOW_SIZE, 50), "window_size")
    min_edge_count = _common.integer(
        get(parameters, Parameters.MIN_EDGE_COUNT, 1), "min_edge_count"
    )
    min_size = _common.integer(get(parameters, Parameters.MIN_SIZE, 2), "min_size")
    penalty = _common.real(
        get(parameters, Parameters.PENALTY, 10.0),
        "penalty",
        minimum=np.finfo(float).tiny,
    )
    standardize = get(parameters, Parameters.STANDARDIZE, True)
    if not isinstance(standardize, bool):
        raise TypeError("standardize must be a Boolean")
    metrics = get(parameters, Parameters.METRICS, _DEFAULT_METRICS)
    if isinstance(metrics, str):
        metrics = (metrics,)
    metrics = tuple(dict.fromkeys(metrics))
    if not metrics or not _AVAILABLE_METRICS.issuperset(metrics):
        raise ValueError(f"metrics must be chosen from {sorted(_AVAILABLE_METRICS)}")

    activity_key = _common.attribute_key(parameters, "activity_key", DEFAULT_NAME_KEY)
    traces = _common.completed_traces(log, parameters)
    starts = range(0, len(traces) - size + 1, size)
    profiles = [
        _block_metrics(traces[start : start + size], activity_key, min_edge_count)
        for start in starts
    ]
    raw_values = np.array(
        [[profile[name] for name in metrics] for profile in profiles], dtype=float
    ).reshape(len(starts), len(metrics))
    values = _common.standardize(raw_values) if standardize else raw_values
    cost = _timeseries.segment_cost(values)
    cuts = _timeseries.pelt(values, penalty, min_size, cost=cost)
    available_at = traces[-1].end if traces else None

    result = _common.DriftResult(
        "trace",
        metadata={
            "mode": "retrospective",
            "trace_order": "completion",
            "window_size": size,
            "min_edge_count": min_edge_count,
            "min_size": min_size,
            "penalty": penalty,
            "standardize": standardize,
            "metrics": metrics,
        },
    )
    for block, start in enumerate(starts):
        score = (
            float(np.linalg.norm(values[block] - values[block - 1])) if block else 0.0
        )
        result.scores.append(
            _common.WindowScore(
                start,
                score,
                traces[start].end,
                available_at,
                details={"metrics": {name: profiles[block][name] for name in metrics}},
            )
        )

    segments = list(pairwise([0, *cuts, len(starts)]))
    for (left, cut), (_, right) in pairwise(segments):
        start = starts[cut]
        before = raw_values[left:cut].mean(axis=0)
        after = raw_values[cut:right].mean(axis=0)
        result.changes.append(
            _common.DriftAlarm(
                start,
                traces[start].end,
                available_at,
                float(cost(left, right) - cost(left, cut) - cost(cut, right)),
                details={
                    "metric_changes": {
                        name: float(delta)
                        for name, delta in zip(metrics, after - before)
                        if delta != 0
                    },
                },
            )
        )
    return result
