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

        return enhanced_tree
