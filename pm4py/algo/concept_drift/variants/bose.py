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
from enum import Enum
from itertools import pairwise
from typing import Any

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift import _common
from pm4py.objects.log.obj import EventLog
from pm4py.util import constants, exec_utils, xes_constants


class Parameters(Enum):
    SUB_LOG_SIZE = "sub_log_size"
    WINDOW_SIZE = "window_size"
    NUM_PERMUTATIONS = "num_permutations"
    THRESH_P_VALUE = "thresh_p_value"
    MAX_NO_CHANGE_POINTS = "max_no_change_points"
    RANDOM_STATE = "random_state"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY


def apply(
    log: EventLog | pd.DataFrame, parameters: dict[Any, Any] | None = None
) -> tuple[list[pd.DataFrame], list[float], list[float]]:
    """
    Apply concept drift detection to an event log, based on the approach described in:

    Bose, RP Jagadeesh Chandra, et al. "Handling concept drift in process mining." Advanced Information Systems Engineering: 23rd International Conference, CAiSE 2011, London, UK, June 20-24, 2011. Proceedings 23. Springer Berlin Heidelberg, 2011.

    This method detects sudden changes (concept drifts) in a process by analyzing an event log over time. It splits the log into sub-logs, extracts global features (e.g., Relation Type Count), and applies statistical tests (permutation tests) over sliding windows to identify change points where the process behavior significantly differs.

    **Parameters**
    --------------
    log : Union[EventLog, pd.DataFrame]
        The input event log, which can be either a PM4Py EventLog object or a Pandas DataFrame. The log contains traces, where each trace is a sequence of events representing a process instance.
    parameters : Optional[Dict[Any, Any]], default=None
        Configuration parameters for the algorithm. If None, default values are used. Possible keys include:

        - `Parameters.SUB_LOG_SIZE` : int, default=50 Number of traces per sub-log.
        - `Parameters.WINDOW_SIZE` : int, default=8 Number of sub-logs in each window for statistical comparison.
        - `Parameters.NUM_PERMUTATIONS` : int, default=100 Number of permutations for the permutation test.
        - `Parameters.THRESH_P_VALUE` : float, default=0.5 Threshold for p-values to consider a change point significant (lower values indicate stronger evidence of drift).
        - `Parameters.MAX_NO_CHANGE_POINTS` : int, default=5 Maximum number of change points to detect.
        - `Parameters.RANDOM_STATE` : int, optional Seed for reproducible permutations.
        - `Parameters.ACTIVITY_KEY` : str, default='concept:name' Key to identify the activity attribute in the event log.
        - `Parameters.TIMESTAMP_KEY` : str, default='time:timestamp' Key to identify the timestamp attribute in the event log.
        - `Parameters.CASE_ID_KEY` : str, default='case:concept:name' Key to identify the case ID attribute in the event log.

    **Returns**
    ------------
    returned_sublogs : List[pd.DataFrame]
        Consecutive disjoint segments of the original log, with cases in first-event order.
    change_timestamps : List[float]
        A list of timestamps where concept drifts are detected. Each timestamp corresponds to the start time of the first trace in the sub-log where a change point occurs, based on case start timestamps.
    p_values : List[float]
        A list of p-values associated with each detected change point, indicating the statistical significance of the drift (lower values suggest stronger evidence of a change).

    **Notes**
    ---------

    - The method uses a permutation test to compare feature vectors (e.g., Relation Type Count) extracted from sub-logs within sliding windows. Change points are identified where the p-value falls below the threshold.
    """
    if parameters is None:
        parameters = {}

    sub_log_size = exec_utils.get_param_value(Parameters.SUB_LOG_SIZE, parameters, 50)
    window_size = exec_utils.get_param_value(Parameters.WINDOW_SIZE, parameters, 8)
    num_permutations = exec_utils.get_param_value(
        Parameters.NUM_PERMUTATIONS, parameters, 100
    )
    thresh_p_value = exec_utils.get_param_value(
        Parameters.THRESH_P_VALUE, parameters, 0.5
    )
    max_no_change_points = exec_utils.get_param_value(
        Parameters.MAX_NO_CHANGE_POINTS, parameters, 5
    )
    random_state = exec_utils.get_param_value(Parameters.RANDOM_STATE, parameters, None)
    traces = sorted(
        _common.completed_traces(log, parameters), key=lambda trace: trace.start
    )
    _, change_points = detect_concept_drift(
        [trace.activities for trace in traces],
        sub_log_size=sub_log_size,
        window_size=window_size,
        num_permutations=num_permutations,
        thresh_p_value=thresh_p_value,
        max_no_change_points=max_no_change_points,
        random_state=random_state,
    )
    if not traces:
        return [], [], []

    boundaries = [index * sub_log_size for index, _ in change_points]
    change_timestamps = [traces[index].start.timestamp() for index in boundaries]
    p_values = [p_value for _, p_value in change_points]
    case_id_key = _common.attribute_key(
        parameters, "case_id_key", constants.CASE_CONCEPT_NAME
    )
    returned_sublogs = [
        _segment_to_dataframe(log, traces, start, stop, case_id_key)
        for start, stop in pairwise([0, *sorted(boundaries), len(traces)])
    ]

    return returned_sublogs, change_timestamps, p_values


