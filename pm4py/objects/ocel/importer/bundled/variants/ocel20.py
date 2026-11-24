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
from pathlib import PurePosixPath
from typing import Optional, Dict, Any, List, Tuple
import codecs
import csv
import io
import json
import math
import os
import re
import zipfile

import pandas as pd

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.importer.csv_rows import read_csv_rows
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.util import constants as pm4_constants, exec_utils, pandas_utils


class Parameters(Enum):
    EVENT_ID = constants.PARAM_EVENT_ID
    EVENT_ACTIVITY = constants.PARAM_EVENT_ACTIVITY
    EVENT_TIMESTAMP = constants.PARAM_EVENT_TIMESTAMP
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    INTERNAL_INDEX = constants.PARAM_INTERNAL_INDEX
    QUALIFIER = constants.PARAM_QUALIFIER
    CHANGED_FIELD = constants.PARAM_CHNGD_FIELD
    ENCODING = "encoding"


_ATTRIBUTE_TYPES = {"string", "time", "integer", "float", "boolean"}
_SAFE_FILENAME_BYTES = set(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
)
_INTEGER_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(
    r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$"
)
_TIMEZONE_RE = re.compile(r"(?:Z|[+-]\d{2}:?\d{2})$")


def _instantiate_dataframe(records: List[Dict[str, Any]], columns: List[str]):
    if records:
        return pandas_utils.instantiate_dataframe(records)
    return pandas_utils.instantiate_dataframe({column: [] for column in columns})


def _require_utf8(encoding: str) -> str:
    try:
        normalized = codecs.lookup(encoding).name
    except LookupError as exc:
        raise ValueError("Unknown OCEL bundle encoding '%s'." % encoding) from exc
    if normalized != "utf-8":
        raise ValueError("OCEL bundle metadata and CSV tables must use UTF-8 encoding.")
    return "utf-8"


def _percent_encode(value: str) -> str:
    encoded = []
    for byte in value.encode("utf-8"):
        encoded.append(chr(byte) if byte in _SAFE_FILENAME_BYTES else "%%%02X" % byte)
    return "".join(encoded)


