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
import sys

from graphviz import Digraph
from pm4py.util import constants
from typing import Dict, List, Tuple
from collections import defaultdict, deque
from pm4py.visualization.common.utils import *


def get_activities_color(activities_count):
    """
    Get frequency color for attributes

    Parameters
    -----------
    activities_count
        Count of attributes in the log

    Returns
    -----------
    activities_color
        Color assigned to attributes in the graph
    """
    activities_color = {}

    min_value, max_value = get_min_max_value(activities_count)

    for ac in activities_count:
        v0 = activities_count[ac]
        v1 = get_trans_freq_color(v0, min_value, max_value)

        activities_color[ac] = v1

    return activities_color


def get_activities_color_serv_time(serv_time):
    """
    Gets the color for the activities based on the service time

    Parameters
    ----------------
    serv_time
        Service time

    Returns
    ----------------
    act_color
        Dictionary associating each activity to a color based on the service time
    """
    activities_color = {}

    min_soj_time, max_soj_time = get_min_max_value(serv_time)

    for ac in serv_time:
        act_soj_time = serv_time[ac]

        trans_base_color = int(
            255 - 100 * (act_soj_time - min_soj_time) / (max_soj_time - min_soj_time + 0.00001))
        trans_base_color_hex = str(hex(trans_base_color))[2:].upper()

        activities_color[ac] = "#" + "FF" + trans_base_color_hex + trans_base_color_hex

    return activities_color


def get_min_max_value(dfg):
    """
    Gets min and max value assigned to edges
    in DFG graph

    Parameters
    -----------
    dfg
        Directly follows graph

    Returns
    -----------
    min_value
        Minimum value in directly follows graph
    max_value
        Maximum value in directly follows graph
    """
    min_value = 9999999999
    max_value = -1

    for edge in dfg:
        if dfg[edge] < min_value:
            min_value = dfg[edge]
        if dfg[edge] > max_value:
            max_value = dfg[edge]

    return min_value, max_value


def assign_penwidth_edges(dfg):
    """
    Assign penwidth to edges in directly-follows graph

    Parameters
    -----------
    dfg
        Direcly follows graph

    Returns
    -----------
    penwidth
        Graph penwidth that edges should have in the direcly follows graph
    """
    penwidth = {}
    min_value, max_value = get_min_max_value(dfg)
    for edge in dfg:
        v0 = dfg[edge]
        v1 = get_arc_penwidth(v0, min_value, max_value)
        penwidth[edge] = str(v1)

    return penwidth


