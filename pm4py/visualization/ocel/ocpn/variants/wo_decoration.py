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
from typing import Optional, Dict, Any
from graphviz import Digraph
from enum import Enum
from pm4py.util import exec_utils
import tempfile
from pm4py.util import vis_utils, constants
from pm4py.objects.petri_net.obj import PetriNet


class Parameters(Enum):
    FORMAT = "format"
    BGCOLOR = "bgcolor"
    RANKDIR = "rankdir"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def ot_to_color(ot: str) -> str:
    ot = int(hash(ot))
    num = []
    while len(num) < 6:
        num.insert(0, ot % 16)
        ot = ot // 16
    ret = "#" + "".join([vis_utils.get_corr_hex(x) for x in num])
    return ret


def apply(ocpn: Dict[str, Any], parameters: Optional[Dict[Any, Any]] = None) -> Digraph:
    """
    Obtains a visualization of the provided object-centric Petri net (without decoration).

    Reference paper: van der Aalst, Wil MP, and Alessandro Berti. "Discovering object-centric Petri nets." Fundamenta informaticae 175.1-4 (2020): 1-40.

    Parameters
    ----------------
    ocpn
        Object-centric Petri net
    variant
        Variant of the algorithm to be used
    parameters
        Variant-specific parameters:
        - Parameters.FORMAT => the format of the visualization ("png", "svg", ...)
        - Parameters.BGCOLOR => the background color
        - Parameters.RANKDIR => the rank direction (LR = left-right, TB = top-bottom)

    Returns
    ---------------
    gviz
        Graphviz digraph
    """
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ)

    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Object-Centric Petri net")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph("ocpn", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    viz.attr('node', shape='ellipse', fixedsize='false')

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>', labelloc="top")

    activities_map = {}
    transition_map = {}
    places = {}

    for act in ocpn["activities"]:
        activities_map[act] = str(uuid.uuid4())
        viz.node(activities_map[act], label=act, shape="box")

    for ot in ocpn["petri_nets"]:
        otc = ot_to_color(ot)
        net, im, fm = ocpn["petri_nets"][ot]
        all_places_diagn = {}
        all_trans_diagn = {}
        if ot in ocpn["tbr_results"]:
            all_places_diagn = ocpn["tbr_results"][ot][0]
            all_trans_diagn = ocpn["tbr_results"][ot][1]

        for place in net.places:
            place_id = str(uuid.uuid4())
            places[place] = place_id
            place_label = " "
            place_shape = "circle"
            place_fontcolor = None
            place_fillcolor = otc

            if place in im:
                place_label = ot
                place_shape = "ellipse"
            elif place in fm:
                place_label = ot
                place_shape = "underline"
                place_fontcolor = otc
                place_fillcolor = None

            # if the place has some TBR diagnostics, override the label in any case
            if place in all_places_diagn:
                this_diagn = all_places_diagn[place]
                place_label = "p=%d m=%d\nc=%d r=%d" % (
                    this_diagn['p'], this_diagn['m'], this_diagn['c'], this_diagn['r'])

            viz.node(places[place], label=place_label, shape=place_shape, style="filled" if place_fillcolor is not None else None, fillcolor=place_fillcolor, fontcolor=place_fontcolor)

        for trans in net.transitions:
            if trans.label is not None:
                transition_map[trans] = activities_map[trans.label]
            else:
                transition_map[trans] = str(uuid.uuid4())
                viz.node(transition_map[trans], label=" ", shape="box", style="filled", fillcolor=otc)

        for arc in net.arcs:
            arc_label = " "
            if type(arc.source) is PetriNet.Place:
                is_double = arc.target.label in ocpn["double_arcs_on_activity"][ot] and \
                            ocpn["double_arcs_on_activity"][ot][arc.target.label]
                penwidth = "4.0" if is_double else "1.0"
                if arc.target in all_trans_diagn:
                    arc_label = str(all_trans_diagn[arc.target])
                viz.edge(places[arc.source], transition_map[arc.target], color=otc, penwidth=penwidth, label=arc_label)
            elif type(arc.source) is PetriNet.Transition:
                is_double = arc.source.label in ocpn["double_arcs_on_activity"][ot] and \
                            ocpn["double_arcs_on_activity"][ot][arc.source.label]
                penwidth = "4.0" if is_double else "1.0"
                if arc.source in all_trans_diagn:
                    arc_label = str(all_trans_diagn[arc.source])
                viz.edge(transition_map[arc.source], places[arc.target], color=otc, penwidth=penwidth, label=arc_label)

    viz.attr(rankdir=rankdir)
    viz.format = image_format.replace("html", "plain-ext")

    return viz
