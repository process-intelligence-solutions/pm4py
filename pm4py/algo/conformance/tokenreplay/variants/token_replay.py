from pm4py.util import xes_constants as xes_util
from pm4py.objects.petri_net import semantics
from pm4py.objects.petri_net.utils.petri_utils import get_places_shortest_path_by_hidden, get_s_components_from_petri
from pm4py.objects.log import obj as log_implementation
from pm4py.objects.petri_net.utils import align_utils
from copy import copy
from enum import Enum
from pm4py.util import exec_utils, constants
from pm4py.util import variants_util, pandas_utils
import importlib.util
from typing import Optional, Dict, Any, Union
from pm4py.objects.log.obj import EventLog
import pandas as pd
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util import typing
from collections import Counter
from pm4py.objects.conversion.log import converter as log_converter


class Parameters(Enum):
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    PARAMETER_VARIANT_DELIMITER = "variant_delimiter"
    VARIANTS = "variants"
    PLACES_SHORTEST_PATH_BY_HIDDEN = "places_shortest_path_by_hidden"
    THREAD_MAX_EX_TIME = "thread_maximum_ex_time"
    DISABLE_VARIANTS = "disable_variants"
    CLEANING_TOKEN_FLOOD = "cleaning_token_flood"
    IS_REDUCTION = "is_reduction"
    WALK_THROUGH_HIDDEN_TRANS = "walk_through_hidden_trans"
    RETURN_NAMES = "return_names"
    STOP_IMMEDIATELY_UNFIT = "stop_immediately_unfit"
    TRY_TO_REACH_FINAL_MARKING_THROUGH_HIDDEN = "try_to_reach_final_marking_through_hidden"
    CONSIDER_REMAINING_IN_FITNESS = "consider_remaining_in_fitness"
    CONSIDER_ACTIVITIES_NOT_IN_MODEL_IN_FITNESS = "consider_activities_not_in_model_in_fitness"
    ENABLE_PLTR_FITNESS = "enable_pltr_fitness"
    SHOW_PROGRESS_BAR = "show_progress_bar"


class TechnicalParameters(Enum):
    MAX_REC_DEPTH = 50
    MAX_IT_FINAL1 = 5
    MAX_IT_FINAL2 = 5
    MAX_REC_DEPTH_HIDTRANSENABL = 2
    MAX_POSTFIX_SUFFIX_LENGTH = 20
    MAX_NO_THREADS = 1024
    MAX_DEF_THR_EX_TIME = 10
    ENABLE_POSTFIX_CACHE = False
    ENABLE_MARKTOACT_CACHE = False


class DebugConst:
    REACH_MRH = -1
    REACH_ITF1 = -1
    REACH_ITF2 = -1


class NoConceptNameException(Exception):
    def __init__(self, message):
        self.message = message


def add_missing_tokens(t, marking):
    """
    Adds missing tokens needed to activate a transition

    Parameters
    ----------
    t
        Transition that should be enabled
    marking
        Current marking
    """
    missing = 0
    tokens_added = {}
    for a in t.in_arcs:
        if marking[a.source] < a.weight:
            missing = missing + (a.weight - marking[a.source])
            tokens_added[a.source] = a.weight - marking[a.source]
            marking[a.source] = marking[a.source] + a.weight
    return [missing, tokens_added]


def get_consumed_tokens(t):
    """
    Get tokens consumed firing a transition

    Parameters
    ----------
    t
        Transition that should be enabled
    """
    consumed = 0
    consumed_map = {}
    for a in t.in_arcs:
        consumed = consumed + a.weight
        consumed_map[a.source] = a.weight
    return consumed, consumed_map


def get_produced_tokens(t):
    """
    Get tokens produced firing a transition

    Parameters
    ----------
    t
        Transition that should be enabled
    """
    produced = 0
    produced_map = {}
    for a in t.out_arcs:
        produced = produced + a.weight
        produced_map[a.target] = a.weight
    return produced, produced_map


def merge_dicts(x, y):
    """
    Merge two dictionaries keeping the least value

    Parameters
    ----------
    x
        First map (string, integer)
    y
        Second map (string, integer)
    """
    for key in y:
        if key not in x:
            x[key] = y[key]
        else:
            if y[key] < x[key]:
                x[key] = y[key]


def get_places_with_missing_tokens(t, marking):
    """
    Get places with missing tokens

    Parameters
    ----------
    t
        Transition to enable
    marking
        Current marking
    """
    places_with_missing = set()
    for a in t.in_arcs:
        if marking[a.source] < a.weight:
            places_with_missing.add(a.source)
    return places_with_missing


def get_hidden_transitions_to_enable(marking, places_with_missing, places_shortest_path_by_hidden):
    """
    Calculate an ordered list of transitions to visit in order to enable a given transition

    Parameters
    ----------
    marking
        Current marking
    places_with_missing
        List of places with missing tokens
    places_shortest_path_by_hidden
        Minimal connection between places by hidden transitions
    """
    hidden_transitions_to_enable = []

    marking_places = [x for x in marking]
    marking_places = sorted(marking_places, key=lambda x: x.name)
    places_with_missing_keys = [x for x in places_with_missing]
    places_with_missing_keys = sorted(places_with_missing_keys, key=lambda x: x.name)
    for p1 in marking_places:
        for p2 in places_with_missing_keys:
            if p1 in places_shortest_path_by_hidden and p2 in places_shortest_path_by_hidden[p1]:
                hidden_transitions_to_enable.append(places_shortest_path_by_hidden[p1][p2])
    hidden_transitions_to_enable = sorted(hidden_transitions_to_enable, key=lambda x: len(x))

    return hidden_transitions_to_enable


def get_req_transitions_for_final_marking(marking, final_marking, places_shortest_path_by_hidden):
    """
    Gets required transitions for final marking

    Parameters
    ----------
    marking
        Current marking
    final_marking
        Final marking assigned to the Petri net
    places_shortest_path_by_hidden
        Minimal connection between places by hidden transitions
    """
    hidden_transitions_to_enable = []

    marking_places = [x for x in marking]
    marking_places = sorted(marking_places, key=lambda x: x.name)
    final_marking_places = [x for x in final_marking]
    final_marking_places = sorted(final_marking_places, key=lambda x: x.name)
    for p1 in marking_places:
        for p2 in final_marking_places:
            if p1 in places_shortest_path_by_hidden and p2 in places_shortest_path_by_hidden[p1]:
                hidden_transitions_to_enable.append(places_shortest_path_by_hidden[p1][p2])
    hidden_transitions_to_enable = sorted(hidden_transitions_to_enable, key=lambda x: len(x))

    return hidden_transitions_to_enable


