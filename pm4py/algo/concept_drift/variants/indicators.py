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
"""Drift detection on calendar-binned process indicators."""

from collections import defaultdict
from enum import Enum

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.util import constants, xes_constants


class Parameters(Enum):
    METHOD = "method"
    BIN_SIZE = "bin_size"
    OBSERVATION_END = "observation_end"
    FEATURES = "features"
    PENALTY = "penalty"
    MIN_SIZE = "min_size"
    STANDARDIZE = "standardize"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    RESOURCE_KEY = constants.PARAMETER_CONSTANT_RESOURCE_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY


DEFAULT_FEATURES = (
    "arrivals",
    "completions",
    "work_in_progress",
    "events",
    "case_duration",
)
_FEATURE_ARGUMENTS = {
    **dict.fromkeys(DEFAULT_FEATURES, 0),
    "active_resources": 0,
    "activity_count": 1,
    "activity_frequency": 1,
    "inter_event_gap": 1,
    "service_time": 1,
    "resource_assignment": 2,
    "resource_handover": 2,
    "case_type": 2,
    "case_value": 1,
}


def _features(parameters):
    requested = _common.parameter(parameters, Parameters.FEATURES, DEFAULT_FEATURES)
    if isinstance(requested, str):
        requested = (requested,)
    features = []
    for item in requested:
        feature = (item,) if isinstance(item, str) else tuple(item)
        if not feature or _FEATURE_ARGUMENTS.get(feature[0]) != len(feature) - 1:
            raise ValueError(f"Invalid process indicator: {item!r}")
        features.append(feature[0] if len(feature) == 1 else feature)
    if not features:
        raise ValueError("At least one process indicator must be selected")
    return list(dict.fromkeys(features))


