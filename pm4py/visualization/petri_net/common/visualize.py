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
import tempfile

from graphviz import Digraph

from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.objects.petri_net import properties as petri_properties
from pm4py.util import exec_utils, constants
from enum import Enum
from typing import List, Tuple, Dict
from collections import defaultdict, deque
from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY, PARAMETER_CONSTANT_TIMESTAMP_KEY


class Parameters(Enum):
    FORMAT = "format"
    DEBUG = "debug"
    RANKDIR = "set_rankdir"
    ACTIVITY_KEY = PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = PARAMETER_CONSTANT_TIMESTAMP_KEY
    AGGREGATION_MEASURE = "aggregationMeasure"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    DECORATIONS = "decorations"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def apply(net, initial_marking, final_marking, decorations=None, parameters=None):
    """
    Apply method for Petri net visualization (it calls the
    graphviz_visualization method)

    Parameters
    -----------
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    decorations
        Decorations for elements in the Petri net
    parameters
        Algorithm parameters

    Returns
    -----------
    viz
        Graph object
    """
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    debug = exec_utils.get_param_value(Parameters.DEBUG, parameters, False)
    set_rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, None)
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, "12")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Petri Net")

    if decorations is None:
        decorations = exec_utils.get_param_value(Parameters.DECORATIONS, parameters, None)

    return graphviz_visualization(net, image_format=image_format, initial_marking=initial_marking,
                                  final_marking=final_marking, decorations=decorations, debug=debug,
                                  set_rankdir=set_rankdir, font_size=font_size, bgcolor=bgcolor,
                                  enable_graph_title=enable_graph_title, graph_title=graph_title)


