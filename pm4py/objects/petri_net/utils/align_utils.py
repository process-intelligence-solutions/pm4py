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
import heapq
import sys
from copy import copy
from typing import List, Tuple

import numpy as np

from pm4py.objects.petri_net import semantics, properties
from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.util.lp import solver as lp_solver

SKIP = ">>"
STD_MODEL_LOG_MOVE_COST = 10000
STD_TAU_COST = 1
STD_SYNC_COST = 0


def search_path_among_sol(
    sync_net: PetriNet,
    ini: Marking,
    fin: Marking,
    activated_transitions: List[PetriNet.Transition],
    skip=SKIP,
) -> Tuple[List[PetriNet.Transition], bool, int]:
    """
    (Efficient method) Searches a firing sequence among the X vector that is the solution of the
    (extended) marking equation

    Parameters
    ---------------
    sync_net
        Synchronous product net
    ini
        Initial marking of the net
    fin
        Final marking of the net
    activated_transitions
        Transitions that have non-zero occurrences in the X vector
    skip
        Skip transition

    Returns
    ---------------
    firing_sequence
        Firing sequence
    reach_fm
        Boolean value that tells if the final marking is reached by the firing sequence
    explained_events
        Number of explained events
    """
    reach_fm = False
    trans_empty_preset = set(
        t for t in sync_net.transitions if len(t.in_arcs) == 0
    )
    trans_with_index = {}
    trans_wo_index = set()
    for t in activated_transitions:
        if properties.TRACE_NET_TRANS_INDEX in t.properties:
            trans_with_index[
                t.properties[properties.TRACE_NET_TRANS_INDEX]
            ] = t
        else:
            trans_wo_index.add(t)
    keys = sorted(list(trans_with_index.keys()))
    trans_with_index = [trans_with_index[i] for i in keys]
    best_tuple = (0, 0, ini, list())
    open_set = [best_tuple]
    heapq.heapify(open_set)
    visited = 0
    closed = set()
    len_trace_with_index = len(trans_with_index)
    while len(open_set) > 0:
        curr = heapq.heappop(open_set)
        index = -curr[0]
        marking = curr[2]
        if marking in closed:
            continue
        if index == len_trace_with_index:
            reach_fm = True
            if curr[0] < best_tuple[0]:
                best_tuple = curr
            break
        if curr[0] < best_tuple[0]:
            best_tuple = curr
        closed.add(marking)
        corr_trans = trans_with_index[index]
        if corr_trans.sub_marking <= marking:
            visited += 1
            new_marking = semantics.weak_execute(corr_trans, marking)
            heapq.heappush(
                open_set,
                (-index - 1, visited, new_marking, curr[3] + [corr_trans]),
            )
        else:
            enabled = copy(trans_empty_preset)
            for p in marking:
                for t in p.ass_trans:
                    if t in trans_wo_index and t.sub_marking <= marking:
                        enabled.add(t)
            for new_trans in enabled:
                visited += 1
                new_marking = semantics.weak_execute(new_trans, marking)
                heapq.heappush(
                    open_set,
                    (-index, visited, new_marking, curr[3] + [new_trans]),
                )
    return best_tuple[-1], reach_fm, -best_tuple[0]


def construct_standard_cost_function(synchronous_product_net, skip):
    """
    Returns the standard cost function, which is:
    * event moves: cost 1000
    * model moves: cost 1000
    * tau moves: cost 1
    * sync moves: cost 0
    :param synchronous_product_net:
    :param skip:
    :return:
    """
    costs = {}
    for t in synchronous_product_net.transitions:
        if (skip == t.label[0] or skip == t.label[1]) and (
            t.label[0] is not None and t.label[1] is not None
        ):
            costs[t] = STD_MODEL_LOG_MOVE_COST
        else:
            if skip == t.label[0] and t.label[1] is None:
                costs[t] = STD_TAU_COST
            else:
                costs[t] = STD_SYNC_COST
    return costs


def pretty_print_alignments(alignments):
    """Takes an alignment and prints it to the console, e.g.::

         A  | B  | C  | D  |
        --------------------
         A  | B  | C  | >> |

    :param alignment: The alignment object (list of moves).
    :return: Nothing.
    """
    if isinstance(alignments, list):
        for alignment in alignments:
            __print_single_alignment(alignment["alignment"])
    else:
        __print_single_alignment(alignments["alignment"])