def enable_hidden_transitions(net, marking, activated_transitions, visited_transitions, all_visited_markings,
                              hidden_transitions_to_enable, t):
    """
    Actually enable hidden transitions on the Petri net

    Parameters
    -----------
    net
        Petri net
    marking
        Current marking
    activated_transitions
        All activated transitions during the replay
    visited_transitions
        All visited transitions by the recursion
    all_visited_markings
        All visited markings
    hidden_transitions_to_enable
        List of hidden transition to enable
    t
        Transition against we should check if they are enabled
    """
    j_indexes = [0] * len(hidden_transitions_to_enable)
    for z in range(10000000):
        something_changed = False
        for k in range(j_indexes[z % len(hidden_transitions_to_enable)], len(
                hidden_transitions_to_enable[z % len(hidden_transitions_to_enable)])):
            t3 = hidden_transitions_to_enable[z % len(hidden_transitions_to_enable)][
                j_indexes[z % len(hidden_transitions_to_enable)]]
            if not t3 == t:
                if semantics.is_enabled(t3, net, marking):
                    if t3 not in visited_transitions:
                        marking = semantics.execute(t3, net, marking)
                        activated_transitions.append(t3)
                        visited_transitions.add(t3)
                        all_visited_markings.append(marking)
                        something_changed = True
            j_indexes[z % len(hidden_transitions_to_enable)] = j_indexes[z % len(hidden_transitions_to_enable)] + 1
            if semantics.is_enabled(t, net, marking):
                break
        if semantics.is_enabled(t, net, marking):
            break
        if not something_changed:
            break
    return [marking, activated_transitions, visited_transitions, all_visited_markings]


def apply_hidden_trans(t, net, marking, places_shortest_paths_by_hidden, act_tr, rec_depth,
                       visit_trans,
                       vis_mark):
    """
    Apply hidden transitions in order to enable a given transition

    Parameters
    ----------
    t
        Transition to eventually enable
    net
        Petri net
    marking
        Marking
    places_shortest_paths_by_hidden
        Shortest paths between places connected by hidden transitions
    act_tr
        All activated transitions
    rec_depth
        Current recursion depth
    visit_trans
        All visited transitions by hiddenTrans method
    vis_mark
        All visited markings
    """
    if rec_depth >= TechnicalParameters.MAX_REC_DEPTH_HIDTRANSENABL.value or t in visit_trans:
        return [net, marking, act_tr, vis_mark]
    # if rec_depth > DebugConst.REACH_MRH:
    #    DebugConst.REACH_MRH = rec_depth
    visit_trans.add(t)
    marking_at_start = copy(marking)
    places_with_missing = get_places_with_missing_tokens(t, marking)
    hidden_transitions_to_enable = get_hidden_transitions_to_enable(marking, places_with_missing,
                                                                    places_shortest_paths_by_hidden)

    if hidden_transitions_to_enable:
        [marking, act_tr, visit_trans, vis_mark] = enable_hidden_transitions(net,
                                                                             marking,
                                                                             act_tr,
                                                                             visit_trans,
                                                                             vis_mark,
                                                                             hidden_transitions_to_enable,
                                                                             t)
        if not semantics.is_enabled(t, net, marking):
            hidden_transitions_to_enable = get_hidden_transitions_to_enable(marking, places_with_missing,
                                                                            places_shortest_paths_by_hidden)
            for z in range(len(hidden_transitions_to_enable)):
                for k in range(len(hidden_transitions_to_enable[z])):
                    t4 = hidden_transitions_to_enable[z][k]
                    if not t4 == t:
                        if t4 not in visit_trans:
                            if not semantics.is_enabled(t4, net, marking):
                                [net, marking, act_tr, vis_mark] = apply_hidden_trans(t4,
                                                                                      net,
                                                                                      marking,
                                                                                      places_shortest_paths_by_hidden,
                                                                                      act_tr,
                                                                                      rec_depth + 1,
                                                                                      visit_trans,
                                                                                      vis_mark)
                            if semantics.is_enabled(t4, net, marking):
                                marking = semantics.execute(t4, net, marking)
                                act_tr.append(t4)
                                visit_trans.add(t4)
                                vis_mark.append(marking)
        if not semantics.is_enabled(t, net, marking):
            if not (marking_at_start == marking):
                [net, marking, act_tr, vis_mark] = apply_hidden_trans(t, net, marking,
                                                                      places_shortest_paths_by_hidden,
                                                                      act_tr,
                                                                      rec_depth + 1,
                                                                      visit_trans,
                                                                      vis_mark)

    return [net, marking, act_tr, vis_mark]


def break_condition_final_marking(marking, final_marking):
    """
    Verify break condition for final marking

    Parameters
    -----------
    marking
        Current marking
    final_marking
        Target final marking
    """
    final_marking_dict = dict(final_marking)
    marking_dict = dict(marking)
    final_marking_dict_keys = set(final_marking_dict.keys())
    marking_dict_keys = set(marking_dict.keys())

    return final_marking_dict_keys.issubset(marking_dict_keys)


