from enum import Enum
from pm4py.util import exec_utils
from pm4py.algo.conformance.alignments.process_tree import algorithm as pt_alignments
from pm4py.objects.process_tree.obj import Operator, EnhancedProcessTree


class Parameters(Enum):
    THRESHOLD = "threshold"


class TreePostProcessor:
    """
    Internal class to handle the structural modification of Process Trees
    based on alignment data. Uses the Order-Preservation Heuristic to group
    alignment tau moves, mirroring the logic of the Hybrid approach.
    """

    def __init__(self, parameters=None):
        self.min_occurrences = 0
        self.parameters = parameters if parameters is not None else {}
        self.threshold = exec_utils.get_param_value(Parameters.THRESHOLD, self.parameters, 0.05)

    def apply(self, log, process_tree):
        total_traces = len(log)
        self.min_occurrences = total_traces * self.threshold

        enhanced_tree = self._convert_to_enhanced(process_tree)

        alignments = pt_alignments.apply(log, enhanced_tree, parameters=self.parameters)

        start_counts = {}
        stop_counts = {}
        skip_list = []

        for trace_alignment in alignments:
            start_cand, stop_cand, skips = self._parse_alignment_trace(trace_alignment)

            if start_cand:
                start_counts[start_cand] = start_counts.get(start_cand, 0) + 1
            if stop_cand:
                stop_counts[stop_cand] = stop_counts.get(stop_cand, 0) + 1

            skip_list.extend(skips)

        for node, count in start_counts.items():
            if count >= self.min_occurrences:
                node.start = True

        for node, count in stop_counts.items():
            if count >= self.min_occurrences:
                node.stop = True

        skip_counts = {}
        for skip in skip_list:
            trigger_id = id(skip['trigger'])
            skipped_ids = tuple(id(n) for n in skip['skipped_nodes'])
            key = (trigger_id, skipped_ids)

            if key not in skip_counts:
                skip_counts[key] = {'data': skip, 'count': 0}
            skip_counts[key]['count'] += 1

        valid_skips = [v['data'] for v in skip_counts.values() if v['count'] >= self.min_occurrences]

        self._apply_skip_rules(enhanced_tree, valid_skips)

        return enhanced_tree

    def _convert_to_enhanced(self, tree, parent=None):
        if isinstance(tree, EnhancedProcessTree):
            return tree

        enhanced_node = EnhancedProcessTree(
            operator=tree.operator,
            label=tree.label,
            parent=parent
        )

        for child in tree.children:
            enhanced_child = self._convert_to_enhanced(child, parent=enhanced_node)
            enhanced_node.children.append(enhanced_child)

        return enhanced_node

    def _get_depth(self, node):
        depth = 0
        curr = node
        while curr.parent is not None:
            depth += 1
            curr = curr.parent
        return depth

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

    def _parse_alignment_trace(self, alignment_dict):
        """
        Parses alignment moves and applies the Order-Preservation heuristic
        to accurately group missing nodes and assign triggers.
        """
        trace_alignment = alignment_dict['alignment']
        model_sequence = []

        for log_move, model_move in trace_alignment:
            if model_move != '>>' and model_move is not None:
                if getattr(model_move, 'label', None) is None:
                    parent = getattr(model_move, 'parent', None)
                    if parent and parent.operator == Operator.LOOP:
                        continue
                is_model_only = (log_move == '>>')
                model_sequence.append({
                    'node': model_move,
                    'is_model_only': is_model_only
                })

        start_candidate = None
        stop_candidate = None
        skip_groups = []

        if not model_sequence:
            return None, None, []

        leading_count = 0
        for move in model_sequence:
            if move['is_model_only']:
                leading_count += 1
            else:
                break

        if 0 < leading_count < len(model_sequence):
            start_candidate = model_sequence[leading_count]['node']

        trailing_count = 0
        for move in reversed(model_sequence):
            if move['is_model_only']:
                trailing_count += 1
            else:
                break

        if trailing_count > 0:
            last_visible_idx = len(model_sequence) - trailing_count - 1
            if last_visible_idx >= 0:
                stop_candidate = model_sequence[last_visible_idx]['node']

        internal_end_idx = len(model_sequence) - trailing_count

        m_long = []
        m_short = []
        for i in range(leading_count, internal_end_idx):
            node = model_sequence[i]['node']
            m_long.append(node)
            if not model_sequence[i]['is_model_only']:
                m_short.append(node)

        if not m_short or len(m_short) == len(m_long):
            return start_candidate, stop_candidate, []

        is_ordered = True
        last_idx = -1
        for item in m_short:
            try:
                idx = m_long.index(item, last_idx + 1)
                last_idx = idx
            except ValueError:
                is_ordered = False
                break

        if is_ordered:
            short_idx = 0
            current_trigger = start_candidate if leading_count > 0 else None
            current_skip_group = []

            for item in m_long:
                if short_idx < len(m_short) and item == m_short[short_idx]:
                    if current_skip_group and current_trigger is not None:
                        skip_groups.append({
                            'trigger': current_trigger,
                            'skipped_nodes': current_skip_group
                        })
                    current_skip_group = []
                    current_trigger = item
                    short_idx += 1
                else:
                    current_skip_group.append(item)

            if current_skip_group and current_trigger is not None:
                skip_groups.append({
                    'trigger': current_trigger,
                    'skipped_nodes': current_skip_group
                })
        else:
            trigger_node = m_short[-1]
            skipped_nodes = [n for n in m_long if n not in m_short]
            if skipped_nodes:
                skip_groups.append({
                    'trigger': trigger_node,
                    'skipped_nodes': skipped_nodes
                })

        return start_candidate, stop_candidate, skip_groups

    def _apply_skip_rules(self, tree, skip_candidates):
        records_by_trigger = {}
        all_taus_dict = {}

        for skip_data in skip_candidates:
            trigger = skip_data['trigger']
            if trigger is None:
                continue

            trig_id = id(trigger)
            if trig_id not in records_by_trigger:
                records_by_trigger[trig_id] = {'trigger_node': trigger, 'target_blocks': []}

            for t_node in skip_data['skipped_nodes']:
                all_taus_dict[id(t_node)] = t_node

                bypassed_block = getattr(t_node, 'parent', None)
                if bypassed_block is None:
                    continue

                if bypassed_block not in records_by_trigger[trig_id]['target_blocks']:
                    records_by_trigger[trig_id]['target_blocks'].append(bypassed_block)

        for record in records_by_trigger.values():
            trigger_node = record['trigger_node']
            target_blocks = record['target_blocks']

            lca_groups = {}
            for t_block in target_blocks:
                lca = self._get_lca(trigger_node, t_block)
                if lca is not None:
                    lca_id = id(lca)
                    if lca_id not in lca_groups:
                        lca_groups[lca_id] = {'lca_node': lca, 'targets': []}
                    lca_groups[lca_id]['targets'].append(t_block)

            sorted_groups = sorted(
                lca_groups.values(),
                key=lambda group: self._get_depth(group['lca_node']),
                reverse=True
            )

            for group in sorted_groups:
                lca = group['lca_node']
                targets = group['targets']

                b_trig = self._get_direct_child_branch(lca, trigger_node)

                b_skips_set = set()
                for t_block in targets:
                    branch = self._get_direct_child_branch(lca, t_block)
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

                            if len(nodes_to_encapsulate) == len(lca.children) or getattr(b_trig, '_is_wrapper', False):
                                b_trig.skip = True
                            else:
                                new_seq = EnhancedProcessTree(operator=Operator.SEQUENCE, parent=lca)
                                new_seq._is_wrapper = True  # Tag the sequence so it cannot be swallowed again

                                for node in nodes_to_encapsulate:
                                    lca.children.remove(node)
                                    new_seq.children.append(node)
                                    node.parent = new_seq

                                b_trig.skip = True
                                lca.children.insert(min_idx, new_seq)
                        except ValueError:
                            continue

        for t_node in all_taus_dict.values():

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

def apply(log, process_tree, parameters=None):
    processor = TreePostProcessor(parameters=parameters)
    return processor.apply(log, process_tree)