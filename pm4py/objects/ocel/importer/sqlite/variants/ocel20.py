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
from enum import Enum
from typing import Optional, Dict, Any

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.obj import OCEL
from pm4py.util import exec_utils, pandas_utils
import pandas as pd
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.objects.ocel.validation import ocel20_rel_validation
from pm4py.util import constants as pm4_constants
from pm4py.objects.log.util import dataframe_utils
import warnings


class Parameters(Enum):
    EVENT_ID = constants.PARAM_EVENT_ID
    EVENT_ACTIVITY = constants.PARAM_EVENT_ACTIVITY
    EVENT_TIMESTAMP = constants.PARAM_EVENT_TIMESTAMP
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    INTERNAL_INDEX = constants.PARAM_INTERNAL_INDEX
    QUALIFIER = constants.PARAM_QUALIFIER
    CHANGED_FIELD = constants.PARAM_CHNGD_FIELD
    CUMCOUNT = "cumcount"
    VALIDATION = "validation"
    EXCEPT_IF_INVALID = "except_if_invalid"


def _normalize_id_series(series: pd.Series) -> pd.Series:
    if series is None:
        return series
    if pd.api.types.is_float_dtype(series):
        non_null = series.dropna()
        if len(non_null) > 0 and ((non_null % 1) == 0).all():
            series = series.astype("Int64")
            return series.astype("string")
    if pd.api.types.is_numeric_dtype(series):
        return series.astype("string")
    series = series.astype("string")
    return series.str.replace(r"\\.0$", "", regex=True)


def _quote_identifier(identifier: str) -> str:
    if identifier is None:
        return identifier
    return '"' + identifier.replace('"', '""') + '"'


def _attribute_types(conn, prefix, type_map):
    schemas = {}
    for name, safe_name in type_map.items():
        table = _quote_identifier(prefix + safe_name)
        schemas[name] = {
            row[1]: row[2]
            for row in conn.execute(f"PRAGMA table_info({table})")
            if row[1] not in {"ocel_id", "ocel_time", "ocel_changed_field", "ocel_change_field"}
        }
    return schemas