def __print_single_alignment(step_list):
    trace_steps = []
    model_steps = []
    max_label_length = 0
    for step in step_list:
        trace_steps.append(" " + str(step[0]) + " ")
        model_steps.append(" " + str(step[1]) + " ")
        if len(step[0]) > max_label_length:
            max_label_length = len(str(step[0]))
        if len(str(step[1])) > max_label_length:
            max_label_length = len(str(step[1]))
    for i in range(len(trace_steps)):
        if len(str(trace_steps[i])) - 2 < max_label_length:
            step_length = len(str(trace_steps[i])) - 2
            spaces_to_add = max_label_length - step_length
            for j in range(spaces_to_add):
                if j % 2 == 0:
                    trace_steps[i] = trace_steps[i] + " "
                else:
                    trace_steps[i] = " " + trace_steps[i]
        print(trace_steps[i], end="|")
    divider = ""
    length_divider = len(trace_steps) * (max_label_length + 3)
    for i in range(length_divider):
        divider += "-"
    print("\n" + divider)
    for i in range(len(model_steps)):
        if len(model_steps[i]) - 2 < max_label_length:
            step_length = len(model_steps[i]) - 2
            spaces_to_add = max_label_length - step_length
            for j in range(spaces_to_add):
                if j % 2 == 0:
                    model_steps[i] = model_steps[i] + " "
                else:
                    model_steps[i] = " " + model_steps[i]

        print(model_steps[i], end="|")
    print("\n\n")


def add_markings(curr, add):
    m = Marking()
    for p in curr.items():
        m[p[0]] = p[1]
    for p in add.items():
        m[p[0]] += p[1]
        if m[p[0]] == 0:
            del m[p[0]]
    return m


def __get_alt(open_set, new_marking):
    for item in open_set:
        if item.m == new_marking:
            return item


def __reconstruct_alignment(
    state,
    visited,
    queued,
    traversed,
    ret_tuple_as_trans_desc=False,
    lp_solved=0,
):
    alignment = list()
    if state.p is not None and state.t is not None:
        parent = state.p
        if ret_tuple_as_trans_desc:
            alignment = [(state.t.name, state.t.label)]
            while parent.p is not None:
                alignment = [(parent.t.name, parent.t.label)] + alignment
                parent = parent.p
        else:
            alignment = [state.t.label]
            while parent.p is not None:
                alignment = [parent.t.label] + alignment
                parent = parent.p
    return {
        "alignment": alignment,
        "cost": state.g,
        "visited_states": visited,
        "queued_states": queued,
        "traversed_arcs": traversed,
        "lp_solved": lp_solved,
    }


def __derive_heuristic(incidence_matrix, cost_vec, x, t, h):
    x_prime = x.copy()
    x_prime[incidence_matrix.transitions[t]] -= 1
    return max(0, h - cost_vec[incidence_matrix.transitions[t]]), x_prime


def __is_model_move(t, skip):
    return t.label[0] == skip and t.label[1] != skip


def __is_log_move(t, skip):
    return t.label[0] != skip and t.label[1] == skip


def __trust_solution(x):
    for v in x:
        if v < -0.001:
            return False
    return True


def __compute_exact_heuristic_new_version(
    sync_net,
    a_matrix,
    h_cvx,
    g_matrix,
    cost_vec,
    incidence_matrix,
    marking,
    fin_vec,
    variant,
    use_cvxopt=False,
    strict=True,
):
    m_vec = incidence_matrix.encode_marking(marking)
    b_term = [i - j for i, j in zip(fin_vec, m_vec)]
    b_term = np.matrix([x * 1.0 for x in b_term]).transpose()

    if not strict:
        g_matrix = np.vstack([g_matrix, a_matrix])
        h_cvx = np.vstack([h_cvx, b_term])
        a_matrix = np.zeros((0, a_matrix.shape[1]))
        b_term = np.zeros((0, b_term.shape[1]))

    if use_cvxopt:
        # not available in the latest version of PM4Py
        from cvxopt import matrix

        b_term = matrix(b_term)

    parameters_solving = {"solver": "glpk"}

    sol = lp_solver.apply(
        cost_vec,
        g_matrix,
        h_cvx,
        a_matrix,
        b_term,
        parameters=parameters_solving,
        variant=variant,
    )
    prim_obj = lp_solver.get_prim_obj_from_sol(sol, variant=variant)
    points = lp_solver.get_points_from_sol(sol, variant=variant)

    prim_obj = prim_obj if prim_obj is not None else sys.maxsize
    points = (
        points if points is not None else [0.0] * len(sync_net.transitions)
    )

    return prim_obj, points