def extract_features(log, parameters=None):
    """Return a pandas DataFrame with one row per calendar bin in UTC.

    ``bin_size`` is a pandas frequency string, default ``"D"``. Bins include
    their left edge, exclude their right edge, and retain empty periods. The
    index is the bin start and the observations are available at bin close.
    With ``observation_end``, return only bins closed by that UTC time, extending
    through recorded empty periods when the end follows the last event. The
    observation end must be at or after the last input event. By default this
    extractor includes the bin containing the last event, which may be partial.

    ``features`` accepts a list of names or tuples. The default indicators
    are event counts, case arrivals and completions, work in progress, and
    mean case duration. Work in progress is cumulative arrivals minus
    completions immediately before the bin closes. The first and last
    observed events define case starts and completions, respectively. Supply
    a log with known case boundaries. In a live event stream, completion-based
    signals and work in progress require knowing when a case actually ends.

    Additional selectors are ``"active_resources"``,
    ``("activity_count", activity)``, ``("activity_frequency", activity)``,
    ``("inter_event_gap", activity)``, ``("service_time", activity)``,
    ``("resource_assignment", activity, resource)``,
    ``("resource_handover", source, target)``, ``("case_type", attribute, value)``
    and ``("case_value", attribute)``. Activity frequency is a share of all
    events. Resource assignment is conditional on the activity and a known
    resource. A handover is a change of known resource between consecutive
    events in a case. Handover counts are assigned to the later event's bin.
    Case frequency and mean numeric case value use cases completed in the bin
    and read EventLog trace attributes or DataFrame ``case:`` columns by
    their unprefixed names.

    Durations are in seconds. Inter-event gaps end at the specified activity.
    Service time additionally requires a start timestamp on the event.
    Undefined means or proportions are missing; counts in empty bins are zero.
    """
    features = _features(parameters)
    bin_size = _common.parameter(parameters, Parameters.BIN_SIZE, "D")
    offset = pd.tseries.frequencies.to_offset(bin_size)
    if offset is None or offset.n <= 0:
        raise ValueError("bin_size must be a positive calendar frequency")

    observation_end = _common.parameter(parameters, Parameters.OBSERVATION_END, None)
    if observation_end is not None:
        observation_end = pd.to_datetime(observation_end, utc=True)
        if not isinstance(observation_end, pd.Timestamp):
            raise ValueError("observation_end must be a timestamp")
    traces = _common.completed_traces(log, parameters)
    if not traces:
        return pd.DataFrame(
            columns=features, index=pd.DatetimeIndex([], tz="UTC"), dtype=float
        )

    resource_key = _common.attribute_key(
        parameters, "resource_key", xes_constants.DEFAULT_RESOURCE_KEY
    )
    start_key = _common.attribute_key(
        parameters, "start_timestamp_key", xes_constants.DEFAULT_START_TIMESTAMP_KEY
    )
    requested = {
        feature[0] if isinstance(feature, tuple) else feature for feature in features
    }
    events = _event_table(traces, resource_key, start_key, "service_time" in requested)
    cases = pd.DataFrame(
        {
            "start": [trace.start for trace in traces],
            "duration": [(trace.end - trace.start).total_seconds() for trace in traces],
        },
        index=pd.DatetimeIndex([trace.end for trace in traces]),
    )

    totals = events.resample(offset, closed="left", label="left").size()
    index = totals.index
    last_event = traces[-1].end
    if observation_end is not None:
        if observation_end < last_event:
            raise ValueError("observation_end precedes the last input event")
        index = pd.date_range(index[0], observation_end, freq=offset)
        totals = totals.reindex(index, fill_value=0)

    def group(values):
        bins = index.searchsorted(values.index, side="right") - 1
        return values.groupby(index.take(bins))

    def count(values):
        return group(values).size().reindex(index, fill_value=0)

    def mean(values):
        groups = group(values)
        means = groups.mean()
        largest = values.abs().max()
        if pd.notna(largest) and largest > np.finfo(float).max / len(values):
            # A bin can have a finite mean even when its unscaled sum overflows.
            for label in means.index[~np.isfinite(means)]:
                members = groups.get_group(label)
                scale = members.abs().max()
                if pd.notna(scale) and scale > 0:
                    means.loc[label] = (members / scale).mean() * scale
        return means.reindex(index)

    arrivals = count(cases.set_index("start"))
    completions = count(cases)
    base = {
        "arrivals": arrivals,
        "completions": completions,
        "work_in_progress": (arrivals - completions).cumsum(),
        "events": totals,
        "case_duration": mean(cases["duration"]),
    }
    columns = {}
    for feature in features:
        if feature in base:
            columns[feature] = base[feature]
        elif feature == "active_resources":
            columns[feature] = (
                group(events["resource"]).nunique().reindex(index, fill_value=0)
            )
        elif feature[0] in ("case_type", "case_value"):
            attribute = pd.Series(
                [trace.attributes.get(feature[1]) for trace in traces],
                index=cases.index,
            ).dropna()
            if feature[0] == "case_type":
                columns[feature] = count(attribute[attribute.eq(feature[2])]) / count(
                    attribute
                )
            else:
                values = pd.to_numeric(attribute, errors="raise").replace(
                    [np.inf, -np.inf], np.nan
                )
                columns[feature] = mean(values)
        elif feature[0] == "resource_handover":
            handover = events["resource"].eq(feature[2]) & events[
                "previous_resource"
            ].eq(feature[1])
            columns[feature] = count(events[handover & events["handover"]])
        else:
            activity_events = events[events["activity"].eq(feature[1])]
            if feature[0] == "activity_count":
                columns[feature] = count(activity_events)
            elif feature[0] == "activity_frequency":
                columns[feature] = count(activity_events) / totals.where(totals > 0)
            elif feature[0] == "resource_assignment":
                resources = activity_events["resource"].dropna()
                columns[feature] = count(resources[resources.eq(feature[2])]) / count(
                    resources
                )
            else:
                columns[feature] = mean(activity_events[feature[0]])
    frame = pd.DataFrame(columns, dtype=float)
    if observation_end is not None:
        frame = frame.loc[index + offset <= observation_end]
    frame.attrs["observed_through"] = (
        last_event if observation_end is None else observation_end
    )
    return frame


def _event_table(traces, resource_key, start_key, service_time):
    rows = []
    for trace in traces:
        previous_time = None
        previous_resource = None
        for timestamp, activity, event in zip(
            trace.timestamps, trace.activities, trace.events
        ):
            resource = event.get(resource_key)
            gap = (
                (timestamp - previous_time).total_seconds()
                if previous_time is not None
                else np.nan
            )
            start = event.get(start_key) if service_time else None
            rows.append((timestamp, activity, resource, previous_resource, gap, start))
            previous_time, previous_resource = timestamp, resource
    events = pd.DataFrame.from_records(
        rows,
        columns=[
            "timestamp",
            "activity",
            "resource",
            "previous_resource",
            "inter_event_gap",
            "start",
        ],
    ).set_index("timestamp")
    events["handover"] = (
        events["resource"].notna()
        & events["previous_resource"].notna()
        & events["resource"].ne(events["previous_resource"])
    )
    if service_time:
        starts = pd.to_datetime(events["start"], utc=True, format="mixed")
        durations = (events.index - starts).dt.total_seconds()
        if (durations < 0).any():
            raise ValueError("A service start timestamp follows its event completion")
        events["service_time"] = durations
    return events