def graphviz_visualization(activities_count, dfg, image_format="png", measure="frequency",
                           max_no_of_edges_in_diagram=100000, start_activities=None, end_activities=None, serv_time=None,
                           font_size="12", bgcolor=constants.DEFAULT_BGCOLOR, rankdir=constants.DEFAULT_RANKDIR_GVIZ,
                           enable_graph_title: bool = constants.DEFAULT_ENABLE_GRAPH_TITLES, graph_title: str = "Directly-Follows Graph"):
    """
    Do GraphViz visualization of a DFG graph

    Parameters
    -----------
    activities_count
        Count of attributes in the log (may include attributes that are not in the DFG graph)
    dfg
        DFG graph
    image_format
        GraphViz should be represented in this format
    measure
        Describes which measure is assigned to edges in direcly follows graph (frequency/performance)
    max_no_of_edges_in_diagram
        Maximum number of edges in the diagram allowed for visualization
    start_activities
        Start activities of the log
    end_activities
        End activities of the log
    serv_time
        For each activity, the service time in the log
    font_size
        Size of the text on the activities/edges
    bgcolor
        Background color of the visualization (i.e., 'transparent', 'white', ...)
    rankdir
        Direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    enable_graph_title
        Enables the visualization of a graph's title
    graph_title
        Graph title to display (if enable_graph_title)

    Returns
    -----------
    viz
        Digraph object
    """
    if start_activities is None:
        start_activities = []
    if end_activities is None:
        end_activities = []

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor, 'rankdir': rankdir})

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="'+str(2*int(font_size))+'">'+graph_title+'</FONT>>', labelloc="top")

    # first, remove edges in diagram that exceeds the maximum number of edges in the diagram
    dfg_key_value_list = []
    for edge in dfg:
        dfg_key_value_list.append([edge, dfg[edge]])
    # more fine grained sorting to avoid that edges that are below the threshold are
    # undeterministically removed
    dfg_key_value_list = sorted(dfg_key_value_list, key=lambda x: (x[1], x[0][0], x[0][1]), reverse=True)
    dfg_key_value_list = dfg_key_value_list[0:min(len(dfg_key_value_list), max_no_of_edges_in_diagram)]
    dfg_allowed_keys = [x[0] for x in dfg_key_value_list]
    dfg_keys = list(dfg.keys())
    for edge in dfg_keys:
        if edge not in dfg_allowed_keys:
            del dfg[edge]

    activities_count_int = copy(activities_count)

    activities_in_dfg = set(activities_count)

    # assign attributes color
    if measure == "frequency":
        activities_color = get_activities_color(activities_count_int)
    else:
        activities_color = get_activities_color_serv_time(serv_time)

    # represent nodes
    viz.attr('node', shape='box')

    if len(activities_in_dfg) == 0:
        activities_to_include = sorted(list(set(activities_count_int)))
    else:
        # take unique elements as a list not as a set (in this way, nodes are added in the same order to the graph)
        activities_to_include = sorted(list(set(activities_in_dfg)))

    start_activities_to_include = [act for act in start_activities if act in activities_to_include]
    end_activities_to_include = [act for act in end_activities if act in activities_to_include]

    # calculate edges penwidth
    ext_dfg = copy(dfg)
    if start_activities_to_include is not None and start_activities_to_include:
        for sact in start_activities_to_include:
            ext_dfg[(constants.DEFAULT_ARTIFICIAL_START_ACTIVITY, sact)] = start_activities[sact]
    if end_activities_to_include is not None and end_activities_to_include:
        for eact in end_activities_to_include:
            ext_dfg[(eact, constants.DEFAULT_ARTIFICIAL_END_ACTIVITY)] = end_activities[eact]

    penwidth = assign_penwidth_edges(ext_dfg)

    dfg_edges = sorted(list(dfg.keys()))

    activities_map = {}

    for act in activities_to_include:
        if "frequency" in measure and act in activities_count_int:
            viz.node(str(hash(act)), act + " (" + str(activities_count_int[act]) + ")", style='filled',
                     fillcolor=activities_color[act], fontsize=font_size)
            activities_map[act] = str(hash(act))
        elif "performance" in measure and act in serv_time and serv_time[act] >= 0:
            viz.node(str(hash(act)), act + " (" + human_readable_stat(serv_time[act]) + ")", fontsize=font_size,
                     style='filled', fillcolor=activities_color[act])
            activities_map[act] = str(hash(act))
        else:
            viz.node(str(hash(act)), act, fontsize=font_size)
            activities_map[act] = str(hash(act))

    # represent edges
    for edge in dfg_edges:
        if "frequency" in measure or "cost" in measure:
            label = str(dfg[edge])
        else:
            label = human_readable_stat(dfg[edge])
        viz.edge(str(hash(edge[0])), str(hash(edge[1])), label=label, penwidth=str(penwidth[edge]), fontsize=font_size)

    if start_activities_to_include:
        viz.node("@@startnode", "<&#9679;>", shape='circle', fontsize="34")
        for act in start_activities_to_include:
            label = str(start_activities[act]) if isinstance(start_activities, dict) and measure == "frequency" else ""
            viz.edge("@@startnode", activities_map[act], label=label, fontsize=font_size, penwidth=str(penwidth[(constants.DEFAULT_ARTIFICIAL_START_ACTIVITY, act)]))

    if end_activities_to_include:
        # <&#9632;>
        viz.node("@@endnode", "<&#9632;>", shape='doublecircle', fontsize="32")
        for act in end_activities_to_include:
            label = str(end_activities[act]) if isinstance(end_activities, dict) and measure == "frequency" else ""
            viz.edge(activities_map[act], "@@endnode", label=label, fontsize=font_size, penwidth=str(penwidth[(act, constants.DEFAULT_ARTIFICIAL_END_ACTIVITY)]))

    viz.attr(overlap='false')
    viz.attr(fontsize='11')

    viz.format = image_format.replace("html", "plain-ext")

    return viz