def apply_trace(trace, net, initial_marking, final_marking, trans_map, enable_pltr_fitness, place_fitness,
                transition_fitness, notexisting_activities_in_model,
                places_shortest_path_by_hidden, consider_remaining_in_fitness, activity_key="concept:name",
                try_to_reach_final_marking_through_hidden=True, stop_immediately_unfit=False,
                walk_through_hidden_trans=True, post_fix_caching=None,
                marking_to_activity_caching=None, is_reduction=False,
                thread_maximum_ex_time=TechnicalParameters.MAX_DEF_THR_EX_TIME.value,
                enable_postfix_cache=False, enable_marktoact_cache=False, cleaning_token_flood=False,
                s_components=None, trace_occurrences=1, consider_activities_not_in_model_in_fitness=False):
    """
    Apply the token replaying algorithm to a trace

    Parameters
    ----------
    trace
        Trace in the event log
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    trans_map
        Map between transitions labels and transitions
    enable_pltr_fitness
        Enable fitness retrieval at place/transition level
    place_fitness
        Current dictionary of places associated with unfit traces
    transition_fitness
        Current dictionary of transitions associated with unfit traces
    notexisting_activities_in_model
        Map that stores the notexisting activities in the model
    places_shortest_path_by_hidden
        Shortest paths between places by hidden transitions
    consider_remaining_in_fitness
        Boolean value telling if the remaining tokens should be considered in fitness evaluation
    activity_key
        Name of the attribute that contains the activity
    try_to_reach_final_marking_through_hidden
        Boolean value that decides if we shall try to reach the final marking through hidden transitions
    stop_immediately_unfit
        Boolean value that decides if we shall stop immediately when a non-conformance is detected
    walk_through_hidden_trans
        Boolean value that decides if we shall walk through hidden transitions in order to enable visible transitions
    post_fix_caching
        Stores the post fix caching object
    marking_to_activity_caching
        Stores the marking-to-activity cache
    is_reduction
        Expresses if the token-based replay is called in a reduction attempt
    thread_maximum_ex_time
        Alignment threads maximum allowed execution time
    enable_postfix_cache
        Enables postfix cache
    enable_marktoact_cache
        Enables marking to activity cache
    cleaning_token_flood
        Decides if a cleaning of the token flood shall be operated
    s_components
        S-components of the Petri net (if workflow net)
    """
    trace_activities = [event[activity_key] for event in trace]
    act_trans = []
    transitions_with_problems = []
    vis_mark = []
    activating_transition_index = {}
    activating_transition_interval = []
    used_postfix_cache = False
    marking = copy(initial_marking)
    vis_mark.append(marking)
    missing = 0
    consumed = 0
    sum_tokens_im = 0
    for place in initial_marking:
        sum_tokens_im = sum_tokens_im + initial_marking[place]
    sum_tokens_fm = 0
    for place in final_marking:
        sum_tokens_fm = sum_tokens_fm + final_marking[place]
    produced = sum_tokens_im
    current_event_map = {}
    current_remaining_map = {}
    for i in range(len(trace)):
        if enable_postfix_cache and (str(trace_activities) in post_fix_caching.cache and
                                     hash(marking) in post_fix_caching.cache[str(trace_activities)]):
            trans_to_act = post_fix_caching.cache[str(trace_activities)][hash(marking)]["trans_to_activate"]
            for z in range(len(trans_to_act)):
                t = trans_to_act[z]
                act_trans.append(t)
            used_postfix_cache = True
            marking = post_fix_caching.cache[str(trace_activities)][hash(marking)]["final_marking"]
            break
        else:
            prev_len_activated_transitions = len(act_trans)
            if enable_marktoact_cache and (hash(marking) in marking_to_activity_caching.cache and
                                           trace[i][activity_key] in marking_to_activity_caching.cache[hash(marking)]
                                           and trace[i - 1][activity_key] ==
                                           marking_to_activity_caching.cache[hash(marking)][trace[i][activity_key]]
                                           ["previousActivity"]):
                this_end_marking = marking_to_activity_caching.cache[hash(marking)][trace[i][activity_key]][
                    "end_marking"]
                this_act_trans = marking_to_activity_caching.cache[hash(marking)][trace[i][activity_key]][
                    "this_activated_transitions"]
                this_vis_markings = marking_to_activity_caching.cache[hash(marking)][trace[i][activity_key]][
                    "this_visited_markings"]
                act_trans = act_trans + this_act_trans
                vis_mark = vis_mark + this_vis_markings
                marking = copy(this_end_marking)
            else:
                if trace[i][activity_key] in trans_map:
                    current_event_map.update(trace[i])
                    # change 14/10/2020: to better support duplicate transitions with this approach, we check
                    # whether in the current marking there is at least one transition corresponding to the activity
                    # key without looking at the transition map (that contains one entry per label)
                    corr_en_t = [x for x in semantics.enabled_transitions(net, marking) if x.label == trace[i][activity_key]]
                    if corr_en_t:
                        t = corr_en_t[0]
                    else:
                        t = trans_map[trace[i][activity_key]]
                    if walk_through_hidden_trans and not semantics.is_enabled(t, net,
                                                                              marking):
                        visited_transitions = set()
                        prev_len_activated_transitions = len(act_trans)
                        [net, new_marking, new_act_trans, new_vis_mark] = apply_hidden_trans(t, net,
                                                                                             copy(marking),
                                                                                             places_shortest_path_by_hidden,
                                                                                             copy(act_trans),
                                                                                             0,
                                                                                             copy(visited_transitions),
                                                                                             copy(vis_mark))
                        for jj5 in range(len(act_trans), len(new_act_trans)):
                            tt5 = new_act_trans[jj5]
                            c, cmap = get_consumed_tokens(tt5)
                            p, pmap = get_produced_tokens(tt5)
                            if enable_pltr_fitness:
                                for pl2 in cmap:
                                    if pl2 in place_fitness:
                                        place_fitness[pl2]["c"] += cmap[pl2] * trace_occurrences
                                for pl2 in pmap:
                                    if pl2 in place_fitness:
                                        place_fitness[pl2]["p"] += pmap[pl2] * trace_occurrences
                            consumed = consumed + c
                            produced = produced + p
                        marking, act_trans, vis_mark = new_marking, new_act_trans, new_vis_mark
                    is_initially_enabled = True
                    old_marking_names = [x.name for x in list(marking.keys())]
                    if not semantics.is_enabled(t, net, marking):
                        is_initially_enabled = False
                        transitions_with_problems.append(t)
                        if stop_immediately_unfit:
                            missing = missing + 1
                            break
                        [m, tokens_added] = add_missing_tokens(t, marking)
                        missing = missing + m
                        if enable_pltr_fitness:
                            for place in tokens_added.keys():
                                if place in place_fitness:
                                    place_fitness[place]["underfed_traces"].add(trace)
                                place_fitness[place]["m"] += tokens_added[place]
                            if trace not in transition_fitness[t]["underfed_traces"]:
                                transition_fitness[t]["underfed_traces"][trace] = list()
                            transition_fitness[t]["underfed_traces"][trace].append(current_event_map)
                    elif enable_pltr_fitness:
                        if trace not in transition_fitness[t]["fit_traces"]:
                            transition_fitness[t]["fit_traces"][trace] = list()
                        transition_fitness[t]["fit_traces"][trace].append(current_event_map)
                    c, cmap = get_consumed_tokens(t)
                    p, pmap = get_produced_tokens(t)
                    consumed = consumed + c
                    produced = produced + p
                    if enable_pltr_fitness:
                        for pl2 in cmap:
                            if pl2 in place_fitness:
                                place_fitness[pl2]["c"] += cmap[pl2] * trace_occurrences
                        for pl2 in pmap:
                            if pl2 in place_fitness:
                                place_fitness[pl2]["p"] += pmap[pl2] * trace_occurrences
                    if semantics.is_enabled(t, net, marking):
                        marking = semantics.execute(t, net, marking)
                        act_trans.append(t)
                        vis_mark.append(marking)
                    if not is_initially_enabled and cleaning_token_flood:
                        # here, a routine for cleaning token flood shall go
                        new_marking_names = [x.name for x in list(marking.keys())]
                        new_marking_names_diff = [x for x in new_marking_names if x not in old_marking_names]
                        new_marking_names_inte = [x for x in new_marking_names if x in old_marking_names]
                        for p1 in new_marking_names_inte:
                            for p2 in new_marking_names_diff:
                                for comp in s_components:
                                    if p1 in comp and p2 in comp:
                                        place_to_delete = [place for place in list(marking.keys()) if place.name == p1]
                                        if len(place_to_delete) == 1:
                                            del marking[place_to_delete[0]]
                                            if not place_to_delete[0] in current_remaining_map:
                                                current_remaining_map[place_to_delete[0]] = 0
                                            current_remaining_map[place_to_delete[0]] = current_remaining_map[
                                                                                            place_to_delete[0]] + 1
                        pass
                else:
                    if not trace[i][activity_key] in notexisting_activities_in_model:
                        notexisting_activities_in_model[trace[i][activity_key]] = {}
                    notexisting_activities_in_model[trace[i][activity_key]][trace] = current_event_map
            del trace_activities[0]
            if len(trace_activities) < TechnicalParameters.MAX_POSTFIX_SUFFIX_LENGTH.value:
                activating_transition_index[str(trace_activities)] = {"index": len(act_trans),
                                                                      "marking": hash(marking)}
            if i > 0:
                activating_transition_interval.append(
                    [trace[i][activity_key], prev_len_activated_transitions, len(act_trans),
                     trace[i - 1][activity_key]])
            else:
                activating_transition_interval.append(
                    [trace[i][activity_key], prev_len_activated_transitions, len(act_trans),
                     ""])

    if try_to_reach_final_marking_through_hidden and not used_postfix_cache:
        for i in range(TechnicalParameters.MAX_IT_FINAL1.value):
            if not break_condition_final_marking(marking, final_marking):
                hidden_transitions_to_enable = get_req_transitions_for_final_marking(marking, final_marking,
                                                                                     places_shortest_path_by_hidden)

                for group in hidden_transitions_to_enable:
                    for t in group:
                        if semantics.is_enabled(t, net, marking):
                            marking = semantics.execute(t, net, marking)
                            act_trans.append(t)
                            vis_mark.append(marking)
                            c, cmap = get_consumed_tokens(t)
                            p, pmap = get_produced_tokens(t)
                            if enable_pltr_fitness:
                                for pl2 in cmap:
                                    if pl2 in place_fitness:
                                        place_fitness[pl2]["c"] += cmap[pl2] * trace_occurrences
                                for pl2 in pmap:
                                    if pl2 in place_fitness:
                                        place_fitness[pl2]["p"] += pmap[pl2] * trace_occurrences
                            consumed = consumed + c
                            produced = produced + p
                    if break_condition_final_marking(marking, final_marking):
                        break
            else:
                break

        # try to reach the final marking in a different fashion, if not already reached
        if not break_condition_final_marking(marking, final_marking):
            if len(final_marking) == 1:
                sink_place = list(final_marking)[0]

                connections_to_sink = []
                for place in marking:
                    if place in places_shortest_path_by_hidden and sink_place in places_shortest_path_by_hidden[place]:
                        connections_to_sink.append([place, places_shortest_path_by_hidden[place][sink_place]])
                connections_to_sink = sorted(connections_to_sink, key=lambda x: len(x[1]))

                for i in range(TechnicalParameters.MAX_IT_FINAL2.value):
                    for j in range(len(connections_to_sink)):
                        for z in range(len(connections_to_sink[j][1])):
                            t = connections_to_sink[j][1][z]
                            if semantics.is_enabled(t, net, marking):
                                marking = semantics.execute(t, net, marking)
                                act_trans.append(t)
                                c, cmap = get_consumed_tokens(t)
                                p, pmap = get_produced_tokens(t)
                                if enable_pltr_fitness:
                                    for pl2 in cmap:
                                        if pl2 in place_fitness:
                                            place_fitness[pl2]["c"] += cmap[pl2] * trace_occurrences
                                    for pl2 in pmap:
                                        if pl2 in place_fitness:
                                            place_fitness[pl2]["p"] += pmap[pl2] * trace_occurrences
                                consumed = consumed + c
                                produced = produced + p
                                vis_mark.append(marking)
                                continue
                            else:
                                break

    marking_before_cleaning = copy(marking)

    # 25/02/2020: fix to the missing tokens mark (if the final marking is not reached)
    # (not inficiating the previous stat)
    diff_fin_mark_mark = Marking()
    for p in final_marking:
        diff = final_marking[p] - marking[p]
        if diff > 0:
            diff_fin_mark_mark[p] = diff

    # set up the remaining tokens count
    remaining = 0
    for p in marking:
        if p in final_marking:
            marking[p] = max(0, marking[p] - final_marking[p])
            if enable_pltr_fitness:
                if marking[p] > 0:
                    if p in place_fitness:
                        if trace not in place_fitness[p]["underfed_traces"]:
                            place_fitness[p]["overfed_traces"].add(trace)
                        place_fitness[p]["r"] += marking[p] * trace_occurrences
        # 25/02/2020: added missing part to statistics
        elif enable_pltr_fitness:
            if p in place_fitness:
                if trace not in place_fitness[p]["underfed_traces"]:
                    place_fitness[p]["overfed_traces"].add(trace)
                place_fitness[p]["r"] += marking[p] * trace_occurrences
        remaining = remaining + marking[p]

    for p in current_remaining_map:
        if enable_pltr_fitness:
            if p in place_fitness:
                if trace not in place_fitness[p]["underfed_traces"] and trace not in place_fitness[p]["overfed_traces"]:
                    place_fitness[p]["overfed_traces"].add(trace)
                place_fitness[p]["r"] += current_remaining_map[p] * trace_occurrences
        remaining = remaining + current_remaining_map[p]

    if consider_remaining_in_fitness:
        is_fit = (missing == 0) and (remaining == 0)
    else:
        is_fit = (missing == 0)

    if consider_activities_not_in_model_in_fitness and notexisting_activities_in_model:
        is_fit = False

    # separate global counts from local statistics in the case these are not enabled by the options
    for pl in final_marking:
        consumed += final_marking[pl]
    # 25/02/2020: update the missing tokens count here
    for pl in diff_fin_mark_mark:
        missing += diff_fin_mark_mark[pl]

    if enable_pltr_fitness:
        for pl in initial_marking:
            place_fitness[pl]["p"] += initial_marking[pl] * trace_occurrences
        for pl in final_marking:
            place_fitness[pl]["c"] += final_marking[pl] * trace_occurrences
        for pl in diff_fin_mark_mark:
            place_fitness[pl]["m"] += diff_fin_mark_mark[pl] * trace_occurrences

    if consumed > 0 and produced > 0:
        trace_fitness = 0.5 * (1.0 - float(missing) / float(consumed)) + 0.5 * (
                1.0 - float(remaining) / float(produced))
    else:
        trace_fitness = 1.0

    if is_fit:
        for suffix in activating_transition_index:
            if suffix not in post_fix_caching.cache:
                post_fix_caching.cache[suffix] = {}
            if activating_transition_index[suffix]["marking"] not in post_fix_caching.cache[suffix]:
                post_fix_caching.cache[suffix][activating_transition_index[suffix]["marking"]] = \
                    {"trans_to_activate": act_trans[activating_transition_index[suffix]["index"]:],
                     "final_marking": marking}
        for trans in activating_transition_interval:
            activity = trans[0]
            start_marking_index = trans[1]
            end_marking_index = trans[2]
            previous_activity = trans[3]
            if end_marking_index < len(vis_mark):
                start_marking_object = vis_mark[start_marking_index]
                start_marking_hash = hash(start_marking_object)
                end_marking_object = vis_mark[end_marking_index]
                if activity in trans_map:
                    this_activated_trans = act_trans[start_marking_index:end_marking_index]
                    this_visited_markings = vis_mark[start_marking_index + 1:end_marking_index + 1]

                    if start_marking_hash not in marking_to_activity_caching.cache:
                        marking_to_activity_caching.cache[start_marking_hash] = {}
                    if activity not in marking_to_activity_caching.cache[start_marking_hash]:
                        marking_to_activity_caching.cache[start_marking_hash][activity] = {
                            "start_marking": start_marking_object, "end_marking": end_marking_object,
                            "this_activated_transitions": this_activated_trans,
                            "this_visited_markings": this_visited_markings,
                            "previousActivity": previous_activity}

    return [is_fit, trace_fitness, act_trans, transitions_with_problems, marking_before_cleaning,
            align_utils.get_visible_transitions_eventually_enabled_by_marking(net, marking_before_cleaning), missing,
            consumed,
            remaining, produced]


