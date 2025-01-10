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
import uuid

from typing import Optional, Dict, Any, Union
from pm4py.objects.transition_system.obj import TransitionSystem
import graphviz

import tempfile

from graphviz import Digraph
from pm4py.util import exec_utils, constants
from enum import Enum


class Parameters(Enum):
    FORMAT = "format"
    BGCOLOR = "bgcolor"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def get_perc(total_events, arc_events):
    if total_events > 0:
        return " " + str(total_events) + " / %.2f %%" % (100.0 * arc_events / total_events)
    return " 0 / 0.00 %"


def apply(tsys: TransitionSystem, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> graphviz.Digraph:
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)

    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Transition System")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph(tsys.name, filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>', labelloc="top")

    states_dictio = {}

    for s in tsys.states:
        node_uuid = str(uuid.uuid4())
        states_dictio[id(s)] = node_uuid

        sum_ingoing = 0
        sum_outgoing = 0

        for t in s.incoming:
            sum_ingoing += len(t.data["events"])

        for t in s.outgoing:
            sum_outgoing += len(t.data["events"])

        fillcolor = "white"

        if sum_ingoing != len(s.data["ingoing_events"]) or sum_outgoing != len(s.data["outgoing_events"]):
            fillcolor = "red"

        taillabel = get_perc(sum_ingoing, len(s.data["ingoing_events"]))
        headlabel = get_perc(sum_outgoing, len(s.data["outgoing_events"]))

        label = "IN=" + taillabel + "\n" + str(s.name) + "\nOUT=" + headlabel

        viz.node(node_uuid, label=label, fontsize="10", style="filled", fillcolor=fillcolor)

    for t in tsys.transitions:
        viz.edge(states_dictio[id(t.from_state)], states_dictio[id(t.to_state)], fontsize="8", label=str(t.name),
                 taillabel=get_perc(len(t.from_state.data["outgoing_events"]), len(t.data["events"])),
                 headlabel=get_perc(len(t.to_state.data["ingoing_events"]), len(t.data["events"])))

    viz.attr(overlap='false')

    viz.format = image_format.replace("html", "plain-ext")

    return viz
