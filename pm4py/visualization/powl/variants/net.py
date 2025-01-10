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
import importlib.resources
import os

from pm4py.objects.powl.obj import POWL
from enum import Enum
import tempfile
import graphviz
from typing import Optional, Dict, Any
from graphviz import Digraph
from pm4py.util import constants, exec_utils
from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.bpmn.util.sorting import get_sorted_nodes_edges
from pm4py.objects.conversion.powl.converter import apply as powl_to_pn
from pm4py.objects.bpmn.util import reduction


class Parameters(Enum):
    FORMAT = "format"
    RANKDIR = "rankdir"
    BGCOLOR = "bgcolor"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


FREQUENCY_TAG_IMAGES = True
min_width = "1.5"  # Set the minimum width in inches
min_height = "0.5"
node_color = "#f2f2f2"
silent_node_color = "black"


class SplitExclusiveGateway(BPMN.ExclusiveGateway):
    pass


class JoinExclusiveGateway(BPMN.ExclusiveGateway):
    pass


def can_connect_without_xor_violation(input_nodes, output_nodes):
    for in_node in input_nodes:
        for out_node in output_nodes:
            if isinstance(in_node, BPMN.ExclusiveGateway) and len(output_nodes) > 1:
                return False
            if isinstance(out_node, BPMN.ExclusiveGateway) and len(input_nodes) > 1:
                return False

    return True


def simplify_and_gateways(nodes, edges):
    for n in nodes:
        if isinstance(n, BPMN.ParallelGateway):
            input_nodes = [edge[0] for edge in edges if edge[1] == n]
            output_nodes = [edge[1] for edge in edges if edge[0] == n]
            if can_connect_without_xor_violation(input_nodes, output_nodes):
                nodes.remove(n)
                edges = [edge for edge in edges if n not in edge]

                for in_node in input_nodes:
                    for out_node in output_nodes:
                        edges.append((in_node, out_node))
                return simplify_and_gateways(nodes, edges)

    return nodes, edges


def add_node(n, viz):
    n_id = str(id(n))
    if isinstance(n, FrequencyTask):
        font_size = '18'
        if FREQUENCY_TAG_IMAGES:
            if n.skippable:
                if n.selfloop:
                    with importlib.resources.path("pm4py.visualization.powl.variants.icons",
                                                  "skip-loop-tag.svg") as gimg:
                        image = str(gimg)
                        viz.node(n_id, label='\n' + n.activity, imagepos='tr',
                                 image=image, style='filled', fillcolor=node_color,
                                 shape='box', width=min_width, fontsize=font_size)
                else:
                    with importlib.resources.path("pm4py.visualization.powl.variants.icons",
                                                  "skip-tag.svg") as gimg:
                        skip_image = str(gimg)
                        viz.node(n_id, label="\n" + n.activity, imagepos='tr',
                                 image=skip_image, style='filled', fillcolor=node_color,
                                 shape='box', width=min_width, fontsize=font_size)
            else:
                if n.selfloop:
                    with importlib.resources.path("pm4py.visualization.powl.variants.icons",
                                                  "loop-tag.svg") as gimg:
                        loop_image = str(gimg)
                        viz.node(n_id, label="\n" + n.activity, imagepos='tr',
                                 image=loop_image, style='filled', fillcolor=node_color,
                                 shape='box', width=min_width, fontsize=font_size)
                else:
                    viz.node(n_id, label=n.activity, style='filled', fillcolor=node_color,
                             shape='box', width=min_width, fontsize=font_size)
        else:
            if n.skippable:
                viz.node(n_id, shape="box", label=n.activity, fontsize=font_size,
                         style="dashed", width=min_width)
            else:
                viz.node(n_id, shape="box", label=n.activity, fontsize=font_size,
                         width=min_width)
            if n.selfloop:
                viz.edge(n_id, n_id)

    elif isinstance(n, BPMN.StartEvent):
        with importlib.resources.path("pm4py.visualization.powl.variants.icons", "play.svg") as gimg:
            start_image = str(gimg)
            viz.node(n_id, image=start_image, label="", shape="none", width='0.35',
                     height='0.35', fixedsize="true", style='filled', fillcolor=node_color)
    elif isinstance(n, BPMN.EndEvent):
        with importlib.resources.path("pm4py.visualization.powl.variants.icons", "end.svg") as gimg:
            end_image = str(gimg)
            viz.node(n_id, image=end_image, label="", shape="none", width='0.35',
                     height='0.35', fixedsize="true", style='filled', fillcolor=node_color)
    elif isinstance(n, BPMN.ParallelGateway):
        viz.node(n_id, label="", shape="square", style="filled", fillcolor=silent_node_color, width='0.3',
                 height='0.3')
    elif isinstance(n, SplitExclusiveGateway):
        with importlib.resources.path("pm4py.visualization.powl.variants.icons", "gate.svg") as gimg:
            xor_image = str(gimg)
            viz.node(n_id, label="", shape="diamond", style="filled", fillcolor="lightgreen",
                     width='0.4', height='0.4', fixedsize="true", image=xor_image)
    elif isinstance(n, JoinExclusiveGateway):
        with importlib.resources.path("pm4py.visualization.powl.variants.icons", "gate.svg") as gimg:
            xor_image = str(gimg)
            viz.node(n_id, label="", shape="diamond", style="filled", fillcolor="orange",
                     width='0.4', height='0.4', fixedsize="true", image=xor_image)
    elif isinstance(n, BPMN.ExclusiveGateway):
        with importlib.resources.path("pm4py.visualization.powl.variants.icons", "gate.svg") as gimg:
            xor_image = str(gimg)
        viz.node(n_id, label="", shape="diamond", style="filled", fillcolor=node_color,
                 width='0.4', height='0.4', fixedsize="true", image=xor_image)
    else:
        raise Exception("Unexpected instance of class " + str(type(n)) + "!")


