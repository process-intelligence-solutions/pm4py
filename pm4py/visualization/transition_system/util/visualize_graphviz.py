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
from copy import copy

from graphviz import Digraph
from pm4py.util import exec_utils, constants
from enum import Enum


class Parameters(Enum):
    FORMAT = "format"
    SHOW_LABELS = "show_labels"
    SHOW_NAMES = "show_names"
    FORCE_NAMES = "force_names"
    FILLCOLORS = "fillcolors"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def visualize(ts, parameters=None):
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    show_labels = exec_utils.get_param_value(Parameters.SHOW_LABELS, parameters, True)
    show_names = exec_utils.get_param_value(Parameters.SHOW_NAMES, parameters, True)
    force_names = exec_utils.get_param_value(Parameters.FORCE_NAMES, parameters, None)
    fillcolors = exec_utils.get_param_value(Parameters.FILLCOLORS, parameters, {})
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 11)
    font_size = str(font_size)
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Transition System")

    for state in ts.states:
        state.label = state.name

    perc_char = '%'

    if force_names:
        nts = copy(ts)
        for index, state in enumerate(nts.states):
            state.name = state.name + " (%.2f)" % (force_names[state])
            state.label = "%.2f" % (force_names[state] * 100.0)
            state.label = state.label + perc_char
        ts = nts

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph(ts.name, filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="'+str(2*int(font_size))+'">'+graph_title+'</FONT>>', labelloc="top")

    # states
    viz.attr('node')
    for s in ts.states:
        if show_names:
            if s in fillcolors:
                viz.node(str(id(s)), str(s.label), style="filled", fillcolor=fillcolors[s], fontsize=font_size)
            else:
                viz.node(str(id(s)), str(s.label), fontsize=font_size)
        else:
            if s in fillcolors:
                viz.node(str(id(s)), "", style="filled", fillcolor=fillcolors[s], fontsize=font_size)
            else:
                viz.node(str(id(s)), "", fontsize=font_size)
    # arcs
    for t in ts.transitions:
        if show_labels:
            viz.edge(str(id(t.from_state)), str(id(t.to_state)), label=t.name, fontsize=font_size)
        else:
            viz.edge(str(id(t.from_state)), str(id(t.to_state)))

    viz.attr(overlap='false')

    viz.format = image_format

    return viz