class ApplyTraceTokenReplay:
    def __init__(self, trace, net, initial_marking, final_marking, trans_map, enable_pltr_fitness, place_fitness,
                 transition_fitness, notexisting_activities_in_model,
                 places_shortest_path_by_hidden, consider_remaining_in_fitness, activity_key="concept:name",
                 reach_mark_through_hidden=True, stop_immediately_when_unfit=False,
                 walk_through_hidden_trans=True, post_fix_caching=None,
                 marking_to_activity_caching=None, is_reduction=False,
                 thread_maximum_ex_time=TechnicalParameters.MAX_DEF_THR_EX_TIME.value,
                 cleaning_token_flood=False, s_components=None, trace_occurrences=1, consider_activities_not_in_model_in_fitness=False):
        """
        Constructor

        net
            Petri net
        initial_marking
            Initial marking
        final_marking
            Final marking
        trans_map
            Map between transitions labels and transitions
        enable_pltr_fitness
            Enable fitness retrieval at place/transition level
        place_fitness
            Current dictionary of places associated with unfit traces
        transition_fitness
            Current dictionary of transitions associated with unfit traces
        notexisting_activities_in_model
            Map that stores the notexisting activities in the model
            triggered in the log
        places_shortest_path_by_hidden
            Shortest paths between places by hidden transitions
        consider_remaining_in_fitness
            Boolean value telling if the remaining tokens should be considered in fitness evaluation
        activity_key
            Name of the attribute that contains the activity
        try_to_reach_final_marking_through_hidden
            Boolean value that decides if we shall try to reach the final marking through hidden transitions
        stop_immediately_unfit
            Boolean value that decides if we shall stop immediately when a non-conformance is detected
        walk_through_hidden_trans
            Boolean value that decides if we shall walk through hidden transitions in order to enable visible transitions
        post_fix_caching
            Stores the post fix caching object
        marking_to_activity_caching
            Stores the marking-to-activity cache
        is_reduction
            Expresses if the token-based replay is called in a reduction attempt
        thread_maximum_ex_time
            Alignment threads maximum allowed execution time
        cleaning_token_flood
            Decides if a cleaning of the token flood shall be operated
        s_components
            S-components of the Petri net
        trace_occurrences
            Trace weight (number of occurrences)
        """
        self.thread_is_alive = True
        self.trace = trace
        self.net = net
        self.initial_marking = initial_marking
        self.final_marking = final_marking
        self.trans_map = trans_map
        self.enable_pltr_fitness = enable_pltr_fitness
        self.place_fitness = place_fitness
        self.transition_fitness = transition_fitness
        self.notexisting_activities_in_model = notexisting_activities_in_model
        self.places_shortest_path_by_hidden = places_shortest_path_by_hidden
        self.consider_remaining_in_fitness = consider_remaining_in_fitness
        self.consider_activities_not_in_model_in_fitness = consider_activities_not_in_model_in_fitness
        self.activity_key = activity_key
        self.try_to_reach_final_marking_through_hidden = reach_mark_through_hidden
        self.stop_immediately_when_unfit = stop_immediately_when_unfit
        self.walk_through_hidden_trans = walk_through_hidden_trans
        self.post_fix_caching = post_fix_caching
        self.marking_to_activity_caching = marking_to_activity_caching
        self.is_reduction = is_reduction
        self.thread_maximum_ex_time = thread_maximum_ex_time
        self.cleaning_token_flood = cleaning_token_flood
        self.enable_postfix_cache = TechnicalParameters.ENABLE_POSTFIX_CACHE.value
        self.enable_marktoact_cache = TechnicalParameters.ENABLE_MARKTOACT_CACHE.value
        if self.is_reduction:
            self.enable_postfix_cache = True
            self.enable_marktoact_cache = True
        self.t_fit = None
        self.t_value = None
        self.act_trans = None
        self.trans_probl = None
        self.reached_marking = None
        self.enabled_trans_in_mark = None
        self.missing = None
        self.consumed = None
        self.remaining = None
        self.produced = None
        self.s_components = s_components
        self.trace_occurrences = trace_occurrences

    def run(self):
        """
        Runs the thread and stores the results
        """
        self.t_fit, self.t_value, self.act_trans, self.trans_probl, self.reached_marking, self.enabled_trans_in_mark, self.missing, self.consumed, self.remaining, self.produced = \
            apply_trace(self.trace, self.net, self.initial_marking, self.final_marking, self.trans_map,
                        self.enable_pltr_fitness, self.place_fitness, self.transition_fitness,
                        self.notexisting_activities_in_model,
                        self.places_shortest_path_by_hidden, self.consider_remaining_in_fitness,
                        activity_key=self.activity_key,
                        try_to_reach_final_marking_through_hidden=self.try_to_reach_final_marking_through_hidden,
                        stop_immediately_unfit=self.stop_immediately_when_unfit,
                        walk_through_hidden_trans=self.walk_through_hidden_trans,
                        post_fix_caching=self.post_fix_caching,
                        marking_to_activity_caching=self.marking_to_activity_caching,
                        is_reduction=self.is_reduction,
                        thread_maximum_ex_time=self.thread_maximum_ex_time,
                        enable_postfix_cache=self.enable_postfix_cache,
                        enable_marktoact_cache=self.enable_marktoact_cache,
                        cleaning_token_flood=self.cleaning_token_flood,
                        s_components=self.s_components,
                        trace_occurrences=self.trace_occurrences,
                        consider_activities_not_in_model_in_fitness=self.consider_activities_not_in_model_in_fitness)
        self.thread_is_alive = False


