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
import pandas as pd
import importlib.util

from pm4py.util import constants, xes_constants
import numpy as np


def get_default_dataframe_environment():
    if importlib.util.find_spec("cudf"):
        # import cudf; return cudf
        try:
            import cudf.pandas

            cudf.pandas.install()
        except BaseException:
            pass
    import pandas as pd

    return pd


DATAFRAME = get_default_dataframe_environment()


def to_dict_records(df):
    """
    Pandas dataframe to dictionary (records method)

    Parameters
    ---------------
    df
        Dataframe

    Returns
    --------------
    list_dictio
        List containing a dictionary for each row
    """
    if is_polars_lazyframe(df):
        return df.collect().to_dicts()

    return df.to_dict(orient="records")


def to_dict_index(df):
    """
    Pandas dataframe to dictionary (index method)

    Parameters
    ---------------
    df
        Dataframe

    Returns
    --------------
    dict
        dict like {index -> {column -> value}}
    """
    if is_polars_lazyframe(df):
        collected_df = df.collect()
        return {
            idx: row
            for idx, row in enumerate(collected_df.iter_rows(named=True))
        }

    return df.to_dict(orient="index")


def insert_index(
    df,
    column_name=constants.DEFAULT_INDEX_KEY,
    copy_dataframe=True,
    reset_index=True,
):
    """
    Inserts the dataframe index in the specified column

    Parameters
    --------------
    df
        Dataframe
    column_name
        Name of the column that should host the index
    copy_dataframe
        Establishes if the original dataframe should be copied before inserting the column

    Returns
    --------------
    df
        Dataframe with index
    """
    if is_polars_lazyframe(df):
        lf = df
        existing_columns = set(_lazyframe_column_names(lf))
        if column_name in existing_columns:
            lf = lf.drop(column_name)
        return lf.with_row_count(name=column_name)

    if copy_dataframe:
        df = df.copy()

    if reset_index:
        df = df.reset_index(drop=True)

    df[column_name] = df.index
    return df


def insert_case_index(
    df,
    column_name=constants.DEFAULT_CASE_INDEX_KEY,
    case_id=constants.CASE_CONCEPT_NAME,
    copy_dataframe=True,
):
    """
    Inserts the case number in the dataframe

    Parameters
    ---------------
    df
        Dataframe
    column_name
        Name of the column that should host the case index
    case_id
        Case identifier
    copy_dataframe
        Establishes if the original dataframe should be copied before inserting the column

    Returns
    ---------------
    df
        Dataframe with case index
    """
    if is_polars_lazyframe(df):
        import polars as pl  # type: ignore[import-untyped]

        lf = df
        existing_columns = set(_lazyframe_column_names(lf))
        if column_name in existing_columns:
            lf = lf.drop(column_name)
        case_map = (
            lf.select(pl.col(case_id))
            .unique(maintain_order=True)
            .with_row_count(name=column_name)
        )
        return lf.join(case_map, on=case_id, how="left")

    if copy_dataframe:
        df = df.copy()

    df[column_name] = df.groupby(case_id).ngroup()
    return df


def insert_ev_in_tr_index(
    df: pd.DataFrame,
    case_id: str = constants.CASE_CONCEPT_NAME,
    column_name: str = constants.DEFAULT_INDEX_IN_TRACE_KEY,
    copy_dataframe=True,
) -> pd.DataFrame:
    """
    Inserts a column that specify the index of the event inside the case

    Parameters
    ---------------
    df
        Dataframe
    case_id
        Column that hosts the case identifier
    column_name
        Name of the column that should host the index

    Returns
    --------------
    df
        Dataframe with index
    """
    if is_polars_lazyframe(df):
        import polars as pl  # type: ignore[import-untyped]

        lf = df
        existing_columns = set(_lazyframe_column_names(lf))
        if column_name in existing_columns:
            lf = lf.drop(column_name)
        return lf.with_columns(
            (pl.col(case_id).cum_count().over(case_id) - 1).alias(column_name)
        )

    if copy_dataframe:
        df = df.copy()

    df_trace_idx = df.groupby(case_id).cumcount()
    df[column_name] = df_trace_idx
    return df


def format_unique(values):
    try:
        values = values.to_numpy()
    except BaseException:
        pass

    try:
        values = values.tolist()
    except AttributeError:
        try:
            values = values.to_list()
        except AttributeError:
            values = list(values)

    return values


