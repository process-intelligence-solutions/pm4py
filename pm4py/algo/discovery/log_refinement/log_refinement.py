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

from pm4py.algo.discovery.log_refinement.refinement_rules import (
    rule_prefix, rule_suffix, rule_infix, rule_concatenation,
    rule_completion_stop, rule_completion_start, rule_skip, rule_duplication
)


class LogRefinement:
    def __init__(self, tuple_log):
        clean_log = {}
        for trace, freq in tuple_log.items():
            clean_trace = []
            for act in trace:
                # Add the activity if we have fewer than 2 items in our clean trace,
                # OR if it is NOT the same as BOTH of the last two activities.
                if len(clean_trace) < 2 or not (clean_trace[-1] == act and clean_trace[-2] == act):
                    clean_trace.append(act)

            clean_trace = tuple(clean_trace)

            # Combine frequencies if multiple messy traces collapse into the same clean pattern
            clean_log[clean_trace] = clean_log.get(clean_trace, 0) + freq

        self.log = clean_log
        self.annotations = {}

        self.active_rules = [
            # REDUCTIVE RULES (Safe for Loopy Logs)
            rule_prefix,
            rule_suffix,
            rule_infix,
            rule_skip,
            # ADDITIVE/FUSION RULES
            rule_completion_stop,
            rule_completion_start,
            rule_concatenation,
            # rule_duplication  # <-- Keep off by default to prevent log explosion
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

    def to_event_log(self, activity_key="concept:name", timestamp_key="time:timestamp"):
        """
        Converts the internal compressed dictionary back into a standard PM4Py EventLog.
        This ensures the output is 100% compatible with top-level PM4Py algorithms.
        """
        from pm4py.objects.log.obj import EventLog, Trace, Event
        from datetime import datetime

        new_log = EventLog()
        for trace_tuple, frequency in self.log.items():
            for _ in range(frequency):
                trace = Trace()
                for activity in trace_tuple:
                    event = Event({
                        activity_key: activity,
                        timestamp_key: datetime.now()
                    })
                    trace.append(event)
                new_log.append(trace)
        return new_log

    def run(self, activity_key="concept:name", timestamp_key="time:timestamp"):
        """The Main Convergence Engine with Untested Trace Tracking"""
        iteration = 1
        print(f"Initial Log Size: {len(self.log)} unique variants")

        untested_traces = set(self.log.keys())

        while True:
            merged_this_round = False

            traces = sorted(list(self.log.keys()), key=len, reverse=True)

            traces_to_delete = set()
            new_traces = {}

            traces_to_test_next = set()

            for i in range(len(traces)):
                if traces[i] in traces_to_delete:
                    continue

                for j in range(len(traces)):
                    if i == j or traces[j] in traces_to_delete:
                        continue

                    t1, t2 = traces[i], traces[j]

                    # If neither trace is marked as untested, we already evaluated this
                    # exact pair in a previous iteration
                    if (t1 not in untested_traces) and (t2 not in untested_traces):
                        continue

                    for rule_func in self.active_rules:
                        result = rule_func(t1, t2)

                        if result:
                            all_new_traces = list(result.get("replacements", {}).values()) + result.get("additions", [])

                            violates_realism = False
                            for nt in all_new_traces:
                                if not self._is_realistic(nt):
                                    violates_realism = True
                                    break

                            # If this rule creates an infinitely looping trace, reject it!
                            if violates_realism:
                                continue

                            if "annotations" in result:
                                for act, props in result["annotations"].items():
                                    for p in props:
                                        self.add_annotation(act, p)

                            if "replacements" in result:
                                for old_trace, new_trace in result["replacements"].items():
                                    freq_to_move = self.log.get(old_trace, 0)

                                    if new_trace not in new_traces:
                                        new_traces[new_trace] = self.log.get(new_trace, 0)

                                    new_traces[new_trace] += freq_to_move
                                    traces_to_delete.add(old_trace)

                                    if new_trace not in self.log:
                                        traces_to_test_next.add(new_trace)

                            if "additions" in result:
                                added_new = False
                                for new_trace in result["additions"]:
                                    if new_trace not in self.log and new_trace not in new_traces:
                                        new_traces[new_trace] = 1
                                        traces_to_test_next.add(new_trace)
                                        added_new = True

                                if not added_new:
                                    continue

                            merged_this_round = True
                            break

                    if merged_this_round and t1 in traces_to_delete:
                        break

            for t in traces_to_delete:
                if t in self.log:
                    del self.log[t]

            for t, freq in new_traces.items():
                self.log[t] = freq

            # The only traces we need to test next round are the ones we just modified
            untested_traces = traces_to_test_next

            if not merged_this_round:
                print(f"Convergence Reached at Iteration {iteration}!")
                break

            print(f"{iteration} Iteration Completed!")

            iteration += 1

        final_event_log = self.to_event_log(activity_key, timestamp_key)
        print(f"Final Log Size: {len(self.log)} unique variants")
        return final_event_log, self.annotations