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
Contact: info@processintelligence.solutions
'''
import numpy as np

from pm4py.util import xes_constants, pandas_utils, constants
from pm4py.util.business_hours import (
    _as_utc_datetime,
    _prepare_scheduled_business_hours,
    soj_time_business_hours_diff,
)
import pandas as pd


def _prepare_scheduled_dataframe(df, timestamp_key, start_timestamp_key):
    """Validate source timestamps and normalise a private frame to UTC."""
    df = df.copy()
    columns = {timestamp_key}
    if start_timestamp_key in df.columns:
        columns.add(start_timestamp_key)
    for column in columns:
        if df.empty and getattr(df[column].dtype, "tz", None) is None:
            raise ValueError("An empty timestamp column needs an aware dtype")
        values = [_as_utc_datetime(value) for value in df[column]]
        df[column] = pd.to_datetime(values, utc=True)
    return df


def get_dfg_graph(
        df,
        measure="frequency",
        activity_key="concept:name",
        case_id_glue="case:concept:name",
        start_timestamp_key=None,
        timestamp_key="time:timestamp",
        perf_aggregation_key="mean",
        sort_caseid_required=True,
        sort_timestamp_along_case_id=True,
        keep_once_per_case=False,
        window=1,
        business_hours=False,
        business_hours_slot=None,
        workcalendar=constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
        target_activity_key=None,
        reduce_columns=True,
        cost_attribute=None,
        business_timezone=None,
):
    """
    Get DFG graph from Pandas dataframe - optimized version

    Parameters
    -----------
    df
        Dataframe
    measure
        Measure to use (frequency/performance/both)
    activity_key
        Activity key to use in the grouping
    case_id_glue
        Case ID identifier
    start_timestamp_key
        Start timestamp key
    timestamp_key
        Timestamp key
    perf_aggregation_key
        Performance aggregation key (mean, median, min, max)
    sort_caseid_required
        Specify if a sort on the Case ID is required
    sort_timestamp_along_case_id
        Specifying if sorting by timestamp along the CaseID is required
    keep_once_per_case
        In the counts, keep only one occurrence of the path per case (the first)
    window
        Window of the DFG (default 1)
    business_timezone
        Optional IANA timezone for scheduled elapsed time. Requires
        business_hours=True and aware timestamps at microsecond precision.

    Returns
    -------
    dfg : dict
        DFG in the chosen measure (may be only the frequency, only the performance, or both)

    """
    if business_timezone is not None:
        if not business_hours:
            raise ValueError("business_timezone requires business_hours=True")
        if business_hours_slot is None:
            business_hours_slot = constants.DEFAULT_BUSINESS_HOUR_SLOTS
        business_hours_slot = tuple(
            tuple(slot) for slot in business_hours_slot
        )
        _prepare_scheduled_business_hours(
            business_hours_slot, business_timezone
        )
        df = _prepare_scheduled_dataframe(
            df,
            timestamp_key,
            (
                xes_constants.DEFAULT_START_TIMESTAMP_KEY
                if start_timestamp_key is None else start_timestamp_key
            ),
        )
        pandas_utils.check_pandas_dataframe_columns(
            df,
            activity_key=activity_key,
            case_id_key=case_id_glue,
            timestamp_key=timestamp_key,
            start_timestamp_key=start_timestamp_key,
        )

    # added support to specify an activity key for the target event which is different
    # from the activity key of the source event.
    if target_activity_key is None:
        target_activity_key = activity_key

    # if not differently specified, set the start timestamp key to the timestamp key
    # to avoid retro-compatibility problems
    st_eq_ct = start_timestamp_key == timestamp_key
    if start_timestamp_key is None:
        start_timestamp_key = xes_constants.DEFAULT_START_TIMESTAMP_KEY
        if start_timestamp_key not in df.columns:
            df[start_timestamp_key] = df[timestamp_key]
        st_eq_ct = True

    # Determine which columns we need to keep before reducing
    needed_columns = {case_id_glue, activity_key, target_activity_key}
    if measure != "frequency" or sort_timestamp_along_case_id:
        needed_columns.update({start_timestamp_key, timestamp_key})
    if measure == "cost":
        needed_columns.add(cost_attribute)

    # Reduce dataframe to necessary columns (more efficient than previous implementation)
    if reduce_columns:
        df = df[list(needed_columns)]

    if measure == "cost":
        df[cost_attribute] = df[cost_attribute].fillna(0)  # Using 0 directly is more efficient

    # Create a view with the needed sorting for more efficient memory usage
    if sort_caseid_required:
        if sort_timestamp_along_case_id:
            df = df.sort_values([case_id_glue, start_timestamp_key, timestamp_key])
        else:
            df = df.sort_values(case_id_glue)

    # Pre-create the suffixed column names for more efficient joining
    suffix = "_2"
    # Get a list of column names before shift to avoid recreating them
    orig_cols = df.columns.tolist()
    shifted_cols = [str(col) + suffix for col in orig_cols]

    # Shift the dataframe by window
    df_shifted = df.shift(-window)
    df_shifted.columns = shifted_cols

    # Concatenate the dataframes efficiently
    df_successive_rows = pandas_utils.DATAFRAME.concat([df, df_shifted], axis=1)

    # Filter for matching case IDs (more efficient with direct access)
    case_id_col = case_id_glue
    case_id_col_shifted = case_id_glue + suffix
    df_successive_rows = df_successive_rows[df_successive_rows[case_id_col] == df_successive_rows[case_id_col_shifted]]

    # Handle keep_once_per_case more efficiently
    if keep_once_per_case:
        # Use drop_duplicates which is more efficient than groupby + first for this operation
        df_successive_rows = df_successive_rows.drop_duplicates(
            subset=[case_id_glue, activity_key, target_activity_key + suffix]
        )

    # Calculate performance metrics if needed
    if measure in ["performance", "both"]:
        if not st_eq_ct:
            # Calculate max more efficiently using numpy
            df_successive_rows[start_timestamp_key + suffix] = np.maximum(
                df_successive_rows[start_timestamp_key + suffix],
                df_successive_rows[timestamp_key]
            )

        # Calculate the time difference
        if business_hours:
            if business_hours_slot is None:
                business_hours_slot = constants.DEFAULT_BUSINESS_HOUR_SLOTS

            # Business hours calculation requires Python datetime objects
            # Use a more efficient approach than apply, but ensure we're working with correct datetime types

            # Convert timestamps - we need to use to_pydatetime() to get Python datetime objects
            # that are compatible with the business hours function
            if hasattr(df_successive_rows[timestamp_key], 'dt'):
                # If timestamps are already pandas datetime, convert to Python datetime
                ts_values = np.array(df_successive_rows[timestamp_key].dt.to_pydatetime())
                start_ts_values = np.array(df_successive_rows[start_timestamp_key + suffix].dt.to_pydatetime())
            else:
                # If timestamps are pandas Timestamp objects or strings, convert properly
                ts_values = np.array(pandas_utils.DATAFRAME.to_datetime(df_successive_rows[timestamp_key]).dt.to_pydatetime())
                start_ts_values = np.array(pandas_utils.DATAFRAME.to_datetime(df_successive_rows[start_timestamp_key + suffix]).dt.to_pydatetime())

            # Use list comprehension which is faster than apply but handles datetime objects correctly
            flow_times = [
                soj_time_business_hours_diff(
                    ts, start_ts, business_hours_slot, workcalendar,
                    business_timezone=business_timezone,
                )
                for ts, start_ts in zip(ts_values, start_ts_values)
            ]

            df_successive_rows[constants.DEFAULT_FLOW_TIME] = flow_times
        else:
            # Vectorized timestamp difference calculation (already efficient)
            difference = df_successive_rows[start_timestamp_key + suffix] - df_successive_rows[timestamp_key]
            df_successive_rows[constants.DEFAULT_FLOW_TIME] = pandas_utils.get_total_seconds(difference)

    # Set up grouping based on measure
    group_cols = [activity_key, target_activity_key + suffix]

    if measure == "performance" or measure == "both":
        agg_col = constants.DEFAULT_FLOW_TIME
    elif measure == "cost":
        agg_col = cost_attribute + suffix
    else:
        # For frequency, find the first non-grouping column to use (more efficient)
        remaining_cols = set(df_successive_rows.columns) - set(group_cols)
        agg_col = next(iter(remaining_cols)) if remaining_cols else case_id_col

    # Create dictionary directly rather than creating a Series object first (more efficient)
    if measure == "frequency" or measure == "both":
        # Use value_counts which is more efficient than groupby+size for frequency
        if type(df) is pd.DataFrame and len(group_cols) == 2:  # Most common case
            temp_df = df_successive_rows[group_cols].copy()
            temp_df['dummy'] = 1  # Add a column to count
            pivot = temp_df.pivot_table(
                index=group_cols[0],
                columns=group_cols[1],
                values='dummy',
                aggfunc='count',
                fill_value=0
            )
            dfg_frequency = {(idx, col): val for idx, row in pivot.iterrows() for col, val in row.items() if val > 0}
        else:
            # Fallback to groupby
            dfg_frequency = df_successive_rows.groupby(group_cols).size().to_dict()

    # Performance metrics calculation
    dfg_performance = {}
    if measure in ["performance", "cost", "both"]:
        grouped = df_successive_rows.groupby(group_cols)[agg_col]

        if perf_aggregation_key == "all":
            # Calculate all metrics at once (more efficient than separate calls)
            metrics = grouped.agg(['mean', 'median', 'max', 'min', 'sum', 'std'])

            if type(metrics) is pd.DataFrame:
                metrics = metrics.iterrows()
            else:
                metrics = metrics.to_pandas().iterrows()

            # Convert to the expected dictionary structure
            dfg_performance = {
                group: {
                    'mean': row['mean'],
                    'median': row['median'],
                    'max': row['max'],
                    'min': row['min'],
                    'sum': row['sum'],
                    'stdev': row['std']
                }
                for group, row in metrics
            }
        elif perf_aggregation_key == "raw_values":
            dfg_performance = grouped.agg(list).to_dict()
        else:
            dfg_performance = grouped.agg(perf_aggregation_key).to_dict()

    # Return appropriate results based on measure
    if measure == "frequency":
        return dfg_frequency
    elif measure == "performance" or measure == "cost":
        return dfg_performance
    else:  # measure == "both"
        return [dfg_frequency, dfg_performance]


def get_partial_order_dataframe(
    df,
    start_timestamp_key=None,
    timestamp_key="time:timestamp",
    case_id_glue="case:concept:name",
    activity_key="concept:name",
    sort_caseid_required=True,
    sort_timestamp_along_case_id=True,
    reduce_dataframe=True,
    keep_first_following=True,
    business_hours=False,
    business_hours_slot=None,
    workcalendar=constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
    event_index=constants.DEFAULT_INDEX_KEY,
):
    """
    Gets the partial order between events (of the same case) in a Pandas dataframe

    Parameters
    --------------
    df
        Dataframe
    start_timestamp_key
        Start timestamp key (if not provided, defaulted to the timestamp_key)
    timestamp_key
        Complete timestamp
    case_id_glue
        Column of the dataframe to use as case ID
    activity_key
        Activity key
    sort_caseid_required
        Tells if a sort by case ID is required (default: True)
    sort_timestamp_along_case_id
        Tells if a sort by timestamp is required along the case ID (default: True)
    reduce_dataframe
        To fasten operation, keep only essential columns in the dataframe
    keep_first_following
        Keep only the first event following the given event
    Returns
    ---------------
    part_ord_dataframe
        Partial order dataframe (with @@flow_time between events)
    """
    # if not differently specified, set the start timestamp key to the timestamp key
    # to avoid retro-compatibility problems
    if start_timestamp_key is None:
        start_timestamp_key = xes_constants.DEFAULT_START_TIMESTAMP_KEY

    if start_timestamp_key not in df:
        df[start_timestamp_key] = df[timestamp_key]

    # to increase the speed of the approaches reduce dataframe to case, activity (and possibly complete timestamp)
    # columns
    if reduce_dataframe:
        needed_columns = {
            case_id_glue,
            activity_key,
            start_timestamp_key,
            timestamp_key,
        }
        if event_index in df.columns:
            needed_columns.add(event_index)
        needed_columns = list(needed_columns)
        df = df[needed_columns]

    # to get rows belonging to same case ID together, we need to sort on case
    # ID
    if sort_caseid_required:
        if sort_timestamp_along_case_id:
            df = df.sort_values(
                [case_id_glue, start_timestamp_key, timestamp_key]
            )
        else:
            df = df.sort_values(case_id_glue)
        df = df.reset_index(drop=True)

    if event_index not in df.columns:
        df = pandas_utils.insert_index(
            df, event_index, copy_dataframe=False, reset_index=False
        )

    df = df.set_index(case_id_glue)

    df = df.join(df, rsuffix="_2")
    df = df[df[event_index] < df[event_index + "_2"]]
    df = df[df[timestamp_key] <= df[start_timestamp_key + "_2"]]

    df = df.reset_index()

    if business_hours:
        if business_hours_slot is None:
            business_hours_slot = constants.DEFAULT_BUSINESS_HOUR_SLOTS
        df[constants.DEFAULT_FLOW_TIME] = df.apply(
            lambda x: soj_time_business_hours_diff(
                x[timestamp_key],
                x[start_timestamp_key + "_2"],
                business_hours_slot,
                workcalendar,
            ),
            axis=1,
        )
    else:
        df[constants.DEFAULT_FLOW_TIME] = pandas_utils.get_total_seconds(
            df[start_timestamp_key + "_2"] - df[timestamp_key]
        )

    if keep_first_following:
        df = df.groupby(constants.DEFAULT_INDEX_KEY).first().reset_index()

    return df


def get_concurrent_events_dataframe(
    df,
    start_timestamp_key=None,
    timestamp_key="time:timestamp",
    case_id_glue="case:concept:name",
    activity_key="concept:name",
    sort_caseid_required=True,
    sort_timestamp_along_case_id=True,
    reduce_dataframe=True,
    max_start_column="@@max_start_column",
    min_complete_column="@@min_complete_column",
    diff_maxs_minc="@@diff_maxs_minc",
    strict=False,
):
    """
    Gets the concurrent events (of the same case) in a Pandas dataframe

    Parameters
    --------------
    df
        Dataframe
    start_timestamp_key
        Start timestamp key (if not provided, defaulted to the timestamp_key)
    timestamp_key
        Complete timestamp
    case_id_glue
        Column of the dataframe to use as case ID
    activity_key
        Activity key
    sort_caseid_required
        Tells if a sort by case ID is required (default: True)
    sort_timestamp_along_case_id
        Tells if a sort by timestamp is required along the case ID (default: True)
    reduce_dataframe
        To fasten operation, keep only essential columns in the dataframe
    strict
        Gets only entries that are strictly concurrent (i.e. the length of the intersection as real interval is > 0)

    Returns
    ---------------
    conc_ev_dataframe
        Concurrent events dataframe (with @@diff_maxs_minc as the size of the intersection of the intervals)
    """
    # if not differently specified, set the start timestamp key to the timestamp key
    # to avoid retro-compatibility problems
    if start_timestamp_key is None:
        start_timestamp_key = xes_constants.DEFAULT_START_TIMESTAMP_KEY
        df[start_timestamp_key] = df[timestamp_key]

    # to get rows belonging to same case ID together, we need to sort on case
    # ID
    if sort_caseid_required:
        if sort_timestamp_along_case_id:
            df = df.sort_values(
                [case_id_glue, start_timestamp_key, timestamp_key]
            )
        else:
            df = df.sort_values(case_id_glue)

    # to increase the speed of the approaches reduce dataframe to case, activity (and possibly complete timestamp)
    # columns
    if reduce_dataframe:
        df = df[
            [case_id_glue, activity_key, start_timestamp_key, timestamp_key]
        ]

    df = pandas_utils.insert_index(df)
    df = df.set_index(case_id_glue)
    df_copy = df.copy()

    df = df.join(df_copy, rsuffix="_2").dropna()
    df = df[
        df[constants.DEFAULT_INDEX_KEY]
        < df[constants.DEFAULT_INDEX_KEY + "_2"]
    ]
    df[max_start_column] = df[
        [start_timestamp_key, start_timestamp_key + "_2"]
    ].max(axis=1)
    df[min_complete_column] = df[[timestamp_key, timestamp_key + "_2"]].min(
        axis=1
    )
    df[max_start_column] = df[max_start_column].apply(lambda x: x.timestamp())
    df[min_complete_column] = df[min_complete_column].apply(
        lambda x: x.timestamp()
    )
    df[diff_maxs_minc] = df[min_complete_column] - df[max_start_column]
    if strict:
        df = df[df[diff_maxs_minc] > 0]
    else:
        df = df[df[diff_maxs_minc] >= 0]

    return df