def _retrospective(values, parameters):
    penalty = _common.parameter(parameters, Parameters.PENALTY, 10.0)
    min_size = _common.parameter(parameters, Parameters.MIN_SIZE, 3)
    standardize = _common.parameter(parameters, Parameters.STANDARDIZE, True)
    if standardize:
        values = _common.standardize(values)
    cost = _timeseries.segment_cost(values)
    cuts = _timeseries.pelt(values, penalty, min_size, cost=cost)
    bounds = [0, *cuts, len(values)]
    for left, cut, right in zip(bounds, cuts, bounds[2:]):
        gain = cost(left, right) - cost(left, cut) - cost(cut, right)
        yield cut, float(gain)


def apply(log, parameters=None):
    """Detect changes by running one detector per selected process indicator.

    ``method`` is ``"pelt"`` (default), ``"page_hinkley"``, or ``"adwin"``.
    PELT segments each indicator independently using a squared-error cost,
    ``penalty`` (default 10) and ``min_size`` (default 3 observed values per
    segment). PELT standardizes each indicator over the full log by default.
    Set ``standardize=False`` to express the penalty in original squared units.
    The sequential methods use raw values and fixed, user-selected indicators.
    Missing observations never update a detector. Sequential methods use
    only bins closed by ``observation_end``, or by the last event timestamp
    if no explicit end is supplied.

    This function replays a complete log. Its sequential availability times
    assume events are observed by their recorded timestamps and case
    completion is known at the last event. The observation count separating
    an estimated boundary from its report may vary by detector and feature.

    Each indicator can trigger an alarm. Alarms estimated at the same bin
    boundary and available at the same time are combined. The main score is
    the number of features signaling at the estimated bin for PELT or at the
    reporting bin for sequential methods. Score details contain the observed
    values and the per-feature detector evidence.
    """
    method = _common.parameter(parameters, Parameters.METHOD, "pelt")
    frame = extract_features(log, parameters)
    bin_size = _common.parameter(parameters, Parameters.BIN_SIZE, "D")
    starts = frame.index
    ends = starts + pd.tseries.frequencies.to_offset(bin_size)
    observed_through = frame.attrs.get("observed_through")
    if method != "pelt" and observed_through is not None:
        frame = frame.loc[ends <= observed_through]
        starts = frame.index
        ends = ends[ends <= observed_through]
    result = _common.DriftResult(
        "calendar_bin",
        metadata={
            "variant": "indicators",
            "method": method,
            "bin_size": bin_size,
            "observed_through": observed_through,
            "features": list(frame.columns),
            "retrospective": method == "pelt",
            "aggregation": "any_feature",
            "case_boundaries": "first_and_last_case_event",
        },
    )
    if method == "pelt":
        result.metadata.update(
            penalty=_common.parameter(parameters, Parameters.PENALTY, 10.0),
            min_size=_common.parameter(parameters, Parameters.MIN_SIZE, 3),
            standardize=_common.parameter(parameters, Parameters.STANDARDIZE, True),
        )
    else:
        result.metadata["detector_settings"] = _timeseries.detector_settings(
            method, parameters
        )

    evidence = [{} for _ in range(len(frame))]
    alarms = defaultdict(dict)
    for feature, series in frame.items():
        values = series.to_numpy()
        present = np.flatnonzero(np.isfinite(values))
        if method == "pelt":
            for cut, gain in _retrospective(values[present], parameters):
                boundary = present[cut]
                evidence[boundary][feature] = gain
                alarms[len(frame) - 1, boundary][feature] = gain
        elif len(present):
            detector = _timeseries.make_detector(method, parameters)
            for offset, bin_index in enumerate(present):
                score, lag = detector.update(float(values[bin_index]))
                evidence[bin_index][feature] = score
                if lag is not None:
                    boundary = present[offset - lag]
                    alarms[bin_index, boundary][feature] = score

    counts = defaultdict(int)
    for (available, boundary), features in sorted(alarms.items()):
        counts[boundary if method == "pelt" else available] += len(features)
        result.changes.append(
            _common.DriftAlarm(
                int(boundary),
                starts[boundary],
                ends[available],
                float(len(features)),
                details={"changed_features": features},
            )
        )
    for index, (timestamp, values) in enumerate(zip(starts, frame.to_dict("records"))):
        result.scores.append(
            _common.WindowScore(
                index,
                float(counts[index]),
                timestamp,
                ends[-1] if method == "pelt" else ends[index],
                details={
                    "values": {
                        feature: value
                        for feature, value in values.items()
                        if np.isfinite(value)
                    },
                    "detector_scores": evidence[index],
                },
            )
        )
    return result