def __get_tuple_from_queue(marking, queue):
    for t in queue:
        if t.m == marking:
            return t
    return None


def __vectorize_initial_final_cost(incidence_matrix, ini, fin, cost_function):
    ini_vec = incidence_matrix.encode_marking(ini)
    fini_vec = incidence_matrix.encode_marking(fin)
    cost_vec = [0] * len(cost_function)
    for t in cost_function.keys():
        cost_vec[incidence_matrix.transitions[t]] = cost_function[t]
    return ini_vec, fini_vec, cost_vec


class SearchTuple:
    # different properties of the class:
    # - g => actual cost of the alignment moves
    # - h => computed heuristic value
    # - f => the sum of g and h, used for the A* algorithm
    # - m => marking reached in the synchronous product net in the current state
    # - p => parent state of the alignment (used at the end to reconstruct the alignment)
    # - t => transition just visited
    # - trustable => indicates if the heuristic comes from an exact solution of an (I)LP problem
    # - x => solution vector of the (I)LP
    def __init__(self, f, g, h, m, p, t, x, trust):
        self.f = f
        self.g = g
        self.h = h
        self.m = m
        self.p = p
        self.t = t
        self.x = x
        self.trust = trust

    def __lt__(self, other):
        if self.f < other.f:
            return True
        elif other.f < self.f:
            return False
        elif self.trust and not other.trust:
            return True
        else:
            return self.h < other.h

    def __get_firing_sequence(self):
        ret = []
        if self.p is not None:
            ret = ret + self.p.__get_firing_sequence()
        if self.t is not None:
            ret.append(self.t)
        return ret

    def __repr__(self):
        string_build = [
            "\nm=" + str(self.m),
            " f=" + str(self.f),
            " g=" + str(self.g),
            " h=" + str(self.h),
            " path=" + str(self.__get_firing_sequence()) + "\n\n",
        ]
        return " ".join(string_build)


class DijkstraSearchTuple:
    def __init__(self, g, m, p, t, l):
        self.g = g
        self.m = m
        self.p = p
        self.t = t
        self.l = l

    def __lt__(self, other):
        if self.g < other.g:
            return True
        elif other.g < self.g:
            return False
        else:
            return other.l < self.l

    def __get_firing_sequence(self):
        ret = []
        if self.p is not None:
            ret = ret + self.p.__get_firing_sequence()
        if self.t is not None:
            ret.append(self.t)
        return ret

    def __repr__(self):
        string_build = [
            "\nm=" + str(self.m),
            " g=" + str(self.g),
            " path=" + str(self.__get_firing_sequence()) + "\n\n",
        ]
        return " ".join(string_build)

class DijkstraSearchTupleForAntiAndMulti:
    # in this version we keep the run and not the previous element
    # the display is different
    def __init__(self, g, m, r):
        self.g = g
        self.m = m
        self.r = r

    def __lt__(self, other):
        if self.g < other.g:
            return True
        elif other.g < self.g:
            return False
        else:
            return len(other.r) < len(self.r)

    def __get_firing_sequence(self):
        return self.r

    def __repr__(self):
        string_build = ["\nm=" + str(self.m), " g=" + str(self.g),
                        " path=" + str(self.__get_firing_sequence()) + "\n\n"]
        return " ".join(string_build)

class TweakedSearchTuple:
    def __init__(self, f, g, h, m, p, t, x, trust, virgin):
        self.f = f
        self.g = g
        self.h = h
        self.m = m
        self.p = p
        self.t = t
        self.x = x
        self.trust = trust
        # a virgin status must be explored in its firing sequence
        self.virgin = virgin

    def __lt__(self, other):
        if self.f < other.f:
            return True
        elif other.f < self.f:
            return False
        elif self.virgin and not other.virgin:
            return True
        elif self.trust and not other.trust:
            return True
        else:
            return self.h < other.h

    def __get_firing_sequence(self):
        ret = []
        if self.p is not None:
            ret = ret + self.p.__get_firing_sequence()
        if self.t is not None:
            ret.append(self.t)
        return ret

    def __repr__(self):
        string_build = [
            "\nm=" + str(self.m),
            " f=" + str(self.f),
            " g=" + str(self.g),
            " h=" + str(self.h),
            " path=" + str(self.__get_firing_sequence()) + "\n\n",
        ]
        return " ".join(string_build)