def graphviz_visualization(net, image_format="png", initial_marking=None, final_marking=None, decorations=None,
                           debug=False, set_rankdir=None, font_size="12", bgcolor=constants.DEFAULT_BGCOLOR,
                           enable_graph_title: bool = constants.DEFAULT_ENABLE_GRAPH_TITLES, graph_title: str = "Petri Net"):
    """
    Provides visualization for the petrinet

    Parameters
    ----------
    net: :class:`pm4py.entities.petri.petrinet.PetriNet`
        Petri net
    image_format
        Format that should be associated to the image
    initial_marking
        Initial marking of the Petri net
    final_marking
        Final marking of the Petri net
    decorations
        Decorations of the Petri net (says how element must be presented)
    debug
        Enables debug mode
    set_rankdir
        Sets the rankdir to LR (horizontal layout)
    enable_graph_title
        Enables the visualization of a graph's title
    graph_title
        Graph title to display (if enable_graph_title)

    Returns
    -------
    viz :
        Returns a graph object
    """
    if initial_marking is None:
        initial_marking = Marking()
    if final_marking is None:
        final_marking = Marking()
    if decorations is None:
        decorations = {}

    font_size = str(font_size)

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph(net.name, filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    if set_rankdir:
        viz.graph_attr['rankdir'] = set_rankdir
    else:
        viz.graph_attr['rankdir'] = 'LR'

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="'+str(2*int(font_size))+'">'+graph_title+'</FONT>>', labelloc="top")

    # transitions
    viz.attr('node', shape='box')
    for t in net.transitions:
        label = decorations[t]["label"] if t in decorations and "label" in decorations[t] else ""
        fillcolor = decorations[t]["color"] if t in decorations and "color" in decorations[t] else None
        textcolor = "black"

        if t.label is not None and not label:
            label = t.label
        if debug:
            label = t.name
        label = str(label)

        if fillcolor is None:
            if t.label is None:
                fillcolor = "black"
                if label:
                    textcolor = "white"
            else:
                fillcolor = bgcolor

        viz.node(str(id(t)), label, style='filled', fillcolor=fillcolor, border='1', fontsize=font_size, fontcolor=textcolor)

        if petri_properties.TRANS_GUARD in t.properties:
            guard = t.properties[petri_properties.TRANS_GUARD]
            viz.node(str(id(t))+"guard", style="dotted", label=guard)
            viz.edge(str(id(t))+"guard", str(id(t)), arrowhead="none", style="dotted")

    # places
    # add places, in order by their (unique) name, to avoid undeterminism in the visualization
    places_sort_list_im = sorted([x for x in list(net.places) if x in initial_marking], key=lambda x: x.name)
    places_sort_list_fm = sorted([x for x in list(net.places) if x in final_marking and not x in initial_marking],
                                 key=lambda x: x.name)
    places_sort_list_not_im_fm = sorted(
        [x for x in list(net.places) if x not in initial_marking and x not in final_marking], key=lambda x: x.name)
    # making the addition happen in this order:
    # - first, the places belonging to the initial marking
    # - after, the places not belonging neither to the initial marking and the final marking
    # - at last, the places belonging to the final marking (but not to the initial marking)
    # in this way, is more probable that the initial marking is on the left and the final on the right
    places_sort_list = places_sort_list_im + places_sort_list_not_im_fm + places_sort_list_fm

    for p in places_sort_list:
        label = decorations[p]["label"] if p in decorations and "label" in decorations[p] else ""
        fillcolor = decorations[p]["color"] if p in decorations and "color" in decorations[p] else bgcolor

        label = str(label)
        if p in initial_marking:
            if initial_marking[p] == 1:
                viz.node(str(id(p)), "<&#9679;>", fontsize="34", fixedsize='true', shape="circle", width='0.75', style="filled", fillcolor=fillcolor)
            else:
                marking_label = str(initial_marking[p])
                if len(marking_label) >= 3:
                    viz.node(str(id(p)), marking_label, fontsize="34",  shape="ellipse", style="filled", fillcolor=fillcolor)
                else:
                    viz.node(str(id(p)), marking_label, fontsize="34", fixedsize='true', shape="circle", width='0.75', style="filled", fillcolor=fillcolor)
        elif p in final_marking:
            # <&#9632;>
            viz.node(str(id(p)), "<&#9632;>", fontsize="32", shape='doublecircle', fixedsize='true', width='0.75', style="filled", fillcolor=fillcolor)
        else:
            if debug:
                viz.node(str(id(p)), str(p.name), fontsize=font_size, shape="ellipse")
            else:
                if p in decorations and "label" in decorations[p]:
                    viz.node(str(id(p)), label, style='filled', fillcolor=fillcolor,
                             fontsize=font_size, shape="ellipse")
                else:
                    viz.node(str(id(p)), label, shape='circle', fixedsize='true', width='0.75', style="filled", fillcolor=fillcolor)

    # add arcs, in order by their source and target objects names, to avoid undeterminism in the visualization
    arcs_sort_list = sorted(list(net.arcs), key=lambda x: (x.source.name, x.target.name))

    # check if there is an arc with weight different than 1.
    # in that case, all the arcs in the visualization should have the arc weight visible
    arc_weight_visible = False
    for arc in arcs_sort_list:
        if arc.weight != 1:
            arc_weight_visible = True
            break

    for a in arcs_sort_list:
        penwidth = decorations[a]["penwidth"] if a in decorations and "penwidth" in decorations[a] else None
        label = decorations[a]["label"] if a in decorations and "label" in decorations[a] else ""
        color = decorations[a]["color"] if a in decorations and "color" in decorations[a] else None

        if not label and arc_weight_visible:
            label = a.weight

        label = str(label)
        arrowhead = "normal"

        if petri_properties.ARCTYPE in a.properties:
            if a.properties[petri_properties.ARCTYPE] == petri_properties.RESET_ARC:
                arrowhead = "vee"
            elif a.properties[petri_properties.ARCTYPE] == petri_properties.INHIBITOR_ARC:
                arrowhead = "dot"

        viz.edge(str(id(a.source)), str(id(a.target)), label=label,
                 penwidth=penwidth, color=color, fontsize=font_size, arrowhead=arrowhead, fontcolor=color)

    viz.attr(overlap='false')

    viz.format = image_format.replace("html", "plain-ext")

    return viz