def apply(file_path: str, parameters: Optional[Dict[Any, Any]] = None):
    if parameters is None:
        parameters = {}

    import sqlite3

    validation = exec_utils.get_param_value(
        Parameters.VALIDATION, parameters, False
    )
    except_if_invalid = exec_utils.get_param_value(
        Parameters.EXCEPT_IF_INVALID, parameters, False
    )

    event_id = exec_utils.get_param_value(
        Parameters.EVENT_ID, parameters, constants.DEFAULT_EVENT_ID
    )
    event_activity = exec_utils.get_param_value(
        Parameters.EVENT_ACTIVITY, parameters, constants.DEFAULT_EVENT_ACTIVITY
    )
    event_timestamp = exec_utils.get_param_value(
        Parameters.EVENT_TIMESTAMP,
        parameters,
        constants.DEFAULT_EVENT_TIMESTAMP,
    )
    object_id = exec_utils.get_param_value(
        Parameters.OBJECT_ID, parameters, constants.DEFAULT_OBJECT_ID
    )
    object_type = exec_utils.get_param_value(
        Parameters.OBJECT_TYPE, parameters, constants.DEFAULT_OBJECT_TYPE
    )
    qualifier_field = exec_utils.get_param_value(
        Parameters.QUALIFIER, parameters, constants.DEFAULT_QUALIFIER
    )
    changed_field = exec_utils.get_param_value(
        Parameters.CHANGED_FIELD, parameters, constants.DEFAULT_CHNGD_FIELD
    )
    if validation:
        satisfied, unsatisfied = ocel20_rel_validation.apply(file_path)
        if unsatisfied and except_if_invalid:
            raise Exception("OCEL 2.0 validation failed.")

    conn = sqlite3.connect(file_path)

    EVENTS = pd.read_sql("SELECT * FROM event", conn)
    OBJECTS = pd.read_sql("SELECT * FROM object", conn)
    EVENTS["ocel_id"] = _normalize_id_series(EVENTS["ocel_id"])
    OBJECTS["ocel_id"] = _normalize_id_series(OBJECTS["ocel_id"])

    etypes = sorted(pandas_utils.format_unique(EVENTS["ocel_type"].unique()))
    otypes = sorted(pandas_utils.format_unique(OBJECTS["ocel_type"].unique()))

    EVENTS = EVENTS.to_dict(orient="records")
    OBJECTS = OBJECTS.to_dict(orient="records")
    events_id_type = {x["ocel_id"]: x["ocel_type"] for x in EVENTS}
    objects_id_type = {x["ocel_id"]: x["ocel_type"] for x in OBJECTS}

    EVENT_CORR_TYPE = pd.read_sql("SELECT * FROM event_map_type", conn)
    OBJECT_CORR_TYPE = pd.read_sql("SELECT * FROM object_map_type", conn)
    EVENT_CORR_TYPE = EVENT_CORR_TYPE.to_dict(orient="records")
    OBJECT_CORR_TYPE = OBJECT_CORR_TYPE.to_dict(orient="records")

    events_type_map = {
        x["ocel_type"]: x["ocel_type_map"] for x in EVENT_CORR_TYPE
    }
    objects_type_map = {
        x["ocel_type"]: x["ocel_type_map"] for x in OBJECT_CORR_TYPE
    }
    schemas = {
        constants.OCEL_EVTYPES_KEY: _attribute_types(conn, "event_", events_type_map),
        constants.OCEL_OBJTYPES_KEY: _attribute_types(conn, "object_", objects_type_map),
    }

    event_types_coll = []
    object_types_coll = []

    for act in etypes:
        act_red = events_type_map[act]
        table_name = _quote_identifier("event_" + act_red)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn, dtype_backend="numpy_nullable")
        df = df.rename(
            columns={"ocel_id": event_id, "ocel_time": event_timestamp}
        )
        df[event_id] = _normalize_id_series(df[event_id])
        event_types_coll.append(df)

    for ot in otypes:
        ot_red = objects_type_map[ot]
        table_name = _quote_identifier("object_" + ot_red)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn, dtype_backend="numpy_nullable")
        if "ocel_changed_field" not in df and "ocel_change_field" in df:
            df = df.rename(columns={"ocel_change_field": "ocel_changed_field"})
        df = df.rename(
            columns={"ocel_id": object_id, "ocel_time": event_timestamp}
        )
        df[object_id] = _normalize_id_series(df[object_id])
        object_types_coll.append(df)

    event_types_coll = (
        pandas_utils.concat(event_types_coll, ignore_index=True)
        if event_types_coll else pd.DataFrame(columns=[event_id, event_timestamp])
    )
    event_types_coll[event_activity] = event_types_coll[event_id].map(
        events_id_type
    )
    event_types_coll = dataframe_utils.convert_timestamp_columns_in_df(
        event_types_coll,
        timest_format=pm4_constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
        timest_columns=[event_timestamp],
    )
    object_types_coll = (
        pandas_utils.concat(object_types_coll, ignore_index=True)
        if object_types_coll else pd.DataFrame(columns=[object_id])
    )
    object_types_coll[object_type] = object_types_coll[object_id].map(
        objects_id_type
    )
    object_types_coll = object_types_coll.rename(
        columns={"ocel_changed_field": changed_field}
    )

    events_timestamp = event_types_coll[[event_id, event_timestamp]].to_dict(
        orient="records"
    )
    events_timestamp = {
        x[event_id]: x[event_timestamp] for x in events_timestamp
    }
    if changed_field in object_types_coll:
        initial = object_types_coll[changed_field].isna() | object_types_coll[changed_field].eq("")
        objects = object_types_coll.loc[initial].drop(columns=[changed_field])
        object_changes = object_types_coll.loc[~initial].copy() if not initial.all() else None
    else:
        objects = object_types_coll.copy()
        object_changes = None

    if event_timestamp in objects:
        del objects[event_timestamp]
    # Details are optional when there are no initial values for an object.
    declared_with_initial_values = set(objects[object_id])
    missing_objects = [
        {object_id: oid, object_type: kind}
        for oid, kind in objects_id_type.items()
        if oid not in declared_with_initial_values
    ]
    if missing_objects:
        objects = pandas_utils.concat([objects, pd.DataFrame(missing_objects)], ignore_index=True)

    E2O = pd.read_sql("SELECT * FROM event_object", conn)
    E2O = E2O.rename(
        columns={
            "ocel_event_id": event_id,
            "ocel_object_id": object_id,
            "ocel_qualifier": qualifier_field,
        }
    )
    E2O[event_id] = _normalize_id_series(E2O[event_id])
    E2O[object_id] = _normalize_id_series(E2O[object_id])
    E2O[event_activity] = E2O[event_id].map(events_id_type)
    E2O[event_timestamp] = E2O[event_id].map(events_timestamp)
    E2O[object_type] = E2O[object_id].map(objects_id_type)

    O2O = pd.read_sql("SELECT * FROM object_object", conn)
    O2O = O2O.rename(
        columns={
            "ocel_source_id": object_id,
            "ocel_target_id": object_id + "_2",
            "ocel_qualifier": qualifier_field,
        }
    )
    if len(O2O) > 0:
        O2O[object_id] = _normalize_id_series(O2O[object_id])
        O2O[object_id + "_2"] = _normalize_id_series(
            O2O[object_id + "_2"]
        )
    if len(O2O) == 0:
        O2O = None

    conn.close()

    event_types_coll = event_types_coll.sort_values(event_timestamp, kind="stable")
    E2O = E2O.sort_values(event_timestamp, kind="stable")

    if object_changes is not None:
        object_changes = dataframe_utils.convert_timestamp_columns_in_df(
            object_changes,
            timest_format=pm4_constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
            timest_columns=[event_timestamp],
        )
        object_changes = object_changes.sort_values(event_timestamp, kind="stable")

    ocel = OCEL(
        events=event_types_coll,
        objects=objects,
        relations=E2O,
        object_changes=object_changes,
        o2o=O2O,
        globals=schemas,
        parameters=parameters,
    )

    ocel = ocel_consistency.apply(ocel, parameters=parameters)
    return ocel_consistency.remove_dangling_relationships(ocel)
