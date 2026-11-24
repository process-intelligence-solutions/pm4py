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
import ast
import json
from enum import Enum
from typing import Optional, Dict, Any

import pandas as pd
import importlib.util

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.obj import OCEL
from pm4py.util import exec_utils, pandas_utils, constants as pm4_constants


class Parameters(Enum):
    OBJECT_TYPE_PREFIX = constants.PARAM_OBJECT_TYPE_PREFIX_EXTENDED
    EVENT_ID = constants.PARAM_EVENT_ID
    EVENT_ACTIVITY = constants.PARAM_EVENT_ACTIVITY
    EVENT_TIMESTAMP = constants.PARAM_EVENT_TIMESTAMP
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    INTERNAL_INDEX = constants.PARAM_INTERNAL_INDEX


def _construct_progress_bar(progress_length):
    if importlib.util.find_spec("tqdm") and pm4_constants.SHOW_PROGRESS_BAR:
        if progress_length > 1:
            from tqdm.auto import tqdm

            return tqdm(
                total=progress_length,
                desc="importing OCEL, parsed rows :: ",
            )
    return None


def _destroy_progress_bar(progress):
    if progress is not None:
        progress.close()
    del progress


def safe_parse_list(value):
    """
    Safely parse a string into a list using ast.literal_eval.

    Args:
        value: The value to parse

    Returns:
        A list if the parsing was successful, otherwise an empty list
    """
    if isinstance(value, str) and value.startswith('['):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return []
    return []


def _disambiguate_typed_objects(objects, relations, object_id, object_type):
    collisions = objects[object_id].duplicated(keep=False)
    if not collisions.any():
        return

    used_ids = set(objects[object_id])
    originals = set(objects.loc[collisions, object_id])
    replacements = {}
    columns = [object_id, object_type]
    for identifier, kind in objects.loc[collisions, columns].itertuples(index=False, name=None):
        replacement = "ocel:typed-object:" + json.dumps([kind, identifier], ensure_ascii=False)
        while replacement in used_ids:
            replacement += ":"
        replacements[identifier, kind] = replacement
        used_ids.add(replacement)

    objects.loc[collisions, "ocel:original-object-id"] = objects.loc[collisions, object_id]
    for table, mask in ((objects, collisions), (relations, relations[object_id].isin(originals))):
        table.loc[mask, object_id] = [
            replacements[pair] for pair in table.loc[mask, columns].itertuples(index=False, name=None)
        ]


