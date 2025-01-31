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
import datetime
import itertools
import uuid
from copy import deepcopy
from enum import Enum

from pm4py.objects.petri_net.utils import petri_utils as pn_util
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.process_tree import obj as pt_operator
from pm4py.objects.process_tree.utils import generic as pt_util
from pm4py.objects.process_tree.utils.generic import tree_sort
from pm4py.util import exec_utils
from pm4py.objects.process_tree.utils.generic import parse

TRANSITION_PREFIX = str(uuid.uuid4())


class Parameters(Enum):
    DEBUG = "debug"
    FOLD = "fold"


def generate_label_for_transition(t):
    return 'tau' if t.label is None else '\'' + t.label.replace("'", "") + '\'' if not t.name.startswith(
        TRANSITION_PREFIX) else t.label


def generate_new_binary_transition(t1, t2, operator, net):
    t = PetriNet.Transition(TRANSITION_PREFIX + str(datetime.datetime.now()))
    t.label = str(operator) + '(' + generate_label_for_transition(
        t1) + ', ' + generate_label_for_transition(t2) + ')'
    return t


def loop_requirement(t1, t2):
    if t1 == t2:
        return False
    for p in pn_util.pre_set(t2):
        if len(pn_util.pre_set(p)) != 1:  # check that the preset of the t2 preset has one entry
            return False
        if t1 not in pn_util.pre_set(p):  # check that t1 is the unique way to mark the preset of t2
            return False
    for p in pn_util.post_set(t2):
        if len(pn_util.post_set(p)) != 1:
            return False
        if t1 not in pn_util.post_set(p):
            return False
    for p in pn_util.pre_set(t1):
        if len(pn_util.post_set(p)) != 1:
            return False
        if t1 not in pn_util.post_set(p):
            return False
        if t2 not in pn_util.pre_set(p):  # t2 has to enable t1!
            return False
    for p in pn_util.post_set(t1):
        if len(pn_util.pre_set(p)) != 1:  # check that the preset of the t2 preset has one entry
            return False
        if t1 not in pn_util.pre_set(p):  # check that t1 is the unique way to mark the preset of t2
            return False
        if t2 not in pn_util.post_set(p):
            return False
    return True


def binary_loop_detection(net):
    c1 = None
    c2 = None
    for t1, t2 in itertools.product(net.transitions, net.transitions):
        if loop_requirement(t1, t2):
            c1 = t1
            c2 = t2
            break
    if c1 is not None and c2 is not None:
        t = generate_new_binary_transition(c1, c2, pt_operator.Operator.LOOP, net)
        net.transitions.add(t)
        # reduce
        for a in c1.in_arcs:
            pn_util.add_arc_from_to(a.source, t, net)
        for a in c1.out_arcs:
            pn_util.add_arc_from_to(t, a.target, net)
        pn_util.remove_transition(net, c1)
        pn_util.remove_transition(net, c2)
        return net
    return None


def concurrent_requirement(t1, t2):
    if t1 == t2:  # check if transitions different
        return False
    if len(pn_util.pre_set(t1)) == 0 or len(pn_util.post_set(t1)) == 0 or len(pn_util.pre_set(t2)) == 0 or len(
            pn_util.post_set(t2)) == 0:  # not possible in WF-net, just checking...
        return False
    pre_pre = set()
    post_post = set()
    for p in pn_util.pre_set(t1):  # check if t1 is unique post of its preset
        pre_pre = set.union(pre_pre, pn_util.pre_set(p))
        if len(pn_util.post_set(p)) > 1 or t1 not in pn_util.post_set(p):
            return False
    for p in pn_util.post_set(t1):  # check if t1 is unique pre of its postset
        post_post = set.union(post_post, pn_util.post_set(p))
        if len(pn_util.pre_set(p)) > 1 or t1 not in pn_util.pre_set(p):
            return False
    for p in pn_util.pre_set(t2):  # check if t2 is unique post of its preset
        pre_pre = set.union(pre_pre, pn_util.pre_set(p))
        if len(pn_util.post_set(p)) > 1 or t2 not in pn_util.post_set(p):
            return False
    for p in pn_util.post_set(t2):  # check if t2 is unique pre of its postset
        post_post = set.union(post_post, pn_util.post_set(p))
        if len(pn_util.pre_set(p)) > 1 or t2 not in pn_util.pre_set(p):
            return False
    for p in set.union(pn_util.pre_set(t1), pn_util.pre_set(t2)):  # check if presets synchronize
        for t in pre_pre:
            if t not in pn_util.pre_set(p):
                return False
    for p in set.union(pn_util.post_set(t1), pn_util.post_set(t2)):  # check if postsets synchronize
        for t in post_post:
            if t not in pn_util.post_set(p):
                return False
    return True


