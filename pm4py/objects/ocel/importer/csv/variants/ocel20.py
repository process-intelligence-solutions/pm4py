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
from typing import Optional, Dict, Any, List, Tuple
import codecs
import csv
from decimal import Decimal
import json
import math
import re

import pandas as pd

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.importer.csv_rows import read_csv_rows
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.util import exec_utils, constants as pm4_constants, pandas_utils


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
    OBJECT_TYPE_PREFIX = "object_type_prefix"
    O2O_ACTIVITY = "o2o_activity"
    CSV_EVENT_ID = "csv_event_id"
    CSV_EVENT_ACTIVITY = "csv_event_activity"
    CSV_EVENT_TIMESTAMP = "csv_event_timestamp"


def _is_empty(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except BaseException:
        pass
    return str(value) == ""


def _strip_value(value) -> str:
    if _is_empty(value):
        return ""
    return str(value).strip()


def _split_entries(value: Any) -> List[str]:
    if _is_empty(value):
        return []

    value = str(value)
    if not any(char in value for char in ("/", "{", "\\")):
        return [value] if value else []

    entries = []
    current = []
    in_string = False
    escape = False
    json_depth = 0

    for char in value:
        if escape:
            current.append(char)
            escape = False
            continue
        if char == "\\":
            current.append(char)
            if json_depth == 0 or in_string:
                escape = True
            continue
        if char == '"':
            current.append(char)
            if json_depth > 0:
                in_string = not in_string
            continue
        if not in_string:
            if char == "{":
                json_depth += 1
            elif char == "}" and json_depth > 0:
                json_depth -= 1
            elif char == "/" and json_depth == 0:
                entry = "".join(current)
                if not entry:
                    raise ValueError("Object reference cells cannot contain empty references.")
                entries.append(entry)
                current = []
                continue
        current.append(char)

    if escape:
        raise ValueError("Object reference cells cannot end with a dangling escape character.")
    entry = "".join(current)
    if not entry:
        raise ValueError("Object reference cells cannot contain empty references.")
    entries.append(entry)
    return entries


def _find_unescaped(value: str, target: str) -> int:
    escape = False
    for index, char in enumerate(value):
        if escape:
            escape = False
        elif char == "\\":
            escape = True
        elif char == target:
            return index
    return -1


def _unescape_reference_part(value: str, name: str) -> str:
    result = []
    escape = False
    for char in value:
        if escape:
            if char not in ("/", "#", "{", "\\"):
                raise ValueError(
                    "Invalid escape sequence '\\%s' in an OCEL2 CSV %s." % (char, name)
                )
            result.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif char in ("/", "#", "{"):
            raise ValueError(
                "Unescaped '%s' in an OCEL2 CSV %s; escape it as '\\%s'." % (char, name, char)
            )
        else:
            result.append(char)
    if escape:
        raise ValueError("Dangling escape character in an OCEL2 CSV %s." % name)
    return "".join(result)


def _split_reference(value: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
    attrs = {}
    value = value.strip()

    json_start = _find_unescaped(value, "{")
    if json_start >= 0:
        json_part = value[json_start:]
        value = value[:json_start]
        attrs = json.loads(
            json_part,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(
                    "Non-finite JSON number '%s' is not valid JSON."
                    % constant
                )
            ),
        )
        if not isinstance(attrs, dict):
            raise ValueError("Object reference JSON attributes must be a JSON object.")

    hash_pos = _find_unescaped(value, "#")
    if hash_pos >= 0:
        object_id, qualifier = value[:hash_pos], value[hash_pos + 1:]
    else:
        object_id, qualifier = value, None

    object_id = _unescape_reference_part(object_id, "object id").strip()
    qualifier = (
        _unescape_reference_part(qualifier, "qualifier").strip()
        if qualifier is not None
        else None
    )

    if not object_id:
        raise ValueError("Object references must contain a non-empty object id.")
    _validate_attribute_values(attrs)

    return object_id, qualifier, attrs


def _validate_attribute_values(attrs: Dict[str, Any]):
    for value in attrs.values():
        if isinstance(value, (list, dict)):
            raise ValueError("JSON arrays and objects are not valid OCEL2 CSV attribute values.")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Non-finite JSON numbers are not valid OCEL2 CSV attribute values.")


def _register_object_type(
    object_id_type: Dict[str, str], object_id: str, object_type: str
):
    existing = object_id_type.get(object_id)
    if existing is not None and existing != object_type:
        raise ValueError(
            "Object '%s' appears with multiple object types: '%s' and '%s'."
            % (object_id, existing, object_type)
        )
    object_id_type[object_id] = object_type


def _instantiate_dataframe(records: List[Dict[str, Any]], columns: List[str], dtype=None):
    if records:
        return pandas_utils.instantiate_dataframe(records, dtype=dtype)
    return pandas_utils.instantiate_dataframe({column: [] for column in columns})


_TIMEZONE_RE = re.compile(r"(?:Z|[+-]\d{2}:?\d{2})$")
_CANONICAL_INTEGER_RE = re.compile(r"^-?(?:0|[1-9]\d*)$")
_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


def _parse_canonical_integer(text: str):
    """Parses text only when it is the canonical form of a 64-bit integer."""
    if not _CANONICAL_INTEGER_RE.match(text):
        return None
    parsed = int(text)
    if parsed < _INT64_MIN or parsed > _INT64_MAX:
        return None
    return parsed


def _parse_canonical_float(text: str):
    """Parses text only when it round-trips through an IEEE 754 double."""
    try:
        parsed = float(text)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    if repr(parsed) == text:
        return parsed
    integer = _parse_canonical_integer(text)
    if integer is not None and float(integer) == integer:
        return float(integer)
    return None


def _parse_timestamp(value, strip_whitespace=True):
    value = _strip_value(value) if strip_whitespace else str(value)
    if not value:
        return ""
    if not _TIMEZONE_RE.search(value):
        raise ValueError("Timestamp '%s' does not contain timezone information." % value)
    try:
        return pd.to_datetime(value, utc=True)
    except BaseException as exc:
        raise ValueError("Timestamp '%s' cannot be parsed." % value) from exc


def _parse_timestamp_column(series):
    non_empty = series != ""
    if not non_empty.any():
        return [""] * len(series)

    missing_timezone = non_empty & ~series.str.contains(_TIMEZONE_RE, regex=True)
    if missing_timezone.any():
        value = series[missing_timezone].iloc[0]
        raise ValueError("Timestamp '%s' does not contain timezone information." % value)

    parsed = pd.Series([""] * len(series), index=series.index, dtype="object")
    try:
        parsed_values = pd.to_datetime(series[non_empty], utc=True, format="mixed")
    except TypeError:
        parsed_values = pd.to_datetime(series[non_empty], utc=True)
    except BaseException as exc:
        raise ValueError("At least one timestamp cannot be parsed.") from exc

    parsed.loc[non_empty] = list(parsed_values)
    return parsed.tolist()


def _collect_object_attribute(
    object_attributes: Dict[Tuple[str, str], List[Tuple[int, Any, Any]]],
    object_id: str,
    attribute: str,
    timestamp: Any,
    value: Any,
    index: int,
):
    object_attributes.setdefault((object_id, attribute), []).append((index, timestamp, value))


def _attribute_sort_key(item):
    index, timestamp, _ = item
    if _is_empty(timestamp):
        return (0, "", index)
    return (1, pd.Timestamp(timestamp).isoformat(), index)


def _try_parse_integer(values):
    parsed = []
    for value in values:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            parsed.append(value)
        elif isinstance(value, str):
            parsed_value = _parse_canonical_integer(value)
            if parsed_value is None:
                return None
            parsed.append(parsed_value)
        else:
            return None
    return parsed


def _try_parse_float(values):
    parsed = []
    for value in values:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            try:
                parsed_value = float(value)
            except OverflowError:
                return None
            if parsed_value != value:
                return None
        elif isinstance(value, str):
            parsed_value = _parse_canonical_float(value)
            if parsed_value is None:
                return None
        else:
            return None
        if not math.isfinite(parsed_value):
            return None
        parsed.append(parsed_value)
    return parsed


def _try_parse_boolean(values):
    parsed = []
    for value in values:
        if isinstance(value, bool):
            parsed.append(value)
        elif isinstance(value, str) and value.casefold() in {"true", "false"}:
            parsed.append(value.casefold() == "true")
        else:
            return None
    return parsed


def _try_parse_timestamp_values(values):
    parsed = []
    for value in values:
        if isinstance(value, pd.Timestamp):
            parsed.append(value)
        elif isinstance(value, str):
            try:
                parsed.append(_parse_timestamp(value, strip_whitespace=False))
            except ValueError:
                return None
        else:
            return None
    return parsed


def _infer_values(values):
    non_empty = [value for value in values if not _is_empty(value)]
    if not non_empty:
        return values

    for parser in (
        _try_parse_integer,
        _try_parse_float,
        _try_parse_boolean,
        _try_parse_timestamp_values,
    ):
        parsed = parser(non_empty)
        if parsed is not None:
            iterator = iter(parsed)
            return [next(iterator) if not _is_empty(value) else value for value in values]

    return [str(value) if not _is_empty(value) else value for value in values]


def _infer_column_type(df, column):
    if len(df) == 0 or column not in df.columns:
        return df
    df = df.copy()
    df[column] = pd.Series(_infer_values(df[column].tolist()), index=df.index, dtype=object)
    return df


def _infer_event_attribute_types(df, attribute_columns):
    for column in attribute_columns:
        df = _infer_column_type(df, column)
    return df


def _infer_object_attribute_types(objects_df, object_changes_df, object_type_column, excluded_columns):
    if len(objects_df) == 0:
        return objects_df, object_changes_df

    attribute_columns = [
        column for column in objects_df.columns if column not in excluded_columns
    ]
    if len(object_changes_df) > 0:
        for column in object_changes_df.columns:
            if column not in excluded_columns and column not in attribute_columns:
                attribute_columns.append(column)

    objects_df = objects_df.copy()
    object_changes_df = object_changes_df.copy()
    object_type_indexes = {
        object_type: objects_df.index[objects_df[object_type_column] == object_type].tolist()
        for object_type in pandas_utils.format_unique(objects_df[object_type_column].dropna().unique())
    }
    change_type_indexes = {}
    if len(object_changes_df) > 0 and object_type_column in object_changes_df.columns:
        change_type_indexes = {
            object_type: object_changes_df.index[
                object_changes_df[object_type_column] == object_type
            ].tolist()
            for object_type in pandas_utils.format_unique(
                object_changes_df[object_type_column].dropna().unique()
            )
        }

    for column in attribute_columns:
        if column not in objects_df.columns:
            objects_df[column] = None
        if column not in object_changes_df.columns:
            object_changes_df[column] = None
        objects_df[column] = objects_df[column].astype("object")
        object_changes_df[column] = object_changes_df[column].astype("object")

    for object_type, object_indexes in object_type_indexes.items():
        change_indexes_for_type = change_type_indexes.get(object_type, [])
        for column in attribute_columns:
            values = []
            change_indexes = []

            values.extend(objects_df.loc[object_indexes, column].tolist())
            change_indexes = change_indexes_for_type
            values.extend(object_changes_df.loc[change_indexes, column].tolist())

            inferred = _infer_values(values)
            pos = 0
            if object_indexes:
                objects_df.loc[object_indexes, column] = inferred[pos:pos + len(object_indexes)]
                pos += len(object_indexes)
            if change_indexes:
                object_changes_df.loc[change_indexes, column] = inferred[pos:pos + len(change_indexes)]

    return objects_df, object_changes_df


def _read_rfc4180(file_path: str, encoding: str) -> pd.DataFrame:
    try:
        with open(file_path, "r", encoding=encoding, newline="") as file:
            rows = read_csv_rows(file)
    except csv.Error as exc:
        raise ValueError("Invalid RFC 4180 CSV syntax.") from exc

    if not rows:
        raise ValueError("An OCEL2 CSV file must contain a header row.")

    header = rows[0]
    if len(header) != len(set(header)):
        raise ValueError("OCEL2 CSV column names must be unique.")
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(
                "CSV row %d has %d fields; expected %d."
                % (line_number, len(row), len(header))
            )
    return pandas_utils.instantiate_dataframe(rows[1:], columns=header, dtype="object")


def _require_utf8(encoding: str) -> str:
    try:
        normalized = codecs.lookup(encoding).name
    except LookupError as exc:
        raise ValueError("Unknown OCEL2 CSV encoding '%s'." % encoding) from exc
    if normalized != "utf-8":
        raise ValueError("OCEL2 CSV files must use UTF-8 encoding.")
    return "utf-8"


def _attribute_value_key(value: Any):
    if value is None:
        return ("null", None)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float)):
        return ("number", Decimal(str(value)))
    return ("string", value)