def insert_feature_activity_position_in_trace(
    df: pd.DataFrame,
    case_id: str = constants.CASE_CONCEPT_NAME,
    activity_key: str = xes_constants.DEFAULT_NAME_KEY,
    prefix="@@position_",
):
    """
    Inserts additional columns @@position_ACT1, @@position_ACT2 ...
    which are populated for every event having activity ACT1, ACT2 respectively,
    with the index of the event inside its case.

    Parameters
    ------------------
    df
        Pandas dataframe
    case_id
        Case idntifier
    activity_key
        Activity
    prefix
        Prefix of the "activity position in trace" feature (default: @@position_)

    Returns
    ------------------
    df
        Pandas dataframe
    """
    if is_polars_lazyframe(df):
        import polars as pl  # type: ignore[import-untyped]

        lf = insert_ev_in_tr_index(
            df,
            case_id=case_id,
            column_name=constants.DEFAULT_INDEX_IN_TRACE_KEY,
            copy_dataframe=False,
        )
        activities = (
            lf.select(pl.col(activity_key))
            .unique()
            .collect()
            .get_column(activity_key)
            .to_list()
        )
        existing_columns = set(_lazyframe_column_names(lf))
        for act in activities:
            column_name = prefix + str(act)
            if column_name in existing_columns:
                lf = lf.drop(column_name)
                existing_columns.discard(column_name)
            lf = lf.with_columns(
                pl.when(pl.col(activity_key) == act)
                .then(pl.col(constants.DEFAULT_INDEX_IN_TRACE_KEY))
                .otherwise(pl.lit(None))
                .alias(column_name)
            )
            existing_columns.add(column_name)
        return lf

    df = insert_ev_in_tr_index(df, case_id=case_id)
    activities = format_unique(df[activity_key].unique())
    for act in activities:
        df[prefix + act] = df[activity_key].apply(
            lambda x: np.nan if x == act else -1
        )
        df[prefix + act] = df[prefix + act].fillna(
            df[constants.DEFAULT_INDEX_IN_TRACE_KEY]
        )
        df[prefix + act] = df[prefix + act].replace(-1, np.nan)
    return df


def insert_case_arrival_finish_rate(
    log: pd.DataFrame,
    case_id_column=constants.CASE_CONCEPT_NAME,
    timestamp_column=xes_constants.DEFAULT_TIMESTAMP_KEY,
    start_timestamp_column=None,
    arrival_rate_column="@@arrival_rate",
    finish_rate_column="@@finish_rate",
) -> pd.DataFrame:
    """
    Inserts the arrival/finish rate in the dataframe.

    Parameters
    -----------------
    log
        Pandas dataframe

    Returns
    -----------------
    log
        Pandas dataframe enriched by arrival and finish rate
    """
    if is_polars_lazyframe(log):
        import polars as pl  # type: ignore[import-untyped]

        if start_timestamp_column is None:
            start_timestamp_column = timestamp_column

        lf = log
        existing_columns = set(_lazyframe_column_names(lf))
        if arrival_rate_column in existing_columns:
            lf = lf.drop(arrival_rate_column)
            existing_columns.discard(arrival_rate_column)
        if finish_rate_column in existing_columns:
            lf = lf.drop(finish_rate_column)

        arrival = (
            lf.select(
                pl.col(case_id_column),
                pl.col(start_timestamp_column).alias("__start_ts"),
            )
            .group_by(case_id_column)
            .agg(pl.col("__start_ts").min().alias("__start_ts"))
            .with_columns(
                pl.col("__start_ts")
                .dt.timestamp()
                .alias("__arrival_microseconds")
            )
            .sort(["__arrival_microseconds", case_id_column])
            .with_columns(
                pl.col("__arrival_microseconds")
                .diff()
                .fill_null(0)
                .truediv(1_000_000)
                .alias(arrival_rate_column)
            )
            .select(case_id_column, arrival_rate_column)
        )

        finish = (
            lf.select(
                pl.col(case_id_column),
                pl.col(timestamp_column).alias("__finish_ts"),
            )
            .group_by(case_id_column)
            .agg(pl.col("__finish_ts").max().alias("__finish_ts"))
            .with_columns(
                pl.col("__finish_ts")
                .dt.timestamp()
                .alias("__finish_microseconds")
            )
            .sort(["__finish_microseconds", case_id_column])
            .with_columns(
                pl.col("__finish_microseconds")
                .diff()
                .fill_null(0)
                .truediv(1_000_000)
                .alias(finish_rate_column)
            )
            .select(case_id_column, finish_rate_column)
        )

        lf = lf.join(arrival, on=case_id_column, how="left")
        lf = lf.join(finish, on=case_id_column, how="left")
        return lf

    if start_timestamp_column is None:
        start_timestamp_column = timestamp_column

    case_arrival = (
        log.groupby(case_id_column)[start_timestamp_column]
        .agg("min")
        .to_dict()
    )
    case_arrival = [[x, y.timestamp()] for x, y in case_arrival.items()]
    case_arrival.sort(key=lambda x: (x[1], x[0]))

    case_finish = (
        log.groupby(case_id_column)[timestamp_column].agg("max").to_dict()
    )
    case_finish = [[x, y.timestamp()] for x, y in case_finish.items()]
    case_finish.sort(key=lambda x: (x[1], x[0]))

    i = len(case_arrival) - 1
    while i > 0:
        case_arrival[i][1] = case_arrival[i][1] - case_arrival[i - 1][1]
        i = i - 1
    case_arrival[0][1] = 0
    case_arrival = {x[0]: x[1] for x in case_arrival}

    i = len(case_finish) - 1
    while i > 0:
        case_finish[i][1] = case_finish[i][1] - case_finish[i - 1][1]
        i = i - 1
    case_finish[0][1] = 0
    case_finish = {x[0]: x[1] for x in case_finish}

    log[arrival_rate_column] = log[case_id_column].map(case_arrival)
    log[finish_rate_column] = log[case_id_column].map(case_finish)

    return log


