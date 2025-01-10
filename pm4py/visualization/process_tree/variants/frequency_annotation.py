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
from copy import deepcopy, copy
from enum import Enum

from graphviz import Graph

from pm4py.objects.process_tree.utils import generic
from pm4py.util import exec_utils
from typing import Optional, Dict, Any, Union
from pm4py.objects.process_tree.obj import ProcessTree
import graphviz
from pm4py.util import vis_utils, constants


class Parameters(Enum):
    FORMAT = "format"
    ENABLE_DEEPCOPY = "enable_deepcopy"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    RANKDIR = "rankdir"
    NUM_EVENTS_PROPERTY = "num_events_property"
    NUM_CASES_PROPERTY = "num_cases_property"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


# maps the operators to the ProM strings
operators_mapping = {"->": "seq", "X": "xor", "+": "and", "*": "xor loop", "O": "or", "<>": "interleaving"}

# root node parameter
ROOT_NODE_PARAMETER = "@@root_node"


def repr_tree_2(tree, viz, parameters):
    num_events_property = exec_utils.get_param_value(Parameters.NUM_EVENTS_PROPERTY, parameters, "num_events")
    num_cases_property = exec_utils.get_param_value(Parameters.NUM_CASES_PROPERTY, parameters, "num_cases")
    root_node = parameters[ROOT_NODE_PARAMETER]

    root_node_num_cases = root_node._properties[num_cases_property]
    this_node_num_cases = tree._properties[num_cases_property] if num_cases_property in tree._properties else 0
    this_node_num_events = tree._properties[num_events_property] if num_events_property in tree._properties else 0

    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 15)
    font_size = str(font_size)

    this_node_id = str(id(tree))

    if tree.operator is None:
        if tree.label is None:
            viz.node(this_node_id, "tau", style='filled', fillcolor='black', shape='point', width="0.075", fontsize=font_size)
        else:
            node_color = vis_utils.get_trans_freq_color(this_node_num_cases, 0, root_node_num_cases)
            node_label = str(tree) + "\nC=%d E=%d" % (this_node_num_cases, this_node_num_events)
            viz.node(this_node_id, node_label, fontsize=font_size, style="filled", fillcolor=node_color)
    else:
        node_color = vis_utils.get_trans_freq_color(this_node_num_cases, 0, root_node_num_cases)
        viz.node(this_node_id, operators_mapping[str(tree.operator)], fontsize=font_size, style="filled", fillcolor=node_color)

        for child in tree.children:
            repr_tree_2(child, viz, parameters)

    if tree.parent is not None:
        viz.edge(str(id(tree.parent)), this_node_id, dirType='none')


def apply(tree: ProcessTree, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> graphviz.Graph:
    """
    Obtain a Process Tree representation through GraphViz

    Parameters
    -----------
    tree
        Process tree
    parameters
        Possible parameters of the algorithm

    Returns
    -----------
    gviz
        GraphViz object
    """
    if parameters is None:
        parameters = {}

    parameters = copy(parameters)
    parameters[ROOT_NODE_PARAMETER] = tree

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ)
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Process Tree")
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 15)
    font_size = str(font_size)

    viz = Graph("pt", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor, "rankdir": rankdir})
    viz.attr('node', shape='ellipse', fixedsize='false')

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="'+str(2*int(font_size))+'">'+graph_title+'</FONT>>', labelloc="top")

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")

    enable_deepcopy = exec_utils.get_param_value(Parameters.ENABLE_DEEPCOPY, parameters, False)

    if enable_deepcopy:
        # since the process tree object needs to be sorted in the visualization, make a deepcopy of it before
        # proceeding
        tree = deepcopy(tree)
        generic.tree_sort(tree)

    repr_tree_2(tree, viz, parameters)

    viz.attr(overlap='false')
    viz.attr(splines='false')
    viz.format = image_format.replace("html", "plain-ext")

    return viz
