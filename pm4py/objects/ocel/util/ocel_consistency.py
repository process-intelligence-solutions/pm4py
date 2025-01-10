'''
    PM4Py – A Process Mining Library for Python
Copyright (C) 2024 Process Intelligence Solutions UG (haftungsbeschränkt)

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
