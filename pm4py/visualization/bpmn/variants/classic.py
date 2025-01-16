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
from pm4py.util import exec_utils
from enum import Enum
import tempfile
from graphviz import Digraph
from typing import Optional, Dict, Any
from pm4py.objects.bpmn.obj import BPMN
from pm4py.visualization.common import gview
from pm4py.visualization.common import save as gsave
from pm4py.util import constants
import graphviz


class Parameters(Enum):
    FORMAT = "format"
    RANKDIR = "rankdir"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    ENABLE_SWIMLANES = "enable_swimlanes"
    INCLUDE_NAME_IN_EVENTS = "include_name_in_events"
    SWIMLANES_MARGIN = "swimlanes_margin"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"
    ENDPOINTS_SHAPE = "endpoints_shape"


def add_bpmn_node(graph, n, font_size, include_name_in_events, endpoints_shape):
    n_id = str(id(n))
    node_label = str(n.name) if include_name_in_events else ""

    if isinstance(n, BPMN.Task):
        graph.node(n_id, shape="box", label=n.get_name(), fontsize=font_size)
    elif isinstance(n, BPMN.StartEvent):
        graph.node(n_id, label="", shape=endpoints_shape, style="filled", fillcolor="green", fontsize=font_size)
    elif isinstance(n, BPMN.EndEvent):
        graph.node(n_id, label="", shape=endpoints_shape, style="filled", fillcolor="orange", fontsize=font_size)
    elif isinstance(n, BPMN.Event):
        graph.node(n_id, label=node_label, shape="underline", fontsize=font_size)
    elif isinstance(n, BPMN.TextAnnotation):
        graph.node(n_id, shape="box", label=n.text, fontsize=font_size)
    elif isinstance(n, BPMN.ParallelGateway):
        graph.node(n_id, label="+", shape="diamond", fontsize=font_size)
    elif isinstance(n, BPMN.ExclusiveGateway):
        graph.node(n_id, label="X", shape="diamond", fontsize=font_size)
    elif isinstance(n, BPMN.EventBasedGateway):
        graph.node(n_id, label="E", shape="diamond", fontsize=font_size)
    elif isinstance(n, BPMN.InclusiveGateway):
        graph.node(n_id, label="O", shape="diamond", fontsize=font_size)
    else:
        # do nothing here
        return False

    return True


def apply(bpmn_graph: BPMN, parameters: Optional[Dict[Any, Any]] = None) -> graphviz.Digraph:
    """
    Visualize a BPMN graph

    Parameters
    -------------
    bpmn_graph
        BPMN graph
    parameters
        Parameters of the visualization, including:
         - Parameters.FORMAT: the format of the visualization
         - Parameters.RANKDIR: the direction of the representation (default: LR)

    Returns
    ------------
    gviz
        Graphviz representation
    """
    if parameters is None:
        parameters = {}

    from pm4py.objects.bpmn.obj import BPMN
    from pm4py.objects.bpmn.util.sorting import get_sorted_nodes_edges

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ)
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 12)
    font_size = str(font_size)
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    enable_swimlanes = exec_utils.get_param_value(Parameters.ENABLE_SWIMLANES, parameters, True)
    include_name_in_events = exec_utils.get_param_value(Parameters.INCLUDE_NAME_IN_EVENTS, parameters, True)
    swimlanes_margin = exec_utils.get_param_value(Parameters.SWIMLANES_MARGIN, parameters, 35)
    swimlanes_margin = str(swimlanes_margin)
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "BPMN Diagram")
    endpoints_shape = exec_utils.get_param_value(Parameters.ENDPOINTS_SHAPE, parameters, "circle")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    viz.graph_attr['rankdir'] = rankdir

    nodes, edges = get_sorted_nodes_edges(bpmn_graph)
    process_ids = []
    for n in nodes:
        if n.process not in process_ids:
            process_ids.append(n.process)
    process_ids_members = {n.process: list() for n in nodes}
    for n in nodes:
        process_ids_members[n.process].append(n)
    participant_nodes = [n for n in nodes if isinstance(n, BPMN.Participant)]
    pref_pname = {x.process_ref: x.name for x in participant_nodes}
    pref_pid = {x.process_ref: str(id(x)) for x in participant_nodes}
    added_nodes = set()

    if len(participant_nodes) < 1 or not enable_swimlanes:
        for n in nodes:
            if add_bpmn_node(viz, n, font_size, include_name_in_events, endpoints_shape):
                added_nodes.add(str(id(n)))
    else:
        # style='invis'
        viz.node('@@anchorStart', style='invis')
        viz.node('@@anchorEnd', style='invis')

        for subp in process_ids:
            this_added_nodes = []
            if subp in pref_pname:
                with viz.subgraph(name="cluster"+pref_pid[subp]) as c:
                    c.attr(label=pref_pname[subp])
                    c.attr(margin=swimlanes_margin)
                    for n in process_ids_members[subp]:
                        if add_bpmn_node(c, n, font_size, include_name_in_events, endpoints_shape):
                            added_nodes.add(str(id(n)))
                            this_added_nodes.append(str(id(n)))
                    #c.attr(rank='same')

                    if this_added_nodes:
                        viz.edge('@@anchorStart', this_added_nodes[0], style='invis')
                        viz.edge(this_added_nodes[-1], '@@anchorEnd', style='invis')

    for e in edges:
        n_id_1 = str(id(e[0]))
        n_id_2 = str(id(e[1]))

        if n_id_1 in added_nodes and n_id_2 in added_nodes:
            viz.edge(n_id_1, n_id_2)

    viz.attr(overlap='false')

    viz.format = image_format.replace("html", "plain-ext")

    return viz


def save(gviz: graphviz.Digraph, output_file_path: str, parameters=None):
    """
    Save the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    output_file_path
        Path where the GraphViz output should be saved
    """
    gsave.save(gviz, output_file_path, parameters=parameters)
    return ""


def view(gviz: graphviz.Digraph, parameters=None):
    """
    View the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    """
    if constants.DEFAULT_ENABLE_VISUALIZATIONS_VIEW:
        return gview.view(gviz, parameters=parameters)


def matplotlib_view(gviz: graphviz.Digraph, parameters=None):
    """
    Views the diagram using Matplotlib

    Parameters
    ---------------
    gviz
        Graphviz
    """
    if constants.DEFAULT_ENABLE_VISUALIZATIONS_VIEW:
        return gview.matplotlib_view(gviz, parameters=parameters)
