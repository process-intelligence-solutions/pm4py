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
import random
import time

from typing import Optional, Set
from copy import copy, deepcopy

from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.petri_net import semantics, properties
from pm4py.objects.petri_net.obj import PetriNet, Marking, ResetNet, InhibitorNet
from pm4py.objects.petri_net.saw_net.obj import StochasticArcWeightNet
from pm4py.util import xes_constants as xes_util


def is_sub_marking(sub_marking: Marking, marking: Marking) -> bool:
    for p in sub_marking:
        if p not in marking:
            return False
        elif marking[p] > sub_marking[p]:
            return False
    return True


def place_set_as_marking(places) -> Marking:
    m = Marking()
    for p in places:
        m[p] = 1
    return m


def get_arc_type(elem):
    if properties.ARCTYPE in elem.properties:
        return elem.properties[properties.ARCTYPE]
    return None


def pre_set(elem, arc_type=None) -> Set:
    pre = set()
    for a in elem.in_arcs:
        if get_arc_type(a) == arc_type:
            pre.add(a.source)
    return pre


def post_set(elem, arc_type=None) -> Set:
    post = set()
    for a in elem.out_arcs:
        if get_arc_type(a) == arc_type:
            post.add(a.target)
    return post


def remove_transition(net: PetriNet, trans: PetriNet.Transition) -> PetriNet:
    """
    Remove a transition from a Petri net

    Parameters
    ----------
    net
        Petri net
    trans
        Transition to remove

    Returns
    ----------
    net
        Petri net
    """
    if trans in net.transitions:
        in_arcs = trans.in_arcs
        for arc in in_arcs:
            place = arc.source
            place.out_arcs.remove(arc)
            net.arcs.remove(arc)
        out_arcs = trans.out_arcs
        for arc in out_arcs:
            place = arc.target
            place.in_arcs.remove(arc)
            net.arcs.remove(arc)
        net.transitions.remove(trans)
    return net


def add_place(net: PetriNet, name=None) -> PetriNet.Place:
    name = name if name is not None else 'p_' + str(len(net.places)) + '_' + str(time.time()) + str(
        random.randint(0, 10000))
    p = PetriNet.Place(name=name)
    net.places.add(p)
    return p


def add_transition(net: PetriNet, name=None, label=None) -> PetriNet.Transition:
    name = name if name is not None else 't_' + str(len(net.transitions)) + '_' + str(time.time()) + str(
        random.randint(0, 10000))
    t = PetriNet.Transition(name=name, label=label)
    net.transitions.add(t)
    return t


def merge(trgt: Optional[PetriNet]=None, nets=None) -> PetriNet:
    trgt = trgt if trgt is not None else PetriNet()
    nets = nets if nets is not None else list()
    for net in nets:
        trgt.transitions.update(net.transitions)
        trgt.places.update(net.places)
        trgt.arcs.update(net.arcs)
    return trgt


def remove_place(net: PetriNet, place: PetriNet.Place) -> PetriNet:
    """
    Remove a place from a Petri net

    Parameters
    -------------
    net
        Petri net
    place
        Place to remove

    Returns
    -------------
    net
        Petri net
    """
    if place in net.places:
        in_arcs = place.in_arcs
        for arc in in_arcs:
            trans = arc.source
            trans.out_arcs.remove(arc)
            net.arcs.remove(arc)
        out_arcs = place.out_arcs
        for arc in out_arcs:
            trans = arc.target
            trans.in_arcs.remove(arc)
            net.arcs.remove(arc)
        net.places.remove(place)
    return net


def add_arc_from_to(fr, to, net: PetriNet, weight=1, type=None) -> PetriNet.Arc:
    """
    Adds an arc from a specific element to another element in some net. Assumes from and to are in the net!

    Parameters
    ----------
    fr: transition/place from
    to:  transition/place to
    net: net to use
    weight: weight associated to the arc

    Returns
    -------
    None
    """
    if type == properties.INHIBITOR_ARC:
        if isinstance(net, InhibitorNet):
            a = InhibitorNet.InhibitorArc(fr, to, weight)
            a.properties[properties.ARCTYPE] = type
        else:
            raise Exception("trying to add an inhibitor arc on a traditional Petri net object.")
    elif type == properties.RESET_ARC:
        if isinstance(net, ResetNet):
            a = ResetNet.ResetArc(fr, to, weight)
            a.properties[properties.ARCTYPE] = type
        else:
            raise Exception("trying to add a reset arc on a traditional Petri net object.")
    elif type == properties.STOCHASTIC_ARC:
        if isinstance(net, StochasticArcWeightNet):
            a = StochasticArcWeightNet.Arc(fr, to, weight)
            #a.properties[properties.ARCTYPE] = type
        else:
            raise Exception("trying to add a stochastic arc on a traditional Petri net object.")
    else:
        a = PetriNet.Arc(fr, to, weight)
    net.arcs.add(a)
    fr.out_arcs.add(a)
    to.in_arcs.add(a)

    return a


