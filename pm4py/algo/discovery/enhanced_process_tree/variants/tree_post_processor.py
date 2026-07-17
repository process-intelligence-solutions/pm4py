from enum import Enum

from pm4py.algo.conformance.alignments.process_tree import algorithm as pt_alignments
from pm4py.algo.discovery.enhanced_process_tree.variants.base_tree_processor import BaseTreeProcessor
from pm4py.objects.process_tree.obj import Operator, EnhancedProcessTree
from pm4py.util import exec_utils


class Parameters(Enum):
    ALIGNMENT_THRESHOLD = "alignment_threshold"
    TAU_DELETION_THRESHOLD = "tau_deletion_threshold"


class TreePostProcessor(BaseTreeProcessor):
    """
    Structural modification of Process Trees based on A* alignment data.
    Uses the Order-Preservation Heuristic and Global Tau Cleanup.
    """

    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.min_occurrences = 0
        self.threshold = exec_utils.get_param_value(Parameters.ALIGNMENT_THRESHOLD, self.parameters, 0.00)
        self.tau_threshold = exec_utils.get_param_value(Parameters.TAU_DELETION_THRESHOLD, self.parameters, 1.0)

    def apply(self, log, process_tree):
        total_traces = len(log)
        self.min_occurrences = total_traces * self.threshold
        max_tau_occurrences = total_traces * self.tau_threshold

        enhanced_tree = self._convert_to_enhanced(process_tree)
        alignments = pt_alignments.apply(log, enhanced_tree, parameters=self.parameters)

        start_counts = {}
        stop_counts = {}
        skip_counts = {}

        global_node_usage = {}

        for trace_alignment in alignments:
            start_cand, stop_cand, skips, l_taus, t_taus, executed_model_nodes = self._parse_alignment_trace(trace_alignment)

            for n in executed_model_nodes:
                nid = id(n)
                if nid not in global_node_usage:
                    global_node_usage[nid] = {'node': n, 'count': 0}
                global_node_usage[nid]['count'] += 1

            if start_cand:
                sc_id = id(start_cand)
                if sc_id not in start_counts:
                    start_counts[sc_id] = {'node': start_cand, 'count': 0, 'taus': {}}
                start_counts[sc_id]['count'] += 1
                for t in l_taus:
                    start_counts[sc_id]['taus'][id(t)] = t

            if stop_cand:
                sc_id = id(stop_cand)
                if sc_id not in stop_counts:
                    stop_counts[sc_id] = {'node': stop_cand, 'count': 0, 'taus': {}}
                stop_counts[sc_id]['count'] += 1
                for t in t_taus:
                    stop_counts[sc_id]['taus'][id(t)] = t

            for skip in skips:
                trigger_id = id(skip['trigger'])
                skipped_ids = tuple(id(n) for n in skip['skipped_nodes'])
                key = (trigger_id, skipped_ids)

                if key not in skip_counts:
                    skip_counts[key] = {'data': skip, 'count': 0, 'taus': {}}
                skip_counts[key]['count'] += 1
                for n in skip['skipped_nodes']:
                    skip_counts[key]['taus'][id(n)] = n

        eligible_taus = {}

        for sc_id, data in start_counts.items():
            if data['count'] >= self.min_occurrences:
                data['node'].start = True
                eligible_taus.update(data['taus'])

        for sc_id, data in stop_counts.items():
            if data['count'] >= self.min_occurrences:
                data['node'].stop = True
                eligible_taus.update(data['taus'])

        valid_skips = []
        for data in skip_counts.values():
            if data['count'] >= self.min_occurrences:
                valid_skips.append(data['data'])
                eligible_taus.update(data['taus'])

        self._apply_skip_rules(enhanced_tree, valid_skips)

        taus_to_delete = []
        for tid, t_node in eligible_taus.items():
            tau_count = global_node_usage.get(tid, {}).get('count', 0)
            parent = t_node.parent

            # We only calculate ratios for XOR blocks.
            if parent and parent.operator == Operator.XOR:
                # How many times did execution reach this specific XOR block?
                # Sum the executions of all children inside the XOR.
                total_decision_visits = 0
                for child in parent.children:
                    total_decision_visits += global_node_usage.get(id(child), {}).get('count', 0)

                if total_decision_visits > 0:
                    usage_ratio = tau_count / total_decision_visits
                else:
                    usage_ratio = 0
            else:
                # If it's not an XOR, it shouldn't be deleted anyway
                usage_ratio = 1.1  # Force it to fail the threshold

            # If the tau usage ratio is LESS than or EQUAL to the threshold, prune it!
            if usage_ratio <= self.tau_threshold:
                taus_to_delete.append(t_node)

        self._cleanup_taus(taus_to_delete)

        if self.optimize_parallel_sequences:
            self._optimize_parallel_sequences(enhanced_tree, log)

        return enhanced_tree

    def _convert_to_enhanced(self, tree, parent=None):
        if isinstance(tree, EnhancedProcessTree):
            return tree
        enhanced_node = EnhancedProcessTree(operator=tree.operator, label=tree.label, parent=parent)
        for child in tree.children:
            enhanced_child = self._convert_to_enhanced(child, parent=enhanced_node)
            enhanced_node.children.append(enhanced_child)
        return enhanced_node

    def _parse_alignment_trace(self, alignment_dict):
        trace_alignment = alignment_dict['alignment']
        model_sequence = []
        executed_taus = []

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

                if is_model_only and getattr(model_move, 'label', None) is None:
                    executed_taus.append(model_move)

        start_candidate = None
        stop_candidate = None
        skip_groups = []
        leading_taus = []
        trailing_taus = []

        if not model_sequence:
            return None, None, [], [], [], []

        leading_count = 0
        for move in model_sequence:
            if move['is_model_only']:
                leading_count += 1
            else:
                break

        if 0 < leading_count < len(model_sequence):
            start_candidate = model_sequence[leading_count]['node']

        for i in range(leading_count):
            node = model_sequence[i]['node']
            if getattr(node, 'label', None) is None:
                leading_taus.append(node)

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

        for i in range(internal_end_idx, len(model_sequence)):
            node = model_sequence[i]['node']
            if getattr(node, 'label', None) is None:
                trailing_taus.append(node)

        m_long = []
        m_short = []
        for i in range(leading_count, internal_end_idx):
            node = model_sequence[i]['node']
            m_long.append(node)
            if not model_sequence[i]['is_model_only']:
                m_short.append(node)

        if not m_short or len(m_short) == len(m_long):
            return start_candidate, stop_candidate, [], leading_taus, trailing_taus, executed_taus

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
                        skip_groups.append({'trigger': current_trigger, 'skipped_nodes': current_skip_group})
                    current_skip_group = []
                    current_trigger = item
                    short_idx += 1
                else:
                    current_skip_group.append(item)

            if current_skip_group and current_trigger is not None:
                skip_groups.append({'trigger': current_trigger, 'skipped_nodes': current_skip_group})
        else:
            trigger_node = m_short[-1]
            skipped_nodes = [n for n in m_long if n not in m_short]
            if skipped_nodes:
                skip_groups.append({'trigger': trigger_node, 'skipped_nodes': skipped_nodes})

        executed_model_nodes = [move['node'] for move in model_sequence]

        return start_candidate, stop_candidate, skip_groups, leading_taus, trailing_taus, executed_model_nodes

    def _apply_skip_rules(self, tree, skip_candidates):
        records_by_trigger = {}

        for skip_data in skip_candidates:
            trigger = skip_data['trigger']
            if trigger is None:
                continue

            trig_id = id(trigger)
            if trig_id not in records_by_trigger:
                records_by_trigger[trig_id] = {'trigger_node': trigger, 'target_blocks': []}

            for t_node in skip_data['skipped_nodes']:
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
                b_trig = self._get_direct_child_branch(lca, trigger_node)

                b_skips_dict = {}
                for t_block in group['targets']:
                    branch = self._get_direct_child_branch(lca, t_block)
                    if branch:
                        b_skips_dict[id(branch)] = branch
                b_skips = list(b_skips_dict.values())

                if b_trig is None or not b_skips:
                    continue

                self._apply_structural_encapsulation(lca, b_trig, b_skips)
