"""Results shared by the concept-drift detectors."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from pm4py.meta import VERSION


@dataclass
class WindowScore:
    """Evidence at a candidate boundary or at an observation."""

    index: int
    score: float
    timestamp: pd.Timestamp | None = None
    available_at: pd.Timestamp | None = None
    p_value: float | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftAlarm:
    """An estimated change and the time at which the detector could report it."""

    index: int
    timestamp: pd.Timestamp | None = None
    available_at: pd.Timestamp | None = None
    score: float | None = None
    p_value: float | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftInterval:
    """A transition with inclusive start and end indices."""

    start_index: int
    end_index: int
    start_timestamp: pd.Timestamp | None = None
    end_timestamp: pd.Timestamp | None = None
    available_at: pd.Timestamp | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionAssignment:
    """The inferred version at an observation or window boundary."""

    index: int
    label: int | str | None
    timestamp: pd.Timestamp | None = None
    confidence: float | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftResult:
    """Drift evidence and detections on a zero-based observation axis."""

    observation_unit: str
    scores: list[WindowScore] = field(default_factory=list)
    changes: list[DriftAlarm] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    intervals: list[DriftInterval] = field(default_factory=list)
    versions: list[VersionAssignment] = field(default_factory=list)

    def __post_init__(self):
        self.metadata = {"pm4py_version": VERSION, **self.metadata}
