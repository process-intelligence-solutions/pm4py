import pm4py
from pm4py.algo.filtering.dfg import dfg_filtering
from pm4py.algo.simulation.playout.dfg.variants import classic as dfg_playout
from examples import examples_conf
import importlib.util
import os
import pandas
from pm4py.objects.log.obj import EventLog, Trace


def execute_script():
    log: pandas.DataFrame = pm4py.read_xes(os.path.join("..", "tests", "input_data", "receipt.xes"))
    activities: dict[str, int] = pm4py.get_event_attribute_values(log, "concept:name")
    dfg: dict
    sa: dict
    ea: dict
    dfg, sa, ea = pm4py.discover_dfg(log)
    # filters the DFG to make a simpler one
    perc: float = 0.5
    dfg, sa, ea, activities = dfg_filtering.filter_dfg_on_activities_percentage(dfg, sa, ea, activities, perc)
    dfg, sa, ea, activities = dfg_filtering.filter_dfg_on_paths_percentage(dfg, sa, ea, activities, perc)
    # creates the simulated log
    simulated_log: EventLog | dict[tuple[str, str], int] = dfg_playout.apply(dfg, sa, ea)
    print(simulated_log)
    print(len(simulated_log))
    print(sum(x.attributes["probability"] for x in simulated_log))
    # shows the two DFGs to show that they are identical

    if importlib.util.find_spec("graphviz"):
        pm4py.view_dfg(dfg, sa, ea, format=examples_conf.TARGET_IMG_FORMAT)
    new_dfg: dict
    new_sa: dict
    new_ea: dict
    new_dfg, new_sa, new_ea = pm4py.discover_dfg(simulated_log)

    if importlib.util.find_spec("graphviz"):
        pm4py.view_dfg(new_dfg, new_sa, new_ea, format=examples_conf.TARGET_IMG_FORMAT)

    for trace in simulated_log:
        print(list(x["concept:name"] for x in trace))
        print(trace.attributes["probability"], dfg_playout.get_trace_probability(trace, dfg, sa, ea))
        break
    dfg, sa, ea = pm4py.discover_dfg(log)
    variants: dict[tuple[str], list[Trace]] = pm4py.get_variants_as_tuples(pm4py.convert_to_event_log(log))
    sum_prob_log_variants: float = 0.0
    for var in variants:
        sum_prob_log_variants += dfg_playout.get_trace_probability(variants[var][0], dfg, sa, ea)
    print("percentage of behavior allowed from DFG that is in the log (from 0.0 to 1.0): ", sum_prob_log_variants)


if __name__ == "__main__":
    execute_script()