def insert_case_service_waiting_time(
    log: pd.DataFrame,
    case_id_column=constants.CASE_CONCEPT_NAME,
    timestamp_column=xes_constants.DEFAULT_TIMESTAMP_KEY,
    start_timestamp_column=None,
    diff_start_end_column="@@diff_start_end",
    service_time_column="@@service_time",
    sojourn_time_column="@@sojourn_time",
    waiting_time_column="@@waiting_time",
) -> pd.DataFrame:
    """
    Inserts the service/waiting/sojourn time in the dataframe.

    Parameters
    ----------------
    log
        Pandas dataframe
    parameters
        Parameters of the method

    Returns
    ----------------
    log
        Pandas dataframe with service, waiting and sojourn time
    """
    if is_polars_lazyframe(log):
        import polars as pl  # type: ignore[import-untyped]

        if start_timestamp_column is None:
            start_timestamp_column = timestamp_column

        lf = log
        existing_columns = set(_lazyframe_column_names(lf))
        for col_name in (
            diff_start_end_column,
            service_time_column,
            sojourn_time_column,
            waiting_time_column,
        ):
            if col_name in existing_columns:
                lf = lf.drop(col_name)
                existing_columns.discard(col_name)

        lf = lf.with_columns(
            (
                pl.col(timestamp_column).dt.timestamp()
                - pl.col(start_timestamp_column).dt.timestamp()
            )
            .truediv(1_000_000)
            .alias(diff_start_end_column)
        )

        service = (
            lf.group_by(case_id_column)
            .agg(
                pl.col(diff_start_end_column)
                .sum()
                .alias(service_time_column)
            )
        )

        sojourn = (
            lf.group_by(case_id_column)
            .agg(
                pl.col(start_timestamp_column)
                .dt.timestamp()
                .min()
                .alias("__case_start_ts"),
                pl.col(timestamp_column)
                .dt.timestamp()
                .max()
                .alias("__case_end_ts"),
            )
            .with_columns(
                (
                    pl.col("__case_end_ts") - pl.col("__case_start_ts")
                )
                .truediv(1_000_000)
                .alias(sojourn_time_column)
            )
            .select(case_id_column, sojourn_time_column)
        )

        lf = lf.join(service, on=case_id_column, how="left")
        lf = lf.join(sojourn, on=case_id_column, how="left")
        lf = lf.with_columns(
            (
                pl.col(sojourn_time_column) - pl.col(service_time_column)
            ).alias(waiting_time_column)
        )
        return lf

    if start_timestamp_column is None:
        start_timestamp_column = timestamp_column

    log[diff_start_end_column] = get_total_seconds(
        log[timestamp_column] - log[start_timestamp_column]
    )
    service_times = (
        log.groupby(case_id_column)[diff_start_end_column].sum().to_dict()
    )
    log[service_time_column] = log[case_id_column].map(service_times)

    start_timestamps = (
        log.groupby(case_id_column)[start_timestamp_column]
        .agg("min")
        .to_dict()
    )
    complete_timestamps = (
        log.groupby(case_id_column)[timestamp_column].agg("max").to_dict()
    )
    sojourn_time_cases = {
        x: complete_timestamps[x].timestamp() - start_timestamps[x].timestamp()
        for x in start_timestamps
    }

    log[sojourn_time_column] = log[case_id_column].map(sojourn_time_cases)
    log[waiting_time_column] = (
        log[sojourn_time_column] - log[service_time_column]
    )

    return log