def _segment_to_dataframe(log, traces, start, stop, case_id_key):
    if isinstance(log, pd.DataFrame):
        frame = pd.DataFrame.from_records(
            (event for trace in traces[start:stop] for event in trace.events),
            columns=log.columns,
        )
        frame.attrs = log.attrs
        return frame

    rows = []
    for index, trace in enumerate(traces[start:stop], start=start):
        case_attributes = {
            constants.CASE_ATTRIBUTE_PREFIX + key: value
            for key, value in trace.attributes.items()
        }
        case_attributes[case_id_key] = trace.attributes.get(
            xes_constants.DEFAULT_TRACEID_KEY, str(index)
        )
        rows.extend(dict(event) | case_attributes for event in trace.events)
    return pd.DataFrame.from_records(rows)


def extract_unique_activities(event_log):
    """Extract unique activities from the event log."""
    all_activities = set()
    for trace in event_log:
        for activity in trace:
            all_activities.add(activity)
    return sorted(all_activities)


def split_into_sub_logs(event_log, sub_log_size=50, keep_leftover=True):
    """
    Split the event log (list of traces) into sub-logs of size `sub_log_size`.
    Optionally keep leftover traces as a final smaller sub-log.
    """
    s = sub_log_size
    k = len(event_log) // s  # how many full-size sublogs we can get
    sub_logs = [event_log[i * s : (i + 1) * s] for i in range(k)]
    if keep_leftover:
        remainder = len(event_log) % s
        if remainder > 0:
            sub_logs.append(event_log[k * s : k * s + remainder])
    return sub_logs


def compute_follows_relation(trace, Sigma):
    """
    Compute the 'eventually follows' relation for a single trace.

    GLOBAL FOLLOWS (original):

    - For each activity 'a' encountered so far, mark that 'a' is followed by the current activity.

    DIRECT FOLLOWS (commented out):

    - For each consecutive pair (a, b), add (a, b).
    """
    follows_in_trace = set()

    # --- GLOBAL FOLLOWS version (as in your original code) ---
    seen = set()
    for activity in trace:
        for a in seen:
            if activity in Sigma:
                follows_in_trace.add((a, activity))
        seen.add(activity)

    # --- DIRECT FOLLOWS version  ---
    # for idx in range(len(trace) - 1):
    #     a = trace[idx]
    #     b = trace[idx + 1]
    #     if a in Sigma and b in Sigma:
    #         follows_in_trace.add((a, b))

    return follows_in_trace


def extract_global_features(sub_log, Sigma):
    """
    Extract the Relation Type Count (RC) feature vector for a sub-log.

    For each activity a in Sigma, count the activities that always,
    sometimes, or never follow a. The denominator is the number of traces
    containing a. A later occurrence of a can follow an earlier one.
    """
    # Count how many traces contain each activity 'a'
    n_a = {a: 0 for a in Sigma}
    # Count how many traces have a->b in the 'follows' relation
    n_a_then_b = {a: {b: 0 for b in Sigma} for a in Sigma}

    for trace in sub_log:
        # which activities appear in this trace?
        activities_in_trace = set(trace)
        for a in activities_in_trace:
            n_a[a] += 1

        # which follows-relations appear in this trace?
        follows_in_trace = compute_follows_relation(trace, Sigma)
        for a, b in follows_in_trace:
            n_a_then_b[a][b] += 1

    # Build the RC feature vector
    fRC = []
    for a in Sigma:
        counts = n_a_then_b[a].values()
        always = sum(0 < count == n_a[a] for count in counts)
        sometimes = sum(0 < count < n_a[a] for count in counts)
        never = len(Sigma) - always - sometimes
        fRC.extend((always, sometimes, never))

    return np.array(fRC, dtype=float)