def apply(powl: POWL, parameters: Optional[Dict[Any, Any]] = None) -> graphviz.Digraph:
    if parameters is None:
        parameters = {}

    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "POWL Model")

    pn_2, init_2, final_2 = powl_to_pn(powl)
    bpmn_graph = to_bpmn(pn_2, init_2, final_2)

    nodes, edges = get_sorted_nodes_edges(bpmn_graph)

    for node in nodes:

        if isinstance(node, BPMN.ExclusiveGateway):

            incoming_edges = [e[0] for e in edges if e[1] is node]
            outgoing_edges = [e[1] for e in edges if e[0] is node]

            if len(incoming_edges) == 1 and len(outgoing_edges) > 1:

                node.__class__ = SplitExclusiveGateway

            elif len(incoming_edges) > 1 and len(outgoing_edges) == 1:

                node.__class__ = JoinExclusiveGateway

    nodes, edges = simplify_and_gateways(nodes, edges)

    rankdir = "LR"
    bgcolor = constants.DEFAULT_BGCOLOR

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    viz.graph_attr['rankdir'] = rankdir

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>', labelloc="top")

    gateway_edges = {}

    for e in edges:
        if isinstance(e[0], BPMN.ParallelGateway) or isinstance(e[0], BPMN.ParallelGateway):
            if e[0] not in gateway_edges:
                gateway_edges[e[0]] = {'in': [], 'out': []}
            gateway_edges[e[0]]['out'].append(e[1])
            continue
        if isinstance(e[1], BPMN.ParallelGateway) or isinstance(e[1], BPMN.ParallelGateway):
            if e[1] not in gateway_edges:
                gateway_edges[e[1]] = {'in': [], 'out': []}
            gateway_edges[e[1]]['in'].append(e[0])
            continue

    for node in nodes:
        add_node(node, viz)
    add_concurrent_subgraphs(viz, find_concurrent_groups(nodes, edges))

    for e in edges:
        n_id_1 = str(id(e[0]))
        n_id_2 = str(id(e[1]))

        viz.edge(n_id_1, n_id_2)

    viz.attr(overlap='false')

    viz.format = "svg"

    return viz