def construct_trace_net(trace, trace_name_key=xes_util.DEFAULT_NAME_KEY, activity_key=xes_util.DEFAULT_NAME_KEY):
    """
    Creates a trace net, i.e. a trace in Petri net form.

    Parameters
    ----------
    trace: :class:`list` input trace, assumed to be a list of events
    trace_name_key: :class:`str` key of the attribute that defines the name of the trace
    activity_key: :class:`str` key of the attribute of the events that defines the activity name

    Returns
    -------
    tuple: :class:`tuple` of the net, initial marking and the final marking

    """
    net = PetriNet(
        'trace net of %s' % trace.attributes[trace_name_key] if trace_name_key in trace.attributes else ' ')
    place_map = {0: PetriNet.Place('p_0')}
    net.places.add(place_map[0])
    for i in range(0, len(trace)):
        t = PetriNet.Transition('t_' + trace[i][activity_key] + '_' + str(i), trace[i][activity_key])
        # 16/02/2021: set the trace index as property of the transition of the trace net
        t.properties[properties.TRACE_NET_TRANS_INDEX] = i
        net.transitions.add(t)
        place_map[i + 1] = PetriNet.Place('p_' + str(i + 1))
        # 16/02/2021: set the place index as property of the place of the trace net
        place_map[i + 1].properties[properties.TRACE_NET_PLACE_INDEX] = i + 1
        net.places.add(place_map[i + 1])
        add_arc_from_to(place_map[i], t, net)
        add_arc_from_to(t, place_map[i + 1], net)
    return net, Marking({place_map[0]: 1}), Marking({place_map[len(trace)]: 1})


def construct_trace_net_cost_aware(trace, costs, trace_name_key=xes_util.DEFAULT_NAME_KEY,
                                   activity_key=xes_util.DEFAULT_NAME_KEY):
    """
    Creates a trace net, i.e. a trace in Petri net form mapping specific costs to transitions.

    Parameters
    ----------
    trace: :class:`list` input trace, assumed to be a list of events
    costs: :class:`list` list of costs, length should be equal to the length of the input trace
    trace_name_key: :class:`str` key of the attribute that defines the name of the trace
    activity_key: :class:`str` key of the attribute of the events that defines the activity name

    Returns
    -------
    tuple: :class:`tuple` of the net, initial marking, final marking and map of costs


    """
    net = PetriNet(
        'trace net of %s' % trace.attributes[trace_name_key] if trace_name_key in trace.attributes else ' ')
    place_map = {0: PetriNet.Place('p_0')}
    net.places.add(place_map[0])
    cost_map = dict()
    for i in range(0, len(trace)):
        t = PetriNet.Transition('t_' + trace[i][activity_key] + '_' + str(i), trace[i][activity_key])
        # 16/02/2021: set the trace index as property of the transition of the trace net
        t.properties[properties.TRACE_NET_TRANS_INDEX] = i
        cost_map[t] = costs[i]
        net.transitions.add(t)
        place_map[i + 1] = PetriNet.Place('p_' + str(i + 1))
        # 16/02/2021: set the place index as property of the place of the trace net
        place_map[i + 1].properties[properties.TRACE_NET_PLACE_INDEX] = i + 1
        net.places.add(place_map[i + 1])
        add_arc_from_to(place_map[i], t, net)
        add_arc_from_to(t, place_map[i + 1], net)
    return net, Marking({place_map[0]: 1}), Marking({place_map[len(trace)]: 1}), cost_map


