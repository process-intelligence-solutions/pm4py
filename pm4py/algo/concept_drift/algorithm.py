"""Dispatchers for concept drift detection in event logs."""

from enum import Enum
from typing import Any

import pandas as pd

from pm4py.algo.concept_drift.result import DriftResult
from pm4py.algo.concept_drift.variants import (
    bose,
    dfg_frequency,
    multivariate,
    supervised_similarity,
)
from pm4py.objects.log.obj import EventLog
from pm4py.util import exec_utils


class Variants(Enum):
    BOSE = bose
    DFG_FREQUENCY = dfg_frequency
    MULTIVARIATE = multivariate
    SUPERVISED_SIMILARITY = supervised_similarity


def apply(
    log: EventLog | pd.DataFrame,
    variant=Variants.BOSE,
    parameters: dict[Any, Any] | None = None,
) -> DriftResult | tuple[list, list[float], list[float]]:
    """Detect concept drift in an EventLog or pandas DataFrame.

    Pass detector-specific options in ``parameters``. The default ``BOSE``
    preserves its original tuple of sublogs, Unix timestamps and p-values.
    Other variants return a :class:`~pm4py.algo.concept_drift.result.DriftResult`
    with scores, change locations, and temporal and configuration metadata.
    """
    return exec_utils.get_variant(variant).apply(log, parameters)
