'''
PM4Py – A Process Mining Library for Python
Copyright (C) 2026 Process Intelligence Solutions GmbH

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
from collections import Counter
from enum import Enum

from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.objects.petri_net.utils import reduction
from pm4py.objects.petri_net.utils.petri_utils import add_arc_from_to, remove_place
from pm4py.util import exec_utils, nx_utils

_SUPPORTED_NODES = (
    BPMN.Task,
    BPMN.StartEvent,
    BPMN.EndEvent,
    BPMN.IntermediateCatchEvent,
    BPMN.IntermediateThrowEvent,
    BPMN.ExclusiveGateway,
    BPMN.ParallelGateway,
    BPMN.InclusiveGateway,
)


class Parameters(Enum):
    USE_ID = "use_id"
    ENABLE_REDUCTION = "enable_reduction"
    RETURN_FLOW_TRANS_MAP = "return_flow_trans_map"


def build_digraph_from_petri_net(net):
    """
    Builds a directed graph from a Petri net
        (for the purpose to add invisibles between inclusive gateways)

    Parameters
    -------------
    net
        Petri net

    Returns
    -------------
    digraph
        Digraph
    """
    graph = nx_utils.DiGraph()
    for place in net.places:
        graph.add_node(place.name)
    for trans in net.transitions:
        in_places = [x.source for x in list(trans.in_arcs)]
        out_places = [x.target for x in list(trans.out_arcs)]
        for pl1 in in_places:
            for pl2 in out_places:
                graph.add_edge(pl1.name, pl2.name)
    return graph


def apply(bpmn_graph, parameters=None):
    """
    Converts a BPMN graph to an accepting Petri net.

    Intermediate events are represented by silent transitions unless USE_ID
    is enabled. Sequence flows connected to unsupported nodes raise ValueError.

    Parameters
    ----------
    bpmn_graph
        BPMN graph
    parameters
        Parameters of the algorithm:

        - Parameters.USE_ID => (default: False) uses the IDs of the objects instead of their labels in the conversion
        - Parameters.ENABLE_REDUCTION => reduces the invisible transitions
        - Parameters.RETURN_FLOW_TRANS_MAP => returns additional information on the conversion: (iv) the places of the obtained Petri net that are corresponding to each BPMN flow. (v) the transitions of the Petri net related to the nodes of the BPMN diagram.

    Returns
    -----------------
    net
        Petri net
    im
        Initial marking
    fm
        Final marking

    """
    if parameters is None:
        parameters = {}

    use_id = exec_utils.get_param_value(Parameters.USE_ID, parameters, False)
    return_flow_trans_map = exec_utils.get_param_value(
        Parameters.RETURN_FLOW_TRANS_MAP, parameters, False
    )
    enable_reduction = exec_utils.get_param_value(
        Parameters.ENABLE_REDUCTION, parameters, True
    )

    if return_flow_trans_map:
        enable_reduction = False

    net = PetriNet("")
    source_place = PetriNet.Place("source")
    net.places.add(source_place)
    sink_place = PetriNet.Place("sink")
    net.places.add(sink_place)
    im = Marking()
    fm = Marking()
    im[source_place] = 1
    fm[sink_place] = 1

    # keep this correspondence for adding invisible transitions for OR-gateways
    inclusive_gateway_exit = set()
    inclusive_gateway_entry = set()

    flow_place = {}
    source_count = Counter()
    target_count = Counter()
    nodes = bpmn_graph.get_nodes()
    for flow in bpmn_graph.get_flows():
        if isinstance(flow, BPMN.SequenceFlow):
            source = flow.get_source()
            target = flow.get_target()
            for node in (source, target):
                if node not in nodes or not isinstance(node, _SUPPORTED_NODES):
                    raise ValueError(
                        f"Cannot convert BPMN sequence flow {flow.get_id()!r}: "
                        f"endpoint {node.get_id()!r} ({type(node).__name__}) "
                        "is missing from the graph or unsupported by the Petri net converter"
                    )
            place = PetriNet.Place(str(flow.get_id()))
            net.places.add(place)
            flow_place[flow] = place
            source_count[source] += 1
            target_count[target] += 1

    for flow, place in flow_place.items():
        source = flow.get_source()
        target = flow.get_target()
        if isinstance(source, BPMN.InclusiveGateway) and source_count[source] > 1:
            inclusive_gateway_exit.add(place.name)
        elif isinstance(target, BPMN.InclusiveGateway) and target_count[target] > 1:
            inclusive_gateway_entry.add(place.name)

    # remove possible places that are both in inclusive_gateway_exit and inclusive_gateway_entry,
    # because we do not need to add invisibles in this situation
    incl_gat_set_inters = inclusive_gateway_entry.intersection(
        inclusive_gateway_exit
    )
    inclusive_gateway_exit = inclusive_gateway_exit.difference(
        incl_gat_set_inters
    )
    inclusive_gateway_entry = inclusive_gateway_entry.difference(
        incl_gat_set_inters
    )

    nodes_entering = {}
    nodes_exiting = {}
    trans_map = {}

    for node in nodes:
        if isinstance(node, _SUPPORTED_NODES):
            entry_place = PetriNet.Place("ent_" + str(node.get_id()))
            net.places.add(entry_place)
            exiting_place = PetriNet.Place("exi_" + str(node.get_id()))
            net.places.add(exiting_place)
            if use_id:
                label = str(node.get_id())
            else:
                label = (
                    str(node.get_name())
                    if isinstance(node, BPMN.Task)
                    else None
                )
                if not label:
                    label = None
            transition = PetriNet.Transition(
                name=str(node.get_id()), label=label
            )
            net.transitions.add(transition)
            trans_map[node] = [transition]
            add_arc_from_to(entry_place, transition, net)
            add_arc_from_to(transition, exiting_place, net)

            if isinstance(node, (BPMN.ParallelGateway, BPMN.InclusiveGateway)):
                if source_count[node] > 1:
                    exiting_object = PetriNet.Transition(
                        str(uuid.uuid4()), None
                    )
                    net.transitions.add(exiting_object)
                    add_arc_from_to(exiting_place, exiting_object, net)
                    trans_map[node].append(exiting_object)
                else:
                    exiting_object = exiting_place

                if target_count[node] > 1:
                    entering_object = PetriNet.Transition(
                        str(uuid.uuid4()), None
                    )
                    net.transitions.add(entering_object)
                    add_arc_from_to(entering_object, entry_place, net)
                    trans_map[node].append(entering_object)
                else:
                    entering_object = entry_place
                nodes_entering[node] = entering_object
                nodes_exiting[node] = exiting_object
            else:
                nodes_entering[node] = entry_place
                nodes_exiting[node] = exiting_place

            if isinstance(node, BPMN.StartEvent):
                start_transition = PetriNet.Transition(str(uuid.uuid4()), None)
                net.transitions.add(start_transition)
                add_arc_from_to(source_place, start_transition, net)
                add_arc_from_to(start_transition, entry_place, net)
                trans_map[node].append(start_transition)
            elif isinstance(node, BPMN.EndEvent):
                end_transition = PetriNet.Transition(str(uuid.uuid4()), None)
                net.transitions.add(end_transition)
                add_arc_from_to(exiting_place, end_transition, net)
                add_arc_from_to(end_transition, sink_place, net)
                trans_map[node].append(end_transition)

    for flow, place in flow_place.items():
        source_object = nodes_exiting[flow.get_source()]
        target_object = nodes_entering[flow.get_target()]

        if isinstance(source_object, PetriNet.Place):
            inv1 = PetriNet.Transition(f"sfl_{flow.get_id()}", None)
            net.transitions.add(inv1)
            add_arc_from_to(source_object, inv1, net)
            source_object = inv1
            trans_map[flow.source].append(inv1)

        if isinstance(target_object, PetriNet.Place):
            inv2 = PetriNet.Transition(f"tfl_{flow.get_id()}", None)
            net.transitions.add(inv2)
            add_arc_from_to(inv2, target_object, net)
            target_object = inv2
            trans_map[flow.target].append(inv2)

        add_arc_from_to(source_object, place, net)
        add_arc_from_to(place, target_object, net)

    if inclusive_gateway_exit and inclusive_gateway_entry:
        # do the following steps if there are inclusive gateways:
        # - calculate the shortest paths
        # - add an invisible transition between couples of corresponding places
        # this ensures soundness and the correct translation of the BPMN
        inv_places = {x.name: x for x in net.places}
        digraph = build_digraph_from_petri_net(net)
        all_shortest_paths = dict(nx_utils.all_pairs_dijkstra(digraph))
        keys = list(all_shortest_paths.keys())

        for pl1 in inclusive_gateway_exit:
            if pl1 in keys:
                output_places = sorted(
                    [
                        (x, len(y))
                        for x, y in all_shortest_paths[pl1][1].items()
                        if x in inclusive_gateway_entry
                    ],
                    key=lambda x: x[1],
                )
                if output_places:
                    inv_trans = PetriNet.Transition(str(uuid.uuid4()), None)
                    net.transitions.add(inv_trans)
                    add_arc_from_to(inv_places[pl1], inv_trans, net)
                    add_arc_from_to(
                        inv_trans, inv_places[output_places[0][0]], net
                    )

    if enable_reduction:
        reduction.apply_simple_reduction(net)

    for place in list(net.places):
        if (
            len(place.in_arcs) == 0
            and len(place.out_arcs) == 0
            and place not in im
            and place not in fm
        ):
            remove_place(net, place)

    if return_flow_trans_map:
        return net, im, fm, flow_place, trans_map

    return net, im, fm
