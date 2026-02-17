'''
    PM4Py â€“ A Process Mining Library for Python
Copyright (C) 2024 Process Intelligence Solutions UG (haftungsbeschrÃ¤nkt)

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
# ========= Imports =========
from copy import copy
from itertools import combinations
from collections import deque
from typing import Union, Set

from pm4py import PetriNet
from pm4py.objects.petri_net.utils import petri_utils as pn_util
from pm4py.algo.analysis.workflow_net import algorithm as wf_eval
from pm4py.objects.powl.BinaryRelation import BinaryRelation
from pm4py.objects.powl.obj import OperatorPOWL, POWL, Operator, StrictPartialOrder, Transition, SilentTransition

from assignment_utilities.manual_coverage_helper import hit

# ========= Utility Functions =========
def id_generator():
    count = 1
    while True:
        yield f"id{count}"
        count += 1


def is_silent(transition) -> bool:
    return transition.label is None


def add_arc_from_to(source: Union[PetriNet.Place, PetriNet.Transition],
                    target: Union[PetriNet.Transition, PetriNet.Place],
                    net: PetriNet):
    arc = PetriNet.Arc(source, target)
    net.arcs.add(arc)
    source.out_arcs.add(arc)
    target.in_arcs.add(arc)


def clone_place(net: PetriNet, place, node_map: dict):
    cloned_place = PetriNet.Place(f"{place.name}_cloned")
    net.places.add(cloned_place)
    node_map[place] = cloned_place
    return cloned_place


def clone_transition(net: PetriNet, transition, node_map: dict):
    cloned_transition = PetriNet.Transition(f"{transition.name}_cloned", transition.label)
    net.transitions.add(cloned_transition)
    node_map[transition] = cloned_transition
    return cloned_transition


def pn_transition_to_powl(transition: PetriNet.Transition) -> Transition:
    label = transition.label
    if label:
        return Transition(label=label)
    else:
        return SilentTransition()


def locally_identical(p1, p2, transitions):
    pre1 = pn_util.pre_set(p1) & transitions
    pre2 = pn_util.pre_set(p2) & transitions
    post1 = pn_util.post_set(p1) & transitions
    post2 = pn_util.post_set(p2) & transitions
    return pre1 == pre2 and post1 == post2


# ========= Graph & Subnet Functions =========
def get_simplified_reachability_graph(net: PetriNet):
    graph = {node: set() for node in net.transitions}
    for start_node in graph.keys():
        reachable = set()
        queue = deque()
        queue.append(start_node)
        while queue:
            node = queue.popleft()
            if node not in reachable:
                reachable.add(node)
                successors = pn_util.post_set(node)
                queue.extend(successors)
        graph[start_node].update(reachable)
    return graph


def get_reachable_transitions_from_place_to_another(start_place: PetriNet.Place,
                                                    end_place: PetriNet.Place):
    visited = set()
    queue = deque()
    queue.append(start_place)
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            if node == end_place:
                continue
            successors = pn_util.post_set(node)
            queue.extend(successors)
    visited = {node for node in visited if isinstance(node, PetriNet.Transition)}
    return visited


def clone_subnet(net: PetriNet, subnet_transitions: Set[PetriNet.Transition],
                 start_place: PetriNet.Place, end_place: PetriNet.Place):
    subnet_net = PetriNet(f"Subnet_{next(id_generator())}")
    node_map = {}

    # Clone transitions
    for node in subnet_transitions:
        clone_transition(subnet_net, node, node_map)

    # Add arcs and remaining places of the subnet
    for arc in net.arcs:
        source = arc.source
        target = arc.target
        if source in subnet_transitions or target in subnet_transitions:
            if source in node_map:
                cloned_source = node_map[source]
            else:
                cloned_source = clone_place(subnet_net, source, node_map)
            if target in node_map:
                cloned_target = node_map[target]
            else:
                cloned_target = clone_place(subnet_net, target, node_map)
            add_arc_from_to(cloned_source, cloned_target, subnet_net)

    mapped_start_place = node_map[start_place]
    mapped_end_place = node_map[end_place]

    return subnet_net, mapped_start_place, mapped_end_place

# Instrumented Version of apply_partial_order_projection with branch coverage tracking
def apply_partial_order_projection(net: PetriNet, subnet_transitions: Set[PetriNet.Transition],
                                   start_places: Set[PetriNet.Place], end_places: Set[PetriNet.Place]):
    print("apply_partial_order_projection CALLED")
    FN = "apply_partial_order_projection"

    subnet_net = PetriNet(f"Subnet_{next(id_generator())}")
    node_map = {}

    # Clone transitions in the subnet
    for node in subnet_transitions:
        hit(FN, 16)  # cloning a transition in the subnet
        clone_transition(subnet_net, node, node_map)

    list_start_places = list(start_places)
    old_start = list_start_places[0]
    for place in list_start_places[1:]:
        hit(FN, 17)  # comparing start places for uniqueness
        if not locally_identical(place, old_start, subnet_transitions):
            hit(FN, 0)  # start uniqueness violated
            raise Exception("Unique local start property is violated!")
        else:
            hit(FN, 1)  # start uniqueness check passed for an iteration

    new_start_place = clone_place(subnet_net, old_start, node_map)
    node_map[old_start] = new_start_place

    if start_places == end_places:
        hit(FN, 2)  # start_places == end_places
        new_end_place = new_start_place
    else:
        hit(FN, 3)  # start_places != end_places
        list_end_places = list(end_places)
        old_end = list_end_places[0]
        for place in list_end_places[1:]:
            hit(FN, 18)  # comparing end places for uniqueness
            if not locally_identical(place, old_end, subnet_transitions):
                hit(FN, 4)  # end uniqueness violated
                raise Exception("Unique local end property is violated!")
            else:
                hit(FN, 5)  # end uniqueness check passed for an iteration
        new_end_place = clone_place(subnet_net, old_end, node_map)
        node_map[old_end] = new_end_place

    # Add arcs and remaining places of the subnet
    for arc in net.arcs:
        hit(FN, 19)  # iterating over an arc in the original net
        source = arc.source
        target = arc.target

        if source in subnet_transitions or target in subnet_transitions:
            hit(FN, 6)  # arc considered (touches subnet transitions)

            if source in node_map:
                hit(FN, 7)  # source found in node_map
                cloned_source = node_map[source]
            else:
                hit(FN, 8)  # source not in node_map

                if source in start_places or source in end_places:
                    hit(FN, 9)  # source is boundary => continue
                    continue
                else:
                    hit(FN, 10)  # source not boundary => clone

                cloned_source = clone_place(subnet_net, source, node_map)

            if target in node_map:
                hit(FN, 11)  # target found in node_map
                cloned_target = node_map[target]
            else:
                hit(FN, 12)  # target not in node_map

                if target in start_places or target in end_places:
                    hit(FN, 13)  # target is boundary => continue
                    continue
                else:
                    hit(FN, 14)  # target not boundary => clone

                cloned_target = clone_place(subnet_net, target, node_map)

            add_arc_from_to(cloned_source, cloned_target, subnet_net)
        else:
            hit(FN, 15)  # arc ignored (does not touch subnet transitions)

    return subnet_net, new_start_place, new_end_place

# def apply_partial_order_projection(net: PetriNet, subnet_transitions: Set[PetriNet.Transition],
#                                    start_places: Set[PetriNet.Place], end_places: Set[PetriNet.Place]):
#     subnet_net = PetriNet(f"Subnet_{next(id_generator())}")
#     node_map = {}
#
#     # Clone transitions in the subnet
#     for node in subnet_transitions:
#         clone_transition(subnet_net, node, node_map)
#
#     list_start_places = list(start_places)
#     old_start = list_start_places[0]
#     for place in list_start_places[1:]:
#         if not locally_identical(place, old_start, subnet_transitions):
#             raise Exception("Unique local start property is violated!")
#     new_start_place = clone_place(subnet_net, old_start, node_map)
#     node_map[old_start] = new_start_place
#
#     if start_places == end_places:
#         new_end_place = new_start_place
#     else:
#         list_end_places = list(end_places)
#         old_end = list_end_places[0]
#         for place in list_end_places[1:]:
#             if not locally_identical(place, old_end, subnet_transitions):
#                 raise Exception("Unique local end property is violated!")
#         new_end_place = clone_place(subnet_net, old_end, node_map)
#         node_map[old_end] = new_end_place
#
#     # Add arcs and remaining places of the subnet
#     for arc in net.arcs:
#         source = arc.source
#         target = arc.target
#         if source in subnet_transitions or target in subnet_transitions:
#             if source in node_map:
#                 cloned_source = node_map[source]
#             else:
#                 if source in start_places or source in end_places:
#                     continue
#                 cloned_source = clone_place(subnet_net, source, node_map)
#             if target in node_map:
#                 cloned_target = node_map[target]
#             else:
#                 if target in start_places or target in end_places:
#                     continue
#                 cloned_target = clone_place(subnet_net, target, node_map)
#             add_arc_from_to(cloned_source, cloned_target, subnet_net)
#
#     return subnet_net, new_start_place, new_end_place


# ========= Mining Functions =========
def mine_base_case(net: PetriNet):
    if len(net.transitions) == 1 and len(net.places) == 2 == len(net.arcs):
        activity = list(net.transitions)[0]
        powl_transition = pn_transition_to_powl(activity)
        return powl_transition
    return None


def mine_self_loop(net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place):
    if start_place == end_place:
        place = start_place
        place_copy = clone_place(net, place, {})
        redo = copy(net.transitions)
        out_arcs = place.out_arcs
        for arc in list(out_arcs):
            target = arc.target
            pn_util.remove_arc(net, arc)
            add_arc_from_to(place_copy, target, net)
        do_transition = PetriNet.Transition(f"silent_do_{place.name}", None)
        do = {do_transition}
        net.transitions.add(do_transition)
        add_arc_from_to(place, do_transition, net)
        add_arc_from_to(do_transition, place_copy, net)
        return do, redo, place, place_copy

    return None


def mine_loop(net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place):
    redo_subnet_transitions = get_reachable_transitions_from_place_to_another(end_place, start_place)

    if len(redo_subnet_transitions) == 0:
        return None, None

    do_subnet_transitions = get_reachable_transitions_from_place_to_another(start_place, end_place)

    if len(do_subnet_transitions) == 0:
        raise Exception("This should not be possible!")

    if do_subnet_transitions & redo_subnet_transitions:
        # This could happen if we have ->(..., Loop)
        return None, None

    if net.transitions != (do_subnet_transitions | redo_subnet_transitions):
        raise Exception("Something went wrong!")

    # A loop is detected: the set of transitions is partitioned into two disjoint, non-empty subsets (do and redo)
    return do_subnet_transitions, redo_subnet_transitions


def __combine_parts(transitions_to_group_together: set[PetriNet.Transition],
                    partition: list[set[PetriNet.Transition]]):
    new_partition = []
    new_combined_group = set()

    for part in partition:
        if part & transitions_to_group_together:
            new_combined_group.update(part)
        else:
            new_partition.append(part)

    if new_combined_group:
        new_partition.append(new_combined_group)

    return new_partition


def mine_xor(net: PetriNet, reachability_map):
    choice_branches = [{t} for t in net.transitions]

    for t1, t2 in combinations(net.transitions, 2):
        if t1 in reachability_map[t2] or t2 in reachability_map[t1]:
            new_branch = {t1, t2}
            choice_branches = __combine_parts(new_branch, choice_branches)

    if net.transitions != set().union(*choice_branches):
        raise Exception("This should not happen!")

    return choice_branches


def mine_partial_order(net, end_place, reachability_map):
    partition = [{t} for t in net.transitions]

    for place in net.places:
        out_size = len(place.out_arcs)
        if out_size > 1 or (place == end_place and out_size > 0):
            xor_branches = []
            for start_transition in pn_util.post_set(place):
                new_branch = {node for node in reachability_map[start_transition]
                              if isinstance(node, PetriNet.Transition)}
                xor_branches.append(new_branch)
            union_of_branches = set().union(*xor_branches)
            if place == end_place:
                not_in_every_branch = union_of_branches
            else:
                intersection_of_branches = set.intersection(*xor_branches)
                not_in_every_branch = union_of_branches - intersection_of_branches
            if len(not_in_every_branch) > 1:
                partition = __combine_parts(not_in_every_branch, partition)

    return partition


# ========= Preprocessing Functions =========
def validate_workflow_net(net: PetriNet):
    places_no_incoming = [p for p in net.places if not p.in_arcs]
    if len(places_no_incoming) == 1:
        start_place = places_no_incoming[0]
    else:
        raise Exception("Not a WF-net!")

    places_no_outgoing = [p for p in net.places if not p.out_arcs]
    if len(places_no_outgoing) == 1:
        end_place = places_no_outgoing[0]
    else:
        raise Exception("Not a WF-net!")

    if not wf_eval.apply(net):
        raise Exception("Not a WF-net!")

    return start_place, end_place


def remove_initial_and_end_silent_activities(net: PetriNet, start_places: set[PetriNet.Place],
                                             end_places: set[PetriNet.Place]):
    change = True
    while change and len(net.transitions) > 1:
        change = False
        if len(start_places) == 1:
            start_place = list(start_places)[0]
            if len(start_place.in_arcs) == 0 and len(start_place.out_arcs) == 1:
                transition = list(start_place.out_arcs)[0].target
                if len(transition.in_arcs) == 1 and is_silent(transition):
                    pn_util.remove_place(net, start_place)
                    start_places.remove(start_place)
                    next_places = list(pn_util.post_set(transition))
                    pn_util.remove_transition(net, transition)
                    for p in next_places:
                        start_places.add(p)
                    change = True

    change = True
    while change and len(net.transitions) > 1:
        change = False
        if len(end_places) == 1:
            end_place = list(end_places)[0]
            if len(end_place.in_arcs) == 1 and len(end_place.out_arcs) == 0:
                transition = list(end_place.in_arcs)[0].source
                if len(transition.out_arcs) == 1 and is_silent(transition):
                    pn_util.remove_transition(net, transition)
                    pn_util.remove_place(net, end_place)
                    end_places.remove(end_place)
                    prev_places = list(pn_util.pre_set(transition))
                    for p in prev_places:
                        end_places.add(p)
                    change = True

    return start_places, end_places


def __get_identical_place(place: PetriNet.Place, places_set: set[PetriNet.Place]):
    for other in places_set:
        if (pn_util.post_set(place) == pn_util.post_set(other)
                and pn_util.pre_set(place) == pn_util.pre_set(other)):
            return other
    return None


def __remove_and_replace_if_present(old_p: PetriNet.Place, new_p: PetriNet.Place, place_set: set[PetriNet.Place]):
    if old_p in place_set:
        place_set.remove(old_p)
        if new_p not in place_set:
            place_set.add(new_p)
    return place_set


def remove_duplicated_places(net: PetriNet, start_places: set[PetriNet.Place], end_places: set[PetriNet.Place]):
    all_places = list(net.places)
    places_to_keep = {all_places[0]}
    for place in all_places[1:]:
        other = __get_identical_place(place, places_to_keep)
        if other:
            pn_util.remove_place(net, place)
            start_places = __remove_and_replace_if_present(place, other, start_places)
            end_places = __remove_and_replace_if_present(place, other, end_places)
        else:
            places_to_keep.add(place)

    return start_places, end_places


def remove_unconnected_places(net: PetriNet, start_places: set[PetriNet.Place], end_places: set[PetriNet.Place]):
    places = list(net.places)
    for p in places:
        if len(p.in_arcs) == 0 and len(p.out_arcs) == 0:
            pn_util.remove_place(net, p)
            start_places.remove(p)
            end_places.remove(p)
    return start_places, end_places


def preprocess(net: PetriNet):
    all_places = net.places
    for p1, p2 in combinations(all_places, 2):
        pre1 = pn_util.pre_set(p1)
        pre2 = pn_util.pre_set(p2)
        post1 = pn_util.post_set(p1)
        post2 = pn_util.post_set(p2)

        if (pre1 == pre2) and (post1 == post2):
            pn_util.remove_place(net, p2)
            return preprocess(net)

        if pre1 == pre2:
            common_post = post1 & post2
            if len(pre1) > 1 or len(common_post) > 0:
                new_place = PetriNet.Place(f"place_{next(id_generator())}")
                net.places.add(new_place)

                for transition in pre1:
                    add_arc_from_to(transition, new_place, net)
                    arcs_to_remove = p1.in_arcs | p2.in_arcs
                    for arc in arcs_to_remove:
                        pn_util.remove_arc(net, arc)

                for transition in common_post:
                    add_arc_from_to(new_place, transition, net)
                    out_arcs = p1.out_arcs | p2.out_arcs
                    for arc in out_arcs:
                        if arc.target in common_post:
                            pn_util.remove_arc(net, arc)

                new_silent = PetriNet.Transition(f"silent_transition_{next(id_generator())}", None)
                net.transitions.add(new_silent)
                add_arc_from_to(new_place, new_silent, net)
                add_arc_from_to(new_silent, p1, net)
                add_arc_from_to(new_silent, p2, net)
                return preprocess(net)

        if post1 == post2:
            common_pre = pre1 & pre2
            if len(post1) > 1 or len(common_pre) > 0:
                new_place = PetriNet.Place(f"place_{next(id_generator())}")
                net.places.add(new_place)

                for transition in post1:
                    add_arc_from_to(new_place, transition, net)
                    arcs_to_remove = p1.out_arcs | p2.out_arcs
                    for arc in arcs_to_remove:
                        pn_util.remove_arc(net, arc)

                for transition in common_pre:
                    add_arc_from_to(transition, new_place, net)
                    in_arcs = p1.in_arcs | p2.in_arcs
                    for arc in in_arcs:
                        if arc.source in common_pre:
                            pn_util.remove_arc(net, arc)

                new_silent = PetriNet.Transition(f"silent_transition_{next(id_generator())}", None)
                net.transitions.add(new_silent)
                add_arc_from_to(p1, new_silent, net)
                add_arc_from_to(p2, new_silent, net)
                add_arc_from_to(new_silent, new_place, net)

                return preprocess(net)

    return net


def __redirect_shared_arcs_to_new_place(net, places: list[PetriNet.Place], new_place_id):
    shared_pre_set = set(pn_util.pre_set(places[0]))
    for p in places[1:]:
        shared_pre_set &= set(pn_util.pre_set(p))

    shared_post_set = set(pn_util.post_set(places[0]))
    for p in places[1:]:
        shared_post_set &= set(pn_util.post_set(p))

    arcs = list(net.arcs)
    for arc in arcs:
        source = arc.source
        target = arc.target
        if (source in shared_pre_set and target in places) or (source in places and target in shared_post_set):
            pn_util.remove_arc(net, arc)

    if len(shared_post_set) > 0 or len(shared_pre_set) > 0:
        new_place = PetriNet.Place(new_place_id)
        net.places.add(new_place)

        for node in shared_pre_set:
            add_arc_from_to(node, new_place, net)
        for node in shared_post_set:
            add_arc_from_to(new_place, node, net)
        return new_place
    else:
        return None


def add_new_start_and_end_if_needed(net, start_places: set[PetriNet.Place], end_places: set[PetriNet.Place]):
    if len(start_places) == 0 or len(end_places) == 0:
        raise Exception("This should not happen!")

    if len(start_places) > 1:
        new_source_id = f"source_{next(id_generator())}"
        new_source = __redirect_shared_arcs_to_new_place(net, list(start_places), new_source_id)
        if new_source:
            new_silent = PetriNet.Transition(f"silent_start_{next(id_generator())}", None)
            net.transitions.add(new_silent)
            for p in start_places:
                add_arc_from_to(new_silent, p, net)
            add_arc_from_to(new_source, new_silent, net)
            start_places = {new_source}

    if len(end_places) > 1:
        new_sink_id = f"sink_{next(id_generator())}"
        new_sink = __redirect_shared_arcs_to_new_place(net, list(end_places), new_sink_id)
        if new_sink:
            new_silent = PetriNet.Transition(f"silent_end_{next(id_generator())}", None)
            net.transitions.add(new_silent)
            for p in end_places:
                add_arc_from_to(p, new_silent, net)
            add_arc_from_to(new_silent, new_sink, net)
            end_places = {new_sink}

    return start_places, end_places


# ========= Translation Functions =========
def __create_sub_powl_model(net, branch: set[PetriNet.Transition],
                            start_place: PetriNet.Place,
                            end_place: PetriNet.Place):
    subnet, subnet_start_place, subnet_end_place = clone_subnet(net, branch, start_place, end_place)
    powl = __translate_petri_to_powl(subnet, subnet_start_place, subnet_end_place)
    return powl


def __translate_xor(net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place,
                    choice_branches: list[set[PetriNet.Transition]]):
    children = []
    for branch in choice_branches:
        child_powl = __create_sub_powl_model(net, branch, start_place, end_place)
        children.append(child_powl)
    xor_operator = OperatorPOWL(operator=Operator.XOR, children=children)
    return xor_operator


def __translate_loop(net: PetriNet, do_nodes, redo_nodes,
                     start_place: PetriNet.Place, end_place: PetriNet.Place) -> OperatorPOWL:
    do_powl = __create_sub_powl_model(net, do_nodes, start_place, end_place)
    redo_powl = __create_sub_powl_model(net, redo_nodes, end_place, start_place)
    loop_operator = OperatorPOWL(operator=Operator.LOOP, children=[do_powl, redo_powl])
    return loop_operator


def __validate_partial_order(po: StrictPartialOrder):
    po.order.add_transitive_edges()
    if po.order.is_irreflexive():
        return po
    else:
        raise Exception("Conversion failed!")


def __translate_partial_order(net, transition_groups, i_place: PetriNet.Place, f_place: PetriNet.Place):
    groups = [tuple(g) for g in transition_groups]
    transition_to_group_map = {transition: g for g in groups for transition in g}

    group_start_places = {g: set() for g in groups}
    group_end_places = {g: set() for g in groups}
    temp_po = BinaryRelation(groups)

    for p in net.places:
        sources = {arc.source for arc in p.in_arcs}
        targets = {arc.target for arc in p.out_arcs}

        if p == i_place:
            for t in targets:
                group_start_places[transition_to_group_map[t]].add(p)
        if p == f_place:
            for t in sources:
                group_end_places[transition_to_group_map[t]].add(p)

        for t1 in sources:
            group_1 = transition_to_group_map[t1]
            for t2 in targets:
                group_2 = transition_to_group_map[t2]
                if group_1 != group_2:
                    temp_po.add_edge(group_1, group_2)
                    group_end_places[group_1].add(p)
                    group_start_places[group_2].add(p)

    group_to_powl_map = {}
    children = []
    for group in groups:
        subnet, subnet_start_place, subnet_end_place = apply_partial_order_projection(net, set(group),
                                                                                      group_start_places[group],
                                                                                      group_end_places[group])
        child = __translate_petri_to_powl(subnet, subnet_start_place, subnet_end_place)
        group_to_powl_map[group] = child
        children.append(child)

    po = StrictPartialOrder(children)
    for source in temp_po.nodes:
        new_source = group_to_powl_map[source]
        for target in temp_po.nodes:
            if temp_po.is_edge(source, target):
                new_target = group_to_powl_map[target]
                po.order.add_edge(new_source, new_target)

    po = __validate_partial_order(po)
    return po


def __translate_petri_to_powl(net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place) -> POWL:
    base_case = mine_base_case(net)
    if base_case:
        return base_case

    reachability_map = get_simplified_reachability_graph(net)

    choice_branches = mine_xor(net, reachability_map)
    if len(choice_branches) > 1:
        return __translate_xor(net, start_place, end_place, choice_branches)

    self_loop = mine_self_loop(net, start_place, end_place)
    if self_loop:
        return __translate_loop(net, self_loop[0], self_loop[1], self_loop[2], self_loop[3])

    do, redo = mine_loop(net, start_place, end_place)
    if do and redo:
        return __translate_loop(net, do, redo, start_place, end_place)

    partitions = mine_partial_order(net, end_place, reachability_map)
    if len(partitions) > 1:
        return __translate_partial_order(net, partitions, start_place, end_place)

    raise Exception(f"Failed to detect a POWL structure over the following transitions: {net.transitions}")


# ========= Main Function =========
def apply(net: PetriNet) -> POWL:
    """
    Convert a Petri net to a POWL model, implementing the approach proposed in:

    Kourani, Humam, Gyunam Park, and Wil van der Aalst. "Translating Workflow Nets into the
    Partially Ordered Workflow Language." arXiv preprint arXiv:2503.20363 (2025).

    Parameters:
      - net: PetriNet

    Returns:
      - POWL model
    """
    start_place, end_place = validate_workflow_net(net)
    net = preprocess(net)
    res = __translate_petri_to_powl(net, start_place, end_place)
    return res
