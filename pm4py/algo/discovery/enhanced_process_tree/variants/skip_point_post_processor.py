from pm4py.algo.discovery.enhanced_process_tree.variants.base_tree_processor import BaseTreeProcessor
from pm4py.objects.process_tree.obj import Operator, EnhancedProcessTree


class SkipPointPostProcessor(BaseTreeProcessor):
    """
    Applies structural skip annotations to an EnhancedProcessTree using
    topological context (skip_records) passed directly from Log Refinement,
    bypassing the need for conformance alignments.
    """

    def __init__(self, parameters=None):
        super().__init__(parameters)

    def apply(self, enhanced_tree: EnhancedProcessTree, skip_records: list) -> EnhancedProcessTree:
        valid_trigger_groups = {}

        for skip_data in skip_records:
            trigger_label = skip_data.get('trigger_label')
            skipped_labels = skip_data.get('skipped_labels', [])

            if not trigger_label or not skipped_labels:
                continue

            trigger_node = self._find_node_by_label(enhanced_tree, trigger_label)
            if not trigger_node:
                continue

            for lbl in skipped_labels:
                s_node = self._find_node_by_label(enhanced_tree, lbl)
                if not s_node:
                    continue

                lca = self._get_lca(trigger_node, s_node)
                if lca is None:
                    continue

                b_skip = self._get_direct_child_branch(lca, s_node)

                b_skip_leaves = self._get_all_leaves(b_skip)
                b_skip_labels = {leaf.label for leaf in b_skip_leaves if leaf.label}
                skipped_set = set(skipped_labels)

                if not b_skip_labels.issubset(skipped_set):
                    continue

                trig_id = id(trigger_node)
                if trig_id not in valid_trigger_groups:
                    valid_trigger_groups[trig_id] = {'trigger_node': trigger_node, 'target_nodes': []}

                if s_node not in valid_trigger_groups[trig_id]['target_nodes']:
                    valid_trigger_groups[trig_id]['target_nodes'].append(s_node)

        for group in valid_trigger_groups.values():
            trigger_node = group['trigger_node']
            target_nodes = group['target_nodes']

            lca_groups = {}
            for s_node in target_nodes:
                lca = self._get_lca(trigger_node, s_node)
                if lca is not None:
                    lca_id = id(lca)
                    if lca_id not in lca_groups:
                        lca_groups[lca_id] = {'lca_node': lca, 'target_nodes': []}
                    lca_groups[lca_id]['target_nodes'].append(s_node)

            sorted_groups = sorted(
                lca_groups.values(),
                key=lambda group: self._get_depth(group['lca_node']),
                reverse=True
            )

            for group in sorted_groups:
                lca = group['lca_node']
                target_nodes = group['target_nodes']

                b_trig = self._get_direct_child_branch(lca, trigger_node)

                b_skips_set = set()
                for s_node in target_nodes:
                    branch = self._get_direct_child_branch(lca, s_node)
                    if branch:
                        b_skips_set.add(branch)
                b_skips = list(b_skips_set)

                if b_trig is None or not b_skips:
                    continue

                self._apply_structural_encapsulation(lca, b_trig, b_skips)

                # if lca.operator in [Operator.PARALLEL, Operator.XOR]:
                #     b_trig.skip = True
                #
                # elif lca.operator == Operator.SEQUENCE:
                #     if b_trig in b_skips:
                #         b_trig.skip = True
                #     else:
                #         try:
                #             idx_trig = lca.children.index(b_trig)
                #             indices_skip = [lca.children.index(bs) for bs in b_skips]
                #
                #             all_indices = [idx_trig] + indices_skip
                #             min_idx = min(all_indices)
                #             max_idx = max(all_indices)
                #
                #             nodes_to_encapsulate = lca.children[min_idx: max_idx + 1]
                #
                #             if len(nodes_to_encapsulate) == len(lca.children) or getattr(b_trig, '_is_wrapper', False):
                #                 b_trig.skip = True
                #             else:
                #                 new_seq = EnhancedProcessTree(operator=Operator.SEQUENCE, parent=lca)
                #                 new_seq._is_wrapper = True
                #                 for node in nodes_to_encapsulate:
                #                     lca.children.remove(node)
                #                     new_seq.children.append(node)
                #                     node.parent = new_seq
                #
                #                 b_trig.skip = True
                #                 lca.children.insert(min_idx, new_seq)
                #         except ValueError:
                #             continue

        return enhanced_tree

    # def _find_node_by_label(self, tree, label):
    #     """Recursively searches the tree to find a leaf node matching the label."""
    #     if tree.label == label:
    #         return tree
    #     for child in tree.children:
    #         found = self._find_node_by_label(child, label)
    #         if found:
    #             return found
    #     return None
    #
    # def _get_lca(self, node_a, node_b):
    #     """Finds the Lowest Common Ancestor block between two nodes."""
    #     if node_a is None or node_b is None:
    #         return None
    #     ancestors_a = []
    #     curr = node_a
    #     while curr is not None:
    #         ancestors_a.append(curr)
    #         curr = curr.parent
    #     curr = node_b
    #     while curr is not None:
    #         if curr in ancestors_a:
    #             return curr
    #         curr = curr.parent
    #     return None
    #
    # def _get_direct_child_branch(self, lca_node, descendant_node):
    #     """Travels up the parent pointers to find the branch directly under the LCA."""
    #     curr = descendant_node
    #     while curr is not None and getattr(curr, 'parent', None) != lca_node:
    #         curr = curr.parent
    #     return curr
    #
    # def _get_depth(self, node):
    #     depth = 0
    #     curr = node
    #     while curr.parent is not None:
    #         depth += 1
    #         curr = curr.parent
    #     return depth
    #
    # def _get_all_leaves(self, tree):
    #     leaves = []
    #     if tree.children:
    #         for child in tree.children:
    #             leaves.extend(self._get_all_leaves(child))
    #     else:
    #         if tree.label is not None:
    #             leaves.append(tree)
    #     return leaves