class FrequencyTask(BPMN.Task):
    def __init__(self, name, properties, id="", in_arcs=None, out_arcs=None, process=None):
        super().__init__(id=id, name=name, in_arcs=in_arcs, out_arcs=out_arcs, process=process)
        self.activity = properties["activity"]
        self.skippable = properties["skippable"]
        self.selfloop = properties["selfloop"]
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.image = os.path.join(script_dir, "xor2.png")


def to_bpmn(net, im, fm):
    """
    Converts an accepting Petri net into a BPMN diagram

    Parameters
    --------------
    net
        Petri net
    im
        initial marking
    fm
        final marking

    Returns
    --------------
    bpmn_graph
        BPMN diagram
    """

    bpmn_graph = BPMN()

    entering_dictio = {}
    exiting_dictio = {}

    for place in net.places:
        node = BPMN.ExclusiveGateway()
        bpmn_graph.add_node(node)
        entering_dictio[place] = node
        exiting_dictio[place] = node

    for trans in net.transitions:
        if trans.label is None:
            if len(trans.in_arcs) > 1:
                node = BPMN.ParallelGateway(gateway_direction=BPMN.Gateway.Direction.CONVERGING)
            elif len(trans.out_arcs) > 1:
                node = BPMN.ParallelGateway(gateway_direction=BPMN.Gateway.Direction.DIVERGING)
            else:
                node = BPMN.ExclusiveGateway(gateway_direction=BPMN.Gateway.Direction.UNSPECIFIED)
            bpmn_graph.add_node(node)
            entering_dictio[trans] = node
            exiting_dictio[trans] = node
        else:
            if len(trans.in_arcs) > 1:
                entering_node = BPMN.ParallelGateway(gateway_direction=BPMN.Gateway.Direction.CONVERGING)
            else:
                entering_node = BPMN.ExclusiveGateway(gateway_direction=BPMN.Gateway.Direction.UNSPECIFIED)

            if len(trans.out_arcs) > 1:
                exiting_node = BPMN.ParallelGateway(gateway_direction=BPMN.Gateway.Direction.DIVERGING)
            else:
                exiting_node = BPMN.ExclusiveGateway(gateway_direction=BPMN.Gateway.Direction.UNSPECIFIED)

            task = FrequencyTask(name=trans.label, properties=trans.properties)
            bpmn_graph.add_node(task)

            bpmn_graph.add_flow(BPMN.SequenceFlow(entering_node, task))
            bpmn_graph.add_flow(BPMN.SequenceFlow(task, exiting_node))

            entering_dictio[trans] = entering_node
            exiting_dictio[trans] = exiting_node

    for arc in net.arcs:
        bpmn_graph.add_flow(BPMN.SequenceFlow(exiting_dictio[arc.source], entering_dictio[arc.target]))

    start_node = BPMN.StartEvent(name="start", isInterrupting=True)
    end_node = BPMN.NormalEndEvent(name="end")
    bpmn_graph.add_node(start_node)
    bpmn_graph.add_node(end_node)
    for place in im:
        bpmn_graph.add_flow(BPMN.SequenceFlow(start_node, entering_dictio[place]))
    for place in fm:
        bpmn_graph.add_flow(BPMN.SequenceFlow(exiting_dictio[place], end_node))

    bpmn_graph = reduction.apply(bpmn_graph)

    for node in bpmn_graph.get_nodes():
        node.set_process(bpmn_graph.get_process_id())

    for edge in bpmn_graph.get_flows():
        edge.set_process(bpmn_graph.get_process_id())

    return bpmn_graph


def find_concurrent_groups(nodes, edges):
    predecessors = {n: [] for n in nodes}
    successors = {n: [] for n in nodes}
    for src, dst in edges:
        successors[src].append(dst)
        predecessors[dst].append(src)

    groups = {}
    for node, preds in predecessors.items():
        if len(preds) == 1:
            pred_id = str(id(preds[0]))
            if pred_id not in groups:
                groups[pred_id] = []
            groups[pred_id].append(node)

    return [group for group in groups.values() if len(group) > 1]


def add_concurrent_subgraphs(graph, concurrent_elements):
    for group in concurrent_elements:
        with graph.subgraph() as s:
            s.attr(rank='same')
            for n in group:
                s.node(str(id(n)))