def check_is_pandas_dataframe(log):
    """
    Checks if a log object is a dataframe

    Parameters
    -------------
    log
        Log object

    Returns
    -------------
    boolean
        Is dataframe?
    """
    log_type = str(type(log)).lower()
    return "dataframe" in log_type or "lazyframe" in log_type


def is_polars_lazyframe(df):
    """Return True if the provided dataframe is a Polars LazyFrame."""
    df_type = str(type(df)).lower()
    return "polars" in df_type and "lazyframe" in df_type


def _lazyframe_schema(df):
    """Return the Polars schema without triggering expensive resolution via .columns/.schema."""
    return df.collect_schema()


def _lazyframe_column_names(df):
    """Return column names for a Polars LazyFrame without collecting the frame."""
    return _lazyframe_schema(df).names()


def instantiate_dataframe(*args, **kwargs):
    return DATAFRAME.DataFrame(*args, **kwargs)


def instantiate_dataframe_from_dict(*args, **kwargs):
    return DATAFRAME.DataFrame.from_dict(*args, **kwargs)


def instantiate_dataframe_from_records(*args, **kwargs):
    return DATAFRAME.DataFrame.from_records(*args, **kwargs)


def get_grouper(*args, **kwargs):
    return DATAFRAME.Grouper(*args, **kwargs)


def get_total_seconds(difference):
    return (
        86400 * difference.dt.days
        + difference.dt.seconds
        + 10**-6 * difference.dt.microseconds
        + 10**-9 * difference.dt.nanoseconds
    )


def convert_to_seconds(dt_column):
    try:
        # Pandas
        return dt_column.values.astype(np.int64) / 10**9
    except BaseException:
        # CUDF
        return [x / 10**9 for x in dt_column.to_numpy().tolist()]


def dataframe_column_string_to_datetime(*args, **kwargs):
    if (
        importlib.util.find_spec("cudf")
        or constants.TEST_CUDF_DATAFRAMES_ENVIRONMENT
    ):
        pass
        """if DATAFRAME == pd:
            format = kwargs["format"] if "format" in kwargs else None
            if format not in [None, 'mixed', 'ISO8601']:
                kwargs["exact"] = False"""

    return DATAFRAME.to_datetime(*args, **kwargs)


def read_csv(*args, **kwargs):
    if (
        importlib.util.find_spec("cudf")
        or constants.TEST_CUDF_DATAFRAMES_ENVIRONMENT
    ):
        if kwargs and "encoding" in kwargs:
            del kwargs["encoding"]

    return DATAFRAME.read_csv(*args, **kwargs)


def concat(*args, **kwargs):
    return DATAFRAME.concat(*args, **kwargs)


def merge(*args, **kwargs):
    return DATAFRAME.merge(*args, **kwargs)


