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
import sys
import uuid
from enum import Enum
from pm4py.util import exec_utils, constants
import tempfile
from graphviz import Digraph
from pm4py.util import vis_utils
from typing import Dict, Optional, Any, Tuple


class Parameters(Enum):
    FORMAT = "format"
    BGCOLOR = "bgcolor"
    ACTIVITY_THRESHOLD = "activity_threshold"
    EDGE_THRESHOLD = "edge_threshold"
    AGGREGATION_MEASURE = "aggregation_measure"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def apply(network_analysis_edges0: Dict[Tuple[str, str], Dict[str, Any]], parameters: Optional[Dict[Any, Any]] = None) -> Digraph:
    """
    Creates a visualization of the network analysis (performance view)

    Parameters
    -----------------
    network_analysis_edges0
        Edges of the network analysis
    parameters
        Parameters of the algorithm, including:
        - Parameters.FORMAT => the format of the visualization
        - Parameters.BGCOLOR => the background color
        - Parameters.ACTIVITY_THRESHOLD => the minimum number of occurrences for an activity to be included (default: 1)
        - Parameters.EDGE_THRESHOLD => the minimum number of occurrences for an edge to be included (default: 1)
        - Parameters.AGGREGATION_MEASURE => the aggregation measure (default: mean)

    Returns
    ------------------
    digraph
        Graphviz graph
    """
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    activity_threshold = exec_utils.get_param_value(Parameters.ACTIVITY_THRESHOLD, parameters, 1)
    edge_threshold = exec_utils.get_param_value(Parameters.EDGE_THRESHOLD, parameters, 1)
    aggregation_measure = exec_utils.get_param_value(Parameters.AGGREGATION_MEASURE, parameters, "mean")

    from statistics import mean, median, stdev

    aggregation_f = mean

    if aggregation_measure == "median":
        aggregation_f = median
    elif aggregation_measure == "min":
        aggregation_f = min
    elif aggregation_measure == "max":
        aggregation_f = max
    elif aggregation_measure == "stdev":
        aggregation_f = stdev
    elif aggregation_measure == "sum":
        aggregation_f = sum

    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Network Analysis")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph("pt", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    viz.attr('node', shape='ellipse', fixedsize='false')

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>', labelloc="top")

    network_analysis_edges = {}
    network_analysis_edges_agg_performance = {}
    for x in network_analysis_edges0:
        network_analysis_edges[x] = {}
        network_analysis_edges_agg_performance[x] = {}
        for y in network_analysis_edges0[x]:
            network_analysis_edges[x][y] = len(network_analysis_edges0[x][y])
            network_analysis_edges_agg_performance[x][y] = aggregation_f(network_analysis_edges0[x][y])

    nodes = set(x[0] for x in network_analysis_edges).union(set(x[1] for x in network_analysis_edges))
    nodes_in_degree = {x: 0 for x in nodes}
    nodes_out_degree = {x: 0 for x in nodes}
    for edge in network_analysis_edges:
        for edge_value in network_analysis_edges[edge]:
            if network_analysis_edges[edge][edge_value] >= edge_threshold:
                nodes_in_degree[edge[1]] += network_analysis_edges[edge][edge_value]
                nodes_out_degree[edge[0]] += network_analysis_edges[edge][edge_value]
    nodes_max_degree = {x: max(nodes_in_degree[x], nodes_out_degree[x]) for x in nodes}

    max_node_value = sys.maxsize
    min_node_value = -sys.maxsize

    nodes_dict = {}
    for node in nodes_max_degree:
        if nodes_max_degree[node] >= activity_threshold:
            nodes_dict[node] = str(uuid.uuid4())
            viz.node(nodes_dict[node], node+"\n(in="+str(nodes_in_degree[node])+"; out="+str(nodes_out_degree[node])+")", style="filled", fillcolor=vis_utils.get_trans_freq_color(nodes_max_degree[node], max_node_value, max_node_value))
            count = nodes_max_degree[node]
            if count > max_node_value:
                max_node_value = count
            elif count < min_node_value:
                min_node_value = count

    min_edge_value = sys.maxsize
    max_edge_value = -sys.maxsize

    for edge in network_analysis_edges:
        if edge[0] in nodes_dict and edge[1] in nodes_dict:
            for edge_value in network_analysis_edges[edge]:
                count = network_analysis_edges[edge][edge_value]
                if count > max_edge_value:
                    max_edge_value = count
                elif count < min_edge_value:
                    min_edge_value = count

    for edge in network_analysis_edges:
        if edge[0] in nodes_dict and edge[1] in nodes_dict:
            for edge_value in network_analysis_edges[edge]:
                if network_analysis_edges[edge][edge_value] >= edge_threshold:
                    viz.edge(nodes_dict[edge[0]], nodes_dict[edge[1]], label=edge_value+"\n"+vis_utils.human_readable_stat(network_analysis_edges_agg_performance[edge][edge_value])+"", penwidth=str(vis_utils.get_arc_penwidth(network_analysis_edges[edge][edge_value], min_edge_value, max_edge_value)))

    viz.format = image_format.replace("html", "plain-ext")

    return viz