class PostFixCaching:
    """
    Post fix caching object
    """

    def __init__(self):
        self.cache = 0
        self.cache = {}


class MarkingToActivityCaching:
    """
    Marking to activity caching
    """

    def __init__(self):
        self.cache = 0
        self.cache = {}


def get_variant_from_trace(trace, activity_key, disable_variants=False):
    """
    Gets the variant from the trace (allow disabling)

    Parameters
    ------------
    trace
        Trace
    activity_key
        Attribute that is the activity
    disable_variants
        Boolean value that disable variants

    Returns
    -------------
    variant
        Variant describing the trace
    """
    if disable_variants:
        return str(hash(trace))
    parameters = {}
    parameters[variants_util.Parameters.ACTIVITY_KEY] = activity_key
    return variants_util.get_variant_from_trace(trace, parameters=parameters)


def transcribe_result(t, return_object_names=True):
    corr_value = {"trace_is_fit": copy(t.t_fit),
                  "trace_fitness": float(copy(t.t_value)),
                  "activated_transitions": copy(t.act_trans),
                  "reached_marking": copy(t.reached_marking),
                  "enabled_transitions_in_marking": copy(
                      t.enabled_trans_in_mark),
                  "transitions_with_problems": copy(
                      t.trans_probl),
                  "missing_tokens": int(t.missing),
                  "consumed_tokens": int(t.consumed),
                  "remaining_tokens": int(t.remaining),
                  "produced_tokens": int(t.produced)}

    if return_object_names:
        corr_value["activated_transitions_labels"] = [x.label for x in
                                                      corr_value[
                                                          "activated_transitions"]]
        corr_value["activated_transitions"] = [x.name for x in corr_value[
            "activated_transitions"]]
        corr_value["enabled_transitions_in_marking_labels"] = [x.label for x in
                                                               corr_value[
                                                                   "enabled_transitions_in_marking"]]
        corr_value["enabled_transitions_in_marking"] = [x.name for x in
                                                        corr_value[
                                                            "enabled_transitions_in_marking"]]
        corr_value["transitions_with_problems"] = [x.name for x in
                                                   corr_value[
                                                       "transitions_with_problems"]]
        corr_value["reached_marking"] = {x.name: y for x, y in
                                         corr_value[
                                             "reached_marking"].items()}

    return corr_value


