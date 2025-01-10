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
from copy import deepcopy
from enum import Enum

from graphviz import Graph

from pm4py.objects.process_tree.utils import generic as util
from pm4py.util import exec_utils, constants
from typing import Optional, Dict, Any, Union
from pm4py.objects.process_tree.obj import ProcessTree
import graphviz


class Parameters(Enum):
    FORMAT = "format"
    COLOR_MAP = "color_map"
    ENABLE_DEEPCOPY = "enable_deepcopy"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    RANKDIR = "rankdir"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def get_color(node, color_map):
    """
    Gets a color for a node from the color map

    Parameters
    --------------
    node
        Node
    color_map
        Color map
    """
    if node in color_map:
        return color_map[node]
    return "black"


def repr_tree(tree, viz, color_map, parameters):
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 9)
    font_size = str(font_size)

    this_node_id = str(id(tree))

    if tree.operator is None:
        if tree.label is None:
            viz.node(this_node_id, "tau", style='filled', fillcolor='black', shape='box', fontsize=font_size)
        else:
            node_color = get_color(tree, color_map)
            viz.node(this_node_id, str(tree), color=node_color, fontcolor=node_color, fontsize=font_size, shape='box')
    else:
        node_color = get_color(tree, color_map)
        viz.node(this_node_id, str(tree.operator), color=node_color, fontcolor=node_color,
                 fontsize=font_size, shape='circle')

        for child in tree.children:
            repr_tree(child, viz, color_map, parameters)

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
    color_map = exec_utils.get_param_value(Parameters.COLOR_MAP, parameters, {})

    enable_deepcopy = exec_utils.get_param_value(Parameters.ENABLE_DEEPCOPY, parameters, True)

    if enable_deepcopy:
        # since the process tree object needs to be sorted in the visualization, make a deepcopy of it before
        # proceeding
        tree = deepcopy(tree)
        util.tree_sort(tree)

    repr_tree(tree, viz, color_map, parameters)

    viz.attr(overlap='false')
    viz.attr(splines='false')
    viz.format = image_format.replace("html", "plain-ext")

    return viz
