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
from typing import Optional, Dict, Any
from graphviz import Digraph
from enum import Enum
from pm4py.util import exec_utils, constants
import tempfile
from uuid import uuid4
from pm4py.util import vis_utils


class Parameters(Enum):
    FORMAT = "format"
    BGCOLOR = "bgcolor"
    RANKDIR = "rankdir"
    ACT_METRIC = "act_metric"
    EDGE_METRIC = "edge_metric"
    ACT_THRESHOLD = "act_threshold"
    EDGE_THRESHOLD = "edge_threshold"
    ANNOTATION = "annotation"
    PERFORMANCE_AGGREGATION_MEASURE = "aggregationMeasure"
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


def add_activity(G: Digraph, act, freq, act_prefix, nodes, annotation, min_freq, max_freq):
    """
    Adds an activity node to the graph
    """
    act_uuid = str(uuid4())
    nodes[act] = act_uuid
    fillcolor = vis_utils.get_trans_freq_color(freq, min_freq, max_freq)
    if annotation == "frequency":
        G.node(act_uuid, label=act + "\n" + act_prefix + str(freq), shape="box", style="filled", fillcolor=fillcolor)
    else:
        G.node(act_uuid, label=act, shape="box")


def add_frequency_edge(G: Digraph, ot, act1, act2, freq, edge_prefix, nodes, min_freq, max_freq):
    """
    Adds a edge (frequency annotation)
    """
    otc = ot_to_color(ot)
    act_uuid1 = nodes[act1]
    act_uuid2 = nodes[act2]
    penwidth = vis_utils.get_arc_penwidth(freq, min_freq, max_freq)
    G.edge(act_uuid1, act_uuid2, label=ot + " " + edge_prefix + str(freq), fontsize="8", penwidth=str(penwidth),
           color=otc, fontcolor=otc)


def add_performance_edge(G: Digraph, ot, act1, act2, perf, edge_prefix, nodes, aggregation_measure):
    """
    Adds an edge (performance annotation)
    """
    from statistics import mean, median

    otc = ot_to_color(ot)
    if aggregation_measure == "median":
        perf = median(perf)
    elif aggregation_measure == "min":
        perf = min(perf)
    elif aggregation_measure == "max":
        perf = max(perf)
    elif aggregation_measure == "sum":
        perf = sum(perf)
    else:
        perf = mean(perf)
    act_uuid1 = nodes[act1]
    act_uuid2 = nodes[act2]
    G.edge(act_uuid1, act_uuid2, label=ot + " " + edge_prefix + vis_utils.human_readable_stat(perf), fontsize="8",
           color=otc, fontcolor=otc)


def add_start_node(G: Digraph, ot, act, freq, edge_prefix, nodes, annotation, min_freq, max_freq):
    """
    Adds a start node to the graph
    """
    otc = ot_to_color(ot)
    act_uuid = nodes[act]
    start_ot = "start_node@#@#" + ot
    if start_ot not in nodes:
        endpoint_uuid = str(uuid4())
        nodes[start_ot] = endpoint_uuid
        G.node(endpoint_uuid, label=ot, shape="ellipse", style="filled", fillcolor=otc)
    start_ot_uuid = nodes[start_ot]
    edge_label = ""
    if annotation == "frequency":
        edge_label = ot + " " + edge_prefix + str(freq)
    penwidth = vis_utils.get_arc_penwidth(freq, min_freq, max_freq)
    G.edge(start_ot_uuid, act_uuid, label=edge_label, fontsize="8", penwidth=str(penwidth), fontcolor=otc, color=otc)


