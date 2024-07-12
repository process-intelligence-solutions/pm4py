from enum import Enum
from typing import Optional, Dict, Any

import pandas as pd
from lxml import etree

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.obj import OCEL
from pm4py.util import exec_utils, constants as pm4_constants
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.objects.ocel.util import attributes_per_type
from pm4py.objects.ocel.util import filtering_utils


class Parameters(Enum):
    EVENT_ID = constants.PARAM_EVENT_ID
    EVENT_ACTIVITY = constants.PARAM_EVENT_ACTIVITY
    EVENT_TIMESTAMP = constants.PARAM_EVENT_TIMESTAMP
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    QUALIFIER = constants.PARAM_QUALIFIER
    CHANGED_FIELD = constants.PARAM_CHNGD_FIELD
    ENCODING = "encoding"


RELOBJ_TAG = "relationship"


def apply(ocel: OCEL, target_path: str, parameters: Optional[Dict[Any, Any]] = None):
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, pm4_constants.DEFAULT_ENCODING)
    event_id_column = exec_utils.get_param_value(Parameters.EVENT_ID, parameters, ocel.event_id_column)
    event_activity_column = exec_utils.get_param_value(Parameters.EVENT_ACTIVITY, parameters, ocel.event_activity)
    event_timestamp_column = exec_utils.get_param_value(Parameters.EVENT_TIMESTAMP, parameters, ocel.event_timestamp)
    object_id_column = exec_utils.get_param_value(Parameters.OBJECT_ID, parameters, ocel.object_id_column)
    object_type_column = exec_utils.get_param_value(Parameters.OBJECT_TYPE, parameters, ocel.object_type_column)
    qualifier_column = exec_utils.get_param_value(Parameters.QUALIFIER, parameters, ocel.qualifier)
    changed_field_column = exec_utils.get_param_value(Parameters.CHANGED_FIELD, parameters, ocel.changed_field)

    ocel = ocel_consistency.apply(ocel, parameters=parameters)
    ocel = filtering_utils.propagate_relations_filtering(ocel, parameters=parameters)

    objects0 = ocel.objects.to_dict("records")
    events0 = ocel.events.to_dict("records")
    object_changes0 = ocel.object_changes.to_dict("records")
    o2o_dict = ocel.o2o.groupby(object_id_column).agg(list).to_dict("tight")
    o2o_dict = {o2o_dict["index"][i]: o2o_dict["data"][i] for i in range(len(o2o_dict["index"]))}

    relations0 = ocel.relations.groupby(event_id_column)[[object_id_column, qualifier_column]].agg(list).to_dict()
    relations0_obj_ids = relations0[object_id_column]
    relations0_qualifiers = relations0[qualifier_column]

    objects0 = {x[object_id_column]: x for x in objects0}
    events0 = {x[event_id_column]: x for x in events0}
    object_changes1 = {}
    object_changes2 = {}
    object_changes3 = {}

    for objid, obj in objects0.items():
        obj = {x: y for x, y in obj.items() if not x.startswith("ocel:") and y is not None and not pd.isna(y)}
        if len(obj) > 0:
            object_changes2[objid] = {}
            object_changes3[objid] = []
            for x, y in obj.items():
                object_changes2[objid][x] = [(y, "1970-01-01T00:00:00Z")]
                object_changes3[objid].append((x, y, "1970-01-01T00:00:00Z"))

    for chng in object_changes0:
        oid = chng[object_id_column]
        if oid not in object_changes1:
            object_changes1[oid] = {}
        if oid not in object_changes2:
            object_changes2[oid] = {}
        if oid not in object_changes3:
            object_changes3[oid] = []
        chng_time = chng[event_timestamp_column]
        if chng_time not in object_changes1[oid]:
            object_changes1[oid][chng_time] = []
        chng_field = chng[changed_field_column]
        if chng_field not in object_changes2[oid]:
            object_changes2[oid][chng_field] = []

        chng_value = chng[chng_field]
        object_changes1[oid][chng_time].append((chng_field, chng_value))
        object_changes2[oid][chng_field].append((chng_value, chng_time.isoformat()))
        object_changes3[oid].append((chng_field, chng_value, chng_time.isoformat()))

    ets, ots = attributes_per_type.get(ocel, parameters=parameters)

    root = etree.Element("log")
    object_types = etree.SubElement(root, "object-types")
    for ot in ots:
        object_type = etree.SubElement(object_types, "object-type")
        object_type.set("name", str(ot))
        object_type_attributes = etree.SubElement(object_type, "attributes")
        if len(ots[ot]) > 0:
            for k, v in ots[ot].items():
                this_type = "string"
                if "date" in v or "time" in v:
                    this_type = "date"
                elif "float" in v or "double" in v:
                    this_type = "float"
                object_type_attribute = etree.SubElement(object_type_attributes, "attribute")
                object_type_attribute.set("name", k)
                object_type_attribute.set("type", this_type)

    event_types = etree.SubElement(root, "event-types")
    for et in ets:
        event_type = etree.SubElement(event_types, "event-type")
        event_type.set("name", str(et))
        event_type_attributes = etree.SubElement(event_type, "attributes")
        if len(ets[et]) > 0:
            for k, v in ets[et].items():
                this_type = "string"
                if "date" in v or "time" in v:
                    this_type = "date"
                elif "float" in v or "double" in v:
                    this_type = "float"
                event_type_attribute = etree.SubElement(event_type_attributes, "attribute")
                event_type_attribute.set("name", k)
                event_type_attribute.set("type", this_type)

    objects = etree.SubElement(root, "objects")
    for objid, obj in objects0.items():
        object = etree.SubElement(objects, "object")
        object.set("id", str(objid))
        object.set("type", str(obj[object_type_column]))

        object_attributes = etree.SubElement(object, "attributes")
        if objid in object_changes3:
            for val in object_changes3[objid]:
                object_attribute = etree.SubElement(object_attributes, "attribute")
                object_attribute.set("name", val[0])
                object_attribute.set("time", val[2])
                object_attribute.text = str(val[1])

        if objid in o2o_dict:
            object_objects = etree.SubElement(object, "objects")
            for i in range(len(o2o_dict[objid][0])):
                object_object = etree.SubElement(object_objects, RELOBJ_TAG)
                object_object.set("object-id", o2o_dict[objid][0][i])
                object_object.set("qualifier", o2o_dict[objid][1][i])

    events = etree.SubElement(root, "events")
    for evid, eve in events0.items():
        event = etree.SubElement(events, "event")
        event.set("id", str(evid))
        event.set("type", str(eve[event_activity_column]))
        event.set("time", eve[event_timestamp_column].isoformat())
        event_attributes = etree.SubElement(event, "attributes")
        event_objects = etree.SubElement(event, "objects")
        if evid in relations0_obj_ids:
            this_ids = relations0_obj_ids[evid]
            this_qualifiers = relations0_qualifiers[evid]
            for i in range(len(this_ids)):
                event_object = etree.SubElement(event_objects, RELOBJ_TAG)
                event_object.set("object-id", str(this_ids[i]))
                event_object.set("qualifier", str(this_qualifiers[i]))
        eve = {x: y for x, y in eve.items() if not x.startswith("ocel:") and y is not None and not pd.isna(y)}
        if len(eve) > 0:
            for k, v in eve.items():
                event_attribute = etree.SubElement(event_attributes, "attribute")
                event_attribute.set("name", k)
                event_attribute.text = str(v)

    tree = etree.ElementTree(root)

    F = open(target_path, "wb")
    tree.write(F, pretty_print=True, xml_declaration=True, encoding=encoding)
    F.close()