def _validate_relative_path(path: Any, label: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path:
        raise ValueError("%s must be a non-empty POSIX relative path." % label)
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError("%s must contain no root, '.' or '..' component." % label)
    return path


def _attribute_descriptors(
    descriptor: Dict[str, Any], label: str, reserved: set
) -> List[Tuple[str, str]]:
    attributes = descriptor.get("attributes")
    if not isinstance(attributes, list):
        raise ValueError("%s attributes must be an array." % label)
    result = []
    names = set()
    for attribute in attributes:
        if not isinstance(attribute, dict):
            raise ValueError("%s attribute declarations must be objects." % label)
        name = attribute.get("name")
        primitive_type = attribute.get("type")
        if not isinstance(name, str) or not name:
            raise ValueError("%s attribute names must be non-empty strings." % label)
        if name in names:
            raise ValueError("Duplicate attribute '%s' in %s metadata." % (name, label))
        if name in reserved:
            raise ValueError("Attribute '%s' collides with a fixed %s column." % (name, label))
        if primitive_type not in _ATTRIBUTE_TYPES:
            raise ValueError(
                "Attribute '%s' in %s has unsupported type '%s'."
                % (name, label, primitive_type)
            )
        names.add(name)
        result.append((name, primitive_type))
    return result


def _validate_metadata(meta: Any) -> Dict[str, Any]:
    if not isinstance(meta, dict):
        raise ValueError("ocel-meta.json must contain a JSON object.")
    if meta.get("ocelVersion") != "2.0":
        raise ValueError("OCEL bundle ocelVersion must be '2.0'.")
    if meta.get("bundleFormatVersion") != "1.0":
        raise ValueError("OCEL bundle bundleFormatVersion must be '1.0'.")
    storage_format = meta.get("storageFormat")
    if storage_format not in {"csv", "parquet"}:
        raise ValueError("OCEL bundle storageFormat must be 'csv' or 'parquet'.")
    event_types = meta.get("eventTypes")
    object_types = meta.get("objectTypes")
    relations = meta.get("relations")
    if not isinstance(event_types, dict) or not isinstance(object_types, dict):
        raise ValueError("OCEL bundle eventTypes and objectTypes must be objects.")
    if not isinstance(relations, dict):
        raise ValueError("OCEL bundle relations must be an object.")

    extension = storage_format
    declared_paths = []
    for event_type, descriptor in event_types.items():
        if not isinstance(event_type, str) or not isinstance(descriptor, dict):
            raise ValueError("Event type metadata entries must map strings to objects.")
        expected = "events/event_%s.%s" % (_percent_encode(event_type), extension)
        path = _validate_relative_path(descriptor.get("file"), "Event table path")
        if path != expected:
            raise ValueError("Event table for '%s' must be '%s'." % (event_type, expected))
        descriptor["_attributes"] = _attribute_descriptors(
            descriptor, "event type '%s'" % event_type, {"ocel_id", "ocel_time"}
        )
        declared_paths.append(path)

    for object_type, descriptor in object_types.items():
        if not isinstance(object_type, str) or not isinstance(descriptor, dict):
            raise ValueError("Object type metadata entries must map strings to objects.")
        encoded = _percent_encode(object_type)
        expected = "objects/object_%s.%s" % (encoded, extension)
        changes_expected = "object_changes/object_changes_%s.%s" % (
            encoded,
            extension,
        )
        path = _validate_relative_path(descriptor.get("file"), "Object table path")
        changes_path = _validate_relative_path(
            descriptor.get("changesFile"), "Object-change table path"
        )
        if path != expected or changes_path != changes_expected:
            raise ValueError(
                "Object tables for '%s' must use the deterministic bundle paths."
                % object_type
            )
        descriptor["_attributes"] = _attribute_descriptors(
            descriptor,
            "object type '%s'" % object_type,
            {"ocel_id", "ocel_time", "ocel_changed_field"},
        )
        declared_paths.extend([path, changes_path])

    expected_e2o = "relations/e2o.%s" % extension
    expected_o2o = "relations/o2o.%s" % extension
    e2o_path = _validate_relative_path(relations.get("e2o"), "E2O table path")
    o2o_path = _validate_relative_path(relations.get("o2o"), "O2O table path")
    if e2o_path != expected_e2o or o2o_path != expected_o2o:
        raise ValueError("Relation tables must use the deterministic bundle paths.")
    declared_paths.extend([e2o_path, o2o_path])
    if len(declared_paths) != len(set(declared_paths)):
        raise ValueError("OCEL bundle metadata declares the same table path more than once.")
    meta["_declared_paths"] = declared_paths
    return meta


def _read_meta(file_path: str, encoding: str) -> Dict[str, Any]:
    if os.path.isdir(file_path):
        meta_path = os.path.join(file_path, "ocel-meta.json")
        with open(meta_path, "r", encoding=encoding) as file:
            return _validate_metadata(json.load(file))
    if not str(file_path).lower().endswith(".ocel.zip"):
        raise ValueError("Bundled OCEL archives use the '.ocel.zip' extension.")
    with zipfile.ZipFile(file_path, "r") as archive:
        try:
            content = archive.read("ocel-meta.json")
        except KeyError as exc:
            raise ValueError("OCEL bundle is missing root ocel-meta.json.") from exc
    return _validate_metadata(json.loads(content.decode(encoding)))


def _container_entries(file_path: str) -> set:
    if os.path.isdir(file_path):
        entries = set()
        root = os.path.realpath(file_path)
        for current_root, _, files in os.walk(file_path):
            for filename in files:
                full_path = os.path.join(current_root, filename)
                real_path = os.path.realpath(full_path)
                if os.path.commonpath([root, real_path]) != root:
                    raise ValueError("OCEL bundle table path escapes the container root.")
                entries.add(os.path.relpath(full_path, file_path).replace(os.sep, "/"))
        return entries

    with zipfile.ZipFile(file_path, "r") as archive:
        names = [info.filename for info in archive.infolist()]
    if len(names) != len(set(names)):
        raise ValueError("OCEL bundle archives cannot contain duplicate entry names.")
    entries = set()
    for name in names:
        normalized = name[:-1] if name.endswith("/") else name
        if normalized:
            _validate_relative_path(normalized, "Archive entry name")
            if not name.endswith("/"):
                entries.add(name)
    return entries


def _validate_container(file_path: str, meta: Dict[str, Any]):
    entries = _container_entries(file_path)
    required = {"ocel-meta.json", *meta["_declared_paths"]}
    missing = required.difference(entries)
    if missing:
        raise ValueError("OCEL bundle is missing declared tables: %s." % ", ".join(sorted(missing)))
    opposite_extension = ".parquet" if meta["storageFormat"] == "csv" else ".csv"
    mixed = sorted(path for path in entries if path.lower().endswith(opposite_extension))
    if mixed:
        raise ValueError("OCEL bundle mixes CSV and Parquet table files.")


def _table_bytes(file_path: str, table_path: str) -> bytes:
    if os.path.isdir(file_path):
        root = os.path.realpath(file_path)
        full_path = os.path.realpath(os.path.join(file_path, *table_path.split("/")))
        if os.path.commonpath([root, full_path]) != root:
            raise ValueError("OCEL bundle table path escapes the container root.")
        with open(full_path, "rb") as file:
            return file.read()
    with zipfile.ZipFile(file_path, "r") as archive:
        return archive.read(table_path)


def _read_csv_table(data: bytes, encoding: str, table_path: str) -> pd.DataFrame:
    try:
        text = data.decode(encoding)
        rows = read_csv_rows(io.StringIO(text, newline=""))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("Invalid UTF-8/RFC 4180 CSV table '%s'." % table_path) from exc
    if not rows:
        raise ValueError("CSV table '%s' must contain a header row." % table_path)
    header = rows[0]
    if len(header) != len(set(header)):
        raise ValueError("CSV table '%s' has duplicate columns." % table_path)
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(
                "CSV table '%s' row %d has the wrong number of fields."
                % (table_path, line_number)
            )
    return pandas_utils.instantiate_dataframe(rows[1:], columns=header, dtype="object")


def _parse_time(value: str, label: str) -> pd.Timestamp:
    if not isinstance(value, str) or not _TIMEZONE_RE.search(value):
        raise ValueError("%s must be an ISO 8601 timestamp with timezone information." % label)
    try:
        return pd.to_datetime(value, utc=True)
    except BaseException as exc:
        raise ValueError("%s is not a valid ISO 8601 timestamp." % label) from exc


def _parse_csv_value(value: str, primitive_type: str, label: str):
    if value == "":
        return None
    if primitive_type == "string":
        return value
    if primitive_type == "integer":
        if not _INTEGER_RE.match(value):
            raise ValueError("%s is not a signed decimal integer." % label)
        return int(value)
    if primitive_type == "float":
        if not _FLOAT_RE.match(value):
            raise ValueError("%s is not a decimal floating-point number." % label)
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("%s is not a finite floating-point number." % label)
        return parsed
    if primitive_type == "boolean":
        if value not in {"true", "false"}:
            raise ValueError("%s must be 'true' or 'false'." % label)
        return value == "true"
    return _parse_time(value, label)


def _arrow_type(primitive_type: str):
    try:
        import pyarrow as pa
    except ImportError as exc:
        raise ImportError("pyarrow is required for specification-compliant OCEL Parquet bundles.") from exc
    return {
        "string": pa.string(),
        "integer": pa.int64(),
        "float": pa.float64(),
        "boolean": pa.bool_(),
        "time": pa.timestamp("us", tz="UTC"),
    }[primitive_type]


def _read_table(
    file_path: str,
    table_path: str,
    storage_format: str,
    encoding: str,
    fixed: List[Tuple[str, str]],
    attributes: List[Tuple[str, str]],
    non_empty_fixed: set,
) -> pd.DataFrame:
    data = _table_bytes(file_path, table_path)
    expected = fixed + attributes
    expected_names = [name for name, _ in expected]
    if storage_format == "csv":
        dataframe = _read_csv_table(data, encoding, table_path)
        if set(dataframe.columns) != set(expected_names):
            raise ValueError("CSV table '%s' columns do not match its metadata." % table_path)
        dataframe = dataframe[expected_names]
        fixed_names = {name for name, _ in fixed}
        for name, primitive_type in expected:
            if name in fixed_names and primitive_type == "string":
                values = dataframe[name].tolist()
            else:
                values = [
                    _parse_csv_value(value, primitive_type, "%s.%s" % (table_path, name))
                    for value in dataframe[name].tolist()
                ]
            if primitive_type == "time":
                dataframe[name] = pd.to_datetime(values, utc=True)
            else:
                dataframe[name] = pd.Series(
                    values, index=dataframe.index, dtype="object"
                )
    else:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise ImportError("pyarrow is required for specification-compliant OCEL Parquet bundles.") from exc
        table = pq.read_table(io.BytesIO(data))
        if set(table.column_names) != set(expected_names):
            raise ValueError("Parquet table '%s' columns do not match its metadata." % table_path)
        schema = table.schema
        fixed_names = {name for name, _ in fixed}
        for name, primitive_type in expected:
            field = schema.field(name)
            expected_type = _arrow_type(primitive_type)
            # Some published bundles use nanoseconds for UTC timestamps.
            utc_nanoseconds = primitive_type == "time" and field.type == pa.timestamp("ns", tz="UTC")
            missing_attribute = name not in fixed_names and table[name].null_count == len(table)
            if field.type != expected_type and not utc_nanoseconds and not missing_attribute:
                raise ValueError(
                    "Parquet column '%s.%s' has type %s; expected %s."
                    % (table_path, name, field.type, expected_type)
                )
            if name in fixed_names and field.nullable:
                raise ValueError("Parquet fixed column '%s.%s' must be required." % (table_path, name))
            if name not in fixed_names and not field.nullable:
                raise ValueError("Parquet attribute column '%s.%s' must be optional." % (table_path, name))
        dataframe = table.select(expected_names).to_pandas(types_mapper=pd.ArrowDtype)

    for name, primitive_type in expected:
        if primitive_type == "time":
            dataframe[name] = pd.to_datetime(dataframe[name], utc=True)
        else:
            dataframe[name] = pd.Series(
                [None if pd.isna(value) else value for value in dataframe[name].tolist()],
                index=dataframe.index,
                dtype="object",
            )

    for name in non_empty_fixed:
        if dataframe[name].isna().any() or (dataframe[name].astype(str) == "").any():
            raise ValueError("Fixed column '%s.%s' cannot contain missing values." % (table_path, name))
    return dataframe


def _reject_duplicates(dataframe: pd.DataFrame, columns: List[str], label: str):
    if len(dataframe) > 0 and dataframe.duplicated(subset=columns).any():
        raise ValueError("%s contains duplicate rows for its OCEL set key." % label)


def apply(file_path: str, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    """Imports an OCEL 2.0 log from the bundled CSV/Parquet format."""
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(
        Parameters.ENCODING, parameters, pm4_constants.DEFAULT_ENCODING
    )
    encoding = _require_utf8(encoding)
    event_id = exec_utils.get_param_value(Parameters.EVENT_ID, parameters, constants.DEFAULT_EVENT_ID)
    event_activity = exec_utils.get_param_value(Parameters.EVENT_ACTIVITY, parameters, constants.DEFAULT_EVENT_ACTIVITY)
    event_timestamp = exec_utils.get_param_value(Parameters.EVENT_TIMESTAMP, parameters, constants.DEFAULT_EVENT_TIMESTAMP)
    object_id = exec_utils.get_param_value(Parameters.OBJECT_ID, parameters, constants.DEFAULT_OBJECT_ID)
    object_type = exec_utils.get_param_value(Parameters.OBJECT_TYPE, parameters, constants.DEFAULT_OBJECT_TYPE)
    qualifier = exec_utils.get_param_value(Parameters.QUALIFIER, parameters, constants.DEFAULT_QUALIFIER)
    changed_field = exec_utils.get_param_value(Parameters.CHANGED_FIELD, parameters, constants.DEFAULT_CHNGD_FIELD)

    file_path = str(file_path)
    meta = _read_meta(file_path, encoding)
    _validate_container(file_path, meta)
    storage_format = meta["storageFormat"]

    event_frames = []
    event_id_type = {}
    event_id_time = {}
    for event_type_name, descriptor in meta["eventTypes"].items():
        attributes = descriptor["_attributes"]
        dataframe = _read_table(
            file_path,
            descriptor["file"],
            storage_format,
            encoding,
            [("ocel_id", "string"), ("ocel_time", "time")],
            attributes,
            {"ocel_id", "ocel_time"},
        ).rename(columns={"ocel_id": event_id, "ocel_time": event_timestamp})
        for eid, timestamp in dataframe[[event_id, event_timestamp]].itertuples(index=False, name=None):
            if eid in event_id_type:
                raise ValueError("Event id '%s' occurs more than once in the bundle." % eid)
            event_id_type[eid] = event_type_name
            event_id_time[eid] = timestamp
        dataframe[event_activity] = event_type_name
        event_frames.append(dataframe)

    object_frames = []
    object_change_frames = []
    object_id_type = {}
    for object_type_name, descriptor in meta["objectTypes"].items():
        attributes = descriptor["_attributes"]
        dataframe = _read_table(
            file_path,
            descriptor["file"],
            storage_format,
            encoding,
            [("ocel_id", "string")],
            attributes,
            {"ocel_id"},
        ).rename(columns={"ocel_id": object_id})
        for oid in dataframe[object_id].tolist():
            if oid in object_id_type:
                raise ValueError("Object id '%s' occurs more than once in the bundle." % oid)
            object_id_type[oid] = object_type_name
        dataframe[object_type] = object_type_name
        object_frames.append(dataframe)

        changes = _read_table(
            file_path,
            descriptor["changesFile"],
            storage_format,
            encoding,
            [
                ("ocel_id", "string"),
                ("ocel_time", "time"),
                ("ocel_changed_field", "string"),
            ],
            attributes,
            {"ocel_id", "ocel_time", "ocel_changed_field"},
        ).rename(
            columns={
                "ocel_id": object_id,
                "ocel_time": event_timestamp,
                "ocel_changed_field": changed_field,
            }
        )
        changes[object_type] = object_type_name
        attribute_names = {name for name, _ in attributes}
        for record in changes.to_dict(orient="records"):
            oid = record[object_id]
            field = record[changed_field]
            if field not in attribute_names:
                raise ValueError("Object-change field '%s' is not declared." % field)
            if pd.Timestamp(record[event_timestamp]).value == 0:
                raise ValueError(
                    "Object-change tables cannot contain assignments at the UNIX epoch; "
                    "initial values belong in the object table."
                )
            if pd.isna(record.get(field)):
                raise ValueError("Object-change row for '%s' has no changed value." % oid)
            if any(
                name != field and not pd.isna(record.get(name))
                for name in attribute_names
            ):
                raise ValueError("An object-change row must assign exactly one attribute.")
        object_change_frames.append(changes)

    events = pandas_utils.concat(event_frames, ignore_index=True) if event_frames else _instantiate_dataframe([], [event_id, event_timestamp, event_activity])
    objects = pandas_utils.concat(object_frames, ignore_index=True) if object_frames else _instantiate_dataframe([], [object_id, object_type])
    object_changes = pandas_utils.concat(object_change_frames, ignore_index=True) if object_change_frames else _instantiate_dataframe([], [object_id, event_timestamp, changed_field, object_type])
    _reject_duplicates(
        object_changes,
        [object_id, event_timestamp, changed_field],
        "Object-change tables",
    )

    for oid, change_type in object_changes[[object_id, object_type]].itertuples(index=False, name=None):
        if object_id_type.get(oid) != change_type:
            raise ValueError("Object change references an unknown or differently typed object '%s'." % oid)

    relations_meta = meta["relations"]
    e2o = _read_table(
        file_path,
        relations_meta["e2o"],
        storage_format,
        encoding,
        [
            ("ocel_event_id", "string"),
            ("ocel_object_id", "string"),
            ("ocel_qualifier", "string"),
        ],
        [],
        {"ocel_event_id", "ocel_object_id"},
    ).rename(columns={"ocel_event_id": event_id, "ocel_object_id": object_id, "ocel_qualifier": qualifier})
    _reject_duplicates(e2o, [event_id, object_id, qualifier], "E2O table")
    if any(eid not in event_id_type for eid in e2o[event_id].tolist()):
        raise ValueError("E2O table references an unknown event.")
    if any(oid not in object_id_type for oid in e2o[object_id].tolist()):
        raise ValueError("E2O table references an unknown object.")
    e2o[event_activity] = e2o[event_id].map(event_id_type)
    e2o[event_timestamp] = e2o[event_id].map(event_id_time)
    e2o[object_type] = e2o[object_id].map(object_id_type)

    o2o = _read_table(
        file_path,
        relations_meta["o2o"],
        storage_format,
        encoding,
        [
            ("ocel_source_id", "string"),
            ("ocel_target_id", "string"),
            ("ocel_qualifier", "string"),
        ],
        [],
        {"ocel_source_id", "ocel_target_id"},
    ).rename(columns={"ocel_source_id": object_id, "ocel_target_id": object_id + "_2", "ocel_qualifier": qualifier})
    _reject_duplicates(o2o, [object_id, object_id + "_2", qualifier], "O2O table")
    if any(oid not in object_id_type for oid in o2o[object_id].tolist()):
        raise ValueError("O2O table references an unknown source object.")
    if any(oid not in object_id_type for oid in o2o[object_id + "_2"].tolist()):
        raise ValueError("O2O table references an unknown target object.")

    for dataframe in (events, e2o, object_changes):
        if len(dataframe) > 0:
            dataframe.sort_values(event_timestamp, kind="stable", inplace=True)

    ocel = OCEL(
        events=events,
        objects=objects,
        relations=e2o,
        o2o=o2o,
        object_changes=object_changes,
        globals={
            constants.OCEL_EVTYPES_KEY: {
                name: dict(descriptor["_attributes"])
                for name, descriptor in meta["eventTypes"].items()
            },
            constants.OCEL_OBJTYPES_KEY: {
                name: dict(descriptor["_attributes"])
                for name, descriptor in meta["objectTypes"].items()
            },
        },
        parameters=parameters,
    )
    return ocel_consistency.apply(ocel, parameters=parameters)