def permutation_test(P1, P2, num_permutations=100, rng=None):
    """
    Perform a permutation test to compare the Euclidean distance
    between means of two sets of feature vectors P1 and P2.
    """
    P1 = np.array(P1)
    P2 = np.array(P2)
    mean_P1 = np.mean(P1, axis=0)
    mean_P2 = np.mean(P2, axis=0)
    d_obs = np.linalg.norm(mean_P1 - mean_P2)  # Observed distance

    # Stack them for shuffling
    all_data = np.vstack((P1, P2))
    n1 = len(P1)

    if rng is None:
        rng = np.random
    count = 0
    for _ in range(num_permutations):
        # A more explicit way:
        perm_indices = rng.permutation(len(all_data))
        perm_data = all_data[perm_indices]

        perm_P1 = perm_data[:n1]
        perm_P2 = perm_data[n1:]

        mean_perm_P1 = np.mean(perm_P1, axis=0)
        mean_perm_P2 = np.mean(perm_P2, axis=0)
        d_perm = np.linalg.norm(mean_perm_P1 - mean_perm_P2)

        if d_perm >= d_obs or np.isclose(d_perm, d_obs, rtol=1e-12, atol=1e-15):
            count += 1

    p_value = (count + 1) / (num_permutations + 1)
    return p_value


def detect_concept_drift(
    event_log,
    sub_log_size=50,
    window_size=8,
    num_permutations=100,
    thresh_p_value=0.5,
    max_no_change_points=5,
    random_state=None,
):
    """
    Detect concept drift in an event log using a permutation test
    over consecutive windows of sub-logs.

    Parameters:
    - event_log: List of lists, where each inner list is a trace of activities.
    - sub_log_size: Number of traces per sub-log (default: 50).
    - window_size: Number of sub-logs in each window for comparison (default: 8).
    - num_permutations: Number of permutations for the statistical test (default: 100).
    - thresh_p_value: Threshold for the p-value
    - max_no_change_points: Maximum number of change points detected
    - random_state: Seed for reproducible permutations

    Returns:
    - sub_logs: list of sub-logs, each with (up to) sub_log_size traces
    - change_points: list of sub-log indices and p-values where drift is detected
    """
    sub_log_size = _common.integer(sub_log_size, "sub_log_size")
    window_size = _common.integer(window_size, "window_size")
    num_permutations = _common.integer(num_permutations, "num_permutations")
    thresh_p_value = _common.real(thresh_p_value, "thresh_p_value", 0, 1)
    max_no_change_points = _common.integer(
        max_no_change_points, "max_no_change_points", minimum=0
    )
    rng = np.random.default_rng(random_state) if random_state is not None else None

    # 1) Extract unique activities
    Sigma = extract_unique_activities(event_log)

    # 2) Split event log into sub-logs
    sub_logs = split_into_sub_logs(
        event_log, sub_log_size=sub_log_size, keep_leftover=True
    )

    # Only equal-sized sub-logs are exchangeable under the permutation test.
    feature_vectors = [
        extract_global_features(slog, Sigma)
        for slog in sub_logs
        if len(slog) == sub_log_size
    ]

    # 4) Perform permutation tests in a sliding-window fashion
    k = len(feature_vectors)
    p_values = []

    # We need at least 2*window_size sub-logs for a valid test
    # because we compare P1= sublogs[i : i+window_size] vs P2= sublogs[i+window_size : i+2*window_size]
    for i in range(k - 2 * window_size + 1):
        P1 = feature_vectors[i : i + window_size]
        P2 = feature_vectors[i + window_size : i + 2 * window_size]

        p_value = permutation_test(P1, P2, num_permutations=num_permutations, rng=rng)
        p_values.append((i + window_size, p_value))

    # 5) Identify change points where p-value < threshold
    change_points = sorted(p_values, key=lambda x: (x[1], x[0]))
    change_points = [x for x in change_points if x[1] < thresh_p_value]
    change_points = change_points[: min(len(change_points), max_no_change_points)]

    return sub_logs, change_points