def apply_log(log, net, initial_marking, final_marking, enable_pltr_fitness=False, consider_remaining_in_fitness=False,
              activity_key="concept:name", reach_mark_through_hidden=True, stop_immediately_unfit=False,
              walk_through_hidden_trans=True, places_shortest_path_by_hidden=None,
              is_reduction=False, thread_maximum_ex_time=TechnicalParameters.MAX_DEF_THR_EX_TIME.value,
              cleaning_token_flood=False, disable_variants=False, return_object_names=False, show_progress_bar=True,
              consider_activities_not_in_model_in_fitness=False, case_id_key=constants.CASE_CONCEPT_NAME):
    """
    Apply token-based replay to a log

    Parameters
    ----------
    log
        Trace log
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    enable_pltr_fitness
        Enable fitness retrieval at place level
    consider_remaining_in_fitness
        Boolean value telling if the remaining tokens should be considered in fitness evaluation
    activity_key
        Name of the attribute that contains the activity
    reach_mark_through_hidden
        Boolean value that decides if we shall try to reach the final marking through hidden transitions
    stop_immediately_unfit
        Boolean value that decides if we shall stop immediately when a non-conformance is detected
    walk_through_hidden_trans
        Boolean value that decides if we shall walk through hidden transitions in order to enable visible transitions
    places_shortest_path_by_hidden
        Shortest paths between places by hidden transitions
    is_reduction
        Expresses if the token-based replay is called in a reduction attempt
    thread_maximum_ex_time
        Alignment threads maximum allowed execution time
    cleaning_token_flood
        Decides if a cleaning of the token flood shall be operated
    disable_variants
        Disable variants grouping
    return_object_names
        Decides whether names instead of object pointers shall be returned
    """
    post_fix_cache = PostFixCaching()
    marking_to_activity_cache = MarkingToActivityCaching()
    if places_shortest_path_by_hidden is None:
        places_shortest_path_by_hidden = get_places_shortest_path_by_hidden(net,
                                                                            TechnicalParameters.MAX_REC_DEPTH.value)

    place_fitness_per_trace = {}
    transition_fitness_per_trace = {}

    aligned_traces = []

    if enable_pltr_fitness:
        for place in net.places:
            place_fitness_per_trace[place] = {"underfed_traces": set(), "overfed_traces": set(), "m": 0, "r": 0, "c": 0,
                                              "p": 0}
        for transition in net.transitions:
            if transition.label:
                transition_fitness_per_trace[transition] = {"underfed_traces": {}, "fit_traces": {}}

    s_components = []

    if cleaning_token_flood:
        s_components = get_s_components_from_petri(net, initial_marking, final_marking)

    notexisting_activities_in_model = {}

    # update 23/04/2024 (removing undeterminism with duplicate transitions)
    # transitions are now fired as follows:
    # - (from a previous update on 14/10/2020) it is checked if in the current market any transition having as label the current activity is enabled. If that's true, then the given transition is fired
    # - otherwise, if there are no corresponding transitions enabled in the current marking, the TBR tries to enable with invisibles always the same transition (removing undeterminism)
    trans_map = {}
    for t in sorted(list(net.transitions), key=lambda x: x.name):
        trans_map[t.label] = t

    if pandas_utils.check_is_pandas_dataframe(log):
        traces = [(tuple(x), y) for y, x in log.groupby(case_id_key)[activity_key].agg(list).to_dict().items()]
        traces = [(traces[i][0], i) for i in range(len(traces))]
    else:
        traces = [(tuple(x[activity_key] for x in log[i]), i) for i in range(len(log))]

    variants = dict()
    for t in traces:
        if t[0] not in variants:
            variants[t[0]] = list()
        variants[t[0]].append(t[1])

    traces = [t[0] for t in traces]

    vc = [(k, v) for k, v in variants.items()]
    vc = list(sorted(vc, key=lambda x: (len(x[1]), x[0]), reverse=True))

    threads_results = {}

    progress = None

    if importlib.util.find_spec("tqdm") and show_progress_bar and len(variants) > 1:
        from tqdm.auto import tqdm

        if disable_variants and not pandas_utils.check_is_pandas_dataframe(log):
            progress = tqdm(total=len(traces), desc="replaying log with TBR, completed traces :: ")
        else:
            progress = tqdm(total=len(variants), desc="replaying log with TBR, completed traces :: ")

    for i in range(len(vc)):
        variant = vc[i][0]
        all_cases = vc[i][1]

        if disable_variants and not pandas_utils.check_is_pandas_dataframe(log):
            for j in range(len(all_cases)):
                case_position = all_cases[j]
                considered_case = log[case_position]
                t = ApplyTraceTokenReplay(considered_case, net, initial_marking, final_marking,
                                          trans_map, enable_pltr_fitness, place_fitness_per_trace,
                                          transition_fitness_per_trace,
                                          notexisting_activities_in_model,
                                          places_shortest_path_by_hidden,
                                          consider_remaining_in_fitness,
                                          activity_key=activity_key,
                                          reach_mark_through_hidden=reach_mark_through_hidden,
                                          stop_immediately_when_unfit=stop_immediately_unfit,
                                          walk_through_hidden_trans=walk_through_hidden_trans,
                                          post_fix_caching=post_fix_cache,
                                          marking_to_activity_caching=marking_to_activity_cache,
                                          is_reduction=is_reduction,
                                          thread_maximum_ex_time=thread_maximum_ex_time,
                                          cleaning_token_flood=cleaning_token_flood,
                                          s_components=s_components, trace_occurrences=1,
                                          consider_activities_not_in_model_in_fitness=consider_activities_not_in_model_in_fitness)
                t.run()
                threads_results[case_position] = transcribe_result(t, return_object_names=return_object_names)
                if progress is not None:
                    progress.update()
        else:
            considered_case = variants_util.variant_to_trace(variant, parameters={constants.PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key})
            t = ApplyTraceTokenReplay(considered_case, net, initial_marking, final_marking,
                                                     trans_map, enable_pltr_fitness, place_fitness_per_trace,
                                                     transition_fitness_per_trace,
                                                     notexisting_activities_in_model,
                                                     places_shortest_path_by_hidden,
                                                     consider_remaining_in_fitness,
                                                     activity_key=activity_key,
                                                     reach_mark_through_hidden=reach_mark_through_hidden,
                                                     stop_immediately_when_unfit=stop_immediately_unfit,
                                                     walk_through_hidden_trans=walk_through_hidden_trans,
                                                     post_fix_caching=post_fix_cache,
                                                     marking_to_activity_caching=marking_to_activity_cache,
                                                     is_reduction=is_reduction,
                                                     thread_maximum_ex_time=thread_maximum_ex_time,
                                                     cleaning_token_flood=cleaning_token_flood,
                                                     s_components=s_components, trace_occurrences=len(vc[i][1]),
                                                     consider_activities_not_in_model_in_fitness=consider_activities_not_in_model_in_fitness)
            t.run()

            for j in range(len(all_cases)):
                case_position = all_cases[j]

                threads_results[case_position] = transcribe_result(t, return_object_names=return_object_names)

            if progress is not None:
                progress.update()

    for i in range(len(traces)):
        aligned_traces.append(threads_results[i])

    # gracefully close progress bar
    if progress is not None:
        progress.close()
    del progress

    if enable_pltr_fitness:
        return aligned_traces, place_fitness_per_trace, transition_fitness_per_trace, notexisting_activities_in_model
    else:
        return aligned_traces