def acyclic_net_variants(net, initial_marking, final_marking, activity_key=xes_util.DEFAULT_NAME_KEY):
    """
    Given an acyclic accepting Petri net, initial and final marking extracts a set of variants (in form of traces)
    replayable on the net.
    Warning: this function is based on a marking exploration. If the accepting Petri net contains loops, the method
    will not work properly as it stops the search if a specific marking has already been encountered.

    Parameters
    ----------
    :param net: An acyclic workflow net
    :param initial_marking: The initial marking of the net.
    :param final_marking: The final marking of the net.
    :param activity_key: activity key to use

    Returns
    -------
    :return: variants: :class:`list` Set of variants - in the form of Trace objects - obtainable executing the net

    """
    active = {(initial_marking, ())}
    visited = set()
    variants = set()
    while active:
        curr_marking, curr_partial_trace = active.pop()
        curr_pair = (curr_marking, curr_partial_trace)
        enabled_transitions = semantics.enabled_transitions(net, curr_marking)
        for transition in enabled_transitions:
            if transition.label is not None:
                next_partial_trace = curr_partial_trace + (transition.label,)
            else:
                next_partial_trace = curr_partial_trace
            next_marking = semantics.execute(transition, net, curr_marking)
            next_pair = (next_marking, next_partial_trace)

            if next_marking == final_marking:
                variants.add(next_partial_trace)
            else:
                # If the next marking is not in visited, if the next marking+partial trace is different from the current one+partial trace
                if next_pair not in visited and curr_pair != next_pair:
                    active.add(next_pair)
        visited.add(curr_pair)
    trace_variants = []
    for variant in variants:
        trace = Trace()
        for activity_label in variant:
            trace.append(Event({activity_key: activity_label}))
        trace_variants.append(trace)
    return trace_variants


def get_place_by_name(net: PetriNet, place_name) -> Optional[PetriNet.Place]:
    """
    Get a place by its name

    Parameters
    ------------
    net
        Petri net
    place_name
        Place name

    Returns
    ------------
    place
        Place object
    """
    for t in net.places:
        if t.name == place_name:
            return t
    return None
    

def get_transition_by_name(net: PetriNet, transition_name) -> Optional[PetriNet.Transition]:
    """
    Get a transition by its name

    Parameters
    ------------
    net
        Petri net
    transition_name
        Transition name

    Returns
    ------------
    transition
        Transition object
    """
    for t in net.transitions:
        if t.name == transition_name:
            return t
    return None


def decorate_places_preset_trans(net: PetriNet):
    """
    Decorate places with information useful for the replay

    Parameters
    -------------
    net
        Petri net
    """
    for place in net.places:
        place.ass_trans = set()

    for trans in net.transitions:
        for place in trans.sub_marking:
            place.ass_trans.add(trans)


def decorate_transitions_prepostset(net: PetriNet):
    """
    Decorate transitions with sub and addition markings

    Parameters
    -------------
    net
        Petri net
    """
    from pm4py.objects.petri_net.obj import Marking
    for trans in net.transitions:
        sub_marking = Marking()
        add_marking = Marking()

        for arc in trans.in_arcs:
            sub_marking[arc.source] = arc.weight
            add_marking[arc.source] = -arc.weight
        for arc in trans.out_arcs:
            if arc.target in add_marking:
                add_marking[arc.target] = arc.weight + add_marking[arc.target]
            else:
                add_marking[arc.target] = arc.weight
        trans.sub_marking = sub_marking
        trans.add_marking = add_marking


def get_places_shortest_path(net, place_to_populate, current_place, places_shortest_path, actual_list, rec_depth,
                             max_rec_depth):
    """
    Get shortest path between places lead by hidden transitions

    Parameters
    ----------
    net
        Petri net
    place_to_populate
        Place that we are populating the shortest map of
    current_place
        Current visited place (must explore its transitions)
    places_shortest_path
        Current dictionary
    actual_list
        Actual list of transitions to enable
    rec_depth
        Recursion depth
    max_rec_depth
        Maximum recursion depth
    """
    if rec_depth > max_rec_depth:
        return places_shortest_path
    if place_to_populate not in places_shortest_path:
        places_shortest_path[place_to_populate] = {}
    for t in current_place.out_arcs:
        if t.target.label is None:
            for p2 in t.target.out_arcs:
                if p2.target not in places_shortest_path[place_to_populate] or len(actual_list) + 1 < len(
                        places_shortest_path[place_to_populate][p2.target]):
                    new_actual_list = copy(actual_list)
                    new_actual_list.append(t.target)
                    places_shortest_path[place_to_populate][p2.target] = copy(new_actual_list)
                    places_shortest_path = get_places_shortest_path(net, place_to_populate, p2.target,
                                                                    places_shortest_path, new_actual_list,
                                                                    rec_depth + 1, max_rec_depth)
    return places_shortest_path