def add_end_node(G: Digraph, ot, act, freq, edge_prefix, nodes, annotation, min_freq, max_freq):
    """
    Adds an end node to the graph
    """
    otc = ot_to_color(ot)
    act_uuid = nodes[act]
    end_ot = "end_node@#@#" + ot
    if end_ot not in nodes:
        endpoint_uuid = str(uuid4())
        nodes[end_ot] = endpoint_uuid
        G.node(endpoint_uuid, label=ot, shape="underline", fontcolor=otc)
    end_ot_uuid = nodes[end_ot]
    edge_label = ""
    if annotation == "frequency":
        edge_label = ot + " " + edge_prefix + str(freq)
    penwidth = vis_utils.get_arc_penwidth(freq, min_freq, max_freq)
    G.edge(act_uuid, end_ot_uuid, label=edge_label, fontsize="8", penwidth=str(penwidth), fontcolor=otc, color=otc)


def apply(ocdfg: Dict[str, Any], parameters: Optional[Dict[Any, Any]] = None) -> Digraph:
    """
    Visualizes an OC-DFG as a Graphviz di-graph

    Parameters
    ---------------
    ocdfg
        OC-DFG
    parameters
        Parameters of the algorithm:
        - Parameters.FORMAT => the format of the output visualization (default: "png")
        - Parameters.BGCOLOR => the default background color (default: "bgcolor")
        - Parameters.RANKDIR => direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
        - Parameters.ACT_METRIC => the metric to use for the activities. Available values:
            - "events" => number of events (default)
            - "unique_objects" => number of unique objects
            - "total_objects" => number of total objects
        - Parameters.EDGE_METRIC => the metric to use for the edges. Available values:
            - "event_couples" => number of event couples (default)
            - "unique_objects" => number of unique objects
            - "total_objects" => number of total objects
        - Parameters.ACT_THRESHOLD => the threshold to apply on the activities frequency (default: 0). Only activities
        having a frequency >= than this are kept in the graph.
        - Parameters.EDGE_THRESHOLD => the threshold to apply on the edges frequency (default 0). Only edges
        having a frequency >= than this are kept in the graph.
        - Parameters.ANNOTATION => the annotation to use for the visualization. Values:
            - "frequency": frequency annotation
            - "performance": performance annotation
        - Parameters.PERFORMANCE_AGGREGATION_MEASURE => the aggregation measure to use for the performance:
            - mean
            - median
            - min
            - max
            - sum

    Returns
    ---------------
    viz
        Graphviz DiGraph
    """
    if parameters is None:
        parameters = {}

    from statistics import mean, median

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ)
    act_metric = exec_utils.get_param_value(Parameters.ACT_METRIC, parameters, "events")
    edge_metric = exec_utils.get_param_value(Parameters.EDGE_METRIC, parameters, "event_couples")
    act_threshold = exec_utils.get_param_value(Parameters.ACT_THRESHOLD, parameters, 0)
    edge_threshold = exec_utils.get_param_value(Parameters.EDGE_THRESHOLD, parameters, 0)
    annotation = exec_utils.get_param_value(Parameters.ANNOTATION, parameters, "frequency")
    performance_aggregation_measure = exec_utils.get_param_value(Parameters.PERFORMANCE_AGGREGATION_MEASURE, parameters,
                                                                 "mean")
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Object-Centric DFG")

    act_count = {}
    act_ot_count = {}
    sa_count = {}
    ea_count = {}
    act_prefix = ""
    edges_count = {}
    edges_performance = {}
    edge_prefix = ""

    if act_metric == "events":
        act_count = ocdfg["activities_indep"]["events"]
        act_ot_count = ocdfg["activities_ot"]["events"]
        sa_count = ocdfg["start_activities"]["events"]
        ea_count = ocdfg["end_activities"]["events"]
        act_prefix = "E="
    elif act_metric == "unique_objects":
        act_count = ocdfg["activities_indep"]["unique_objects"]
        act_ot_count = ocdfg["activities_ot"]["unique_objects"]
        sa_count = ocdfg["start_activities"]["unique_objects"]
        ea_count = ocdfg["end_activities"]["unique_objects"]
        act_prefix = "UO="
    elif act_metric == "total_objects":
        act_count = ocdfg["activities_indep"]["total_objects"]
        act_ot_count = ocdfg["activities_ot"]["total_objects"]
        sa_count = ocdfg["start_activities"]["total_objects"]
        ea_count = ocdfg["end_activities"]["total_objects"]
        act_prefix = "TO="

    if edge_metric == "event_couples":
        edges_count = ocdfg["edges"]["event_couples"]
        edges_performance = ocdfg["edges_performance"]["event_couples"]
        edge_prefix = "EC="
    elif edge_metric == "unique_objects":
        edges_count = ocdfg["edges"]["unique_objects"]
        edge_prefix = "UO="
    elif edge_metric == "total_objects":
        edges_count = ocdfg["edges"]["total_objects"]
        edges_performance = ocdfg["edges_performance"]["total_objects"]
        edge_prefix = "TO="

    if annotation == "performance" and edge_metric == "unique_objects":
        raise Exception("unsupported performance visualization for unique objects!")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph("ocdfg", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    viz.attr('node', shape='ellipse', fixedsize='false')

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>', labelloc="top")

    min_edges_count = {}
    max_edges_count = {}

    for ot in edges_count:
        all_edges_count = [len(y) for y in edges_count[ot].values()]
        min_edges_count[ot] = min(all_edges_count)
        max_edges_count[ot] = max(all_edges_count)
        all_sa_count = [len(y) for y in sa_count[ot].values()]
        min_edges_count[ot] = min(min(all_sa_count), min_edges_count[ot])
        max_edges_count[ot] = max(max(all_sa_count), max_edges_count[ot])
        all_ea_count = [len(y) for y in ea_count[ot].values()]
        min_edges_count[ot] = min(min(all_ea_count), min_edges_count[ot])
        max_edges_count[ot] = max(max(all_ea_count), max_edges_count[ot])

    act_count_values = [len(y) for y in act_count.values()]
    min_act_count = min(act_count_values)
    max_act_count = max(act_count_values)

    nodes = {}
    for act in act_count:
        if len(act_count[act]) >= act_threshold:
            add_activity(viz, act, len(act_count[act]), act_prefix, nodes, annotation, min_act_count, max_act_count)

    for ot in edges_count:
        for act_cou in edges_count[ot]:
            if act_cou[0] in nodes and act_cou[1] in nodes:
                if len(edges_count[ot][act_cou]) >= edge_threshold:
                    if annotation == "frequency":
                        add_frequency_edge(viz, ot, act_cou[0], act_cou[1], len(edges_count[ot][act_cou]), edge_prefix,
                                           nodes, min_edges_count[ot], max_edges_count[ot])
                    elif annotation == "performance":
                        add_performance_edge(viz, ot, act_cou[0], act_cou[1], edges_performance[ot][act_cou],
                                             edge_prefix, nodes, performance_aggregation_measure)

    for ot in sa_count:
        for act in sa_count[ot]:
            if act in nodes:
                if len(sa_count[ot][act]) >= edge_threshold:
                    miec = min_edges_count[ot] if ot in min_edges_count else len(sa_count[ot][act])
                    maec = max_edges_count[ot] if ot in max_edges_count else len(sa_count[ot][act])
                    add_start_node(viz, ot, act, len(sa_count[ot][act]), edge_prefix, nodes, annotation,
                                   miec, maec)

    for ot in ea_count:
        for act in ea_count[ot]:
            if act in nodes:
                if len(ea_count[ot][act]) >= edge_threshold:
                    miec = min_edges_count[ot] if ot in min_edges_count else len(ea_count[ot][act])
                    maec = max_edges_count[ot] if ot in max_edges_count else len(ea_count[ot][act])
                    add_end_node(viz, ot, act, len(ea_count[ot][act]), edge_prefix, nodes, annotation,
                                 miec, maec)

    viz.attr(rankdir=rankdir)
    viz.format = image_format.replace("html", "plain-ext")

    return viz