def apply(log: EventLog, net: PetriNet, initial_marking: Marking, final_marking: Marking, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> typing.ListAlignments:
    """
    Method to apply token-based replay

    Parameters
    -----------
    log
        Log
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    parameters
        Parameters of the algorithm
    """
    if parameters is None:
        parameters = {}

    enable_pltr_fitness = exec_utils.get_param_value(Parameters.ENABLE_PLTR_FITNESS, parameters, False)
    # changed default to uniform behavior with token-based replay fitness
    consider_remaining_in_fitness = exec_utils.get_param_value(Parameters.CONSIDER_REMAINING_IN_FITNESS, parameters,
                                                               True)
    try_to_reach_final_marking_through_hidden = exec_utils.get_param_value(
        Parameters.TRY_TO_REACH_FINAL_MARKING_THROUGH_HIDDEN, parameters, True)
    stop_immediately_unfit = exec_utils.get_param_value(Parameters.STOP_IMMEDIATELY_UNFIT, parameters, False)
    walk_through_hidden_trans = exec_utils.get_param_value(Parameters.WALK_THROUGH_HIDDEN_TRANS, parameters, True)
    is_reduction = exec_utils.get_param_value(Parameters.IS_REDUCTION, parameters, False)
    cleaning_token_flood = exec_utils.get_param_value(Parameters.CLEANING_TOKEN_FLOOD, parameters, False)
    disable_variants = exec_utils.get_param_value(Parameters.DISABLE_VARIANTS, parameters, enable_pltr_fitness)
    return_names = exec_utils.get_param_value(Parameters.RETURN_NAMES, parameters, False)
    thread_maximum_ex_time = exec_utils.get_param_value(Parameters.THREAD_MAX_EX_TIME, parameters,
                                                        TechnicalParameters.MAX_DEF_THR_EX_TIME.value)
    places_shortest_path_by_hidden = exec_utils.get_param_value(Parameters.PLACES_SHORTEST_PATH_BY_HIDDEN, parameters,
                                                                None)
    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_util.DEFAULT_NAME_KEY)
    consider_activities_not_in_model_in_fitness = exec_utils.get_param_value(Parameters.CONSIDER_ACTIVITIES_NOT_IN_MODEL_IN_FITNESS, parameters, False)

    show_progress_bar = exec_utils.get_param_value(Parameters.SHOW_PROGRESS_BAR, parameters, constants.SHOW_PROGRESS_BAR)
    case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, constants.CASE_CONCEPT_NAME)

    if type(log) is not pd.DataFrame:
        log = log_converter.apply(log, variant=log_converter.Variants.TO_EVENT_LOG, parameters=parameters)

    return apply_log(log, net, initial_marking, final_marking, enable_pltr_fitness=enable_pltr_fitness,
                     consider_remaining_in_fitness=consider_remaining_in_fitness,
                     reach_mark_through_hidden=try_to_reach_final_marking_through_hidden,
                     stop_immediately_unfit=stop_immediately_unfit,
                     walk_through_hidden_trans=walk_through_hidden_trans,
                     places_shortest_path_by_hidden=places_shortest_path_by_hidden, activity_key=activity_key,
                     is_reduction=is_reduction, thread_maximum_ex_time=thread_maximum_ex_time,
                     cleaning_token_flood=cleaning_token_flood, disable_variants=disable_variants,
                     return_object_names=return_names, show_progress_bar=show_progress_bar,
                     consider_activities_not_in_model_in_fitness=consider_activities_not_in_model_in_fitness,
                     case_id_key=case_id_key)


