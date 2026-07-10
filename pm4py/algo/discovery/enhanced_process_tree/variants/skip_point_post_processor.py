from pm4py.objects.process_tree.obj import Operator, EnhancedProcessTree


class SkipPointPostProcessor:
    """
    Applies structural skip annotations to an EnhancedProcessTree using
    topological context (skip_records) passed directly from Log Refinement,
    bypassing the need for conformance alignments.
    """

    def __init__(self, parameters=None):
        self.parameters = parameters if parameters is not None else {}

    def apply(self, enhanced_tree: EnhancedProcessTree, skip_records: list) -> EnhancedProcessTree:
        for skip_data in skip_records:
            trigger_label = skip_data.get('trigger_label')
            skipped_labels = skip_data.get('skipped_labels', [])

            if not trigger_label or not skipped_labels:
                continue

            trigger_node = self._find_node_by_label(enhanced_tree, trigger_label)

            skipped_nodes = []
            for lbl in skipped_labels:
                found_node = self._find_node_by_label(enhanced_tree, lbl)
                if found_node is not None:
                    skipped_nodes.append(found_node)

            if trigger_node is None or not skipped_nodes:
                continue

            # 1. Group skipped nodes by their specific LCA with the trigger
            lca_groups = {}
            for s_node in skipped_nodes:
                lca = self._get_lca(trigger_node, s_node)
                if lca is not None:
                    lca_id = id(lca)
                    if lca_id not in lca_groups:
                        lca_groups[lca_id] = {'lca_node': lca, 'target_nodes': []}
                    lca_groups[lca_id]['target_nodes'].append(s_node)

            # 2. Sort LCAs by depth to ensure bottom-up cascading resolution
            sorted_groups = sorted(
                lca_groups.values(),
                key=lambda group: self._get_depth(group['lca_node']),
                reverse=True
            )

            # 3. Process each topological layer independently
            for group in sorted_groups:
                lca = group['lca_node']
                target_nodes = group['target_nodes']

                b_trig = self._get_direct_child_branch(lca, trigger_node)

                # ... (the rest of your rule logic remains exactly the same starting from here) ...
                b_skips_set = set()
                for s_node in target_nodes:
                    branch = self._get_direct_child_branch(lca, s_node)
                    if branch:
                        b_skips_set.add(branch)
                b_skips = list(b_skips_set)

                if b_trig is None or not b_skips:
                    continue

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

                            if len(nodes_to_encapsulate) == len(lca.children):
                                b_trig.skip = True
                            else:
                                new_seq = EnhancedProcessTree(operator=Operator.SEQUENCE, parent=lca)
                                for node in nodes_to_encapsulate:
                                    lca.children.remove(node)
                                    new_seq.children.append(node)
                                    node.parent = new_seq

                                b_trig.skip = True

                                lca.children.insert(min_idx, new_seq)
                        except ValueError:
                            continue

        return enhanced_tree

    # --- Helper Functions ---

    def _find_node_by_label(self, tree, label):
        """Recursively searches the tree to find a leaf node matching the label."""
        if tree.label == label:
            return tree
        for child in tree.children:
            found = self._find_node_by_label(child, label)
            if found:
                return found
        return None

    def _get_lca(self, node_a, node_b):
        """Finds the Lowest Common Ancestor block between two nodes."""
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
        """Travels up the parent pointers to find the branch directly under the LCA."""
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