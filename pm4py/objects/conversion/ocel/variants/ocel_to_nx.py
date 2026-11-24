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
from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any
from pm4py.util import exec_utils, nx_utils
from pm4py.objects.conversion.log.variants import to_event_stream
from copy import copy


class Parameters(Enum):
    INCLUDE_DF = "include_df"
    INCLUDE_OBJECT_CHANGES = "include_object_changes"
    INCLUDE_NODE_ID_TYPE = "include_node_id_type"


def apply(ocel: OCEL, parameters: Optional[Dict[Any, Any]] = None):
    """
    Converts an OCEL to a NetworkX MultiDiGraph object.
    The nodes are the events and objects of the OCEL.
    Edges represent event-object and object-object relations, directly-follows
    relations in object lifecycles, and links from attribute changes to objects.

    Parameters
    ---------------
    ocel
        Object-centric event log
    parameters
        Parameters of the algorithm, including:
        - Parameters.INCLUDE_DF => include the directly-follows relationship
        - Parameters.INCLUDE_OBJECT_CHANGES => include object attribute changes
        - Parameters.INCLUDE_NODE_ID_TYPE => prefix node IDs with their type
          (EVENT, OBJECT, CHANGE) to keep the ID namespaces separate

    Returns
    ---------------
    G
        NetworkX MultiDiGraph
    """
    if parameters is None:
        parameters = {}

    include_df = exec_utils.get_param_value(
        Parameters.INCLUDE_DF, parameters, True
    )
    include_object_changes = exec_utils.get_param_value(
        Parameters.INCLUDE_OBJECT_CHANGES, parameters, True
    )
    include_node_id_type = exec_utils.get_param_value(
        Parameters.INCLUDE_NODE_ID_TYPE, parameters, False
    )

    def node_id(kind, identifier):
        return f"{kind}:{identifier}" if include_node_id_type else identifier

    G = nx_utils.MultiDiGraph()

    stream = ocel.events.to_dict(orient="records")
    stream = to_event_stream.__postprocess_stream(stream)
    for ev in stream:
        ev["type"] = "EVENT"
        G.add_node(node_id("EVENT", ev[ocel.event_id_column]), attr=ev)

    stream = ocel.objects.to_dict(orient="records")
    stream = to_event_stream.__postprocess_stream(stream)
    for obj in stream:
        obj["type"] = "OBJECT"
        G.add_node(node_id("OBJECT", obj[ocel.object_id_column]), attr=obj)

    rel_cols = {ocel.event_id_column, ocel.object_id_column, ocel.qualifier}

    relations = ocel.relations[list(rel_cols)]
    stream = relations.to_dict(orient="records")
    for rel in stream:
        qualifier = rel[ocel.qualifier]
        if qualifier is None:
            qualifier = ""
        G.add_edge(
            node_id("EVENT", rel[ocel.event_id_column]),
            node_id("OBJECT", rel[ocel.object_id_column]),
            attr={"type": "E2O", "qualifier": qualifier},
        )

    obj_relations = ocel.o2o[
        [ocel.object_id_column, ocel.object_id_column + "_2", ocel.qualifier]
    ]
    stream = obj_relations.to_dict(orient="records")
    for rel in stream:
        qualifier = rel[ocel.qualifier]
        if qualifier is None:
            qualifier = ""
        G.add_edge(
            node_id("OBJECT", rel[ocel.object_id_column]),
            node_id("OBJECT", rel[ocel.object_id_column + "_2"]),
            attr={"type": "O2O", "qualifier": qualifier},
        )

    if include_df:
        lifecycle = (
            relations[[ocel.event_id_column, ocel.object_id_column]]
            .drop_duplicates()
            .merge(
                ocel.events[[ocel.event_id_column, ocel.event_timestamp]],
                on=ocel.event_id_column,
            )
            .sort_values(ocel.event_timestamp, kind="stable")
            .groupby(ocel.object_id_column)
            .agg(list)
            .to_dict()[ocel.event_id_column]
        )
        for obj in lifecycle:
            lif = lifecycle[obj]
            for i in range(len(lif) - 1):
                G.add_edge(
                    node_id("EVENT", lif[i]),
                    node_id("EVENT", lif[i + 1]),
                    attr={"type": "DF", "object": obj},
                )

    if include_object_changes:
        object_changes = ocel.object_changes.to_dict(orient="records")
        for i in range(len(object_changes)):
            change_id = node_id("CHANGE", i) if include_node_id_type else "@@change##%d" % i
            change_dict = copy(object_changes[i])
            change_dict["type"] = "CHANGE"
            G.add_node(change_id, attr=change_dict)
            G.add_edge(
                change_id,
                node_id("OBJECT", object_changes[i][ocel.object_id_column]),
                attr={"type": "CHANGE"},
            )

    return G