def apply_variants_list(variants_list, net, initial_marking, final_marking, parameters=None):
    if parameters is None:
        parameters = {}
    parameters[Parameters.RETURN_NAMES] = True

    log = log_implementation.EventLog()
    for var_item in variants_list:
        trace = variants_util.variant_to_trace(var_item[0], parameters=parameters)

        log.append(trace)

    return apply(log, net, initial_marking, final_marking, parameters=parameters)


def apply_variants_dictionary(variants, net, initial_marking, final_marking, parameters=None):
    if parameters is None:
        parameters = {}

    var_list = {x: len(y) for x, y in variants.items()}
    return apply_variants_list(var_list, net, initial_marking, final_marking, parameters=parameters)


def apply_variants_list_petri_string(variants_list, petri_string, parameters=None):
    if parameters is None:
        parameters = {}

    from pm4py.objects.petri_net.importer.variants import pnml as petri_importer

    net, im, fm = petri_importer.import_petri_from_string(petri_string, parameters=parameters)

    return apply_variants_list(variants_list, net, im, fm, parameters=parameters)


def apply_variants_list_petri_string_multiprocessing(output, variants_list, petri_string, parameters=None):
    if parameters is None:
        parameters = {}

    ret = apply_variants_list_petri_string(variants_list, petri_string, parameters=parameters)

    output.put(ret)


def get_diagnostics_dataframe(log: EventLog, tbr_output: typing.ListAlignments, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> pd.DataFrame:
    """
    Gets the results of token-based replay in a dataframe

    Parameters
    --------------
    log
        Event log
    tbr_output
        Output of the token-based replay technique

    Returns
    --------------
    dataframe
        Diagnostics dataframe
    """
    if parameters is None:
        parameters = {}

    case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, xes_util.DEFAULT_TRACEID_KEY)

    import pandas as pd

    diagn_stream = []

    for index in range(len(log)):
        case_id = log[index].attributes[case_id_key]
        is_fit = tbr_output[index]["trace_is_fit"]
        trace_fitness = tbr_output[index]["trace_fitness"]
        missing = tbr_output[index]["missing_tokens"]
        remaining = tbr_output[index]["remaining_tokens"]
        produced = tbr_output[index]["produced_tokens"]
        consumed = tbr_output[index]["consumed_tokens"]

        diagn_stream.append({"case_id": case_id, "is_fit": is_fit, "trace_fitness": trace_fitness, "missing": missing, "remaining": remaining, "produced": produced, "consumed": consumed})

    return pandas_utils.instantiate_dataframe(diagn_stream)
