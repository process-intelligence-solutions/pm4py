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
from itertools import groupby
from typing import Optional, Dict, Any

from lxml import etree

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.importer.attribute_time import object_change_time
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import compression
from pm4py.util import exec_utils, dt_parsing, pandas_utils
from pm4py.objects.ocel.util import ocel_consistency


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


def parse_xml(value, attribute_type, parser):
    if attribute_type in ("string", None):
        return value if value is not None else ""
    if value in (None, "null"):
        return None
    if attribute_type in ("float", "double"):
        return float(value)
    if attribute_type in ("int", "integer"):
        return int(value)
    if attribute_type == "boolean":
        return {"true": True, "false": False, "1": True, "0": False}.get(value.strip().lower(), value)
    if attribute_type in ("date", "time"):
        return embed_date_parser(parser.apply, value)
    return value


def embed_date_parser(date_parser, x):
    try:
        return date_parser(x)
    except BaseException:
        from dateutil.parser import parse

        try:
            return parse(x)
        except BaseException:
            return parse(x, fuzzy=True)


def _iter_xml_rows(file_path, encoding):
    """Yield records beneath the log's top-level sections and free them after use."""
    tags = ("{*}object-type", "{*}event-type", "{*}object", "{*}event")
    with compression.open_binary(file_path, "rb") as source:
        for _, element in etree.iterparse(
            source, events=("end",), tag=tags, encoding=encoding, remove_comments=True
        ):
            section = element.getparent()
            root = section.getparent() if section is not None else None
            # Some logs use <object> for relationship entries nested inside records.
            if root is None or root.getparent() is not None:
                continue
            yield element
            element.clear()
            while element.getprevious() is not None:
                del section[0]