def binary_concurrency_detection(net):
    c1 = None
    c2 = None
    for t1, t2 in itertools.product(net.transitions, net.transitions):
        if concurrent_requirement(t1, t2):
            c1 = t1
            c2 = t2
            break
    if c1 is not None and c2 is not None:
        t = generate_new_binary_transition(c1, c2, pt_operator.Operator.PARALLEL, net)
        net.transitions.add(t)
        # reduce
        for a in c1.in_arcs:
            pn_util.add_arc_from_to(a.source, t, net)
        for a in c1.out_arcs:
            pn_util.add_arc_from_to(t, a.target, net)
        for a in c2.in_arcs:
            pn_util.add_arc_from_to(a.source, t, net)
        for a in c2.out_arcs:
            pn_util.add_arc_from_to(t, a.target, net)
        pn_util.remove_transition(net, c1)
        pn_util.remove_transition(net, c2)
        return net
    return None


def choice_requirement(t1, t2):
    return t1 != t2 and pn_util.pre_set(t1) == pn_util.pre_set(t2) and pn_util.post_set(t1) == pn_util.post_set(
        t2) and len(pn_util.pre_set(t1)) > 0 and len(
        pn_util.post_set(t1)) > 0


def binary_choice_detection(net):
    c1 = None
    c2 = None
    for t1, t2 in itertools.product(net.transitions, net.transitions):
        if choice_requirement(t1, t2):
            c1 = t1
            c2 = t2
            break
    if c1 is not None and c2 is not None:
        t = generate_new_binary_transition(c1, c2, pt_operator.Operator.XOR, net)
        net.transitions.add(t)
        for a in c1.in_arcs:
            pn_util.add_arc_from_to(a.source, t, net)
        for a in c2.out_arcs:
            pn_util.add_arc_from_to(t, a.target, net)
        pn_util.remove_transition(net, c1)
        pn_util.remove_transition(net, c2)
        return net
    return None


def sequence_requirement(t1, t2):
    if t1 == t2:
        return False
    if len(pn_util.pre_set(t2)) == 0:
        return False
    for p in pn_util.post_set(t1):
        if len(pn_util.pre_set(p)) != 1 or len(pn_util.post_set(p)) != 1:
            return False
        if t1 not in pn_util.pre_set(p):
            return False
        if t2 not in pn_util.post_set(p):
            return False
    for p in pn_util.pre_set(t2):
        if len(pn_util.pre_set(p)) != 1 or len(pn_util.post_set(p)) != 1:
            return False
        if t1 not in pn_util.pre_set(p):
            return False
        if t2 not in pn_util.post_set(p):  # redundant check, just to be sure...
            return False
    return True


def binary_sequence_detection(net):
    c1 = None
    c2 = None
    for t1, t2 in itertools.product(net.transitions, net.transitions):
        if sequence_requirement(t1, t2):
            c1 = t1
            c2 = t2
            break
    if c1 is not None and c2 is not None:
        t = generate_new_binary_transition(c1, c2, pt_operator.Operator.SEQUENCE, net)
        net.transitions.add(t)
        for a in c1.in_arcs:
            pn_util.add_arc_from_to(a.source, t, net)
        for a in c2.out_arcs:
            pn_util.add_arc_from_to(t, a.target, net)
        for p in pn_util.post_set(c1):
            pn_util.remove_place(net, p)
        pn_util.remove_transition(net, c1)
        pn_util.remove_transition(net, c2)
        return net
    return None