def get_visible_transitions_eventually_enabled_by_marking(net, marking):
    """
    Get visible transitions eventually enabled by marking (passing possibly
    through hidden transitions)

    Parameters
    ----------
    net
        Petri net
    marking
        Current marking

    """
    all_enabled_transitions = sorted(
        list(semantics.enabled_transitions(net, marking)),
        key=lambda x: (str(x.name), id(x)),
    )
    initial_all_enabled_transitions_marking_dictio = {}
    all_enabled_transitions_marking_dictio = {}
    for trans in all_enabled_transitions:
        all_enabled_transitions_marking_dictio[trans] = marking
        initial_all_enabled_transitions_marking_dictio[trans] = marking
    visible_transitions = set()
    visited_transitions = set()

    i = 0
    while i < len(all_enabled_transitions):
        t = all_enabled_transitions[i]
        marking_copy = copy(all_enabled_transitions_marking_dictio[t])

        if repr([t, marking_copy]) not in visited_transitions:
            if t.label is not None:
                visible_transitions.add(t)
            else:
                if semantics.is_enabled(t, net, marking_copy):
                    new_marking = semantics.execute(t, net, marking_copy)
                    new_enabled_transitions = sorted(
                        list(semantics.enabled_transitions(net, new_marking)),
                        key=lambda x: (str(x.name), id(x)),
                    )
                    for t2 in new_enabled_transitions:
                        all_enabled_transitions.append(t2)
                        all_enabled_transitions_marking_dictio[t2] = (
                            new_marking
                        )
            visited_transitions.add(repr([t, marking_copy]))
        i = i + 1

    return visible_transitions

def discountedEditDistance(s1,s2,exponent=2, modeled=True):
    '''
    Fast implementation of the discounted distance
    Inspired from the faster version of the edit distance
    '''
    #print(s1,s2)
    if len(s1) < len(s2):
        return discountedEditDistance(s2, s1,exponent=exponent,modeled=False)

    previous_row = [0]
    for a in range(len(s2)):
        if not modeled and (s2[a]=="tau" or s2[a]isNone or s2[a][0]=="n"):
            previous_row.append(previous_row[-1])
        else :
            previous_row.append(previous_row[-1]+exponent**(-(a)))
    for i, c1 in enumerate(s1):
        if modeled:
            exp1 = sum(exponent**(-(a))  for a in range(i+1) if s1[a]!="tau" and s1[a]is notNone and s1[a][0]!="n")
        else :
            exp1 = sum(exponent**(-(a))  for a in range(i+1))
        current_row =  [exp1]
        for j, c2 in enumerate(s2):

            exp2 = exponent**(-(i+1 + j))
            if modeled and  (c1 in ["tau", None] or c1[0]=="n" or "skip" in c1):
                insertions = previous_row[j +1 ]  # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + exp2    # than s2
            elif not modeled and (c2 in ["tau", None] or c2[0]=="n"):
                insertions = previous_row[j +1 ] + exp2 # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j]
            else :
                insertions = previous_row[j +1 ] + exp2 # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + exp2
            if (c1 != c2):
                current_row.append(min(insertions, deletions))
            else :
                substitutions = previous_row[j]
                current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row
    return len(s1)+len(s2),previous_row[-1]


def levenshtein(seq1, seq2):
    '''
    Edit distance without substitution
    '''
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros ((size_x, size_y))
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        matrix [0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x-1] in [None,"tau"] or seq1[x-1][0]=='n' or "skip" in seq1[x-1] or "tau" in seq1[x-1] :
                matrix [x,y] = min(
                    matrix[x-1, y],
                    matrix[x,y-1] + 1
                )
            elif seq1[x-1] == seq2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x,y-1] + 1
                )
    return (matrix[size_x - 1, size_y - 1])

