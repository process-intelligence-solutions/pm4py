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
from enum import Enum

from pm4py.objects.process_tree.obj import Operator, EnhancedProcessTree
from pm4py.util import exec_utils


class Parameters(Enum):
    OPTIMIZE_PARALLEL_SEQUENCES = "optimize_parallel_sequences"

class BaseTreeProcessor:
    """
    Master class containing shared tree-traversal algorithms and
    structural encapsulation logic for Process Tree mutation.
    """

    def __init__(self, parameters=None):
        self.parameters = parameters if parameters is not None else {}
        self.optimize_parallel_sequences = exec_utils.get_param_value(
            Parameters.OPTIMIZE_PARALLEL_SEQUENCES, self.parameters, False)

    def _apply_structural_encapsulation(self, lca, b_trig, b_skips):
        """
        Executes the shared core logic for encapsulating sequences or marking parallel blocks.
        """
        if lca.operator in [Operator.PARALLEL, Operator.XOR]:
            b_trig.skip = True

        elif lca.operator == Operator.SEQUENCE:
            if b_trig in b_skips:
                b_trig.skip = True
            else:
                try:
                    idx_trig = lca.children.index(b_trig)
                    indices_skip = [lca.children.index(bs) for bs in b_skips]

                    all_indices = [idx_trig] + indices_skip
                    min_idx = min(all_indices)
                    max_idx = max(all_indices)

                    nodes_to_encapsulate = lca.children[min_idx: max_idx + 1]

                    if len(nodes_to_encapsulate) == len(lca.children) or getattr(b_trig, '_is_wrapper', False):
                        b_trig.skip = True
                    else:
                        new_seq = EnhancedProcessTree(operator=Operator.SEQUENCE, parent=lca)
                        new_seq._is_wrapper = True
                        for node in nodes_to_encapsulate:
                            lca.children.remove(node)
                            new_seq.children.append(node)
                            node.parent = new_seq

                        b_trig.skip = True
                        lca.children.insert(min_idx, new_seq)
                except ValueError:
                    pass

    def _cleanup_taus(self, taus_to_delete):
        """
        Global Tau Cleanup Phase.
        Executes structurally safe deletion of tau nodes and collapses wrappers.
        """
        for t_node in taus_to_delete:
            if getattr(t_node, 'label', None) is not None:
                continue

            bypassed_block = getattr(t_node, 'parent', None)

            if not bypassed_block or bypassed_block.operator == Operator.LOOP:
                continue

            if t_node in bypassed_block.children:
                bypassed_block.children.remove(t_node)

            if len(bypassed_block.children) == 1:
                single_child = bypassed_block.children[0]
                bb_parent = bypassed_block.parent
                if bb_parent is not None:
                    try:
                        if getattr(bypassed_block, 'skip', False):
                            single_child.skip = True
                        if getattr(bypassed_block, 'start', False):
                            single_child.start = True
                        if getattr(bypassed_block, 'stop', False):
                            single_child.stop = True

                        bb_idx = bb_parent.children.index(bypassed_block)
                        bb_parent.children[bb_idx] = single_child
                        single_child.parent = bb_parent
                    except ValueError:
                        pass

    def _optimize_parallel_sequences(self, tree, log):
        """
        Executes Intra-Block Causality Analysis.
        Automatically converts the log, finds loose activities inside PARALLEL blocks,
        and groups them into SEQUENCE blocks if they exhibit Eventual Precedence.
        Safely cascades structural routing properties (skip) up the hierarchy.
        """
        from pm4py.algo.discovery.enhanced_process_tree.algorithm import Parameters

        simplified_log = []
        if isinstance(log, dict):
            simplified_log = [list(trace) for trace in log.keys()]
        else:
            import pm4py
            ack = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, self.parameters, "concept:name")
            variants = pm4py.get_variants(log, activity_key=ack)
            simplified_log = [list(trace) for trace in variants.keys()]

        parallel_blocks = self._get_all_blocks_of_type(tree, Operator.PARALLEL)

        for p_block in parallel_blocks:
            leaf_children = [child for child in p_block.children if
                             child.label is not None and len(child.children) == 0]

            if len(leaf_children) < 2:
                continue

            labels = {child.label: child for child in leaf_children}
            label_names = list(labels.keys())

            co_occurrence = {a: {b: False for b in label_names} for a in label_names}
            x_before_y = {a: {b: True for b in label_names} for a in label_names}

            for trace in simplified_log:
                events = [act for act in trace if act in label_names]

                if len(events) < 2:
                    continue

                for i in range(len(events)):
                    for j in range(i + 1, len(events)):
                        x = events[i]
                        y = events[j]

                        co_occurrence[x][y] = True
                        co_occurrence[y][x] = True
                        x_before_y[y][x] = False

            strict_precedence = {a: set() for a in label_names}
            for x in label_names:
                for y in label_names:
                    if x != y and co_occurrence[x][y]:
                        if x_before_y[x][y] and not x_before_y[y][x]:
                            strict_precedence[x].add(y)

            direct_outgoing = {a: [] for a in label_names}
            direct_incoming = {a: [] for a in label_names}

            for x in label_names:
                for y in strict_precedence[x]:
                    is_direct = True
                    for z in strict_precedence[x]:
                        if z != y and y in strict_precedence[z]:
                            is_direct = False
                            break
                    if is_direct:
                        direct_outgoing[x].append(y)
                        direct_incoming[y].append(x)

            linear_next = {}
            for x, outs in direct_outgoing.items():
                if len(outs) == 1:
                    y = outs[0]
                    if len(direct_incoming[y]) == 1:
                        linear_next[x] = y

            chains = []
            assigned = set()
            for x in label_names:
                if x in assigned: continue
                if x in linear_next and x not in linear_next.values():
                    chain = [x]
                    curr = x
                    while curr in linear_next:
                        assigned.add(curr)
                        curr = linear_next[curr]
                        chain.append(curr)
                        assigned.add(curr)
                    chains.append(chain)

            for chain in chains:
                nodes_in_chain = [labels[lbl] for lbl in chain]

                for node in nodes_in_chain:
                    p_block.children.remove(node)

                seq_block = EnhancedProcessTree(operator=Operator.SEQUENCE, parent=p_block)
                for node in nodes_in_chain:
                    seq_block.children.append(node)
                    node.parent = seq_block

                if any(getattr(node, 'skip', False) for node in nodes_in_chain):
                    seq_block.skip = True

                    last_node = nodes_in_chain[-1]
                    if getattr(last_node, 'skip', False):
                        last_node.skip = False

                p_block.children.append(seq_block)

    def _get_all_blocks_of_type(self, tree, operator_type):
        """Helper to recursively fetch all blocks of a specific operator."""
        blocks = []
        if tree.operator == operator_type:
            blocks.append(tree)
        for child in tree.children:
            blocks.extend(self._get_all_blocks_of_type(child, operator_type))
        return blocks

    def _find_node_by_label(self, tree, label):
        if tree.label == label:
            return tree
        for child in tree.children:
            found = self._find_node_by_label(child, label)
            if found:
                return found
        return None

    def _get_lca(self, node_a, node_b):
        if node_a is None or node_b is None:
            return None
        ancestors_a = []
        curr = node_a
        while curr is not None:
            ancestors_a.append(curr)
            curr = curr.parent
        curr = node_b
        while curr is not None:
            if curr in ancestors_a:
                return curr
            curr = curr.parent
        return None

    def _get_direct_child_branch(self, lca_node, descendant_node):
        curr = descendant_node
        while curr is not None and getattr(curr, 'parent', None) != lca_node:
            curr = curr.parent
        return curr

    def _get_depth(self, node):
        depth = 0
        curr = node
        while curr.parent is not None:
            depth += 1
            curr = curr.parent
        return depth

    def _get_all_leaves(self, tree):
        leaves = []
        if tree.children:
            for child in tree.children:
                leaves.extend(self._get_all_leaves(child))
        else:
            if tree.label is not None:
                leaves.append(tree)
        return leaves