def __group_blocks_internal(net, parameters=None):
    if parameters is None:
        parameters = {}

    if binary_choice_detection(net) is not None:
        return True
    elif binary_sequence_detection(net) is not None:
        return True
    elif binary_concurrency_detection(net) is not None:
        return True
    elif binary_loop_detection(net) is not None:
        return True
    else:
        return False


def __insert_dummy_invisibles(net, im, fm, ini_places, parameters=None):
    if parameters is None:
        parameters = {}

    places = list(net.places)

    for p in places:
        if p.name in ini_places:
            if p not in im and p not in fm:
                source_trans = [x.source for x in p.in_arcs]
                target_trans = [x.target for x in p.out_arcs]

                pn_util.remove_place(net, p)
                source_p = PetriNet.Place(str(uuid.uuid4()))
                target_p = PetriNet.Place(str(uuid.uuid4()))
                skip = PetriNet.Transition(str(uuid.uuid4()))
                net.places.add(source_p)
                net.places.add(target_p)
                net.transitions.add(skip)

                pn_util.add_arc_from_to(source_p, skip, net)
                pn_util.add_arc_from_to(skip, target_p, net)

                for t in source_trans:
                    pn_util.add_arc_from_to(t, source_p, net)
                for t in target_trans:
                    pn_util.add_arc_from_to(target_p, t, net)


def group_blocks_in_net(net, parameters=None):
    """
    Groups the blocks in the Petri net

    Parameters
    --------------
    net
        Petri net
    parameters
        Parameters of the algorithm

    Returns
    --------------
    grouped_net
        Petri net (blocks are grouped according to the algorithm)
    """
    if parameters is None:
        parameters = {}

    from pm4py.algo.analysis.workflow_net import algorithm as wf_eval

    if not wf_eval.apply(net):
        raise ValueError('The Petri net provided is not a WF-net')

    net = deepcopy(net)
    ini_places = set(x.name for x in net.places)

    while len(net.transitions) > 1:
        im = Marking({p: 1 for p in net.places if len(p.in_arcs) == 0})
        fm = Marking({p: 1 for p in net.places if len(p.out_arcs) == 0})

        if len(im) != 1 and len(fm) != 1:
            # start/end conditions for block-structured nets
            # do not hold
            break

        if __group_blocks_internal(net, parameters):
            continue
        else:
            __insert_dummy_invisibles(net, im, fm, ini_places, parameters)
            if __group_blocks_internal(net, parameters):
                continue
            else:
                break

    return net


def apply(net, im, fm, parameters=None):
    """
    Transforms a WF-net to a process tree

    Parameters
    -------------
    net
        Petri net
    im
        Initial marking
    fm
        Final marking

    Returns
    -------------
    tree
        Process tree
    """
    if parameters is None:
        parameters = {}

    debug = exec_utils.get_param_value(Parameters.DEBUG, parameters, False)
    fold = exec_utils.get_param_value(Parameters.FOLD, parameters, True)

    grouped_net = group_blocks_in_net(net, parameters=parameters)

    if debug:
        from pm4py.visualization.petri_net import visualizer as pn_viz
        pn_viz.view(pn_viz.apply(grouped_net, parameters={"format": "svg"}))
        return grouped_net
    else:
        if len(grouped_net.transitions) == 1:
            pt_str = list(grouped_net.transitions)[0].label
            pt = parse(pt_str)
            ret = pt_util.fold(pt) if fold else pt
            tree_sort(ret)
            return ret
        else:
            raise ValueError('Parsing of WF-net Failed')