def apply(file_path: str, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    if parameters is None:
        parameters = {}

    events_list = []
    relations_list = []
    objects_list = []
    object_changes_list = []
    o2o_list = []

    encoding = exec_utils.get_param_value(
        Parameters.ENCODING, parameters, None
    )

    event_id_column = exec_utils.get_param_value(
        Parameters.EVENT_ID, parameters, constants.DEFAULT_EVENT_ID
    )
    event_activity_column = exec_utils.get_param_value(
        Parameters.EVENT_ACTIVITY, parameters, constants.DEFAULT_EVENT_ACTIVITY
    )
    event_timestamp_column = exec_utils.get_param_value(
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
    qualifier_field = exec_utils.get_param_value(
        Parameters.QUALIFIER, parameters, constants.DEFAULT_QUALIFIER
    )
    changed_field = exec_utils.get_param_value(
        Parameters.CHANGED_FIELD, parameters, constants.DEFAULT_CHNGD_FIELD
    )
    obj_type_dict = {}

    date_parser = dt_parsing.parser.get()

    object_type_attributes = {}
    event_type_attributes = {}

    rows = _iter_xml_rows(file_path, encoding)
    for section, child in groupby(rows, key=lambda element: element.getparent().tag):
        if section.endswith("object-types"):
            for object_type in child:
                object_type_name = object_type.get("name")
                object_type_attributes[object_type_name] = {}
                for attributes in object_type:
                    for attribute in attributes:
                        attribute_name = attribute.get("name")
                        attribute_type = attribute.get("type")
                        object_type_attributes[object_type_name][
                            attribute_name
                        ] = attribute_type
        elif section.endswith("event-types"):
            for event_type in child:
                event_type_name = event_type.get("name")
                event_type_attributes[event_type_name] = {}
                for attributes in event_type:
                    for attribute in attributes:
                        attribute_name = attribute.get("name")
                        attribute_type = attribute.get("type")
                        event_type_attributes[event_type_name][
                            attribute_name
                        ] = attribute_type
        elif section.endswith("objects"):
            object_id = None
            object_type = None

            for object in child:
                object_id = object.get("id")
                object_type = object.get("type")

                obj_dict = {
                    object_id_column: object_id,
                    object_type_column: object_type,
                }
                obj_type_dict[object_id] = object_type
                for child2 in object:
                    if child2.tag.endswith("objects"):
                        for target_object in child2:
                            target_object_id = target_object.get("object-id")
                            qualifier = target_object.get("qualifier")

                            o2o_dict = {
                                object_id_column: object_id,
                                object_id_column + "_2": target_object_id,
                                qualifier_field: qualifier,
                            }
                            o2o_list.append(o2o_dict)

                    elif child2.tag.endswith("attributes"):
                        for attribute in child2:
                            attribute_name = attribute.get("name")
                            attribute_time = object_change_time(attribute.get("time"))
                            try:
                                attribute_type = object_type_attributes[
                                    object_type
                                ][attribute_name]
                            except BaseException:
                                attribute_type = "string"
                            attribute_text = parse_xml(
                                attribute.text, attribute_type, date_parser
                            )
                            if attribute_time is None:
                                obj_dict[attribute_name] = attribute_text
                            else:
                                object_changes_list.append(
                                    {
                                        object_id_column: object_id,
                                        object_type_column: object_type,
                                        attribute_name: attribute_text,
                                        changed_field: attribute_name,
                                        event_timestamp_column: attribute_time,
                                    }
                                )

                objects_list.append(obj_dict)

        elif section.endswith("events"):
            event_id = None
            event_type = None
            event_time = None

            for event in child:
                event_id = event.get("id")
                event_type = event.get("type")
                event_time = embed_date_parser(
                    date_parser.apply, event.get("time")
                )

                ev_dict = {
                    event_id_column: event_id,
                    event_activity_column: event_type,
                    event_timestamp_column: event_time,
                }

                for child2 in event:
                    if child2.tag.endswith("objects"):
                        for target_object in child2:
                            target_object_id = target_object.get("object-id")
                            qualifier = target_object.get("qualifier")

                            if target_object_id in obj_type_dict:
                                rel_dict = {
                                    event_id_column: event_id,
                                    event_activity_column: event_type,
                                    event_timestamp_column: event_time,
                                    object_id_column: target_object_id,
                                    object_type_column: obj_type_dict[
                                        target_object_id
                                    ],
                                    qualifier_field: qualifier,
                                }
                                relations_list.append(rel_dict)
                    elif child2.tag.endswith("attributes"):
                        for attribute in child2:
                            attribute_name = attribute.get("name")
                            attribute_text = attribute.text
                            try:
                                attribute_type = event_type_attributes[
                                    event_type
                                ][attribute_name]
                            except BaseException:
                                attribute_type = "string"
                            ev_dict[attribute_name] = parse_xml(
                                attribute_text, attribute_type, date_parser
                            )

                events_list.append(ev_dict)

    events_list = (
        pandas_utils.instantiate_dataframe(events_list, dtype="object")
        if events_list
        else None
    )
    objects_list = (
        pandas_utils.instantiate_dataframe(objects_list, dtype="object")
        if objects_list
        else None
    )
    relations_list = (
        pandas_utils.instantiate_dataframe(relations_list)
        if relations_list
        else None
    )
    o2o_list = (
        pandas_utils.instantiate_dataframe(o2o_list) if o2o_list else None
    )
    object_changes_list = (
        pandas_utils.instantiate_dataframe(object_changes_list, dtype="object")
        if object_changes_list
        else None
    )
    for table in (events_list, relations_list, object_changes_list):
        if table is not None:
            table[event_timestamp_column] = table[event_timestamp_column].infer_objects()
            table.sort_values(event_timestamp_column, kind="stable", inplace=True)

    ocel = OCEL(
        events=events_list,
        objects=objects_list,
        relations=relations_list,
        globals={
            constants.OCEL_EVTYPES_KEY: event_type_attributes,
            constants.OCEL_OBJTYPES_KEY: object_type_attributes,
        },
        o2o=o2o_list,
        object_changes=object_changes_list,
        parameters=parameters,
    )
    ocel = ocel_consistency.apply(ocel, parameters=parameters)
    return ocel_consistency.remove_dangling_relationships(ocel)
