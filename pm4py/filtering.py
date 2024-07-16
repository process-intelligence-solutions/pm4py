__doc__ = """
The ``pm4py.filtering`` module contains the filtering features offered in ``pm4py``
"""

from typing import Union, Set, List, Tuple, Collection, Any, Dict, Optional

import pandas as pd

from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.util import constants, xes_constants, pandas_utils, nx_utils
import warnings
from pm4py.util.pandas_utils import check_is_pandas_dataframe, check_pandas_dataframe_columns
from pm4py.utils import get_properties, __event_log_deprecation_warning
from pm4py.objects.ocel.obj import OCEL
import datetime


def filter_log_relative_occurrence_event_attribute(log: Union[EventLog, pd.DataFrame], min_relative_stake: float, attribute_key : str = xes_constants.DEFAULT_NAME_KEY, level="cases", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the event log keeping only the events having an attribute value which occurs:
    - in at least the specified (min_relative_stake) percentage of events, when level="events"
    - in at least the specified (min_relative_stake) percentage of cases, when level="cases"

    :param log: event log / Pandas dataframe
    :param min_relative_stake: minimum percentage of cases (expressed as a number between 0 and 1) in which the attribute should occur.
    :param attribute_key: the attribute to filter
    :param level: the level of the filter (if level="events", then events / if level="cases", then cases)
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_log_relative_occurrence_event_attribute(dataframe, 0.5, level='cases', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, timestamp_key=timestamp_key, case_id_key=case_id_key, activity_key=attribute_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.attributes import attributes_filter
        parameters[attributes_filter.Parameters.ATTRIBUTE_KEY] = attribute_key
        parameters[attributes_filter.Parameters.KEEP_ONCE_PER_CASE] = True if level == "cases" else False
        return attributes_filter.filter_df_relative_occurrence_event_attribute(log, min_relative_stake, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.attributes import attributes_filter
        parameters[attributes_filter.Parameters.ATTRIBUTE_KEY] = attribute_key
        parameters[attributes_filter.Parameters.KEEP_ONCE_PER_CASE] = True if level == "cases" else False
        return attributes_filter.filter_log_relative_occurrence_event_attribute(log, min_relative_stake, parameters=parameters)


def filter_start_activities(log: Union[EventLog, pd.DataFrame], activities: Union[Set[str], List[str]], retain: bool = True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> \
Union[EventLog, pd.DataFrame]:
    """
    Filter cases having a start activity in the provided list

    :param log: event log / Pandas dataframe
    :param activities: collection of start activities
    :param retain: if True, we retain the traces containing the given start activities, if false, we drop the traces
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_start_activities(dataframe, ['Act. A'], activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.start_activities import start_activities_filter
        parameters[start_activities_filter.Parameters.POSITIVE] = retain
        return start_activities_filter.apply(log, activities,
                                             parameters=parameters)
    else:
        from pm4py.algo.filtering.log.start_activities import start_activities_filter
        parameters[start_activities_filter.Parameters.POSITIVE] = retain
        return start_activities_filter.apply(log, activities,
                                             parameters=parameters)


def filter_end_activities(log: Union[EventLog, pd.DataFrame], activities:  Union[Set[str], List[str]], retain: bool = True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[
    EventLog, pd.DataFrame]:
    """
    Filter cases having an end activity in the provided list

    :param log: event log / Pandas dataframe
    :param activities: collection of end activities
    :param retain: if True, we retain the traces containing the given end activities, if false, we drop the traces
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_end_activities(dataframe, ['Act. Z'], activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
        parameters[end_activities_filter.Parameters.POSITIVE] = retain
        return end_activities_filter.apply(log, activities,
                                           parameters=parameters)
    else:
        from pm4py.algo.filtering.log.end_activities import end_activities_filter
        parameters[end_activities_filter.Parameters.POSITIVE] = retain
        return end_activities_filter.apply(log, activities,
                                           parameters=parameters)


def filter_event_attribute_values(log: Union[EventLog, pd.DataFrame], attribute_key: str, values:  Union[Set[str], List[str]],
                                  level: str = "case", retain: bool = True, case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filter a log object on the values of some event attribute

    :param log: event log / Pandas dataframe
    :param attribute_key: attribute to filter
    :param values: admitted (or forbidden) values
    :param level: specifies how the filter should be applied ('case' filters the cases where at least one occurrence happens, 'event' filter the events eventually trimming the cases)
    :param retain: specifies if the values should be kept or removed
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_event_attribute_values(dataframe, 'concept:name', ['Act. A', 'Act. Z'], case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, case_id_key=case_id_key)
    parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = attribute_key
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.attributes import attributes_filter
        if level == "event":
            parameters[attributes_filter.Parameters.POSITIVE] = retain
            return attributes_filter.apply_events(log, values,
                                                  parameters=parameters)
        elif level == "case":
            parameters[attributes_filter.Parameters.POSITIVE] = retain
            return attributes_filter.apply(log, values, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.attributes import attributes_filter
        if level == "event":
            parameters[attributes_filter.Parameters.POSITIVE] = retain
            return attributes_filter.apply_events(log, values,
                                                  parameters=parameters)
        elif level == "case":
            parameters[attributes_filter.Parameters.POSITIVE] = retain
            return attributes_filter.apply(log, values, parameters=parameters)


def filter_trace_attribute_values(log: Union[EventLog, pd.DataFrame], attribute_key: str, values:  Union[Set[str], List[str]],
                                  retain: bool = True, case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filter a log on the values of a trace attribute

    :param log: event log / Pandas dataframe
    :param attribute_key: attribute to filter
    :param values: collection of values to filter
    :param retain: boolean value (keep/discard matching traces)
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_trace_attribute_values(dataframe, 'case:creator', ['Mike'], case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, case_id_key=case_id_key)
    parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = attribute_key
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.attributes import attributes_filter
        parameters[attributes_filter.Parameters.POSITIVE] = retain
        return attributes_filter.apply(log, values,
                                       parameters=parameters)
    else:
        from pm4py.algo.filtering.log.attributes import attributes_filter
        parameters[attributes_filter.Parameters.POSITIVE] = retain
        return attributes_filter.apply_trace_attribute(log, values, parameters=parameters)


def filter_variants(log: Union[EventLog, pd.DataFrame], variants:  Union[Set[str], List[str], List[Tuple[str]]], retain: bool = True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[
    EventLog, pd.DataFrame]:
    """
    Filter a log on a specified set of variants

    :param log: event log / Pandas dataframe
    :param variants: collection of variants to filter; A variant should be specified as a list of tuples of activity names, e.g., [('a', 'b', 'c')]
    :param retain: boolean; if True all traces conforming to the specified variants are retained; if False, all those traces are removed
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_variants(dataframe, [('Act. A', 'Act. B', 'Act. Z'), ('Act. A', 'Act. C', 'Act. Z')], activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    from pm4py.util import variants_util
    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.variants import variants_filter
        parameters[variants_filter.Parameters.POSITIVE] = retain
        return variants_filter.apply(log, variants,
                                     parameters=parameters)
    else:
        from pm4py.algo.filtering.log.variants import variants_filter
        parameters[variants_filter.Parameters.POSITIVE] = retain
        return variants_filter.apply(log, variants,
                                     parameters=parameters)


def filter_directly_follows_relation(log: Union[EventLog, pd.DataFrame], relations: List[str], retain: bool = True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> \
        Union[EventLog, pd.DataFrame]:
    """
    Retain traces that contain any of the specified 'directly follows' relations.
    For example, if relations == [('a','b'),('a','c')] and log [<a,b,c>,<a,c,b>,<a,d,b>]
    the resulting log will contain traces describing [<a,b,c>,<a,c,b>].

    :param log: event log / Pandas dataframe
    :param relations: list of activity name pairs, which are allowed/forbidden paths
    :param retain: parameter that says whether the paths should be kept/removed
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_directly_follows_relation(dataframe, [('A','B'),('A','C')], activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        from pm4py.algo.filtering.pandas.paths import paths_filter
        parameters[paths_filter.Parameters.POSITIVE] = retain
        return paths_filter.apply(log, relations, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.paths import paths_filter
        parameters[paths_filter.Parameters.POSITIVE] = retain
        return paths_filter.apply(log, relations, parameters=parameters)


def filter_eventually_follows_relation(log: Union[EventLog, pd.DataFrame], relations: List[str], retain: bool = True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> \
        Union[EventLog, pd.DataFrame]:
    """
    Retain traces that contain any of the specified 'eventually follows' relations.
    For example, if relations == [('a','b'),('a','c')] and log [<a,b,c>,<a,c,b>,<a,d,b>]
    the resulting log will contain traces describing [<a,b,c>,<a,c,b>,<a,d,b>].

    :param log: event log / Pandas dataframe
    :param relations: list of activity name pairs, which are allowed/forbidden paths
    :param retain: parameter that says whether the paths should be kept/removed
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_eventually_follows_relation(dataframe, [('A','B'),('A','C')], activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        from pm4py.algo.filtering.pandas.ltl import ltl_checker
        parameters[ltl_checker.Parameters.POSITIVE] = retain
        if retain:
            cases = set()
        else:
            cases = set(log[case_id_key].to_numpy().tolist())
        for path in relations:
            filt_log = ltl_checker.eventually_follows(log, path,
                                                      parameters=parameters)
            this_traces = set(filt_log[case_id_key].to_numpy().tolist())
            if retain:
                cases = cases.union(this_traces)
            else:
                cases = cases.intersection(this_traces)
        return log[log[case_id_key].isin(cases)]
    else:
        from pm4py.algo.filtering.log.ltl import ltl_checker
        parameters[ltl_checker.Parameters.POSITIVE] = retain
        if retain:
            cases = set()
        else:
            cases = set(id(trace) for trace in log)
        for path in relations:
            filt_log = ltl_checker.eventually_follows(log, path,
                                                      parameters=parameters)
            this_traces = set(id(trace) for trace in filt_log)
            if retain:
                cases = cases.union(this_traces)
            else:
                cases = cases.intersection(this_traces)
        filtered_log = EventLog(attributes=log.attributes, extensions=log.extensions, omni_present=log.omni_present,
                                classifiers=log.classifiers, properties=log.properties)
        for trace in log:
            if id(trace) in cases:
                filtered_log.append(trace)
        return filtered_log


def filter_time_range(log: Union[EventLog, pd.DataFrame], dt1: str, dt2: str, mode="events", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[
    EventLog, pd.DataFrame]:
    """
    Filter a log on a time interval

    :param log: event log / Pandas dataframe
    :param dt1: left extreme of the interval
    :param dt2: right extreme of the interval
    :param mode: modality of filtering (events, traces_contained, traces_intersecting). events: any event that fits the time frame is retained; traces_contained: any trace completely contained in the timeframe is retained; traces_intersecting: any trace intersecting with the time-frame is retained.
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe1 = pm4py.filter_time_range(dataframe, '2010-01-01 00:00:00', '2011-01-01 00:00:00', mode='traces_contained', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        filtered_dataframe1 = pm4py.filter_time_range(dataframe, '2010-01-01 00:00:00', '2011-01-01 00:00:00', mode='traces_intersecting', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        filtered_dataframe1 = pm4py.filter_time_range(dataframe, '2010-01-01 00:00:00', '2011-01-01 00:00:00', mode='events', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(log, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        from pm4py.algo.filtering.pandas.timestamp import timestamp_filter
        if mode == "events":
            return timestamp_filter.apply_events(log, dt1, dt2, parameters=properties)
        elif mode == "traces_contained":
            return timestamp_filter.filter_traces_contained(log, dt1, dt2, parameters=properties)
        elif mode == "traces_intersecting":
            return timestamp_filter.filter_traces_intersecting(log, dt1, dt2, parameters=properties)
        else:
            if constants.SHOW_INTERNAL_WARNINGS:
                warnings.warn('mode provided: ' + mode + ' is not recognized; original log returned!')
            return log
    else:
        from pm4py.algo.filtering.log.timestamp import timestamp_filter
        if mode == "events":
            return timestamp_filter.apply_events(log, dt1, dt2, parameters=properties)
        elif mode == "traces_contained":
            return timestamp_filter.filter_traces_contained(log, dt1, dt2, parameters=properties)
        elif mode == "traces_intersecting":
            return timestamp_filter.filter_traces_intersecting(log, dt1, dt2, parameters=properties)
        else:
            if constants.SHOW_INTERNAL_WARNINGS:
                warnings.warn('mode provided: ' + mode + ' is not recognized; original log returned!')
            return log


def filter_between(log: Union[EventLog, pd.DataFrame], act1: Union[str, List[str]], act2: Union[str, List[str]], activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Finds all the sub-cases leading from an event with activity "act1" to an event with activity "act2" in the log,
    and returns a log containing only them.

    Example:

    Log
    A B C D E F
    A B E F C
    A B F C B C B E F C

    act1 = B
    act2 = C

    Returned sub-cases:
    B C (from the first case)
    B E F C (from the second case)
    B F C (from the third case)
    B C (from the third case)
    B E F C (from the third case)

    :param log: event log / Pandas dataframe
    :param act1: source activity  (or collection of activities)
    :param act2: target activity  (or collection of activities)
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_between(dataframe, 'A', 'D', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.between import between_filter
        return between_filter.apply(log, act1, act2, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.between import between_filter
        return between_filter.apply(log, act1, act2, parameters=parameters)


def filter_case_size(log: Union[EventLog, pd.DataFrame], min_size: int, max_size: int, case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the event log, keeping the cases having a length (number of events) included between min_size
    and max_size

    :param log: event log / Pandas dataframe
    :param min_size: minimum allowed number of events
    :param max_size: maximum allowed number of events
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_case_size(dataframe, 5, 10, case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.cases import case_filter
        case_id = parameters[
            constants.PARAMETER_CONSTANT_CASEID_KEY] if constants.PARAMETER_CONSTANT_CASEID_KEY in parameters else constants.CASE_CONCEPT_NAME
        return case_filter.filter_on_case_size(log, case_id, min_size, max_size)
    else:
        from pm4py.algo.filtering.log.cases import case_filter
        return case_filter.filter_on_case_size(log, min_size, max_size)


def filter_case_performance(log: Union[EventLog, pd.DataFrame], min_performance: float, max_performance: float, timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the event log, keeping the cases having a duration (the timestamp of the last event minus the timestamp
    of the first event) included between min_performance and max_performance

    :param log: event log / Pandas dataframe
    :param min_performance: minimum allowed case duration
    :param max_performance: maximum allowed case duration
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_case_performance(dataframe, 3600.0, 86400.0, timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.cases import case_filter
        return case_filter.filter_case_performance(log, min_performance, max_performance, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.cases import case_filter
        return case_filter.filter_case_performance(log, min_performance, max_performance, parameters=parameters)


def filter_activities_rework(log: Union[EventLog, pd.DataFrame], activity: str, min_occurrences: int = 2, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the event log, keeping the cases where the specified activity occurs at least min_occurrences times.

    :param log: event log / Pandas dataframe
    :param activity: activity
    :param min_occurrences: minimum desidered number of occurrences
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_activities_rework(dataframe, 'Approve Order', 2, activity_key='concept:name', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    parameters["min_occurrences"] = min_occurrences
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.rework import rework_filter
        return rework_filter.apply(log, activity, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.rework import rework_filter
        return rework_filter.apply(log, activity, parameters=parameters)


def filter_paths_performance(log: Union[EventLog, pd.DataFrame], path: Tuple[str, str], min_performance: float, max_performance: float, keep=True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the event log, either:
    - (keep=True) keeping the cases having the specified path (tuple of 2 activities) with a duration included between min_performance and max_performance
    - (keep=False) discarding the cases having the specified path with a duration included between min_performance and max_performance

    :param log: event log / Pandas dataframe
    :param path: tuple of two activities (source_activity, target_activity)
    :param min_performance: minimum allowed performance (of the path)
    :param max_performance: maximum allowed performance (of the path)
    :param keep: keep/discard the cases having the specified path with a duration included between min_performance and max_performance
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_paths_performance(dataframe, ('A', 'D'), 3600.0, 86400.0, activity_key='concept:name', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    parameters["positive"] = keep
    parameters["min_performance"] = min_performance
    parameters["max_performance"] = max_performance
    path = tuple(path)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.paths import paths_filter
        return paths_filter.apply_performance(log, path, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.paths import paths_filter
        return paths_filter.apply_performance(log, path, parameters=parameters)


def filter_variants_top_k(log: Union[EventLog, pd.DataFrame], k: int, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Keeps the top-k variants of the log

    :param log: event log / Pandas dataframe
    :param k: number of variants that should be kept
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_variants_top_k(dataframe, 5, activity_key='concept:name', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.variants import variants_filter
        return variants_filter.filter_variants_top_k(log, k, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.variants import variants_filter
        return variants_filter.filter_variants_top_k(log, k, parameters=parameters)


def filter_variants_by_coverage_percentage(log: Union[EventLog, pd.DataFrame], min_coverage_percentage: float, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the variants of the log by a coverage percentage
    (e.g., if min_coverage_percentage=0.4, and we have a log with 1000 cases,
    of which 500 of the variant 1, 400 of the variant 2, and 100 of the variant 3,
    the filter keeps only the traces of variant 1 and variant 2).

    :param log: event log / Pandas dataframe
    :param min_coverage_percentage: minimum allowed percentage of coverage
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_variants_by_coverage_percentage(dataframe, 0.1, activity_key='concept:name', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.variants import variants_filter
        return variants_filter.filter_variants_by_coverage_percentage(log, min_coverage_percentage, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.variants import variants_filter
        return variants_filter.filter_variants_by_coverage_percentage(log, min_coverage_percentage, parameters=parameters)


def filter_prefixes(log: Union[EventLog, pd.DataFrame], activity: str, strict=True, first_or_last="first", activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the log, keeping the prefixes to a given activity. E.g., for a log with traces:

    A,B,C,D
    A,B,Z,A,B,C,D
    A,B,C,D,C,E,C,F

    The prefixes to "C" are respectively:

    A,B
    A,B,Z,A,B
    A,B

    :param log: event log / Pandas dataframe
    :param activity: target activity of the filter
    :param strict: applies the filter strictly (cuts the occurrences of the selected activity).
    :param first_or_last: decides if the first or last occurrence of an activity should be selected as baseline for the filter.
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_prefixes(dataframe, 'Act. C', activity_key='concept:name', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    parameters["strict"] = strict
    parameters["first_or_last"] = first_or_last

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.prefixes import prefix_filter
        return prefix_filter.apply(log, activity, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.prefixes import prefix_filter
        return prefix_filter.apply(log, activity, parameters=parameters)


def filter_suffixes(log: Union[EventLog, pd.DataFrame], activity: str, strict=True, first_or_last="first", activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters the log, keeping the suffixes from a given activity. E.g., for a log with traces:

    A,B,C,D
    A,B,Z,A,B,C,D
    A,B,C,D,C,E,C,F

    The suffixes from "C" are respectively:

    D
    D
    D,C,E,C,F

    :param log: event log / Pandas dataframe
    :param activity: target activity of the filter
    :param strict: applies the filter strictly (cuts the occurrences of the selected activity).
    :param first_or_last: decides if the first or last occurrence of an activity should be selected as baseline for the filter.
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_prefixes(dataframe, 'Act. C', activity_key='concept:name', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    parameters["strict"] = strict
    parameters["first_or_last"] = first_or_last

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.suffixes import suffix_filter
        return suffix_filter.apply(log, activity, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.suffixes import suffix_filter
        return suffix_filter.apply(log, activity, parameters=parameters)


def filter_ocel_event_attribute(ocel: OCEL, attribute_key: str, attribute_values: Collection[Any], positive: bool = True) -> OCEL:
    """
    Filters the object-centric event log on the provided event attributes values

    :param ocel: object-centric event log
    :param attribute_key: attribute at the event level
    :param attribute_values: collection of attribute values
    :param positive: decides if the values should be kept (positive=True) or removed (positive=False)
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_event_attribute(ocel, 'ocel:activity', ['A', 'B', 'D'])
    """
    from pm4py.algo.filtering.ocel import event_attributes

    return event_attributes.apply(ocel, attribute_values, parameters={event_attributes.Parameters.ATTRIBUTE_KEY: attribute_key, event_attributes.Parameters.POSITIVE: positive})


def filter_ocel_object_attribute(ocel: OCEL, attribute_key: str, attribute_values: Collection[Any], positive: bool = True) -> OCEL:
    """
    Filters the object-centric event log on the provided object attributes values

    :param ocel: object-centric event log
    :param attribute_key: attribute at the event level
    :param attribute_values: collection of attribute values
    :param positive: decides if the values should be kept (positive=True) or removed (positive=False)
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_object_attribute(ocel, 'ocel:type', ['order'])
    """
    from pm4py.algo.filtering.ocel import object_attributes

    return object_attributes.apply(ocel, attribute_values, parameters={object_attributes.Parameters.ATTRIBUTE_KEY: attribute_key, object_attributes.Parameters.POSITIVE: positive})


def filter_ocel_object_types_allowed_activities(ocel: OCEL, correspondence_dict: Dict[str, Collection[str]]) -> OCEL:
    """
    Filters an object-centric event log keeping only the specified object types
    with the specified activity set (filters out the rest).

    :param ocel: object-centric event log
    :param correspondence_dict: dictionary containing, for every object type of interest, a collection of allowed activities. Example: {"order": ["Create Order"], "element": ["Create Order", "Create Delivery"]}
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_object_types_allowed_activities(ocel, {'order': ['create order', 'pay order'], 'item})
    """
    from pm4py.algo.filtering.ocel import activity_type_matching

    return activity_type_matching.apply(ocel, correspondence_dict)


def filter_ocel_object_per_type_count(ocel: OCEL, min_num_obj_type: Dict[str, int]) -> OCEL:
    """
    Filters the events of the object-centric logs which are related to at least
    the specified amount of objects per type.

    E.g. pm4py.filter_object_per_type_count(ocel, {"order": 1, "element": 2})

    Would keep the following events:

      ocel:eid ocel:timestamp ocel:activity ocel:type:element ocel:type:order
    0       e1     1980-01-01  Create Order  [i4, i1, i3, i2]            [o1]
    1      e11     1981-01-01  Create Order          [i6, i5]            [o2]
    2      e14     1981-01-04  Create Order          [i8, i7]            [o3]

    :param ocel: object-centric event log
    :param min_num_obj_type: minimum number of objects per type
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_object_per_type_count(ocel, {'order': 1, 'element': 2})
    """
    from pm4py.algo.filtering.ocel import objects_ot_count

    return objects_ot_count.apply(ocel, min_num_obj_type)


def filter_ocel_start_events_per_object_type(ocel: OCEL, object_type: str) -> OCEL:
    """
    Filters the events in which a new object for the given object type is spawn.
    (E.g. an event with activity "Create Order" might spawn new orders).

    :param ocel: object-centric event log
    :param object_type: object type to consider
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_start_events_per_object_type(ocel, 'delivery')
    """
    from pm4py.algo.filtering.ocel import ot_endpoints
    return ot_endpoints.filter_start_events_per_object_type(ocel, object_type)


def filter_ocel_end_events_per_object_type(ocel: OCEL, object_type: str) -> OCEL:
    """
    Filters the events in which an object for the given object type terminates its lifecycle.
    (E.g. an event with activity "Pay Order" might terminate an order).

    :param ocel: object-centric event log
    :param object_type: object type to consider
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_end_events_per_object_type(ocel, 'delivery')
    """
    from pm4py.algo.filtering.ocel import ot_endpoints
    return ot_endpoints.filter_end_events_per_object_type(ocel, object_type)


def filter_ocel_events_timestamp(ocel: OCEL, min_timest: Union[datetime.datetime, str], max_timest: Union[datetime.datetime, str], timestamp_key: str = "ocel:timestamp") -> OCEL:
    """
    Filters the object-centric event log keeping events in the provided timestamp range

    :param ocel: object-centric event log
    :param min_timest: left extreme of the allowed timestamp interval (provided in the format: YYYY-mm-dd HH:MM:SS)
    :param max_timest: right extreme of the allowed timestamp interval (provided in the format: YYYY-mm-dd HH:MM:SS)
    :param timestamp_key: the attribute to use as timestamp (default: ocel:timestamp)
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        filtered_ocel = pm4py.filter_ocel_events_timestamp(ocel, '1990-01-01 00:00:00', '2010-01-01 00:00:00')
    """
    from pm4py.algo.filtering.ocel import event_attributes
    return event_attributes.apply_timestamp(ocel, min_timest, max_timest, parameters={"pm4py:param:timestamp_key": timestamp_key})


def filter_four_eyes_principle(log: Union[EventLog, pd.DataFrame], activity1: str, activity2: str, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name", resource_key: str = "org:resource", keep_violations: bool = False) -> Union[EventLog, pd.DataFrame]:
    """
    Filter out the cases of the log violating the four eyes principle on the provided activities.

    :param log: event log
    :param activity1: first activity
    :param activity2: second activity
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :param resource_key: attribute to be used as resource
    :param keep_violations: boolean to discard (if False) or retain (if True) the violations
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_four_eyes_principle(dataframe, 'Act. A', 'Act. B', activity_key='concept:name', resource_key='org:resource', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key, resource_key=resource_key)
    properties["positive"] = not keep_violations

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)

        from pm4py.algo.filtering.pandas.ltl import ltl_checker
        return ltl_checker.four_eyes_principle(log, activity1, activity2, parameters=properties)
    else:
        from pm4py.algo.filtering.log.ltl import ltl_checker
        return ltl_checker.four_eyes_principle(log, activity1, activity2, parameters=properties)


def filter_activity_done_different_resources(log: Union[EventLog, pd.DataFrame], activity: str, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name", resource_key: str = "org:resource", keep_violations: bool = True) -> Union[EventLog, pd.DataFrame]:
    """
    Filters the cases where an activity is repeated by different resources.

    :param log: event log
    :param activity: activity to consider
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :param resource_key: attribute to be used as resource
    :param keep_violations: boolean to discard (if False) or retain (if True) the violations
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        filtered_dataframe = pm4py.filter_activity_done_different_resources(dataframe, 'Act. A', activity_key='concept:name', resource_key='org:resource', timestamp_key='time:timestamp', case_id_key='case:concept:name')
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key, resource_key=resource_key)
    properties["positive"] = keep_violations

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)

        from pm4py.algo.filtering.pandas.ltl import ltl_checker
        return ltl_checker.attr_value_different_persons(log, activity, parameters=properties)
    else:
        from pm4py.algo.filtering.log.ltl import ltl_checker
        return ltl_checker.attr_value_different_persons(log, activity, parameters=properties)


def filter_trace_segments(log: Union[EventLog, pd.DataFrame], admitted_traces: List[List[str]], positive: bool = True, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name") -> Union[EventLog, pd.DataFrame]:
    """
    Filters an event log on a set of traces. A trace is a sequence of activities and "...", in which:
    - a "..." before an activity tells that other activities can precede the given activity
    - a "..." after an activity tells that other activities can follow the given activity

    For example:
    - pm4py.filter_trace_segments(log, [["A", "B"]]) <- filters only the cases of the event log having exactly the process variant A,B
    - pm4py.filter_trace_segments(log, [["...", "A", "B"]]) <- filters only the cases of the event log ending with the activities A,B
    - pm4py.filter_trace_segments(log, [["A", "B", "..."]]) <- filters only the cases of the event log starting with the activities A,B
    - pm4py.filter_trace_segments(log, [["...", "A", "B", "C", "..."], ["...", "D", "E", "F", "..."]]
                                <- filters only the cases of the event log in which at any point
                                    there is A followed by B followed by C, and in which at any other point there is
                                    D followed by E followed by F

    :param log: event log / Pandas dataframe
    :param admitted_traces: collection of traces admitted from the filter (with the aforementioned criteria)
    :param positive: (boolean) indicates if the filter should keep/discard the cases satisfying the filter
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``Union[EventLog, pd.DataFrame]``

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes("tests/input_data/running-example.xes")

        filtered_log = pm4py.filter_trace_segments(log, [["...", "check ticket", "decide", "reinitiate request", "..."]])
        print(filtered_log)
    """
    __event_log_deprecation_warning(log)

    parameters = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
    parameters["positive"] = positive

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)
        from pm4py.algo.filtering.pandas.traces import trace_filter
        return trace_filter.apply(log, admitted_traces, parameters=parameters)
    else:
        from pm4py.algo.filtering.log.traces import trace_filter
        return trace_filter.apply(log, admitted_traces, parameters=parameters)


def filter_ocel_object_types(ocel: OCEL, obj_types: Collection[str], positive: bool = True, level: int = 1) -> OCEL:
    """
    Filters the object types of an object-centric event log.

    :param ocel: object-centric event log
    :param obj_types: object types to keep/remove
    :param positive: boolean value (True=keep, False=remove)
    :param level: recursively expand the set of object identifiers until the specified level
    
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_object_types(ocel, ['order'])
    """
    from copy import copy
    from pm4py.objects.ocel.util import filtering_utils
    if level == 1:
        filtered_ocel = copy(ocel)
        if positive:
            filtered_ocel.objects = filtered_ocel.objects[filtered_ocel.objects[filtered_ocel.object_type_column].isin(obj_types)]
        else:
            filtered_ocel.objects = filtered_ocel.objects[~filtered_ocel.objects[filtered_ocel.object_type_column].isin(obj_types)]
        return filtering_utils.propagate_object_filtering(filtered_ocel)
    else:
        object_ids = pandas_utils.format_unique(ocel.objects[ocel.objects[ocel.object_type_column].isin(obj_types)][ocel.object_id_column].unique())
        return filter_ocel_objects(ocel, object_ids, level=level, positive=positive)


def filter_ocel_objects(ocel: OCEL, object_identifiers: Collection[str], positive: bool = True, level: int = 1) -> OCEL:
    """
    Filters the object identifiers of an object-centric event log.

    :param ocel: object-centric event log
    :param object_identifiers: object identifiers to keep/remove
    :param positive: boolean value (True=keep, False=remove)
    :param level: recursively expand the set of object identifiers until the specified level
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_objects(ocel, ['o1'], level=1)
    """
    object_identifiers = set(object_identifiers)
    if level > 1:
        ev_rel_obj = ocel.relations.groupby(ocel.event_id_column)[ocel.object_id_column].agg(list).to_dict()
        objects_ids = ocel.objects[ocel.object_id_column].to_numpy().tolist()
        graph = {o: set() for o in objects_ids}
        for ev in ev_rel_obj:
            rel_obj = ev_rel_obj[ev]
            for o1 in rel_obj:
                for o2 in rel_obj:
                    if o1 != o2:
                        graph[o1].add(o2)
        while level > 1:
            curr = list(object_identifiers)
            for el in curr:
                for el2 in graph[el]:
                    object_identifiers.add(el2)
            level = level - 1
    from copy import copy
    from pm4py.objects.ocel.util import filtering_utils
    filtered_ocel = copy(ocel)
    if positive:
        filtered_ocel.objects = filtered_ocel.objects[filtered_ocel.objects[filtered_ocel.object_id_column].isin(object_identifiers)]
    else:
        filtered_ocel.objects = filtered_ocel.objects[~filtered_ocel.objects[filtered_ocel.object_id_column].isin(object_identifiers)]
    return filtering_utils.propagate_object_filtering(filtered_ocel)


def filter_ocel_events(ocel: OCEL, event_identifiers: Collection[str], positive: bool = True) -> OCEL:
    """
    Filters the event identifiers of an object-centric event log.

    :param ocel: object-centric event log
    :param event_identifiers: event identifiers to keep/remove
    :param positive: boolean value (True=keep, False=remove)
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_events(ocel, ['e1'])
    """
    from copy import copy
    from pm4py.objects.ocel.util import filtering_utils
    filtered_ocel = copy(ocel)
    if positive:
        filtered_ocel.events = filtered_ocel.events[filtered_ocel.events[filtered_ocel.event_id_column].isin(event_identifiers)]
    else:
        filtered_ocel.events = filtered_ocel.events[~filtered_ocel.events[filtered_ocel.event_id_column].isin(event_identifiers)]
    return filtering_utils.propagate_event_filtering(filtered_ocel)


def filter_ocel_activities_connected_object_type(ocel: OCEL, object_type: str) -> OCEL:
    """
    Filter an OCEL on the set of activities executed on objects of the given object type.

    :param ocel: object-centric event log
    :param object_type: object type
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2("tests/input_data/ocel/ocel20_example.xmlocel")
        filtered_ocel = pm4py.filter_ocel_activities_connected_object_type(ocel, "Purchase Order")
        print(filtered_ocel)
    """
    from copy import copy
    from pm4py.objects.ocel.util import filtering_utils
    relations = ocel.relations[ocel.relations[ocel.object_type_column] == object_type]
    activities = relations[ocel.event_activity].unique()
    filtered_ocel = copy(ocel)
    filtered_ocel.relations = filtered_ocel.relations[filtered_ocel.relations[ocel.event_activity].isin(activities)]

    return filtering_utils.propagate_relations_filtering(filtered_ocel)


def filter_ocel_cc_object(ocel: OCEL, object_id: str, conn_comp: Optional[List[List[str]]] = None, return_conn_comp: bool = False) -> Union[OCEL, Tuple[OCEL, List[List[str]]]]:
    """
    Returns the connected component of the object-centric event log
    to which the object with the provided identifier belongs.

    :param ocel: object-centric event log
    :param object_id: object identifier
    :param conn_comp: (optional) connected components of the objects of the OCEL
    :param return_conn_comp: if True, returns the computed connected components of the OCEL
    :rtype: ``Union[OCEL, Tuple[OCEL, List[List[str]]]]``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_cc_object(ocel, 'order1')
    """
    if conn_comp is None:
        from pm4py.algo.transformation.ocel.graphs import object_interaction_graph

        g0 = object_interaction_graph.apply(ocel)
        g = nx_utils.Graph()

        for edge in g0:
            g.add_edge(edge[0], edge[1])

        conn_comp = list(nx_utils.connected_components(g))

    for cc in conn_comp:
        if object_id in cc:
            if return_conn_comp:
                return filter_ocel_objects(ocel, cc), conn_comp
            else:
                return filter_ocel_objects(ocel, cc)

    if return_conn_comp:
        return filter_ocel_objects(ocel, [object_id]), conn_comp
    else:
        return filter_ocel_objects(ocel, [object_id])


def filter_ocel_cc_length(ocel: OCEL, min_cc_length: int, max_cc_length: int) -> OCEL:
    """
    Keeps only the objects in an OCEL belonging to a connected component with a length
    falling in a specified range

    Paper:
    Adams, Jan Niklas, et al. "Defining cases and variants for object-centric event data." 2022 4th International Conference on Process Mining (ICPM). IEEE, 2022.

    :param ocel: object-centric event log
    :param min_cc_length: minimum allowed length for the connected component
    :param max_cc_length: maximum allowed length for the connected component
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_cc_length(ocel, 2, 10)
    """
    from pm4py.algo.transformation.ocel.graphs import object_interaction_graph

    g0 = object_interaction_graph.apply(ocel)
    g = nx_utils.Graph()

    for edge in g0:
        g.add_edge(edge[0], edge[1])

    conn_comp = list(nx_utils.connected_components(g))
    conn_comp = [x for x in conn_comp if min_cc_length <= len(x) <= max_cc_length]
    objs = [y for x in conn_comp for y in x]

    return filter_ocel_objects(ocel, objs)


def filter_ocel_cc_otype(ocel: OCEL, otype: str, positive: bool = True) -> OCEL:
    """
    Filters the objects belonging to the connected components having at least an object
    of the provided object type.

    Paper:
    Adams, Jan Niklas, et al. "Defining cases and variants for object-centric event data." 2022 4th International Conference on Process Mining (ICPM). IEEE, 2022.

    :param ocel: object-centric event log
    :param otype: object type
    :param positive: boolean that keeps or discards the objects of these components
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_cc_otype(ocel, 'order')
    """
    if positive:
        objs = set(ocel.objects[ocel.objects[ocel.object_type_column] == otype][ocel.object_id_column])
    else:
        objs = set(ocel.objects[~(ocel.objects[ocel.object_type_column] == otype)][ocel.object_id_column])

    from pm4py.algo.transformation.ocel.graphs import object_interaction_graph

    g0 = object_interaction_graph.apply(ocel)
    g = nx_utils.Graph()

    for edge in g0:
        g.add_edge(edge[0], edge[1])

    conn_comp = list(nx_utils.connected_components(g))
    conn_comp = [x for x in conn_comp if len(set(x).intersection(objs)) > 0]

    objs = [y for x in conn_comp for y in x]

    return filter_ocel_objects(ocel, objs)


def filter_ocel_cc_activity(ocel: OCEL, activity: str) -> OCEL:
    """
    Filters the objects belonging to the connected components having at least an event
    with the provided activity.

    Paper:
    Adams, Jan Niklas, et al. "Defining cases and variants for object-centric event data." 2022 4th International Conference on Process Mining (ICPM). IEEE, 2022.

    :param ocel: object-centric event log
    :param activity: activity
    :rtype: ``OCEL``

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('log.jsonocel')
        filtered_ocel = pm4py.filter_ocel_cc_activity(ocel, 'Create Order')
    """
    evs = ocel.events[ocel.events[ocel.event_activity] == activity][ocel.event_id_column].to_numpy().tolist()
    objs = pandas_utils.format_unique(ocel.relations[ocel.relations[ocel.event_id_column].isin(evs)][ocel.object_id_column].unique())

    from pm4py.algo.transformation.ocel.graphs import object_interaction_graph

    g0 = object_interaction_graph.apply(ocel)
    g = nx_utils.Graph()

    for edge in g0:
        g.add_edge(edge[0], edge[1])

    conn_comp = list(nx_utils.connected_components(g))
    conn_comp = [x for x in conn_comp if len(set(x).intersection(objs)) > 0]

    objs = [y for x in conn_comp for y in x]

    return filter_ocel_objects(ocel, objs)
