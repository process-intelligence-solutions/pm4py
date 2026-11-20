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
"""Dispatchers for concept drift detection in event logs."""

from enum import Enum
from typing import Any

import pandas as pd

from pm4py.algo.concept_drift.result import DriftResult
from pm4py.algo.concept_drift.variants import (
    bose,
    cluster_frequency,
    conformance,
    conformance_profile,
    cv_indicators,
    declare_profiles,
    dfg_frequency,
    earth_mover,
    event_relations,
    graph_metrics,
    indicators,
    lcdd,
    multivariate,
    relation_invariance,
    run_distribution,
    supervised_similarity,
    trace_variant_frequency,
    version_clustering,
)
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.util import exec_utils


class Variants(Enum):
    BOSE = bose
    DFG_FREQUENCY = dfg_frequency
    EVENT_RELATIONS = event_relations
    LCDD = lcdd
    RELATION_INVARIANCE = relation_invariance
    GRAPH_METRICS = graph_metrics
    RUN_DISTRIBUTION = run_distribution
    TRACE_VARIANT_FREQUENCY = trace_variant_frequency
    EARTH_MOVER = earth_mover
    INDICATORS = indicators
    CV_INDICATORS = cv_indicators
    CONFORMANCE = conformance
    CONFORMANCE_PROFILE = conformance_profile
    DECLARE_PROFILES = declare_profiles
    VERSION_CLUSTERING = version_clustering
    CLUSTER_FREQUENCY = cluster_frequency
    MULTIVARIATE = multivariate
    SUPERVISED_SIMILARITY = supervised_similarity


def apply(
    log: EventLog | EventStream | pd.DataFrame,
    variant=Variants.BOSE,
    parameters: dict[Any, Any] | None = None,
) -> DriftResult | tuple[list, list[float], list[float]]:
    """Detect concept drift in an EventLog or pandas DataFrame.

    The event-relations variant also accepts an EventStream.
    Pass detector-specific options in ``parameters``. The default ``BOSE``
    preserves its original tuple of sublogs, Unix timestamps and p-values.
    Other variants return a :class:`~pm4py.algo.concept_drift.result.DriftResult`
    with scores, change locations, and temporal and configuration metadata.
    """
    return exec_utils.get_variant(variant).apply(log, parameters)