def get_ocel_from_extended_table(
        df: pd.DataFrame,
        objects_df: Optional[pd.DataFrame] = None,
        parameters: Optional[Dict[Any, Any]] = None,
        chunk_size: int = 50000,  # Default chunk size
) -> OCEL:
    """
    Get an OCEL object from an extended table format.

    Args:
        df: The DataFrame in extended table format
        objects_df: Optional DataFrame of objects
        parameters: Optional parameters dictionary
        chunk_size: Size of chunks to process

    Returns:
        An OCEL object
    """
    if parameters is None:
        parameters = {}

    # Extract parameters
    object_type_prefix = exec_utils.get_param_value(
        Parameters.OBJECT_TYPE_PREFIX,
        parameters,
        constants.DEFAULT_OBJECT_TYPE_PREFIX_EXTENDED,
    )
    event_activity = exec_utils.get_param_value(
        Parameters.EVENT_ACTIVITY, parameters, constants.DEFAULT_EVENT_ACTIVITY
    )
    event_id = exec_utils.get_param_value(
        Parameters.EVENT_ID, parameters, constants.DEFAULT_EVENT_ID
    )
    event_timestamp = exec_utils.get_param_value(
        Parameters.EVENT_TIMESTAMP,
        parameters,
        constants.DEFAULT_EVENT_TIMESTAMP,
    )
    object_id_column = exec_utils.get_param_value(
        Parameters.OBJECT_ID, parameters, constants.DEFAULT_OBJECT_ID
    )
    object_type_column = exec_utils.get_param_value(
        Parameters.OBJECT_TYPE, parameters, constants.DEFAULT_OBJECT_TYPE
    )
    internal_index = exec_utils.get_param_value(
        Parameters.INTERNAL_INDEX, parameters, constants.DEFAULT_INTERNAL_INDEX
    )

    # Preserve homogeneous timestamps and normalize inconsistent offsets to UTC.
    timestamp_format = pm4_constants.DEFAULT_TIMESTAMP_PARSE_FORMAT
    try:
        timestamps = pandas_utils.dataframe_column_string_to_datetime(
            df[event_timestamp], format=timestamp_format
        )
    except ValueError:
        timestamps = None
    if timestamps is None or pd.api.types.is_object_dtype(timestamps.dtype):
        timestamps = pandas_utils.dataframe_column_string_to_datetime(
            df[event_timestamp], format=timestamp_format, utc=True
        )
    df[event_timestamp] = timestamps
    timestamp_timezone = getattr(timestamps.dtype, "tz", None)

    # Identify columns efficiently
    object_type_columns = [col for col in df.columns if col.startswith(object_type_prefix)]
    non_object_type_columns = [col for col in df.columns if not col.startswith(object_type_prefix)]

    # Pre-compute object type mappings
    object_type_mapping = {ot: ot.split(object_type_prefix)[1] for ot in object_type_columns}

    # Create events DataFrame (only non-object columns)
    events_df = df[non_object_type_columns].copy()

    # Add internal index for sorting events
    events_df.loc[:, internal_index] = events_df.index

    # Sort by timestamp and index
    events_df = events_df.sort_values([event_timestamp, internal_index])

    # Track unique objects if needed
    unique_objects = {ot: set() for ot in object_type_columns} if objects_df is None else None

    # Initialize progress bar
    progress = _construct_progress_bar(len(events_df))

    # Create a filtered DataFrame with only needed columns
    needed_columns = [event_id, event_activity, event_timestamp] + object_type_columns
    filtered_df = df[needed_columns]
    del df

    pa = None
    use_pyarrow = False
    if importlib.util.find_spec("pyarrow") is not None:
        try:
            import pyarrow as pa  # type: ignore

            use_pyarrow = True
        except ModuleNotFoundError:
            pa = None
            use_pyarrow = False

    class RelationAccumulator:
        """
        Accumulate relation data either through PyArrow arrays or plain Python lists,
        depending on the availability of PyArrow.
        """

        _order = ("event_id", "event_activity", "event_timestamp", "object_id", "object_type")

        def __init__(self, use_pyarrow: bool, pa_module):
            self.use_pyarrow = use_pyarrow
            self.pa = pa_module
            if use_pyarrow and pa_module is not None:
                self._types = {
                    "event_id": pa_module.large_string(),
                    "event_activity": pa_module.large_string(),
                    "event_timestamp": pa_module.timestamp("ns", tz=timestamp_timezone),
                    "object_id": pa_module.large_string(),
                    "object_type": pa_module.large_string(),
                }
                self._chunks = {key: [] for key in self._order}
            else:
                self._chunks = {key: [] for key in self._order}
                self.use_pyarrow = False
                self.pa = None

        def append_chunk(self, event_ids, event_activities, event_timestamps, object_ids, object_types):
            if not event_ids:
                return
            if self.use_pyarrow:
                pa_module = self.pa
                self._chunks["event_id"].append(pa_module.array(event_ids, type=self._types["event_id"]))
                self._chunks["event_activity"].append(pa_module.array(event_activities, type=self._types["event_activity"]))
                self._chunks["event_timestamp"].append(pa_module.array(event_timestamps, type=self._types["event_timestamp"]))
                self._chunks["object_id"].append(pa_module.array(object_ids, type=self._types["object_id"]))
                self._chunks["object_type"].append(pa_module.array(object_types, type=self._types["object_type"]))
            else:
                self._chunks["event_id"].extend(event_ids)
                self._chunks["event_activity"].extend(event_activities)
                self._chunks["event_timestamp"].extend(event_timestamps)
                self._chunks["object_id"].extend(object_ids)
                self._chunks["object_type"].extend(object_types)

        def has_data(self) -> bool:
            values = self._chunks["event_id"]
            if self.use_pyarrow:
                return bool(values) and any(len(arr) > 0 for arr in values)
            return bool(values)

        def to_columns(self):
            if not self.use_pyarrow:
                return {key: self._chunks[key] for key in self._order}

            pa_module = self.pa
            result = {}
            for key in self._order:
                arrays = self._chunks[key]
                if arrays:
                    concatenated = pa_module.concat_arrays(arrays) if len(arrays) > 1 else arrays[0]
                else:
                    concatenated = pa_module.array([], type=self._types[key])
                result[key] = concatenated.to_pandas()
            return result

    relations_accumulator = RelationAccumulator(use_pyarrow, pa)

    # Process DataFrame in chunks to avoid memory issues
    total_rows = len(filtered_df)

    for chunk_start in range(0, total_rows, chunk_size):
        chunk_end = min(chunk_start + chunk_size, total_rows)

        # Extract a chunk
        chunk = filtered_df.iloc[chunk_start:chunk_end]

        # Convert small chunk to records for faster processing
        chunk_records = chunk.to_dict(orient='records')

        # Create chunk-specific temporary lists
        chunk_ev_ids = []
        chunk_ev_activities = []
        chunk_ev_timestamps = []
        chunk_obj_ids = []
        chunk_obj_types = []
        chunk_unique_objects = {ot: list() for ot in object_type_columns} if objects_df is None else None

        # Process records in the current chunk
        for record in chunk_records:
            for ot in object_type_columns:
                obj_list = safe_parse_list(record[ot])
                if obj_list:
                    ot_striped = object_type_mapping[ot]

                    # Update unique objects for this chunk if tracking
                    if chunk_unique_objects is not None:
                        chunk_unique_objects[ot].extend(obj_list)

                    # Extend chunk-specific data efficiently
                    n_objs = len(obj_list)
                    chunk_ev_ids.extend([record[event_id]] * n_objs)
                    chunk_ev_activities.extend([record[event_activity]] * n_objs)
                    chunk_ev_timestamps.extend([record[event_timestamp]] * n_objs)
                    chunk_obj_ids.extend(obj_list)
                    chunk_obj_types.extend([ot_striped] * n_objs)

            # Update progress (1 item at a time)
            if progress is not None:
                progress.update(1)

        del chunk_records

        relations_accumulator.append_chunk(
            chunk_ev_ids,
            chunk_ev_activities,
            chunk_ev_timestamps,
            chunk_obj_ids,
            chunk_obj_types,
        )
        del chunk_ev_ids, chunk_ev_activities, chunk_ev_timestamps, chunk_obj_ids, chunk_obj_types

        # Merge unique objects if tracking
        if unique_objects is not None:
            for ot in object_type_columns:
                unique_objects[ot].update(set(chunk_unique_objects[ot]))

        # Free memory
        if chunk_unique_objects is not None:
            del chunk_unique_objects

    # Clean up progress bar
    _destroy_progress_bar(progress)

    del filtered_df

    # Create the relations DataFrame only once at the end
    relations = pandas_utils.DATAFRAME.DataFrame()
    if relations_accumulator.has_data():
        relation_columns = relations_accumulator.to_columns()
        relations = pandas_utils.DATAFRAME.DataFrame({
            event_id: relation_columns["event_id"],
            event_activity: relation_columns["event_activity"],
            event_timestamp: relation_columns["event_timestamp"],
            object_id_column: relation_columns["object_id"],
            object_type_column: relation_columns["object_type"]
        })

        # Add internal index for sorting the relations
        relations[internal_index] = relations.index

        # Sort by timestamp and index
        if type(relations) is pd.DataFrame:
            relations.sort_values([event_timestamp, internal_index], inplace=True)
        else:
            relations = relations.sort_values([event_timestamp, internal_index])

        # Remove temporary index column
        del relations[internal_index]

    # Remove temporary index column from events
    del events_df[internal_index]

    # Create objects DataFrame if not provided
    if objects_df is None:
        obj_types_list = []
        obj_ids_list = []

        for ot in object_type_columns:
            ot_striped = object_type_mapping[ot]
            obj_ids = list(unique_objects[ot])

            if obj_ids:
                obj_types_list.extend([ot_striped] * len(obj_ids))
                obj_ids_list.extend(obj_ids)

        objects_df = pandas_utils.DATAFRAME.DataFrame({
            object_type_column: obj_types_list,
            object_id_column: obj_ids_list
        })
        _disambiguate_typed_objects(objects_df, relations, object_id_column, object_type_column)

        # Free memory
        del obj_types_list, obj_ids_list, unique_objects

    # Create and return OCEL object
    return OCEL(
        events=events_df,
        objects=objects_df,
        relations=relations,
        parameters=parameters,
    )
