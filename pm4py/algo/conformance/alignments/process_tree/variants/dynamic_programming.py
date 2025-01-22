from typing import Any, Dict, List, Union, Optional, Collection
from pm4py.utils import project_on_event_attribute
import pandas as pd
from pm4py.util import exec_utils
from enum import Enum
from pm4py.util import constants, xes_constants
from pm4py.objects.log.obj import EventLog
import importlib.util
from pm4py.objects.process_tree.utils import generic
from pm4py.objects.process_tree.obj import ProcessTree, Operator
import time
import sys


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    SHOW_PROGRESS_BAR = "show_progress_bar"
    MAX_TOTAL_TIME = "max_total_time"


def align_trace_with_process_tree(trace, tree):
    """
    Aligns a trace with a process tree using dynamic programming.
    Returns both the cost and the actual alignment.

    Based on:
    A Dynamic Programming Approach for Alignments on Process Trees
    http://processquerying.com/wp-content/uploads/2024/09/PQMI_2024_279_A_Dynamic_Programming_Approach_for_Alignments_on_Process_Trees.pdf

    """
    # Memoization tables to store costs and alignments
    CostTable = {}
    AlignmentTable = {}

    # Precompute the labels for each subtree to optimize the parallel operator
    label_cache = {}

    def get_labels(subtree):
        if subtree in label_cache:
            return label_cache[subtree]
        if subtree.operator is None:  # Leaf node
            labels = set([subtree.label]) if subtree.label is not None else set()
        else:
            labels = set()
            for child in subtree.children:
                labels.update(get_labels(child))
        label_cache[subtree] = labels
        return labels

    get_labels(tree)  # Initialize label cache

    # The main COST function with alignment tracking
    def COST(w, T):
        key = (tuple(w), id(T))
        if key in CostTable:
            return CostTable[key], AlignmentTable[key]
        if T.operator is None:  # Leaf node
            if T.label is None:  # Silent transition (tau)
                cost = len(w)  # All moves are deletions (move-on-log)
                alignment = [(a, '>>') for a in w]  # Deletion moves
            else:
                if len(w) == 0:
                    # Move-on-model (insertion)
                    cost = 1
                    alignment = [('>>', T.label)]
                elif len(w) == 1:
                    if w[0] == T.label:
                        cost = 0
                        alignment = [(w[0], w[0])]  # Synchronous move
                    else:
                        # Move-on-log and move-on-model
                        cost = 2
                        alignment = [(w[0], '>>'), ('>>', T.label)]
                else:
                    if T.label in w:
                        idx = w.index(T.label)
                        # Deletions before match, match, deletions after match
                        cost = idx + (len(w) - idx - 1)
                        alignment = [(a, '>>') for a in w[:idx]] + [(w[idx], w[idx])] + [(a, '>>') for a in w[idx + 1:]]
                    else:
                        # All deletions plus move-on-model
                        cost = len(w) + 1
                        alignment = [(a, '>>') for a in w] + [('>>', T.label)]
        elif T.operator == Operator.SEQUENCE:
            cost = float('inf')
            best_alignment = []
            # Try all possible splits
            for i in range(len(w) + 1):
                w1 = w[:i]
                w2 = w[i:]
                c1, a1 = COST(w1, T.children[0])
                c2, a2 = COST(w2, T.children[1])
                total_cost = c1 + c2
                if total_cost < cost:
                    cost = total_cost
                    alignment = a1 + a2
        elif T.operator == Operator.XOR:
            # Minimum cost between alternatives
            cost = float('inf')
            for child in T.children:
                c, a = COST(w, child)
                if c < cost:
                    cost = c
                    alignment = a
        elif T.operator == Operator.PARALLEL:
            labels_T1 = get_labels(T.children[0])
            labels_T2 = get_labels(T.children[1])
            w1 = [a for a in w if a in labels_T1]
            w2 = [a for a in w if a in labels_T2]
            w_rest = [a for a in w if a not in labels_T1 and a not in labels_T2]
            # Handle unmatched activities as move-on-log
            c1, a1 = COST(w1, T.children[0])
            c2, a2 = COST(w2, T.children[1])
            cost = c1 + c2 + len(w_rest)  # Add cost for move-on-log
            # Reconstruct alignment to match original sequence
            idx_w1 = idx_w2 = 0
            alignment = []
            for a in w:
                if a in labels_T1:
                    alignment.append(a1[idx_w1])
                    idx_w1 += 1
                elif a in labels_T2:
                    alignment.append(a2[idx_w2])
                    idx_w2 += 1
                else:
                    alignment.append((a, '>>'))  # Move-on-log
        elif T.operator == Operator.LOOP:
            n = len(w)
            # Initialize distances and predecessors
            distances = [float('inf')] * (n + 1)
            predecessors = [None] * (n + 1)
            distances[0] = 0
            # We start by trying to match T1 (initial T1 execution)
            for pos in range(n + 1):
                # Try matching T1 starting from position 0
                c_T1_start, a_T1_start = COST(w[:pos], T.children[0])
                if distances[pos] > c_T1_start:
                    distances[pos] = c_T1_start
                    predecessors[pos] = ('T1', 0, pos, a_T1_start)
            # Now expand from each position
            for i in range(n + 1):
                if distances[i] < float('inf'):
                    # Try to exit the loop by matching T1 from position i
                    c_T1_exit, a_T1_exit = COST(w[i:], T.children[0])
                    total_cost_exit = distances[i] + c_T1_exit
                    if distances[n] > total_cost_exit:
                        distances[n] = total_cost_exit
                        predecessors[n] = ('T1_exit', i, n, a_T1_exit)
                    # Try to execute the loop body T2
                    for j in range(i + 1, n + 1):
                        c_T2, a_T2 = COST(w[i:j], T.children[1])
                        total_cost_T2 = distances[i] + c_T2
                        # After T2, we must match T1 again
                        for k in range(j, n + 1):
                            c_T1_again, a_T1_again = COST(w[j:k], T.children[0])
                            total_cost_loop = total_cost_T2 + c_T1_again
                            if distances[k] > total_cost_loop:
                                distances[k] = total_cost_loop
                                predecessors[k] = ('loop', i, j, k, a_T2, a_T1_again)
            # Reconstruct alignment
            cost = distances[n]
            alignment = []
            position = n
            while position != 0:
                pred = predecessors[position]
                if pred is None:
                    break  # Cannot reconstruct alignment
                if pred[0] == 'T1_exit':
                    _, i, j, a_T1_exit = pred
                    alignment = a_T1_exit + alignment
                    position = i
                elif pred[0] == 'T1':
                    _, i, j, a_T1 = pred
                    alignment = a_T1 + alignment
                    position = i
                elif pred[0] == 'loop':
                    _, i, j, k, a_T2, a_T1_again = pred
                    alignment = a_T2 + a_T1_again + alignment
                    position = i
            CostTable[key] = cost
            AlignmentTable[key] = alignment
            return cost, alignment
        else:
            raise NotImplementedError(f"Operator {T.operator} not implemented.")

        CostTable[key] = cost
        AlignmentTable[key] = alignment
        return cost, alignment

    cost, alignment = COST(trace, tree)
    return cost, alignment


