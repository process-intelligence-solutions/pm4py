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


def rule_prefix(t1, t2):
    if len(t1) < len(t2):
        t_small, t_large = t1, t2
    elif len(t2) < len(t1):
        t_small, t_large = t2, t1
    else:
        return None

    if t_large[:len(t_small)] == t_small:
        return {
            "replacements": {t_small: t_large},
            "annotations": {t_small[-1]: ["stop"]}
        }

    return None


def rule_suffix(t1, t2):
    if len(t1) < len(t2):
        t_small, t_large = t1, t2
    elif len(t2) < len(t1):
        t_small, t_large = t2, t1
    else:
        return None

    if t_large[-len(t_small):] == t_small:
        return {
            "replacements": {t_small: t_large},
            "annotations": {t_small[0]: ["start"]}
        }

    return None


def rule_infix(t1, t2):
    if len(t1) < len(t2):
        t_small, t_large = t1, t2
    elif len(t2) < len(t1):
        t_small, t_large = t2, t1
    else:
        return None

    # We only check from index 1 to the second-to-last index to ensure
    # it is strictly an INFIX, avoiding overlap with prefix/suffix rules.
    for k in range(1, len(t_large) - len(t_small)):
        if t_large[k: k + len(t_small)] == t_small:
            return {
                "replacements": {t_small: t_large},
                "annotations": {
                    t_small[0]: ["start"],
                    t_small[-1]: ["stop"]
                }
            }

    return None


def rule_concatenation(t1, t2):
    """
    Looks for the longest overlapping sequence where the end of one trace
    perfectly matches the beginning of another trace.
    """
    # The maximum possible overlap is the length of the shorter trace minus 1.
    # (If the overlap was the full length, it would be a prefix/suffix, which
    # are handled by other rules).
    max_overlap = min(len(t1), len(t2)) - 1

    for k in range(max_overlap, 0, -1):

        if t1[-k:] == t2[:k]:
            merged = t1[:-k] + t2

            start_node = t2[0]
            stop_node = t1[-1]

            if start_node == stop_node:
                annotations = {start_node: ["start", "stop"]}
            else:
                annotations = {
                    start_node: ["start"],
                    stop_node: ["stop"]
                }

            return {
                "replacements": {t1: merged, t2: merged},
                "annotations": annotations
            }

        elif t2[-k:] == t1[:k]:
            merged = t2[:-k] + t1

            start_node = t1[0]
            stop_node = t2[-1]

            if start_node == stop_node:
                annotations = {start_node: ["start", "stop"]}
            else:
                annotations = {
                    start_node: ["start"],
                    stop_node: ["stop"]
                }

            return {
                "replacements": {t1: merged, t2: merged},
                "annotations": annotations
            }

    return None


def _check_completion_start(t_short, t_long, min_overlap=1):
    max_overlap = min(len(t_short), len(t_long) - 1)

    if max_overlap < min_overlap:
        return None

    for k in range(max_overlap, min_overlap - 1, -1):
        prefix = t_short[:k]

        for i in range(1, len(t_long) - k + 1):
            if t_long[i: i + k] == prefix:
                before_extension = t_long[:i]
                completed_trace = before_extension + t_short
                start_node = t_short[0]

                return {
                    "replacements": {t_short: completed_trace},
                    "annotations": {start_node: ["start"]}
                }
    return None


def rule_completion_start(t1, t2, min_overlap=1):
    """Rules 5b & 6b: Completes traces that started late."""
    res = _check_completion_start(t1, t2, min_overlap)
    if res: return res
    return _check_completion_start(t2, t1, min_overlap)


def _check_completion_stop(t_short, t_long, min_overlap=1):
    max_overlap = min(len(t_short), len(t_long) - 1)

    if max_overlap < min_overlap:
        return None

    for k in range(max_overlap, min_overlap - 1, -1):
        suffix = t_short[-k:]

        for i in range(len(t_long) - k):
            if t_long[i: i + k] == suffix:
                extension = t_long[i + k:]
                completed_trace = t_short + extension
                stop_node = t_short[-1]

                return {
                    "replacements": {t_short: completed_trace},
                    "annotations": {stop_node: ["stop"]}
                }
    return None


def rule_completion_stop(t1, t2, min_overlap=1):
    """Rules 5 & 6: Completes traces that stopped early."""
    res = _check_completion_stop(t1, t2, min_overlap)
    if res: return res
    return _check_completion_stop(t2, t1, min_overlap)


def rule_skip(t1, t2):
    """
    Identifies a local bypass (skip).
    Requires traces to share a common prefix AND a common suffix.
    """
    if len(t1) < len(t2):
        t_short, t_long = t1, t2
    elif len(t2) < len(t1):
        t_short, t_long = t2, t1
    else:
        return None

    p = 0
    while p < len(t_short) and t_short[p] == t_long[p]:
        p += 1

    s = 0
    while s < len(t_short) - p and t_short[-(s + 1)] == t_long[-(s + 1)]:
        s += 1

    if p == 0 or s == 0:
        return None

    m_short = t_short[p: len(t_short) - s]
    m_long = t_long[p: len(t_long) - s]

    skipped_activities = list((Counter(m_long) - Counter(m_short)).elements())

    if len(m_short) == 0:
        trigger_node = t_short[p - 1]
        return {
            "replacements": {t_short: t_long},
            "skip_data": [{
                "trigger_label": trigger_node,
                "skipped_labels": skipped_activities
            }]
        }

    if set(m_short).issubset(set(m_long)):
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
            multiple_skips = []
            short_idx = 0
            current_trigger = t_short[p - 1]
            current_skip_group = []

            for item in m_long:
                if short_idx < len(m_short) and item == m_short[short_idx]:
                    if current_skip_group:
                        multiple_skips.append({
                            "trigger_label": current_trigger,
                            "skipped_labels": current_skip_group
                        })
                        current_skip_group = []
                    current_trigger = item
                    short_idx += 1
                else:
                    current_skip_group.append(item)

            if current_skip_group:
                multiple_skips.append({
                    "trigger_label": current_trigger,
                    "skipped_labels": current_skip_group
                })

            return {
                "replacements": {t_short: t_long},
                "skip_data": multiple_skips
            }

        else:
            trigger_node = m_short[-1]
            return {
                "replacements": {t_short: t_long},
                "skip_data": [{
                    "trigger_label": trigger_node,
                    "skipped_labels": skipped_activities
                }]
            }

    return None
