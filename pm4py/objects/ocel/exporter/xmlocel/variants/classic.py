from enum import Enum
from typing import Optional, Dict, Any

import pandas as pd
from lxml import etree

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.exporter.util import clean_dataframes
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import attributes_names
from pm4py.objects.ocel.util import related_objects
from pm4py.util import exec_utils, constants as pm4_constants, pandas_utils
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.objects.ocel.util import filtering_utils


class Parameters(Enum):
    EVENT_ID = constants.PARAM_EVENT_ID
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    ENCODING = "encoding"


def get_type(t0):
    if "float" in str(t0).lower() or "double" in str(t0).lower():
        return "float"
    elif "date" in str(t0).lower():
        return "date"
    elif "object" in str(t0).lower():
        return "string"
    else:
        return "string"


def apply(ocel: OCEL, target_path: str, parameters: Optional[Dict[Any, Any]] = None):
    """
    Exports an object-centric event log to a XML-OCEL file, using LXML.

    Parameters
    -----------------
    ocel
        Object-centric event log
    target_path
        Destination path
    parameters
        Parameters of the algorithm, including:
            - Parameters.EVENT_ID => the event ID column
            - Parameters.OBJECT_ID => the object ID column
            - Parameters.OBJECT_TYPE => the object type column
    """
    if parameters is None:
        parameters = {}

    event_id = exec_utils.get_param_value(Parameters.EVENT_ID, parameters, ocel.event_id_column)
    object_id = exec_utils.get_param_value(Parameters.OBJECT_ID, parameters, ocel.object_id_column)
    object_type = exec_utils.get_param_value(Parameters.OBJECT_TYPE, parameters, ocel.object_type_column)
    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, pm4_constants.DEFAULT_ENCODING)

    ocel = ocel_consistency.apply(ocel, parameters=parameters)
    ocel = filtering_utils.propagate_relations_filtering(ocel, parameters=parameters)

    all_object_types = pandas_utils.format_unique(ocel.objects[object_type].unique())
    all_attribute_names = attributes_names.get_attribute_names(ocel, parameters=parameters)
    global_event_items = ocel.globals[
        constants.OCEL_GLOBAL_EVENT] if constants.OCEL_GLOBAL_EVENT in ocel.globals else constants.DEFAULT_GLOBAL_EVENT
    global_object_items = ocel.globals[
        constants.OCEL_GLOBAL_OBJECT] if constants.OCEL_GLOBAL_OBJECT in ocel.globals else constants.DEFAULT_GLOBAL_OBJECT
    rel_objs = related_objects.related_objects_dct_overall(ocel, parameters=parameters)

    ev_cols_dtypes = {x: get_type(str(ocel.events[x].dtype)) for x in ocel.events.columns}
    ob_cols_dtypes = {x: get_type(str(ocel.objects[x].dtype)) for x in ocel.objects.columns}

    events_items, objects_items = clean_dataframes.get_dataframes_from_ocel(ocel, parameters=parameters)

    root = etree.Element("log")

    global_event = etree.SubElement(root, "global")
    global_event.set("scope", "event")
    for k, v in global_event_items.items():
        child = etree.SubElement(global_event, "string")
        child.set("key", k)
        child.set("value", v)

    global_object = etree.SubElement(root, "global")
    global_object.set("scope", "object")
    for k, v in global_object_items.items():
        child = etree.SubElement(global_object, "string")
        child.set("key", k)
        child.set("value", v)

    global_log = etree.SubElement(root, "global")
    global_log.set("scope", "log")
    attribute_names = etree.SubElement(global_log, "list")
    attribute_names.set("key", "attribute-names")
    object_types = etree.SubElement(global_log, "list")
    object_types.set("key", "object-types")

    for k in all_attribute_names:
        subel = etree.SubElement(attribute_names, "string")
        subel.set("key", "attribute-name")
        subel.set("value", k)
    for k in all_object_types:
        subel = etree.SubElement(object_types, "string")
        subel.set("key", "object-type")
        subel.set("value", k)
    version = etree.SubElement(global_log, "string")
    version.set("key", "version")
    version.set("value", constants.CURRENT_VERSION)
    ordering = etree.SubElement(global_log, "string")
    ordering.set("key", "ordering")
    ordering.set("value", constants.DEFAULT_ORDERING)

    events = etree.SubElement(root, "events")
    objects = etree.SubElement(root, "objects")

    events_items = events_items.to_dict("records")
    i = 0
    while i < len(events_items):
        event = etree.SubElement(events, "event")
        event_item = events_items[i]
        eid = event_item[event_id]
        event_item = {k: v for k, v in event_item.items() if pd.notnull(v)}
        vmap = {k: v for k, v in event_item.items() if not k.startswith(constants.OCEL_PREFIX)}
        event_item = {k: v for k, v in event_item.items() if k.startswith(constants.OCEL_PREFIX) and k != event_id}
        event_omap_items = rel_objs[eid]
        xml_event_id = etree.SubElement(event, "string")
        xml_event_id.set("key", constants.OCEL_ID_KEY.split(constants.OCEL_PREFIX)[1])
        xml_event_id.set("value", str(eid))
        for k, v in event_item.items():
            typ = ev_cols_dtypes[k]
            prop = etree.SubElement(event, typ)
            prop.set("key", k.split(constants.OCEL_PREFIX)[1])
            prop.set("value", v)
        event_omap = etree.SubElement(event, "list")
        event_omap.set("key", "omap")
        for kk in event_omap_items:
            obj = etree.SubElement(event_omap, "string")
            obj.set("key", "object-id")
            obj.set("value", str(kk))
        event_vmap = etree.SubElement(event, "list")
        event_vmap.set("key", "vmap")
        for k, v in vmap.items():
            typ = ev_cols_dtypes[k]
            attr = etree.SubElement(event_vmap, typ)
            attr.set("key", k)
            attr.set("value", str(v))
        i = i + 1
    del events_items

    objects_items = objects_items.to_dict("records")
    i = 0
    while i < len(objects_items):
        object = etree.SubElement(objects, "object")
        object_item = objects_items[i]
        oid = object_item[object_id]
        xml_object_id = etree.SubElement(object, "string")
        xml_object_id.set("key", constants.OCEL_ID_KEY.split(constants.OCEL_PREFIX)[1])
        xml_object_id.set("value", str(oid))
        xml_object_type = etree.SubElement(object, "string")
        xml_object_type.set("key", object_type.split(constants.OCEL_PREFIX)[1])
        xml_object_type.set("value", object_item[object_type])
        xml_ovmap = etree.SubElement(object, "list")
        xml_ovmap.set("key", constants.OCEL_OVMAP_KEY.split(constants.OCEL_PREFIX)[1])
        ovmap = {k: v for k, v in object_item.items() if pd.notnull(v) and not k.startswith(constants.OCEL_PREFIX)}
        for k, v in ovmap.items():
            typ = ob_cols_dtypes[k]
            attr = etree.SubElement(xml_ovmap, typ)
            attr.set("key", k)
            attr.set("value", str(v))
        i = i + 1
    del objects_items

    tree = etree.ElementTree(root)

    F = open(target_path, "wb")
    tree.write(F, pretty_print=True, xml_declaration=True, encoding=encoding)
    F.close()
