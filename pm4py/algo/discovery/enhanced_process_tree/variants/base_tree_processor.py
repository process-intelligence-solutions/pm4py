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
from pm4py.objects.process_tree.obj import Operator, EnhancedProcessTree


class BaseTreeProcessor:
    """
    Master class containing shared tree-traversal algorithms and
    structural encapsulation logic for Process Tree mutation.
    """

    def __init__(self, parameters=None):
        self.parameters = parameters if parameters is not None else {}

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