def _construct_progress_bar(progress_length, parameters):
    if exec_utils.get_param_value(Parameters.SHOW_PROGRESS_BAR, parameters,
                                  constants.SHOW_PROGRESS_BAR) and importlib.util.find_spec("tqdm"):
        if progress_length > 1:
            from tqdm.auto import tqdm
            return tqdm(total=progress_length, desc="aligning log, completed variants :: ")
    return None


def _destroy_progress_bar(progress):
    if progress is not None:
        progress.close()
    del progress


def apply_list_tuple_activities(list_tuple_activities: List[Collection[str]], process_tree: ProcessTree,
                                parameters: Optional[Dict[Any, Any]] = None) -> List[
    Dict[str, Any]]:
    if parameters is None:
        parameters = {}

    max_total_time = exec_utils.get_param_value(Parameters.MAX_TOTAL_TIME, parameters, sys.maxsize)

    process_tree = generic.process_tree_to_binary_process_tree(process_tree)

    variants = set(list_tuple_activities)
    variants_align = {}

    progress = _construct_progress_bar(len(variants), parameters)

    empty_cost, empty_moves = align_trace_with_process_tree([], process_tree)
    empty_cost = round(empty_cost + 10 ** -14, 13)

    t0 = time.time_ns()
    for v in variants:
        alignment_cost, alignment_moves = align_trace_with_process_tree(v, process_tree)
        alignment_cost = round(alignment_cost + 10 ** -14, 13)

        fitness = 1.0 - alignment_cost / (empty_cost + len(v)) if (empty_cost + len(v)) > 0 else 0.0

        alignment = {"cost": alignment_cost, "alignment": alignment_moves, "fitness": fitness}
        variants_align[v] = alignment

        if progress is not None:
            progress.update()

        t1 = time.time_ns()

        if (t1-t0)/10**9 > max_total_time:
            return None

    _destroy_progress_bar(progress)

    return [variants_align[t] for t in list_tuple_activities]


def apply(log: Union[pd.DataFrame, EventLog], process_tree: ProcessTree, parameters: Optional[Dict[Any, Any]] = None) -> \
        List[Dict[str, Any]]:
    """
    Aligns an event log against a process tree model, using the approach described in:
    Schwanen, Christopher T., Wied Pakusa, and Wil MP van der Aalst. "Process tree alignments." Enterprise Design, Operations, and Computing, ser. LNCS, Cham: Springer International Publishing (2024).
    Parameters
    ---------------
    log
        Event log or Pandas dataframe
    process_tree
        Process tree
    parameters
        Parameters of the algorithm, including:
        - Parameters.ACTIVITY_KEY => the attribute to be used as activity
        - Parameters.SHOW_PROGRESS_BAR => shows the progress bar
    Returns
    ---------------
    aligned_traces
        List that contains the alignment for each trace
    """
    if parameters is None:
        parameters = {}

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)

    list_tuple_activities = project_on_event_attribute(log, activity_key)
    list_tuple_activities = [tuple(x) for x in list_tuple_activities]

    return apply_list_tuple_activities(list_tuple_activities, process_tree, parameters=parameters)
