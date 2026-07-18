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
from collections import Counter

from pm4py.algo.discovery.enhanced_process_tree.variants.refinement_rules import (
    rule_prefix, rule_suffix, rule_infix, rule_concatenation,
    rule_completion_stop, rule_completion_start, rule_skip
)


class LogRefinement:
    def __init__(self, tuple_log, variant_threshold=0.0):
        self.log = {}
        if tuple_log:
            max_freq = max(tuple_log.values())
            cutoff = max_freq * variant_threshold

            for trace, freq in tuple_log.items():
                if freq >= cutoff:
                    self.log[trace] = freq
        self.annotations = {}
        self.skip_records = []

        self.active_rules = [
            # REDUCTIVE RULES (Safe for Loopy Logs)
            rule_prefix,
            rule_suffix,
            rule_infix,
            rule_skip,
            # ADDITIVE/FUSION RULES
            rule_concatenation,
            rule_completion_stop,
            rule_completion_start,
        ]

        self.max_loop_depths = {}
        for trace in self.log.keys():
            counts = Counter(trace)
            for act, count in counts.items():
                if count > self.max_loop_depths.get(act, 0):
                    self.max_loop_depths[act] = count

    def _is_realistic(self, new_trace):
        """
        Validates that a newly synthesized trace does not violate
        the maximum loop depths observed in the raw domain data.
        """
        counts = Counter(new_trace)
        for act, count in counts.items():
            if count > self.max_loop_depths.get(act, 0):
                return False
        return True

    def add_annotation(self, activity, property_type):
        if activity not in self.annotations:
            self.annotations[activity] = set()
        self.annotations[activity].add(property_type)

    def run(self, limit=25):
        """The Main Convergence Engine with Untested Trace Tracking"""
        iteration = 1
        print(f"Initial Log Size: {len(self.log)} unique variants")

        untested_traces = set(self.log.keys())
        previous_log_size = len(self.log)
        stagnation_history = []

        while True:
            merged_this_round = False
            additions_this_round = []

            traces = sorted(list(self.log.keys()), key=len, reverse=True)
            traces_to_delete = set()
            new_traces = {}
            traces_to_test_next = set()

            for i in range(len(traces)):
                if traces[i] in traces_to_delete:
                    continue

                for j in range(i + 1, len(traces)):
                    if i == j:
                        continue

                    t1, t2 = traces[i], traces[j]

                    if (t1 not in untested_traces) and (t2 not in untested_traces):
                        continue

                    for rule_func in self.active_rules:
                        result = rule_func(t1, t2)

                        if result:
                            all_new_traces = list(result.get("replacements", {}).values())

                            violates_realism = False
                            for nt in all_new_traces:
                                if not self._is_realistic(nt):
                                    violates_realism = True
                                    break

                            if violates_realism:
                                continue

                            if "annotations" in result:
                                for act, props in result["annotations"].items():
                                    for p in props:
                                        self.add_annotation(act, p)

                            if "replacements" in result:
                                for old_trace, new_trace in result["replacements"].items():

                                    added_elements = list((Counter(new_trace) - Counter(old_trace)).elements())
                                    if added_elements:
                                        additions_this_round.extend(added_elements)
                                    freq_to_move = new_traces.get(old_trace, self.log.get(old_trace, 0))

                                    if new_trace not in new_traces:
                                        new_traces[new_trace] = self.log.get(new_trace, 0)

                                    new_traces[new_trace] += freq_to_move
                                    traces_to_delete.add(old_trace)

                                    if old_trace in new_traces:
                                        del new_traces[old_trace]

                                    traces_to_test_next.add(new_trace)

                            if "skip_data" in result:
                                self.skip_records.extend(result["skip_data"])

                            merged_this_round = True
                            break

                    if merged_this_round and t1 in traces_to_delete:
                        break

            for t in traces_to_delete:
                if t in self.log:
                    del self.log[t]

            for t, freq in new_traces.items():
                self.log[t] = freq

            untested_traces = traces_to_test_next
            current_log_size = len(self.log)
            round_summary = dict(Counter(additions_this_round))

            if current_log_size == previous_log_size:
                stagnation_history.append(round_summary)

                if len(stagnation_history) >= limit:
                    last_n = stagnation_history[-limit:]
                    summaries_identical = all(s == last_n[0] for s in last_n)

                    if summaries_identical and len(last_n[0]) > 0:
                        print(f"\n[CIRCUIT BREAKER] Stutter Crawl (Runaway Train) Detected!")
                        print(f"Log size stagnated at {current_log_size} variants for {limit} iterations.")
                        print(f"Theoretical convergence reached at Iteration {iteration}.")
                        print("--- Audit Trail of Exhausted Patience ---")
                        print(f"  -> The engine continuously synthesized {last_n[0]} without achieving consolidation.")
                        print("-----------------------------------------")
                        break
            else:
                stagnation_history.clear()

            previous_log_size = current_log_size

            if not merged_this_round:
                print(f"Convergence Reached at Iteration {iteration}!")
                break

            print(f"{iteration} Iteration Completed!")

            iteration += 1

        print(f"Final Log Size: {len(self.log)} unique variants")
        return self.log, self.annotations, self.skip_records