def _deduplicate_assignments(object_id: str, attribute: str, values):
    unique = []
    by_timestamp = {}
    for index, timestamp, value in sorted(values, key=_attribute_sort_key):
        normalized_timestamp = _EPOCH if _is_empty(timestamp) else pd.Timestamp(timestamp)
        value_key = _attribute_value_key(value)
        if normalized_timestamp in by_timestamp:
            if by_timestamp[normalized_timestamp] != value_key:
                raise ValueError(
                    "Object attribute '%s' of object '%s' has different values at timestamp %s."
                    % (attribute, object_id, normalized_timestamp.isoformat())
                )
            continue
        by_timestamp[normalized_timestamp] = value_key
        unique.append((index, normalized_timestamp, value))
    return unique


def apply(
    file_path: str,
    objects_path: str = None,
    parameters: Optional[Dict[Any, Any]] = None,
) -> OCEL:
    """
    Imports an OCEL 2.0 object-centric event log from the compact CSV format.
    """
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(
        Parameters.ENCODING, parameters, pm4_constants.DEFAULT_ENCODING
    )
    encoding = _require_utf8(encoding)
    event_id_column = exec_utils.get_param_value(
        Parameters.EVENT_ID, parameters, constants.DEFAULT_EVENT_ID
    )
    event_activity_column = exec_utils.get_param_value(
        Parameters.EVENT_ACTIVITY, parameters, constants.DEFAULT_EVENT_ACTIVITY
    )
    event_timestamp_column = exec_utils.get_param_value(
        Parameters.EVENT_TIMESTAMP, parameters, constants.DEFAULT_EVENT_TIMESTAMP
    )
    object_id_column = exec_utils.get_param_value(
        Parameters.OBJECT_ID, parameters, constants.DEFAULT_OBJECT_ID
    )
    object_type_column = exec_utils.get_param_value(
        Parameters.OBJECT_TYPE, parameters, constants.DEFAULT_OBJECT_TYPE
    )
    qualifier_column = exec_utils.get_param_value(
        Parameters.QUALIFIER, parameters, constants.DEFAULT_QUALIFIER
    )
    changed_field_column = exec_utils.get_param_value(
        Parameters.CHANGED_FIELD, parameters, constants.DEFAULT_CHNGD_FIELD
    )
    object_type_prefix = exec_utils.get_param_value(
        Parameters.OBJECT_TYPE_PREFIX, parameters, "ot:"
    )
    o2o_activity = exec_utils.get_param_value(
        Parameters.O2O_ACTIVITY, parameters, "o2o"
    )
    csv_event_id = exec_utils.get_param_value(
        Parameters.CSV_EVENT_ID, parameters, "id"
    )
    csv_event_activity = exec_utils.get_param_value(
        Parameters.CSV_EVENT_ACTIVITY, parameters, "activity"
    )
    csv_event_timestamp = exec_utils.get_param_value(
        Parameters.CSV_EVENT_TIMESTAMP, parameters, "timestamp"
    )

    table = _read_rfc4180(file_path, encoding)
    for column in (csv_event_id, csv_event_activity, csv_event_timestamp):
        if column not in table.columns:
            raise ValueError("Missing required OCEL2 CSV column '%s'." % column)
    table[csv_event_id] = table[csv_event_id].astype(str).str.strip()
    table[csv_event_activity] = table[csv_event_activity].astype(str).str.strip()
    table[csv_event_timestamp] = table[csv_event_timestamp].astype(str).str.strip()
    parsed_timestamps = _parse_timestamp_column(table[csv_event_timestamp])

    object_type_columns = [
        column for column in table.columns if str(column).startswith(object_type_prefix)
    ]
    if any(str(column) == object_type_prefix for column in object_type_columns):
        raise ValueError("OCEL2 CSV object type columns must name an object type.")
    event_attribute_columns = [
        column
        for column in table.columns
        if column not in {csv_event_id, csv_event_activity, csv_event_timestamp}
        and column not in object_type_columns
    ]

    events = []
    relations = []
    o2o = []
    object_id_type = {}
    object_attributes = {}
    declared_object_types = {}
    event_ids = set()
    relation_keys = set()
    o2o_keys = set()

    records = table.to_dict(orient="records")
    object_type_column_pairs = [
        (column, str(column)[len(object_type_prefix):]) for column in object_type_columns
    ]

    for index, row in enumerate(records):
        row_id = row.get(csv_event_id, "")
        row_activity = row.get(csv_event_activity, "")
        row_timestamp = row.get(csv_event_timestamp, "")
        parsed_timestamp = parsed_timestamps[index]

        is_o2o_row = (
            bool(row_activity)
            and row_activity.casefold() == str(o2o_activity).casefold()
        )
        is_object_attribute_row = not row_id and not row_activity and bool(row_timestamp)
        is_object_declaration_row = not row_id and not row_activity and not row_timestamp
        is_event_row = bool(row_id) and bool(row_activity) and bool(row_timestamp) and not is_o2o_row

        if is_o2o_row:
            if not row_id:
                raise ValueError("Object-to-object rows must contain a source object id.")
        elif not (is_event_row or is_object_attribute_row or is_object_declaration_row):
            raise ValueError(
                "Invalid OCEL2 CSV row %d: unsupported id/activity/timestamp combination."
                % (index + 2)
            )

        if not is_event_row and any(
            not _is_empty(row.get(column, "")) for column in event_attribute_columns
        ):
            raise ValueError(
                "Event attribute values are only valid in event rows (CSV row %d)."
                % (index + 2)
            )

        if is_event_row:
            if row_id in event_ids:
                raise ValueError("Duplicate event id '%s' in OCEL2 CSV file." % row_id)
            event_ids.add(row_id)
            event = {
                event_id_column: row_id,
                event_activity_column: row_activity,
                event_timestamp_column: parsed_timestamp,
            }
            for column in event_attribute_columns:
                if not _is_empty(row.get(column, "")):
                    event[column] = row[column]
            events.append(event)

        if is_o2o_row:
            if row_id not in declared_object_types:
                raise ValueError(
                    "Source object '%s' in an object-to-object row has no previously declared object type."
                    % row_id
                )
        reference_count = 0
        for column, object_type in object_type_column_pairs:
            for entry in _split_entries(row.get(column, "")):
                reference_count += 1
                object_id, qualifier, attrs = _split_reference(entry)

                _register_object_type(object_id_type, object_id, object_type)

                if is_event_row:
                    declared_object_types[object_id] = object_type
                    relation_key = (
                        row_id,
                        object_id,
                        "" if qualifier is None else qualifier,
                    )
                    if relation_key in relation_keys:
                        raise ValueError("Duplicate event-to-object relation in OCEL2 CSV file.")
                    relation_keys.add(relation_key)
                    relations.append(
                        {
                            event_id_column: row_id,
                            event_activity_column: row_activity,
                            event_timestamp_column: parsed_timestamp,
                            object_id_column: object_id,
                            object_type_column: object_type,
                            qualifier_column: "" if qualifier is None else qualifier,
                        }
                    )
                    for attr, value in attrs.items():
                        _collect_object_attribute(
                            object_attributes, object_id, attr, parsed_timestamp, value, index
                        )
                elif is_o2o_row:
                    declared_object_types[object_id] = object_type
                    o2o_key = (
                        row_id,
                        object_id,
                        "" if qualifier is None else qualifier,
                    )
                    if o2o_key in o2o_keys:
                        raise ValueError("Duplicate object-to-object relation in OCEL2 CSV file.")
                    o2o_keys.add(o2o_key)
                    o2o.append(
                        {
                            object_id_column: row_id,
                            object_id_column + "_2": object_id,
                            qualifier_column: "" if qualifier is None else qualifier,
                        }
                    )
                    if attrs and not parsed_timestamp:
                        raise ValueError(
                            "Object-to-object rows with JSON attributes must contain a timestamp."
                        )
                    for attr, value in attrs.items():
                        _collect_object_attribute(
                            object_attributes, object_id, attr, parsed_timestamp, value, index
                        )
                elif is_object_attribute_row:
                    declared_object_types[object_id] = object_type
                    if not attrs:
                        raise ValueError(
                            "Object attribute rows must contain JSON attributes."
                        )
                    for attr, value in attrs.items():
                        _collect_object_attribute(
                            object_attributes, object_id, attr, parsed_timestamp, value, index
                        )
                elif is_object_declaration_row:
                    if qualifier is not None:
                        raise ValueError(
                            "Object declaration rows cannot contain qualifiers."
                        )
                    declared_object_types[object_id] = object_type
                    for attr, value in attrs.items():
                        _collect_object_attribute(
                            object_attributes, object_id, attr, None, value, index
                        )

        if is_object_attribute_row and reference_count == 0:
            raise ValueError("Object attribute rows must contain an object reference.")
        if is_o2o_row and reference_count == 0:
            raise ValueError("Object-to-object rows must contain a target object reference.")

    events_df = _instantiate_dataframe(
        events, [event_id_column, event_activity_column, event_timestamp_column]
    )
    relations_df = _instantiate_dataframe(
        relations,
        [
            event_id_column,
            event_activity_column,
            event_timestamp_column,
            object_id_column,
            object_type_column,
            qualifier_column,
        ],
    )
    o2o_df = _instantiate_dataframe(
        o2o, [object_id_column, object_id_column + "_2", qualifier_column]
    )

    events_df = _infer_event_attribute_types(events_df, event_attribute_columns)

    if object_id_type:
        object_records = []
        for object_id, object_type in object_id_type.items():
            object_records.append(
                {object_id_column: object_id, object_type_column: object_type}
            )
    else:
        object_records = []

    object_changes = []
    object_records_by_id = {record[object_id_column]: record for record in object_records}

    for (object_id, attr), values in object_attributes.items():
        values = _deduplicate_assignments(object_id, attr, values)
        object_type = object_id_type.get(object_id)
        if object_id not in object_records_by_id:
            object_records_by_id[object_id] = {
                object_id_column: object_id,
                object_type_column: object_type,
            }

        for _, timestamp, value in values:
            if timestamp == _EPOCH:
                object_records_by_id[object_id][attr] = value
            else:
                change = {
                    object_id_column: object_id,
                    object_type_column: object_type,
                    event_timestamp_column: timestamp,
                    changed_field_column: attr,
                    attr: value,
                }
                object_changes.append(change)

    objects_df = _instantiate_dataframe(
        list(object_records_by_id.values()), [object_id_column, object_type_column], dtype=object
    )
    object_changes_df = _instantiate_dataframe(
        object_changes,
        [object_id_column, object_type_column, event_timestamp_column, changed_field_column],
        dtype=object,
    )
    objects_df, object_changes_df = _infer_object_attribute_types(
        objects_df,
        object_changes_df,
        object_type_column,
        {
            object_id_column,
            object_type_column,
            event_timestamp_column,
            changed_field_column,
        },
    )

    object_changes_df[event_timestamp_column] = object_changes_df[event_timestamp_column].infer_objects()
    for table in (events_df, relations_df, object_changes_df):
        table.sort_values(event_timestamp_column, kind="stable", inplace=True)

    ocel = OCEL(
        events=events_df,
        objects=objects_df,
        relations=relations_df,
        o2o=o2o_df,
        object_changes=object_changes_df,
        parameters=parameters,
    )
    ocel = ocel_consistency.apply(ocel, parameters=parameters)

    return ocel
