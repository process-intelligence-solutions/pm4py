from typing import Any, Dict, List, Tuple, Union, Optional, Collection
import networkx as nx
import numpy as np
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.process_tree.utils.generic import is_leaf, is_tau_leaf
from pm4py.util.lp import solver
from pm4py.utils import project_on_event_attribute
from scipy import sparse
import pandas as pd
from pm4py.util import exec_utils
from enum import Enum
from pm4py.util import constants, xes_constants
from pm4py.objects.log.obj import EventLog
import importlib.util


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    SHOW_PROGRESS_BAR = "show_progress_bar"


class ProcessTreeAligner:
    """
    Implementation of the approach described in:

    Schwanen, Christopher T., Wied Pakusa, and Wil MP van der Aalst. "Process tree alignments." Enterprise Design, Operations, and Computing, ser. LNCS, Cham: Springer International Publishing (2024).
    """

    def __init__(self, tree: ProcessTree):
        self.tree = tree
        self.graph = nx.MultiDiGraph()
        self.node_id_counter = 0  # Initialize node ID counter
        self._build_process_tree_graph(self.tree)

    def _get_new_node_id(self) -> int:
        node_id = self.node_id_counter
        self.node_id_counter += 1
        return node_id

    def _build_process_tree_graph(self, tree: ProcessTree) -> None:
        start_node = self._get_new_node_id()
        self.graph.add_node(start_node, source=True)

        if is_tau_leaf(tree):
            self.graph.nodes[start_node]["sink"] = True
            return

        if tree.operator == Operator.LOOP:
            if len(tree.children) != 2:
                raise Exception(f"Loop {tree} does not have exactly two children")
            if is_tau_leaf(tree.children[0]):
                # Special handling when the first child of loop is a tau transition
                self.graph.nodes[start_node]["sink"] = True
                self._build_process_tree_subgraph(tree.children[1], start_node, start_node)
            else:
                end_node = self._get_new_node_id()
                self.graph.add_node(end_node, sink=True)
                self._build_process_tree_subgraph(tree.children[0], start_node, end_node)
                self._build_process_tree_subgraph(tree.children[1], end_node, start_node)
        else:
            end_node = self._get_new_node_id()
            self.graph.add_node(end_node, sink=True)
            self._build_process_tree_subgraph(tree, start_node, end_node)

    def _build_process_tree_subgraph(self, tree: ProcessTree, start_node: Any, end_node: Any, iac: int = 1) -> None:
        if tree.operator is None:
            self._build_process_tree_subgraph_leaf(tree, start_node, end_node, iac)
        elif tree.operator == Operator.SEQUENCE:
            self._build_process_tree_subgraph_sequence(tree, start_node, end_node, iac)
        elif tree.operator == Operator.XOR:
            self._build_process_tree_subgraph_xor(tree, start_node, end_node, iac)
        elif tree.operator == Operator.PARALLEL:
            self._build_process_tree_subgraph_parallel(tree, start_node, end_node, iac)
        elif tree.operator == Operator.LOOP:
            self._build_process_tree_subgraph_loop(tree, start_node, end_node, iac)
        else:
            raise Exception(f"Operator {tree.operator} is not supported")

    def _build_process_tree_subgraph_leaf(self, tree: ProcessTree, start_node: Any, end_node: Any, iac: int) -> None:
        if not is_leaf(tree):
            raise Exception(f"Subtree {tree} is not a leaf")
        self.graph.add_edge(
            start_node,
            end_node,
            label=tree.label,
            capacity=1. / iac,
            cost=iac if tree.label is not None else 0
        )

    def _build_process_tree_subgraph_sequence(self, tree: ProcessTree, start_node: Any, end_node: Any,
                                              iac: int) -> None:
        if len(tree.children) == 1:
            self._build_process_tree_subgraph(tree.children[0], start_node, end_node, iac)
            return

        nodes = [start_node] + [self._get_new_node_id() for _ in range(len(tree.children) - 1)] + [end_node]
        for i in range(len(tree.children)):
            self._build_process_tree_subgraph(tree.children[i], nodes[i], nodes[i + 1], iac)

    def _build_process_tree_subgraph_xor(self, tree: ProcessTree, start_node: Any, end_node: Any, iac: int) -> None:
        for child in tree.children:
            self._build_process_tree_subgraph(child, start_node, end_node, iac)

    def _build_process_tree_subgraph_parallel(self, tree: ProcessTree, start_node: Any, end_node: Any,
                                              iac: int) -> None:
        if tree.operator != Operator.PARALLEL:
            raise Exception(f"Operator {tree.operator} is not a parallel")

        # Ensure start_node and end_node are added to the graph
        if start_node not in self.graph.nodes:
            self.graph.add_node(start_node)
        if end_node not in self.graph.nodes:
            self.graph.add_node(end_node)

        if 'shuffle' not in self.graph.nodes[start_node]:
            self.graph.nodes[start_node]["shuffle"] = []
            self.graph.nodes[start_node]["iac"] = iac
            self.graph.nodes[start_node]["is_split"] = True
        if 'shuffle' not in self.graph.nodes[end_node]:
            self.graph.nodes[end_node]["shuffle"] = []
            self.graph.nodes[end_node]["iac"] = iac
            self.graph.nodes[end_node]["is_join"] = True

        shuffle_split = []
        shuffle_join = []
        local_iac = iac * len(tree.children)

        for child in tree.children:
            spread_node_start = self._get_new_node_id()
            spread_node_end = self._get_new_node_id()
            self.graph.add_node(spread_node_start)
            self.graph.add_node(spread_node_end)

            # Record shuffle edges
            shuffle_split.append((start_node, spread_node_start, 0))
            shuffle_join.append((spread_node_end, end_node, 0))

            # Add shuffle edges with appropriate capacity
            self.graph.add_edge(
                start_node, spread_node_start,
                label=None, capacity=1. / local_iac, cost=0, shuffle=True
            )
            self.graph.add_edge(
                spread_node_end, end_node,
                label=None, capacity=1. / local_iac, cost=0, shuffle=True
            )

            # Build subgraph for the child
            self._build_process_tree_subgraph(child, spread_node_start, spread_node_end, local_iac)

        self.graph.nodes[start_node]["shuffle"].append(shuffle_split)
        self.graph.nodes[end_node]["shuffle"].append(shuffle_join)

    def _build_process_tree_subgraph_loop(self, tree: ProcessTree, start_node: Any, end_node: Any, iac: int) -> None:
        old_start_node = start_node
        start_node = self._get_new_node_id()
        self.graph.add_node(start_node)
        self.graph.add_edge(
            old_start_node, start_node,
            label=None, capacity=1. / iac, cost=0
        )
        old_end_node = end_node
        end_node = self._get_new_node_id()
        self.graph.add_node(end_node)
        self.graph.add_edge(
            end_node, old_end_node,
            label=None, capacity=1. / iac, cost=0
        )

        self._build_process_tree_subgraph(tree.children[0], start_node, end_node, iac)
        self._build_process_tree_subgraph(tree.children[1], end_node, start_node, iac)

    def align(self, trace: List[str]) -> Tuple[float, List[Tuple[str, str]]]:
        align_variant = "pulp"

        num_steps = len(trace) + 1
        graph = self.graph

        edges = list(graph.edges(keys=True))
        nodes = list(graph.nodes())

        # Variable indexing
        var_index = {}
        var_counter = 0

        x_vars = {}  # Flow variables
        y_vars = {}  # Log move variables
        z_vars = {}  # Sync move variables
        s_vars = {}  # Shuffle variables

        # x variables
        for i in range(num_steps):
            for e in edges:
                x_vars[(i,) + e] = var_counter
                var_index[var_counter] = ('x', i, e)
                var_counter += 1

        # y variables (continuous between 0 and 1)
        for i in range(1, num_steps):
            for v in nodes:
                y_vars[(i, v)] = var_counter
                var_index[var_counter] = ('y', i, v)
                var_counter += 1

        # z variables (continuous between 0 and capacity)
        sync_edges = {}
        for idx, activity in enumerate(trace):
            step = idx + 1
            matching_edges = [e for e in edges if graph.edges[e].get('label') == activity]
            sync_edges[step] = matching_edges
            for e in matching_edges:
                z_vars[(step,) + e] = var_counter
                var_index[var_counter] = ('z', step, e)
                var_counter += 1

        # s variables (binary)
        shuffles = {}
        for v in nodes:
            node_data = graph.nodes[v]
            if node_data.get('shuffle'):
                for idx, shuffle_edges in enumerate(node_data['shuffle']):
                    shuffles[(v, idx)] = shuffle_edges
        for i in range(num_steps):
            for key in shuffles.keys():
                s_vars[(i, key)] = var_counter
                var_index[var_counter] = ('s', i, key)
                var_counter += 1

        num_vars = var_counter

        # Objective function coefficients
        c = np.zeros(num_vars)

        # For x variables
        for key, idx in x_vars.items():
            i, u, v, k = key
            cost = graph.edges[(u, v, k)].get('cost', 0)
            c[idx] = cost

        # For y variables
        for idx in y_vars.values():
            c[idx] = 1

        # For z variables
        for key, idx in z_vars.items():
            step, u, v, k = key
            edge_cost = graph.edges[(u, v, k)].get('cost', 0)
            c[idx] = 1 - edge_cost if edge_cost > 1 else 0

        # Constraints
        Aeq_rows = []
        beq = []

        # Flow conservation constraints
        for i in range(num_steps):
            for v in nodes:
                row = {}
                rhs = 0

                # Sum of inflow arcs
                for e in edges:
                    if e[1] == v:
                        idx = x_vars.get((i,) + e)
                        if idx is not None:
                            row[idx] = row.get(idx, 0) + 1

                # Sum of outflow arcs
                for e in edges:
                    if e[0] == v:
                        idx = x_vars.get((i,) + e)
                        if idx is not None:
                            row[idx] = row.get(idx, 0) - 1

                # Add y and z variables
                if i > 0:
                    idx_y = y_vars.get((i, v))
                    if idx_y is not None:
                        row[idx_y] = row.get(idx_y, 0) + 1
                    for e in edges:
                        if e[1] == v:
                            idx_z = z_vars.get((i,) + e)
                            if idx_z is not None:
                                row[idx_z] = row.get(idx_z, 0) + 1
                if i < num_steps - 1:
                    idx_y = y_vars.get((i + 1, v))
                    if idx_y is not None:
                        row[idx_y] = row.get(idx_y, 0) - 1
                    for e in edges:
                        if e[0] == v:
                            idx_z = z_vars.get((i + 1,) + e)
                            if idx_z is not None:
                                row[idx_z] = row.get(idx_z, 0) - 1

                # Handle source and sink nodes
                if i == 0 and graph.nodes[v].get('source'):
                    rhs = -1
                elif i == len(trace) and graph.nodes[v].get('sink'):
                    rhs = 1

                if row:
                    Aeq_rows.append((row, rhs))

        # Shuffle constraints
        for key, shuffle_edges in shuffles.items():
            v, idx = key
            iac = graph.nodes[v]['iac']
            for i in range(num_steps):
                row = {}
                for u, w, _ in shuffle_edges:
                    edge = (u, w, 0)
                    idx_x = x_vars.get((i,) + edge)
                    if idx_x is not None:
                        row[idx_x] = row.get(idx_x, 0) + 1
                idx_s = s_vars.get((i, key))
                if idx_s is not None:
                    row[idx_s] = row.get(idx_s, 0) - (1.0 / iac)
                Aeq_rows.append((row, 0))

        # Duplicate labels constraints
        Aub_rows = []
        bub = []
        for i in sync_edges:
            if len(sync_edges[i]) > 1:
                row = {}
                for e in sync_edges[i]:
                    idx_z = z_vars.get((i,) + e)
                    if idx_z is not None:
                        edge_cost = graph.edges[e].get('cost', 0)
                        row[idx_z] = edge_cost
                Aub_rows.append((row, 1))

        # Variable bounds
        lb = np.zeros(num_vars)
        ub = np.full(num_vars, np.inf)

        # x variables
        for key, idx in x_vars.items():
            i, u, v, k = key
            capacity = graph.edges[(u, v, k)].get('capacity', np.inf)
            ub[idx] = capacity

        # y variables
        for idx in y_vars.values():
            ub[idx] = 1

        # z variables
        for key, idx in z_vars.items():
            i, u, v, k = key
            capacity = graph.edges[(u, v, k)].get('capacity', np.inf)
            ub[idx] = capacity

        # s variables
        for idx in s_vars.values():
            ub[idx] = 1
            lb[idx] = 0

        # Variable types
        vartype = [0] * num_vars
        for idx in s_vars.values():
            vartype[idx] = 1

        # Build Aeq
        Aeq_data = []
        Aeq_row_idx = []
        Aeq_col_idx = []
        for row_idx, (row, rhs_value) in enumerate(Aeq_rows):
            for var_idx, coeff in row.items():
                Aeq_data.append(coeff)
                Aeq_row_idx.append(row_idx)
                Aeq_col_idx.append(var_idx)
            beq.append(rhs_value)

        Aeq = sparse.csr_matrix((Aeq_data, (Aeq_row_idx, Aeq_col_idx)), shape=(len(Aeq_rows), num_vars))

        # Build Aub
        Aub_data = []
        Aub_row_idx = []
        Aub_col_idx = []
        for row_idx, (row, rhs_value) in enumerate(Aub_rows):
            for var_idx, coeff in row.items():
                Aub_data.append(coeff)
                Aub_row_idx.append(row_idx)
                Aub_col_idx.append(var_idx)
            bub.append(rhs_value)

        Aeq = Aeq.toarray()

        Aub = sparse.csr_matrix((Aub_data, (Aub_row_idx, Aub_col_idx)), shape=(len(Aub_rows), num_vars))
        Aub = Aub.toarray()

        # Solver parameters
        bounds = [(lb[i], ub[i]) for i in range(num_vars)]
        parameters = {
            'bounds': bounds,
            'integrality': vartype,
        }

        c = [float(x) for x in c]
        bub = [float(x) for x in bub]
        beq = [float(x) for x in beq]

        if align_variant == "cvxopt_solver_custom_align_ilp":
            del parameters["bounds"]

            Aub_add = np.zeros((2 * len(bounds), len(c)))

            for idx, b in enumerate(bounds):
                Aub_add[2 * idx, idx] = -1.0
                Aub_add[2 * idx + 1, idx] = 1.0
                bub.append(-b[0])
                bub.append(b[1])

            Aub = np.vstack([Aub, Aub_add])

            bub = np.asarray(bub)[:, np.newaxis]
            beq = np.asarray(beq)[:, np.newaxis]

            from cvxopt import matrix

            Aub = matrix(Aub.astype(np.float64))
            bub = matrix(bub)
            Aeq = matrix(Aeq.astype(np.float64))
            beq = matrix(beq)
            c = matrix(c)

        # Solve the LP problem
        try:
            sol = solver.apply(c, Aub, bub, Aeq, beq, variant=align_variant, parameters=parameters)

            prim_obj = solver.get_prim_obj_from_sol(sol, variant=align_variant)
            var_values = solver.get_points_from_sol(sol, variant=align_variant)

            # Reconstruct the alignment moves
            alignment_moves = []
            i = 1  # Start from step 1
            while i <= len(trace):
                activity = trace[i - 1]
                move_recorded = False

                # Check for synchronous moves (z variables)
                for e in sync_edges.get(i, []):
                    idx_z = z_vars.get((i,) + e)
                    if idx_z is not None and var_values[idx_z] > 1e-5:
                        # Synchronous move
                        alignment_moves.append((activity, activity))
                        move_recorded = True
                        break

                if move_recorded:
                    i += 1
                    continue

                # Check for moves on log (y variables)
                for v in nodes:
                    idx_y = y_vars.get((i, v))
                    if idx_y is not None and var_values[idx_y] > 1e-5:
                        alignment_moves.append((activity, '>>'))
                        move_recorded = True
                        break

                if move_recorded:
                    i += 1
                    continue

                # If neither z nor y variables are active, it's a move on model
                # Find active x variables at position i
                model_moves = []
                for e in edges:
                    idx_x = x_vars.get((i,) + e)
                    if idx_x is not None and var_values[idx_x] > 1e-5:
                        label = graph.edges[e].get('label')
                        if label is not None and label not in model_moves:
                            model_moves.append(label)
                if model_moves:
                    for label in model_moves:
                        alignment_moves.append(('>>', label))
                    i += 1  # Advance to the next step
                else:
                    # No move detected; advance to prevent infinite loop
                    alignment_moves.append((activity, '>>'))
                    i += 1

            return prim_obj, alignment_moves
        except Exception as e:
            raise Exception(f"Optimization failed: {str(e)}")


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


def apply_list_tuple_activities(list_tuple_activities: List[Collection[str]], aligner: ProcessTreeAligner,
                                parameters: Optional[Dict[Any, Any]] = None) -> List[
    Dict[str, Any]]:
    if parameters is None:
        parameters = {}

    variants = set(list_tuple_activities)
    variants_align = {}

    progress = _construct_progress_bar(len(variants), parameters)

    empty_cost, empty_moves = aligner.align([])
    empty_cost = round(empty_cost + 10 ** -14, 13)

    for v in variants:
        alignment_cost, alignment_moves = aligner.align(v)
        alignment_cost = round(alignment_cost + 10 ** -14, 13)

        fitness = 1.0 - alignment_cost / (empty_cost + len(v)) if (empty_cost + len(v)) > 0 else 0.0

        alignment = {"cost": alignment_cost, "alignment": alignment_moves, "fitness": fitness}
        variants_align[v] = alignment

        if progress is not None:
            progress.update()

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

    aligner = ProcessTreeAligner(process_tree)

    return apply_list_tuple_activities(list_tuple_activities, aligner, parameters=parameters)
