import json
from enum import Enum
from typing import Optional, Dict, Any

from pm4py.objects.ocel import constants
from pm4py.objects.ocel.obj import OCEL
from pm4py.util import exec_utils, constants as pm4_constants
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.objects.ocel.util import filtering_utils
from pm4py.objects.ocel.exporter.jsonocel.variants import classic
from pm4py.objects.ocel.util import attributes_per_type


class Parameters(Enum):
    EVENT_ID = constants.PARAM_EVENT_ID
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    EVENT_ACTIVITY = constants.PARAM_EVENT_ACTIVITY
    EVENT_TIMESTAMP = constants.PARAM_EVENT_TIMESTAMP
    ENCODING = "encoding"


def get_enriched_object(ocel: OCEL, parameters: Optional[Dict[Any, Any]] = None):
    event_id = exec_utils.get_param_value(Parameters.EVENT_ID, parameters, ocel.event_id_column)
    object_id = exec_utils.get_param_value(Parameters.OBJECT_ID, parameters, ocel.object_id_column)
    object_type = exec_utils.get_param_value(Parameters.OBJECT_TYPE, parameters, ocel.object_type_column)
    event_activity = exec_utils.get_param_value(Parameters.EVENT_ACTIVITY, parameters, ocel.event_activity)
    event_timestamp = exec_utils.get_param_value(Parameters.EVENT_TIMESTAMP, parameters, ocel.event_timestamp)

    ocel = ocel_consistency.apply(ocel, parameters=parameters)
    ocel = filtering_utils.propagate_relations_filtering(ocel, parameters=parameters)

    base_object = classic.get_base_json_object(ocel, parameters=parameters)

    ets, ots = attributes_per_type.get(ocel, parameters=parameters)

    base_object[constants.OCEL_EVTYPES_KEY] = {}
    for et in ets:
        base_object[constants.OCEL_EVTYPES_KEY][et] = {}
        et_atts = ets[et]
        for k, v in et_atts.items():
            this_type = "string"
            if "date" in v or "time" in v:
                this_type = "date"
            elif "float" in v or "double" in v:
                this_type = "float"
            base_object[constants.OCEL_EVTYPES_KEY][et][k] = this_type

    base_object[constants.OCEL_OBJTYPES_KEY] = {}
    for ot in ots:
        base_object[constants.OCEL_OBJTYPES_KEY][ot] = {}
        ot_atts = ots[ot]
        for k, v in ot_atts.items():
            this_type = "string"
            if "date" in v or "time" in v:
                this_type = "date"
            elif "float" in v or "double" in v:
                this_type = "float"
            base_object[constants.OCEL_OBJTYPES_KEY][ot][k] = this_type

    base_object[constants.OCEL_OBJCHANGES_KEY] = []
    if len(ocel.object_changes) > 0:
        object_changes = ocel.object_changes.to_dict("records")
        for i in range(len(object_changes)):
            object_changes[i][event_timestamp] = object_changes[i][event_timestamp].isoformat()

        base_object[constants.OCEL_OBJCHANGES_KEY] = object_changes

    e2o_list = ocel.relations[[event_id, object_id, constants.DEFAULT_QUALIFIER]].to_dict("records")
    eids = set()

    for elem in e2o_list:
        eid = elem[event_id]
        oid = elem[object_id]
        qualifier = elem[constants.DEFAULT_QUALIFIER]

        if eid not in eids:
            base_object[constants.OCEL_EVENTS_KEY][eid][constants.OCEL_TYPED_OMAP_KEY] = []
            eids.add(eid)

        base_object[constants.OCEL_EVENTS_KEY][eid][constants.OCEL_TYPED_OMAP_KEY].append({object_id: oid, constants.DEFAULT_QUALIFIER: qualifier})

    o2o_list = ocel.o2o.to_dict("records")
    oids = set()

    for elem in o2o_list:
        oid = elem[object_id]
        oid2 = elem[object_id+"_2"]
        qualifier = elem[constants.DEFAULT_QUALIFIER]

        if oid not in oids:
            base_object[constants.OCEL_OBJECTS_KEY][oid][constants.OCEL_O2O_KEY] = []
            oids.add(oid)

        base_object[constants.OCEL_OBJECTS_KEY][oid][constants.OCEL_O2O_KEY].append({object_id: oid2, constants.DEFAULT_QUALIFIER: qualifier})

    return base_object


def apply(ocel: OCEL, target_path: str, parameters: Optional[Dict[Any, Any]] = None):
    """
    Exports an object-centric event log (OCEL 2.0) in a JSONOCEL 2.0 file, using the classic JSON dump

    Parameters
    ------------------
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

    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, pm4_constants.DEFAULT_ENCODING)

    json_object = get_enriched_object(ocel, parameters=parameters)

    F = open(target_path, "w", encoding=encoding)
    json.dump(json_object, F, indent=2)
    F.close()