def get_places_shortest_path_by_hidden(net: PetriNet, max_rec_depth):
    """
    Get shortest path between places lead by hidden transitions

    Parameters
    ----------
    net
        Petri net
    max_rec_depth
        Maximum recursion depth
    """
    places_shortest_path = {}
    for p in net.places:
        places_shortest_path = get_places_shortest_path(net, p, p, places_shortest_path, [], 0, max_rec_depth)
    return places_shortest_path


def invert_spaths_dictionary(spaths):
    """
    Invert the shortest paths (between places) dictionary,
    from target-source to source-target

    Parameters
    -------------
    spaths
        Shortest paths dictionary

    Returns
    -------------
    inv_spaths
        Inverted shortest paths dictionary
    """
    inv_spaths = {}
    for target_place in spaths:
        for source_place in spaths[target_place]:
            if not source_place in inv_spaths:
                inv_spaths[source_place] = {}
            if not target_place in inv_spaths[source_place]:
                inv_spaths[source_place][target_place] = set()
            inv_spaths[source_place][target_place] = inv_spaths[source_place][target_place].union(
                spaths[target_place][source_place])
    return inv_spaths


def remove_unconnected_components(net: PetriNet) -> PetriNet:
    """
    Remove unconnected components from a Petri net

    Parameters
    -----------
    net
        Petri net

    Returns
    -----------
    net
        Cleaned Petri net
    """
    changed_something = True
    while changed_something:
        changed_something = False
        places = list(net.places)
        for place in places:
            if len(place.in_arcs) == 0 and len(place.out_arcs) == 0:
                remove_place(net, place)
                changed_something = True
        transitions = list(net.transitions)
        for trans in transitions:
            if len(trans.in_arcs) == 0 or len(trans.out_arcs) == 0:
                remove_transition(net, trans)
                changed_something = True
    return net


def get_s_components_from_petri(net, im, fm, rec_depth=0, curr_s_comp=None, visited_places=None,
                                list_s_components=None, max_rec_depth=6):
    """
    Gets the S-components from a Petri net

    Parameters
    -------------
    net
        Petri net
    im
        Initial marking
    fm
        Final marking
    curr_s_comp
        Current S component
    visited_places
        Visited places
    list_s_components
        List of S-components
    max_rec_depth
        Maximum recursion depth

    Returns
    --------------
    s_components
        List of S-components
    """
    if list_s_components is None:
        list_s_components = []
    if len(im) > 1 or len(fm) > 1:
        return list_s_components
    source = list(im.keys())[0]
    if curr_s_comp is None:
        curr_s_comp = [source]
    if visited_places is None:
        visited_places = []
    something_changed = True
    while something_changed and rec_depth < max_rec_depth:
        something_changed = False
        places_to_visit = sorted(list(set(curr_s_comp[len(visited_places):])), key=lambda x: len(x.out_arcs),
                                 reverse=True)
        for place_to_visit in places_to_visit:
            visited_places.append(place_to_visit)
            target_trans = sorted(list(set([arc.target for arc in place_to_visit.out_arcs])),
                                  key=lambda x: len(x.out_arcs))
            for trans in target_trans:
                visited_places_names = [x.name for x in visited_places]
                target_trans_target = list(
                    set([arc.target for arc in trans.out_arcs if arc.target.name not in visited_places_names]))
                if target_trans_target:
                    something_changed = True
                    if len(target_trans_target) == 1:
                        new_place = target_trans_target[0]
                        curr_s_comp.append(new_place)
                    else:
                        for new_place in target_trans_target:
                            [new_curr_s_comp, new_visited_places] = deepcopy([curr_s_comp, visited_places])
                            new_curr_s_comp.append(new_place)
                            list_s_components = get_s_components_from_petri(net, im, fm, rec_depth=rec_depth + 1,
                                                                            curr_s_comp=new_curr_s_comp,
                                                                            visited_places=new_visited_places,
                                                                            list_s_components=list_s_components,
                                                                            max_rec_depth=max_rec_depth)

    if not set([place.name for place in curr_s_comp]) in list_s_components:
        list_s_components.append(set([place.name for place in curr_s_comp]))

    return list_s_components


def remove_arc(net: PetriNet, arc: PetriNet.Arc) -> PetriNet:
    """
    Removes an arc from a Petri net

    Parameters
    ---------------
    net
        Petri net
    arc
        Arc of the Petri net

    Returns
    -------------
    net
        Petri net
    """
    net.arcs.remove(arc)
    arc.source.out_arcs.remove(arc)
    arc.target.in_arcs.remove(arc)

    return net
