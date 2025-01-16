from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any
import warnings


def apply(ocel: OCEL, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    """
    Forces the consistency of the OCEL, ensuring that the event/object identifier,
    event/object type are of type string and non-empty.

    Parameters
    --------------
    ocel
        OCEL
    parameters
        Possible parameters of the method

    Returns
    --------------
    ocel
        Consistent OCEL
    """
    if parameters is None:
        parameters = {}

    fields = {
        "events": [ocel.event_id_column, ocel.event_activity],
        "objects": [ocel.object_id_column, ocel.object_type_column],
        "relations": [ocel.event_id_column, ocel.object_id_column, ocel.event_activity, ocel.object_type_column],
        "o2o": [ocel.object_id_column, ocel.object_id_column+"_2"],
        "e2e": [ocel.event_id_column, ocel.event_id_column+"_2"],
        "object_changes": [ocel.object_id_column]
    }

    for tab in fields:
        df = getattr(ocel, tab)
        for fie in fields[tab]:
            df = df.dropna(subset=[fie], how="any")
            df[fie] = df[fie].astype("string")
            df = df.dropna(subset=[fie], how="any")
            df = df[df[fie].str.len() > 0]
            setattr(ocel, tab, df)

    # check if the event IDs or object IDs are unique
    num_ev_ids = ocel.events[ocel.event_id_column].nunique()
    num_obj_ids = ocel.objects[ocel.object_id_column].nunique()

    if num_ev_ids < len(ocel.events):
        warnings.warn("The event identifiers in the OCEL are not unique!")

    if num_obj_ids < len(ocel.objects):
        warnings.warn("The object identifiers in the OCEL are not unique!")

    return ocel