def check_pandas_dataframe_columns(
    df,
    activity_key=None,
    case_id_key=None,
    timestamp_key=None,
    start_timestamp_key=None,
):
    """
    Checks if the dataframe contains all the required columns.
    If not, raise an exception

    Parameters
    --------------
    df
        Pandas dataframe
    """
    if is_polars_lazyframe(df):
        import polars as pl  # type: ignore[import-untyped]

        schema = _lazyframe_schema(df)
        columns = list(schema.names())
        column_set = set(columns)
        if len(columns) < 3:
            raise Exception(
                "the dataframe should (at least) contain a column for the case identifier, a column for the activity and a column for the timestamp."
            )

        str_columns = {
            col
            for col, dtype in schema.items()
            if any(
                token in str(dtype).lower()
                for token in ("str", "utf8", "categorical", "enum", "object")
            )
        }
        timest_columns = {
            col
            for col, dtype in schema.items()
            if any(token in str(dtype).lower() for token in ("date", "time", "datetime"))
        }

        if len(str_columns) < 2:
            raise Exception(
                "the dataframe should (at least) contain a column of type string for the case identifier and a column of type string for the activity."
            )

        if len(timest_columns) < 1:
            raise Exception("the dataframe should (at least) contain a column of type date")

        def raise_if_missing(column_name):
            raise Exception(
                "the specified {} column is not contained in the dataframe. Available columns: {}".format(
                    column_name,
                    sorted(list(columns)),
                )
            )

        def ensure_no_null(col, label):
            has_null_df = df.select(
                pl.col(col).is_null().any().alias("__has_null")
            ).collect()
            if bool(has_null_df[0, "__has_null"]):
                raise Exception(
                    "the {} column should not contain any empty value.".format(label)
                )

        if case_id_key is not None:
            if case_id_key not in column_set:
                raise_if_missing("case ID")
            if case_id_key not in str_columns:
                raise Exception("the case ID column should be of type string.")
            ensure_no_null(case_id_key, "case ID")

        if activity_key is not None:
            if activity_key not in column_set:
                raise_if_missing("activity")
            if activity_key not in str_columns:
                raise Exception("the activity column should be of type string.")
            ensure_no_null(activity_key, "activity")

        if timestamp_key is not None:
            if timestamp_key not in column_set:
                raise_if_missing("timestamp")
            if timestamp_key not in timest_columns:
                raise Exception(
                    "the timestamp column should be of type datetime. Use the function pandas.to_datetime"
                )
            ensure_no_null(timestamp_key, "timestamp")

        if start_timestamp_key is not None:
            if start_timestamp_key not in column_set:
                raise_if_missing("start timestamp")
            if start_timestamp_key not in timest_columns:
                raise Exception(
                    "the start timestamp column should be of type datetime. Use the function pandas.to_datetime"
                )
            ensure_no_null(start_timestamp_key, "start timestamp")

        return

    if len(df.columns) < 3:
        raise Exception(
            "the dataframe should (at least) contain a column for the case identifier, a column for the activity and a column for the timestamp."
        )

    str_columns = {
        x
        for x in df.columns
        if "str" in str(df[x].dtype).lower()
        or "obj" in str(df[x].dtype).lower()
    }
    timest_columns = {
        x
        for x in df.columns
        if "date" in str(df[x].dtype).lower()
        or "time" in str(df[x].dtype).lower()
    }

    if len(str_columns) < 2:
        raise Exception(
            "the dataframe should (at least) contain a column of type string for the case identifier and a column of type string for the activity."
        )

    if len(timest_columns) < 1:
        raise Exception(
            "the dataframe should (at least) contain a column of type date"
        )

    if case_id_key is not None:
        if case_id_key not in df.columns:
            raise Exception(
                "the specified case ID column is not contained in the dataframe. Available columns: "
                + str(sorted(list(df.columns)))
            )

        if case_id_key not in str_columns:
            raise Exception("the case ID column should be of type string.")

        if df[case_id_key].isnull().values.any():
            raise Exception(
                "the case ID column should not contain any empty value."
            )

    if activity_key is not None:
        if activity_key not in df.columns:
            raise Exception(
                "the specified activity column is not contained in the dataframe. Available columns: "
                + str(sorted(list(df.columns)))
            )

        if activity_key not in str_columns:
            raise Exception("the activity column should be of type string.")

        if df[activity_key].isnull().values.any():
            raise Exception(
                "the activity column should not contain any empty value."
            )

    if timestamp_key is not None:
        if timestamp_key not in df.columns:
            raise Exception(
                "the specified timestamp column is not contained in the dataframe. Available columns: "
                + str(sorted(list(df.columns)))
            )

        if timestamp_key not in timest_columns:
            raise Exception(
                "the timestamp column should be of time datetime. Use the function pandas.to_datetime"
            )

        if df[timestamp_key].isnull().values.any():
            raise Exception(
                "the timestamp column should not contain any empty value."
            )

    if start_timestamp_key is not None:
        if start_timestamp_key not in df.columns:
            raise Exception(
                "the specified start timestamp column is not contained in the dataframe. Available columns: "
                + str(sorted(list(df.columns)))
            )

        if start_timestamp_key not in timest_columns:
            raise Exception(
                "the start timestamp column should be of time datetime. Use the function pandas.to_datetime"
            )

        if df[start_timestamp_key].isnull().values.any():
            raise Exception(
                "the start timestamp column should not contain any empty value."
            )


