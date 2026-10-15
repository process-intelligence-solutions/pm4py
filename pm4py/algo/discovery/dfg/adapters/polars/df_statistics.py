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

from typing import Dict, List, Optional, Tuple, Union

import polars as pl

from pm4py.util import constants, xes_constants
from pm4py.util.business_hours import (
    _prepare_scheduled_business_hours,
    soj_time_business_hours_diff,
)


def _ensure_start_timestamp(
    lf: pl.LazyFrame, start_timestamp_key: str, timestamp_key: str
) -> pl.LazyFrame:
    schema_names = lf.collect_schema().names()
    if start_timestamp_key not in schema_names:
        lf = lf.with_columns(pl.col(timestamp_key).alias(start_timestamp_key))
    return lf


def _ensure_row_index(lf: pl.LazyFrame, column_name: str) -> pl.LazyFrame:
    schema_names = lf.collect_schema().names()
    if column_name in schema_names:
        return lf
    return lf.with_row_index(column_name)


def get_dfg_graph(
    df: pl.LazyFrame,
    measure: str = "frequency",
    activity_key: str = "concept:name",
    case_id_glue: str = "case:concept:name",
    start_timestamp_key: Optional[str] = None,
    timestamp_key: str = "time:timestamp",
    perf_aggregation_key: str = "mean",
    sort_caseid_required: bool = True,
    sort_timestamp_along_case_id: bool = True,
    keep_once_per_case: bool = False,
    window: int = 1,
    business_hours: bool = False,
    business_hours_slot=None,
    workcalendar=constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
    target_activity_key: Optional[str] = None,
    reduce_columns: bool = True,
    cost_attribute: Optional[str] = None,
    business_timezone: Optional[str] = None,
) -> Union[Dict[Tuple[str, str], int], Dict[Tuple[str, str], float], List[Dict]]:
    """Compute DFG statistics on a Polars LazyFrame.

    An explicit business_timezone selects scheduled elapsed time and requires
    business_hours=True with aware timestamps at microsecond precision.
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
        schema = df.collect_schema()
        columns = {timestamp_key}
        selected_start = (
            xes_constants.DEFAULT_START_TIMESTAMP_KEY
            if start_timestamp_key is None else start_timestamp_key
        )
        if selected_start in schema:
            columns.add(selected_start)
        for column in columns:
            dtype = schema[column]
            if not isinstance(dtype, pl.Datetime) or dtype.time_zone is None:
                raise ValueError(
                    "Scheduled elapsed time requires aware timestamps"
                )
            invalid = pl.col(column).is_null()
            if dtype.time_unit == "ns":
                invalid = invalid | (pl.col(column).cast(pl.Int64) % 1000 != 0)
            if df.select(invalid.any()).collect().item():
                raise ValueError(
                    "Timestamps must be non-null and at microsecond precision"
                )
        df = df.with_columns(
            [pl.col(column).dt.convert_time_zone("UTC") for column in columns]
        )

    if target_activity_key is None:
        target_activity_key = activity_key

    if start_timestamp_key is None:
        start_timestamp_key = xes_constants.DEFAULT_START_TIMESTAMP_KEY

    schema_names = df.collect_schema().names()
    st_eq_ct = start_timestamp_key == timestamp_key

    if start_timestamp_key not in schema_names:
        df = df.with_columns(pl.col(timestamp_key).alias(start_timestamp_key))
        schema_names = df.collect_schema().names()
        st_eq_ct = True

    needed_columns = {case_id_glue, activity_key, target_activity_key}
    if measure != "frequency" or sort_timestamp_along_case_id:
        needed_columns.update({start_timestamp_key, timestamp_key})
    if measure == "cost" and cost_attribute:
        needed_columns.add(cost_attribute)

    if reduce_columns:
        available = [col for col in schema_names if col in needed_columns]
        df = df.select([pl.col(col) for col in available])
        schema_names = df.collect_schema().names()

    if measure == "cost" and cost_attribute:
        df = df.with_columns(pl.col(cost_attribute).fill_null(0))
        schema_names = df.collect_schema().names()

    if sort_caseid_required:
        if sort_timestamp_along_case_id:
            sort_cols = [case_id_glue]
            if start_timestamp_key in schema_names:
                sort_cols.append(start_timestamp_key)
            if timestamp_key in schema_names:
                sort_cols.append(timestamp_key)
            df = df.sort(sort_cols, maintain_order=True)
        else:
            df = df.sort(case_id_glue, maintain_order=True)

    suffix = "_2"
    shift_exprs = [
        pl.col(case_id_glue)
        .shift(-window)
        .over(case_id_glue)
        .alias(case_id_glue + suffix),
        pl.col(target_activity_key)
        .shift(-window)
        .over(case_id_glue)
        .alias(target_activity_key + suffix),
    ]

    if start_timestamp_key in schema_names or start_timestamp_key == timestamp_key:
        shift_exprs.append(
            pl.col(start_timestamp_key)
            .shift(-window)
            .over(case_id_glue)
            .alias(start_timestamp_key + suffix)
        )
    if timestamp_key in schema_names:
        shift_exprs.append(
            pl.col(timestamp_key)
            .shift(-window)
            .over(case_id_glue)
            .alias(timestamp_key + suffix)
        )
    if measure == "cost" and cost_attribute:
        shift_exprs.append(
            pl.col(cost_attribute)
            .shift(-window)
            .over(case_id_glue)
            .alias(cost_attribute + suffix)
        )

    pairs = df.with_columns(shift_exprs)
    pairs = pairs.filter(pl.col(case_id_glue + suffix).is_not_null())
    pairs = pairs.filter(pl.col(target_activity_key + suffix).is_not_null())

    if keep_once_per_case:
        pairs = pairs.unique(
            subset=[case_id_glue, activity_key, target_activity_key + suffix],
            keep="first",
        )

    if measure in {"performance", "both", "cost"}:
        if not st_eq_ct:
            pairs = pairs.with_columns(
                pl.max_horizontal(
                    [pl.col(start_timestamp_key + suffix), pl.col(timestamp_key)]
                ).alias(start_timestamp_key + suffix)
            )

        if business_hours:
            if business_hours_slot is None:
                business_hours_slot = constants.DEFAULT_BUSINESS_HOUR_SLOTS
            pairs = pairs.with_columns(
                pl.struct(
                    [pl.col(timestamp_key), pl.col(start_timestamp_key + suffix)]
                )
                .map_elements(
                    lambda row: soj_time_business_hours_diff(
                        row[timestamp_key],
                        row[start_timestamp_key + suffix],
                        business_hours_slot,
                        workcalendar,
                        business_timezone=business_timezone,
                    ),
                    return_dtype=pl.Float64,
                )
                .alias(constants.DEFAULT_FLOW_TIME)
            )
        else:
            pairs = pairs.with_columns(
                (
                    pl.col(start_timestamp_key + suffix) - pl.col(timestamp_key)
                )
                .dt.total_seconds()
                .alias(constants.DEFAULT_FLOW_TIME)
            )

    group_cols = [activity_key, target_activity_key + suffix]

    freq_dict: Dict[Tuple[str, str], int] = {}
    perf_dict: Dict[Tuple[str, str], Union[float, Dict[str, float], List[float]]] = {}

    if measure in {"frequency", "both"}:
        freq_df = (
            pairs.group_by(group_cols)
            .agg(pl.len().alias("count"))
            .collect()
        )
        freq_dict = {
            (row[group_cols[0]], row[group_cols[1]]): row["count"]
            for row in freq_df.iter_rows(named=True)
            if row[group_cols[0]] is not None and row[group_cols[1]] is not None
        }

    if measure in {"performance", "both", "cost"}:
        if measure == "cost" and cost_attribute:
            value_expr = pl.col(cost_attribute + suffix)
        else:
            value_expr = pl.col(constants.DEFAULT_FLOW_TIME)

        if perf_aggregation_key == "all":
            agg_exprs = [
                value_expr.mean().alias("mean"),
                value_expr.median().alias("median"),
                value_expr.max().alias("max"),
                value_expr.min().alias("min"),
                value_expr.sum().alias("sum"),
                value_expr.std().alias("stdev"),
            ]
            perf_df = pairs.group_by(group_cols).agg(agg_exprs).collect()
            perf_dict = {
                (row[group_cols[0]], row[group_cols[1]]): {
                    "mean": row["mean"],
                    "median": row["median"],
                    "max": row["max"],
                    "min": row["min"],
                    "sum": row["sum"],
                    "stdev": row["stdev"],
                }
                for row in perf_df.iter_rows(named=True)
            }
        elif perf_aggregation_key == "raw_values":
            perf_df = (
                pairs.group_by(group_cols)
                .agg(value_expr.implode().alias("raw_values"))
                .collect()
            )
            perf_dict = {
                (row[group_cols[0]], row[group_cols[1]]): row["raw_values"]
                for row in perf_df.iter_rows(named=True)
            }
        else:
            if not hasattr(pl.Expr, perf_aggregation_key):
                raise ValueError(
                    f"Unsupported aggregation key: {perf_aggregation_key}"
                )
            agg_expr = getattr(value_expr, perf_aggregation_key)().alias(
                perf_aggregation_key
            )
            perf_df = (
                pairs.group_by(group_cols).agg(agg_expr).collect()
            )
            perf_dict = {
                (row[group_cols[0]], row[group_cols[1]]): row[perf_aggregation_key]
                for row in perf_df.iter_rows(named=True)
            }

    if measure == "frequency":
        return freq_dict
    if measure in {"performance", "cost"}:
        return perf_dict
    return [freq_dict, perf_dict]


def get_partial_order_dataframe(
    df: pl.LazyFrame,
    start_timestamp_key: Optional[str] = None,
    timestamp_key: str = "time:timestamp",
    case_id_glue: str = "case:concept:name",
    activity_key: str = "concept:name",
    sort_caseid_required: bool = True,
    sort_timestamp_along_case_id: bool = True,
    reduce_dataframe: bool = True,
    keep_first_following: bool = True,
    business_hours: bool = False,
    business_hours_slot=None,
    workcalendar=constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
    event_index: str = constants.DEFAULT_INDEX_KEY,
) -> pl.LazyFrame:
    """Compute partial order dataframe using Polars."""

    if start_timestamp_key is None:
        start_timestamp_key = xes_constants.DEFAULT_START_TIMESTAMP_KEY

    df = _ensure_start_timestamp(df, start_timestamp_key, timestamp_key)

    if reduce_dataframe:
        schema_names = df.collect_schema().names()
        columns = {
            case_id_glue,
            activity_key,
            start_timestamp_key,
            timestamp_key,
        }
        if event_index in schema_names:
            columns.add(event_index)
        df = df.select([pl.col(col) for col in schema_names if col in columns])

    if sort_caseid_required:
        if sort_timestamp_along_case_id:
            df = df.sort([case_id_glue, start_timestamp_key, timestamp_key], maintain_order=True)
        else:
            df = df.sort(case_id_glue, maintain_order=True)

    df = _ensure_row_index(df, event_index)

    joined = df.join(df, on=case_id_glue, how="inner", suffix="_2", maintain_order="left")
    joined = joined.filter(
        pl.col(event_index) < pl.col(event_index + "_2")
    )
    joined = joined.filter(
        pl.col(timestamp_key) <= pl.col(start_timestamp_key + "_2")
    )

    if business_hours:
        if business_hours_slot is None:
            business_hours_slot = constants.DEFAULT_BUSINESS_HOUR_SLOTS
        joined = joined.with_columns(
            pl.struct(
                [pl.col(timestamp_key), pl.col(start_timestamp_key + "_2")]
            )
            .map_elements(
                lambda row: soj_time_business_hours_diff(
                    row[timestamp_key],
                    row[start_timestamp_key + "_2"],
                    business_hours_slot,
                    workcalendar,
                ),
                return_dtype=pl.Float64,
            )
            .alias(constants.DEFAULT_FLOW_TIME)
        )
    else:
        joined = joined.with_columns(
            (
                pl.col(start_timestamp_key + "_2") - pl.col(timestamp_key)
            )
            .dt.total_seconds()
            .alias(constants.DEFAULT_FLOW_TIME)
        )

    if keep_first_following:
        joined = joined.sort([case_id_glue, event_index, event_index + "_2"], maintain_order=True)
        joined = joined.unique(
            subset=[event_index], keep="first", maintain_order=True
        )

    return joined


def get_concurrent_events_dataframe(
    df: pl.LazyFrame,
    start_timestamp_key: Optional[str] = None,
    timestamp_key: str = "time:timestamp",
    case_id_glue: str = "case:concept:name",
    activity_key: str = "concept:name",
    sort_caseid_required: bool = True,
    sort_timestamp_along_case_id: bool = True,
    reduce_dataframe: bool = True,
    max_start_column: str = "@@max_start_column",
    min_complete_column: str = "@@min_complete_column",
    diff_maxs_minc: str = "@@diff_maxs_minc",
    strict: bool = False,
) -> pl.LazyFrame:
    """Compute concurrency dataframe using Polars."""

    if start_timestamp_key is None:
        start_timestamp_key = xes_constants.DEFAULT_START_TIMESTAMP_KEY

    df = _ensure_start_timestamp(df, start_timestamp_key, timestamp_key)

    if reduce_dataframe:
        columns = [case_id_glue, activity_key, start_timestamp_key, timestamp_key]
        df = df.select([pl.col(col) for col in df.schema if col in columns])

    if sort_caseid_required:
        if sort_timestamp_along_case_id:
            df = df.sort([case_id_glue, start_timestamp_key, timestamp_key], maintain_order=True)
        else:
            df = df.sort(case_id_glue, maintain_order=True)

    df = _ensure_row_index(df, constants.DEFAULT_INDEX_KEY)

    joined = df.join(df, on=case_id_glue, how="inner", suffix="_2", maintain_order="left")
    joined = joined.filter(
        pl.col(constants.DEFAULT_INDEX_KEY)
        < pl.col(constants.DEFAULT_INDEX_KEY + "_2")
    )

    joined = joined.filter(
        pl.col(timestamp_key)
        <= pl.col(start_timestamp_key + "_2")
    )

    joined = joined.with_columns([
        pl.max_horizontal(
            [pl.col(start_timestamp_key), pl.col(start_timestamp_key + "_2")]
        ).alias(max_start_column),
        pl.min_horizontal([pl.col(timestamp_key), pl.col(timestamp_key + "_2")]).alias(
            min_complete_column
        ),
    ])

    joined = joined.with_columns(
        (
            pl.col(min_complete_column) - pl.col(max_start_column)
        )
        .dt.total_seconds()
        .alias(diff_maxs_minc)
    )

    if strict:
        joined = joined.filter(pl.col(diff_maxs_minc) > 0)
    else:
        joined = joined.filter(pl.col(diff_maxs_minc) >= 0)

    return joined.drop(constants.DEFAULT_INDEX_KEY + "_2")