def get_traces(log, case_id_key, activity_key):
    if is_polars_lazyframe(log):
        import polars as pl  # type: ignore[import-untyped]

        collected = (
            log.select(pl.col(case_id_key), pl.col(activity_key))
            .group_by(case_id_key, maintain_order=True)
            .agg(pl.col(activity_key).alias("__acts"))
            .collect()
        )
        traces = [tuple(seq) for seq in collected["__acts"].to_list()]
    else:
        # Pandas dataframe management
        traces = [
            tuple(x)
            for x in log.groupby(case_id_key)[activity_key]
            .agg(list)
            .to_dict()
            .values()
        ]
    return traces


def get_attribute_values_count(log, attribute):
    if is_polars_lazyframe(log):
        import importlib.util

        if importlib.util.find_spec("polars") is None:
            raise RuntimeError(
                "Polars LazyFrame provided but 'polars' package is not installed."
            )

        import polars as pl  # type: ignore[import-untyped]

        available_columns = set(_lazyframe_column_names(log))
        if attribute not in available_columns:
            raise Exception(
                f"Column '{attribute}' is not present in the provided Polars LazyFrame."
            )

        result = (
            log.group_by(attribute)
            .agg(pl.len().alias("__pm4py_count__"))
            .collect()
        )

        return {
            row[attribute]: row["__pm4py_count__"]
            for row in result.iter_rows(named=True)
        }
    else:
        return log[attribute].value_counts().to_dict()


def df_row_count(log):
    if is_polars_lazyframe(log):
        return len(log.collect())
    else:
        return len(log)


def get_pivot_timestamp_distribution(
        dataframe: pd.DataFrame,
        frequency_alias="M",
        case_id_col="case:concept:name",
        timestamp_col="time:timestamp"
) -> pd.DataFrame:
    """
    Creates a pivot table showing the distribution of timestamp occurrences
    for each case, grouped by a specified time frequency.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The input event log as a pandas DataFrame, with at least case and timestamp columns.
    frequency_alias : str, default 'M'
        The frequency at which to group (bin) the timestamps. This value should be a valid
        pandas frequency alias, such as:

            - 'A' or 'Y'   : Yearly (e.g., 2024)
            - 'Q'          : Quarterly (e.g., 2024Q2)
            - 'M'          : Monthly (e.g., 2024-06)
            - 'W'          : Weekly (e.g., 2024-06-17/2024-06-23)
            - 'D'          : Daily (e.g., 2024-06-18)
            - 'H'          : Hourly (e.g., 2024-06-18 15:00)
            - 'T', 'min'   : Minutely (e.g., 2024-06-18 15:30)
            - 'S'          : Secondly (e.g., 2024-06-18 15:30:00) For a complete list, see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects case_id_col : str, default 'case:concept:name' The name of the column identifying each case. timestamp_col : str, default 'time:timestamp' The name of the column containing the event timestamps (must be pandas datetime dtype).

    Returns
    -------
    pd.DataFrame
        A pivot table where each row represents a case, columns represent time bins (according
        to the frequency), and values are the counts of events in each bin.

    Example
    -------
    get_pivot_timestamp_distribution(df, frequency_alias='D')

    """
    # Create column for binning
    dataframe["@@binning"] = dataframe[timestamp_col].dt.to_period(frequency_alias).astype(str)

    # Pivot table: cases as rows, yearmonths as columns, counts as values
    pivot = dataframe.pivot_table(
        index=case_id_col,
        columns="@@binning",
        values=timestamp_col,
        aggfunc="count",
        fill_value=0
    )

    pivot = pivot.reindex(sorted(pivot.columns), axis=1).reset_index()
    pivot.columns = [x if x == case_id_col else "@@evcount_"+x for x in pivot.columns]

    return pivot
