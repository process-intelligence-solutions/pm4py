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
__doc__ = """
The ``pm4py.discovery`` module contains the process discovery algorithms implemented in ``pm4py``.
"""

import importlib.util
from collections import Counter
from typing import Tuple, Union, List, Dict, Any, Optional, Set, TextIO

import pandas as pd
from pandas import DataFrame

from pm4py.algo.discovery.enhanced_process_tree.algorithm import Variant as EnhancedTreeVariant
from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.dfg.obj import DFG
from pm4py.objects.heuristics_net.obj import HeuristicsNet
from pm4py.objects.log.obj import EventLog
from pm4py.objects.log.obj import EventStream
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.powl.obj import POWL
from pm4py.objects.process_tree.obj import ProcessTree, EnhancedProcessTree
from pm4py.objects.transition_system.obj import TransitionSystem
from pm4py.objects.trie.obj import Trie
from pm4py.util import constants
from pm4py.util import deprecation
from pm4py.util.pandas_utils import (
    check_is_pandas_dataframe,
    check_pandas_dataframe_columns,
)
from pm4py.utils import get_properties, __event_log_deprecation_warning, is_polars_lazyframe


def discover_dfg(
        log: Union[EventLog, pd.DataFrame],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[dict, dict, dict]:
    """
    Discovers a Directly-Follows Graph (DFG) from a log.

    This method returns a tuple containing:

    - A dictionary with pairs of directly-following activities as keys and the frequency of the relationship as values.
    - A dictionary of start activities with their respective frequencies.
    - A dictionary of end activities with their respective frequencies.

    :param log: Event log or Pandas DataFrame.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A tuple of three dictionaries: (dfg, start_activities, end_activities).
    :rtype: ``Tuple[dict, dict, dict]``

    .. code-block:: python3

        import pm4py

        dfg, start_activities, end_activities = pm4py.discover_dfg(
            dataframe,
            case_id_key='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )
        from pm4py.util import constants

        if is_polars_lazyframe(log):
            from pm4py.algo.discovery.dfg.adapters.polars.df_statistics import get_dfg_graph
            from pm4py.statistics.start_activities.polars import get as start_activities_module
            from pm4py.statistics.end_activities.polars import get as end_activities_module
        else:
            from pm4py.algo.discovery.dfg.adapters.pandas.df_statistics import (
                get_dfg_graph,
            )
            from pm4py.statistics.start_activities.pandas import (
                get as start_activities_module,
            )
            from pm4py.statistics.end_activities.pandas import (
                get as end_activities_module,
            )

        dfg = get_dfg_graph(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_glue=case_id_key,
        )

        start_activities = start_activities_module.get_start_activities(
            log, parameters=properties
        )
        end_activities = end_activities_module.get_end_activities(
            log, parameters=properties
        )
    else:
        from pm4py.algo.discovery.dfg import algorithm as dfg_discovery

        dfg = dfg_discovery.apply(log, parameters=properties)
        from pm4py.statistics.start_activities.log import (
            get as start_activities_module,
        )
        from pm4py.statistics.end_activities.log import (
            get as end_activities_module,
        )

        start_activities = start_activities_module.get_start_activities(
            log, parameters=properties
        )
        end_activities = end_activities_module.get_end_activities(
            log, parameters=properties
        )
    return dfg, start_activities, end_activities


def discover_directly_follows_graph(
        log: Union[EventLog, pd.DataFrame],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[dict, dict, dict]:
    return discover_dfg(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )


def discover_dfg_typed(
        log: pd.DataFrame,
        case_id_key: str = "case:concept:name",
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
) -> DFG:
    """
    Discovers a typed Directly-Follows Graph (DFG) from a log.

    This method returns a typed DFG object, as specified in ``pm4py.objects.dfg.obj.py`` (``DirectlyFollowsGraph`` Class).
    The DFG object includes the graph, start activities, and end activities.
    - The graph is a collection of triples of the form (a, b, f) representing an arc a->b with frequency f.
    - The start activities are a collection of tuples of the form (a, f) representing that activity a starts f cases.
    - The end activities are a collection of tuples of the form (a, f) representing that activity a ends f cases.

    This method replaces ``pm4py.discover_dfg`` and ``pm4py.discover_directly_follows_graph``. In future releases, these functions will adopt the same behavior as this function.

    :param log: ``pandas.DataFrame``
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :return: A typed DFG object containing the graph, start activities, and end activities.
    :rtype: ``DFG``

    .. code-block:: python3

        import pm4py

        dfg = pm4py.discover_dfg_typed(
            log,
            case_id_key='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )
    """
    from pm4py.objects.dfg.obj import DFG

    dfg, sa, ea = discover_dfg(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    return DFG(dfg, sa, ea)


def discover_performance_dfg(
        log: Union[EventLog, pd.DataFrame],
        business_hours: bool = False,
        business_hour_slots=constants.DEFAULT_BUSINESS_HOUR_SLOTS,
        workcalendar=constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        perf_aggregation_key: str = "all",
) -> Tuple[dict, dict, dict]:
    """
    Discovers a Performance Directly-Follows Graph from an event log.

    This method returns a tuple containing:

    - A dictionary with pairs of directly-following activities as keys and the performance metrics of the relationship as values.
    - A dictionary of start activities with their respective frequencies.
    - A dictionary of end activities with their respective frequencies.

    :param log: Event log or Pandas DataFrame.
    :param business_hours: Enables or disables computation based on business hours (default: False).
    :param business_hour_slots: Work schedule of the company, provided as a list of tuples where each tuple represents one time slot of business hours. Each slot consists of a start and end time given in seconds since the week start.

    Example::

            [
                (7 * 60 * 60, 17 * 60 * 60),  # Monday 07:00 - 17:00
                ((24 + 7) * 60 * 60, (24 + 12) * 60 * 60),  # Tuesday 07:00 - 12:00
                ((24 + 13) * 60 * 60, (24 + 17) * 60 * 60)   # Tuesday 13:00 - 17:00
            ]

    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param perf_aggregation_key: Selector for the type of aggregation (all, mean, median, max, min, sum, stdev)
    :return: A tuple of three dictionaries: (performance_dfg, start_activities, end_activities).
    :rtype: ``Tuple[dict, dict, dict]``

    .. code-block:: python3

        import pm4py

        performance_dfg, start_activities, end_activities = pm4py.discover_performance_dfg(
            dataframe,
            case_id_key='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )
        from pm4py.util import constants

        if is_polars_lazyframe(log):
            from pm4py.algo.discovery.dfg.adapters.polars.df_statistics import get_dfg_graph
            from pm4py.statistics.start_activities.polars import get as start_activities_module
            from pm4py.statistics.end_activities.polars import get as end_activities_module
        else:
            from pm4py.algo.discovery.dfg.adapters.pandas.df_statistics import (
                get_dfg_graph,
            )
            from pm4py.statistics.start_activities.pandas import (
                get as start_activities_module,
            )
            from pm4py.statistics.end_activities.pandas import (
                get as end_activities_module,
            )

        dfg = get_dfg_graph(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_glue=case_id_key,
            measure="performance",
            perf_aggregation_key=perf_aggregation_key,
            business_hours=business_hours,
            business_hours_slot=business_hour_slots,
            workcalendar=workcalendar,
        )

        start_activities = start_activities_module.get_start_activities(
            log, parameters=properties
        )
        end_activities = end_activities_module.get_end_activities(
            log, parameters=properties
        )
    else:
        from pm4py.algo.discovery.dfg.variants import (
            performance as dfg_discovery,
        )

        properties[dfg_discovery.Parameters.AGGREGATION_MEASURE] = (
            perf_aggregation_key
        )
        properties[dfg_discovery.Parameters.BUSINESS_HOURS] = business_hours
        properties[dfg_discovery.Parameters.BUSINESS_HOUR_SLOTS] = (
            business_hour_slots
        )
        dfg = dfg_discovery.apply(log, parameters=properties)
        from pm4py.statistics.start_activities.log import (
            get as start_activities_module,
        )
        from pm4py.statistics.end_activities.log import (
            get as end_activities_module,
        )

        start_activities = start_activities_module.get_start_activities(
            log, parameters=properties
        )
        end_activities = end_activities_module.get_end_activities(
            log, parameters=properties
        )
    return dfg, start_activities, end_activities


def discover_petri_net_alpha(
        log: Union[EventLog, pd.DataFrame],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using the Alpha Miner.

    :param log: Event log or Pandas DataFrame.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A tuple containing the Petri net, initial marking, and final marking.
    :rtype: ``Tuple[PetriNet, Marking, Marking]``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_alpha(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    from pm4py.algo.discovery.alpha import algorithm as alpha_miner

    return alpha_miner.apply(
        log,
        variant=alpha_miner.Variants.ALPHA_VERSION_CLASSIC,
        parameters=get_properties(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        ),
    )


def discover_petri_net_ilp(
        log: Union[EventLog, pd.DataFrame],
        alpha: float = 1.0,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using the ILP Miner.

    :param log: Event log or Pandas DataFrame.
    :param alpha: Noise threshold for the sequence encoding graph (1.0=no filtering, 0.0=maximum filtering) (default: 1.0).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A tuple containing the Petri net, initial marking, and final marking.
    :rtype: ``Tuple[PetriNet, Marking, Marking]``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_ilp(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    parameters = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    parameters["alpha"] = alpha

    from pm4py.algo.discovery.ilp import algorithm as ilp_miner

    return ilp_miner.apply(
        log, variant=ilp_miner.Variants.CLASSIC, parameters=parameters
    )


def discover_petri_net_genetic(
        log: Union[EventLog, pd.DataFrame],
        population_size: int = 500,
        elitism_rate: float = 0.01,
        crossover_rate: float = 1.0,
        mutation_rate: float = 0.01,
        generations: int = 100,
        elitism_min_sample: int = 5,
        log_csv: TextIO = None,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using the Genetic Miner.

    Reference paper:
    Maximilian Josef Frank. "Optimising and Implementing the Genetic Miner in PM4Py" (2026).

    :param log: Event log or Pandas DataFrame.
    :param population_size: Population size of genetic sampling (default: 500).
    :param elitism_rate: Rate of best models used in next generation (default: 0.01).
    :param crossover_rate: Rate of genetically combined models (offsprings) used in next generation (default: 1.0).
    :param mutation_rate: Random model mutation rate (default: 0.01).
    :param generations: Iterations of model improvement (default: 100).
    :param elitism_min_sample: Minimum sample size for selecting best models (default: 5).
    :param log_csv: Output stream for CSV log (default: None).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A tuple containing the Petri net, initial marking, and final marking.
    :rtype: ``Tuple[PetriNet, Marking, Marking]``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_genetic(
            dataframe,
            activity_key='concept:name',
            timestamp_key='time:timestamp',
            case_id_key='case:concept:name'
        )
    """
    __event_log_deprecation_warning(log)

    from pm4py.algo.discovery.genetic import algorithm as genetic_miner

    genetic_parameters = genetic_miner.Parameters
    parameters = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    parameters[genetic_parameters.POPULATION_SIZE] = population_size
    parameters[genetic_parameters.ELITISM_RATE] = elitism_rate
    parameters[genetic_parameters.CROSSOVER_RATE] = crossover_rate
    parameters[genetic_parameters.MUTATION_RATE] = mutation_rate
    parameters[genetic_parameters.GENERATIONS] = generations
    parameters[genetic_parameters.ELITISM_MIN_SAMPLE] = elitism_min_sample
    parameters[genetic_parameters.LOG_CSV] = log_csv

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    return genetic_miner.apply(
        log,
        variant=genetic_miner.Variants.CLASSIC,
        parameters=parameters,
    )


@deprecation.deprecated(
    deprecated_in="2.3.0",
    removed_in="3.0.0",
    details="This method will be removed in a future release.",
)
def discover_petri_net_alpha_plus(
        log: Union[EventLog, pd.DataFrame],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using the Alpha+ algorithm.

    .. deprecated:: 2.3.0
        This method will be removed in version 3.0.0. Use other discovery methods instead.

    :param log: Event log or Pandas DataFrame.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A tuple containing the Petri net, initial marking, and final marking.
    :rtype: ``Tuple[PetriNet, Marking, Marking]``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_alpha_plus(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    from pm4py.algo.discovery.alpha import algorithm as alpha_miner

    return alpha_miner.apply(
        log,
        variant=alpha_miner.Variants.ALPHA_VERSION_PLUS,
        parameters=get_properties(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        ),
    )


def discover_petri_net_inductive(
        log: Union[EventLog, pd.DataFrame, DFG],
        multi_processing: bool = constants.ENABLE_MULTIPROCESSING_DEFAULT,
        noise_threshold: float = 0.0,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        disable_fallthroughs: bool = False,
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using the Inductive Miner algorithm.

    The Inductive Miner detects a 'cut' in the log (e.g., sequential, parallel, concurrent, loop) and recursively applies the algorithm to sublogs until a base case is found.
    Inductive miner models typically use hidden transitions for skipping or looping portions of the model, and each visible transition has a unique label.

    :param log: Event log, Pandas DataFrame, or typed DFG.
    :param multi_processing: Enables or disables multiprocessing in the Inductive Miner (default: constants.ENABLE_MULTIPROCESSING_DEFAULT).
    :param noise_threshold: Noise threshold (default: 0.0).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param disable_fallthroughs: Disables the Inductive Miner fall-throughs (default: False).
    :return: A tuple containing the Petri net, initial marking, and final marking.
    :rtype: ``Tuple[PetriNet, Marking, Marking]``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_inductive(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    pt = discover_process_tree_inductive(
        log,
        noise_threshold,
        multi_processing=multi_processing,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
        disable_fallthroughs=disable_fallthroughs,
    )
    from pm4py.convert import convert_to_petri_net

    return convert_to_petri_net(pt)


def discover_petri_net_heuristics(
        log: Union[EventLog, pd.DataFrame],
        dependency_threshold: float = 0.5,
        and_threshold: float = 0.65,
        loop_two_threshold: float = 0.5,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using the Heuristics Miner.

    Heuristics Miner operates on the Directly-Follows Graph, handling noise and identifying common constructs such as dependencies between activities and parallelism.
    The output is a Heuristics Net, which can then be converted into a Petri net.

    :param log: Event log or Pandas DataFrame.
    :param dependency_threshold: Dependency threshold (default: 0.5).
    :param and_threshold: AND threshold for parallelism (default: 0.65).
    :param loop_two_threshold: Loop two threshold (default: 0.5).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A tuple containing the Petri net, initial marking, and final marking.
    :rtype: ``Tuple[PetriNet, Marking, Marking]``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_heuristics(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    from pm4py.algo.discovery.heuristics.variants import (
        classic as heuristics_miner,
    )

    heu_parameters = heuristics_miner.Parameters
    parameters = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    parameters[heu_parameters.DEPENDENCY_THRESH] = dependency_threshold
    parameters[heu_parameters.AND_MEASURE_THRESH] = and_threshold
    parameters[heu_parameters.LOOP_LENGTH_TWO_THRESH] = loop_two_threshold

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )
        return heuristics_miner.apply_pandas(log, parameters=parameters)
    else:
        return heuristics_miner.apply(log, parameters=parameters)


def discover_process_tree_inductive(
        log: Union[EventLog, pd.DataFrame, DFG],
        noise_threshold: float = 0.0,
        multi_processing: bool = constants.ENABLE_MULTIPROCESSING_DEFAULT,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        disable_fallthroughs: bool = False,
) -> ProcessTree:
    """
    Discovers a Process Tree using the Inductive Miner algorithm.

    The Inductive Miner detects a 'cut' in the log (e.g., sequential, parallel, concurrent, loop) and recursively applies the algorithm to sublogs until a base case is found.
    Inductive miner models typically use hidden transitions for skipping or looping portions of the model, and each visible transition has a unique label.

    :param log: Event log, Pandas DataFrame, or typed DFG.
    :param noise_threshold: Noise threshold (default: 0.0).
    :param multi_processing: Enables or disables multiprocessing in the Inductive Miner (default: constants.ENABLE_MULTIPROCESSING_DEFAULT).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param disable_fallthroughs: Disables the Inductive Miner fall-throughs (default: False).
    :return: A ProcessTree object.
    :rtype: ``ProcessTree``

    .. code-block:: python3

        import pm4py

        process_tree = pm4py.discover_process_tree_inductive(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    from pm4py.algo.discovery.inductive import algorithm as inductive_miner

    parameters = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    parameters["noise_threshold"] = noise_threshold
    parameters["multiprocessing"] = multi_processing
    parameters["disable_fallthroughs"] = disable_fallthroughs

    variant = (
        inductive_miner.Variants.IMf
        if noise_threshold > 0
        else inductive_miner.Variants.IM
    )

    if isinstance(log, DFG):
        variant = inductive_miner.Variants.IMd

    return inductive_miner.apply(log, variant=variant, parameters=parameters)


def discover_enhanced_process_tree(
        log: Union[EventLog, pd.DataFrame],
        variant: EnhancedTreeVariant = EnhancedTreeVariant.REFINEMENT_HYBRID,
        noise_threshold: float = 0.0,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        limit: int = 25,
) -> EnhancedProcessTree:
    """
        Discovers an Enhanced Process Tree utilizing dynamic routing annotations (start, stop, skip).

        The algorithm supports three distinct architectural variants:
        1. REFINEMENT_HYBRID: Utilizes Log Refinement to synthesize a compressed log and
           simultaneously extracts topological skip contexts. Extremely fast, bypassing alignments.
        2. ALIGNMENTS: Standard Inductive Miner discovery followed by a post-discovery
           A* conformance alignment phase to locate invisible tau (routing) deviations.
        3. REFINED_ALIGNMENTS: A hybrid pipeline that utilizes Log Refinement strictly to build
           a robust, noise-free base model, but relies on A* alignments for exception discovery.

        :param log: Event log or Pandas DataFrame.
        :param variant: The architectural pipeline to use (default: EnhancedTreeVariant.REFINEMENT_HYBRID).
        :param noise_threshold: Noise threshold applied to the underlying Inductive Miner (default: 0.0).
        :param activity_key: Attribute to be used for the activity (default: "concept:name").
        :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
        :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
        :param limit: Attribute to set the limit of repeated steps in log refinement (default: 25).
        :return: An EnhancedProcessTree object.

        .. code-block:: python3

            import pm4py
            from pm4py.algo.discovery.enhanced_process_tree.algorithm import Variant

            # Example: Using the fast Log Refinement hybrid pipeline
            process_tree = pm4py.discover_enhanced_process_tree(
                dataframe,
                variant=Variant.REFINEMENT_HYBRID
            )
        """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    from pm4py.algo.discovery.enhanced_process_tree import algorithm as enhanced_tree_discovery

    parameters = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )

    parameters[enhanced_tree_discovery.Parameters.NOISE_THRESHOLD] = noise_threshold
    parameters[enhanced_tree_discovery.Parameters.LIMIT] = limit

    return enhanced_tree_discovery.apply(log, variant=variant, parameters=parameters)


def discover_heuristics_net(
        log: Union[EventLog, pd.DataFrame],
        dependency_threshold: float = 0.5,
        and_threshold: float = 0.65,
        loop_two_threshold: float = 0.5,
        min_act_count: int = 1,
        min_dfg_occurrences: int = 1,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        decoration: str = "frequency",
) -> HeuristicsNet:
    """
    Discovers a Heuristics Net.

    Heuristics Miner operates on the Directly-Follows Graph, handling noise and identifying common constructs such as dependencies between activities and parallelism.
    The output is a Heuristics Net, which can then be converted into a Petri net.

    :param log: Event log or Pandas DataFrame.
    :param dependency_threshold: Dependency threshold (default: 0.5).
    :param and_threshold: AND threshold for parallelism (default: 0.65).
    :param loop_two_threshold: Loop two threshold (default: 0.5).
    :param min_act_count: Minimum number of occurrences per activity to be included in the discovery (default: 1).
    :param min_dfg_occurrences: Minimum number of occurrences per arc in the DFG to be included in the discovery (default: 1).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param decoration: The decoration to be used ("frequency" or "performance") (default: "frequency").
    :return: A HeuristicsNet object.
    :rtype: ``HeuristicsNet``

    .. code-block:: python3

        import pm4py

        heu_net = pm4py.discover_heuristics_net(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    from pm4py.algo.discovery.heuristics.variants import (
        classic as heuristics_miner,
    )

    heu_parameters = heuristics_miner.Parameters
    parameters = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    parameters[heu_parameters.DEPENDENCY_THRESH] = dependency_threshold
    parameters[heu_parameters.AND_MEASURE_THRESH] = and_threshold
    parameters[heu_parameters.LOOP_LENGTH_TWO_THRESH] = loop_two_threshold
    parameters[heu_parameters.MIN_ACT_COUNT] = min_act_count
    parameters[heu_parameters.MIN_DFG_OCCURRENCES] = min_dfg_occurrences
    parameters[heu_parameters.HEU_NET_DECORATION] = decoration

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )
        return heuristics_miner.apply_heu_pandas(log, parameters=parameters)
    else:
        return heuristics_miner.apply_heu(log, parameters=parameters)


def derive_minimum_self_distance(
        log: Union[DataFrame, EventLog, EventStream],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Dict[str, int]:
    """
    Computes the minimum self-distance for each activity observed in an event log.

    The self-distance of activity `a` in `<a>` is infinity,
    in `<a, a>` is 0,
    in `<a, b, a>` is 1,
    etc. The activity key 'concept:name' is used.

    :param log: Event log or Pandas DataFrame.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A dictionary mapping each activity to its minimum self-distance.
    :rtype: ``Dict[str, int]``

    .. code-block:: python3

        import pm4py

        msd = pm4py.derive_minimum_self_distance(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    from pm4py.algo.discovery.minimum_self_distance import algorithm as msd

    return msd.apply(
        log,
        parameters=get_properties(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        ),
    )


def discover_footprints(
        *args: Union[EventLog, Tuple[PetriNet, Marking, Marking], ProcessTree, POWL]
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Discovers the footprints from the provided event log or process model.

    Footprints are a high-level representation of the behavior captured in the event log or process model.

    :param args: Event log, process model (Petri net and markings), or ProcessTree, or POWL.
    :return: A list of footprint dictionaries or a single footprint dictionary.
    :rtype: ``Union[List[Dict[str, Any]], Dict[str, Any]]``

    .. code-block:: python3

        import pm4py

        footprints = pm4py.discover_footprints(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    from pm4py.algo.discovery.footprints import algorithm as fp_discovery

    return fp_discovery.apply(*args)


def discover_eventually_follows_graph(
        log: Union[EventLog, pd.DataFrame],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Dict[Tuple[str, str], int]:
    """
    Generates the Eventually-Follows Graph from a log.

    The Eventually-Follows Graph is a dictionary that maps each pair of activities to the number of times one activity eventually follows the other in the log.

    :param log: Event log or Pandas DataFrame.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A dictionary mapping each pair of activities to the count of their eventually-follows relationship.
    :rtype: ``Dict[Tuple[str, str], int]``

    .. code-block:: python3

        import pm4py

        efg = pm4py.discover_eventually_follows_graph(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

        if is_polars_lazyframe(log):
            from pm4py.statistics.eventually_follows.polars import get
            return get.apply(log, parameters=properties)
        else:
            from pm4py.statistics.eventually_follows.pandas import get
            return get.apply(log, parameters=properties)
    else:
        from pm4py.statistics.eventually_follows.log import get

        return get.apply(log, parameters=properties)


def discover_bpmn_inductive(
        log: Union[EventLog, pd.DataFrame, DFG],
        noise_threshold: float = 0.0,
        multi_processing: bool = constants.ENABLE_MULTIPROCESSING_DEFAULT,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        disable_fallthroughs: bool = False,
) -> BPMN:
    """
    Discovers a BPMN model using the Inductive Miner algorithm.

    The Inductive Miner detects a 'cut' in the log (e.g., sequential, parallel, concurrent, loop) and recursively applies the algorithm to sublogs until a base case is found.
    Inductive miner models typically use hidden transitions for skipping or looping portions of the model, and each visible transition has a unique label.

    :param log: Event log, Pandas DataFrame, or typed DFG.
    :param noise_threshold: Noise threshold (default: 0.0).
    :param multi_processing: Enables or disables multiprocessing in the Inductive Miner (default: constants.ENABLE_MULTIPROCESSING_DEFAULT).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param disable_fallthroughs: Disables the Inductive Miner fall-throughs (default: False).
    :return: A BPMN object representing the discovered BPMN model.
    :rtype: ``BPMN``

    .. code-block:: python3

        import pm4py

        bpmn_graph = pm4py.discover_bpmn_inductive(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    pt = discover_process_tree_inductive(
        log,
        noise_threshold,
        multi_processing=multi_processing,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
        disable_fallthroughs=disable_fallthroughs,
    )
    from pm4py.convert import convert_to_bpmn

    return convert_to_bpmn(pt)


def discover_transition_system(
        log: Union[EventLog, pd.DataFrame],
        direction: str = "forward",
        window: int = 2,
        view: str = "sequence",
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> TransitionSystem:
    """
    Discovers a Transition System from a log.

    The Transition System is built based on the specified direction, window size, and view. It captures the transitions between states of activity sequences.

    :param log: Event log or Pandas DataFrame.
    :param direction: Direction in which the transition system is built ("forward" or "backward") (default: "forward").
    :param window: Window size for state construction (e.g., 2, 3) (default: 2).
    :param view: View to use in the construction of the states ("sequence", "set", "multiset") (default: "sequence").
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A TransitionSystem object representing the discovered transition system.
    :rtype: ``TransitionSystem``

    .. code-block:: python3

        import pm4py

        transition_system = pm4py.discover_transition_system(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    properties["direction"] = direction
    properties["window"] = window
    properties["view"] = view

    from pm4py.algo.discovery.transition_system import (
        algorithm as ts_discovery,
    )

    return ts_discovery.apply(log, parameters=properties)


def discover_prefix_tree(
        log: Union[EventLog, pd.DataFrame],
        max_path_length: Optional[int] = None,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Trie:
    """
    Discovers a Prefix Tree from the provided log.

    A Prefix Tree represents all the unique prefixes of activity sequences in the log.

    :param log: Event log or Pandas DataFrame.
    :param max_path_length: maximum path length (each trace is trimmed afterwards).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A Trie object representing the discovered prefix tree.
    :rtype: ``Trie``

    .. code-block:: python3

        import pm4py

        prefix_tree = pm4py.discover_prefix_tree(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )

    properties["max_path_length"] = max_path_length

    from pm4py.algo.transformation.log_to_trie import (
        algorithm as trie_discovery,
    )

    return trie_discovery.apply(log, parameters=properties)


def discover_temporal_profile(
        log: Union[EventLog, pd.DataFrame],
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Dict[Tuple[str, str], Tuple[float, float]]:
    """
    Discovers a Temporal Profile from a log.

    Implements the approach described in:
    Stertz, Florian, Jürgen Mangler, and Stefanie Rinderle-Ma. "Temporal Conformance Checking at Runtime based on Time-infused Process Models." arXiv preprint arXiv:2008.07262 (2020).

    The output is a dictionary containing, for every pair of activities that eventually follow each other in at least one case of the log,
    the average and the standard deviation of the time difference between their timestamps.

    Example:
    If the log has two cases:

    - Case 1: A (timestamp: 1980-01) → B (timestamp: 1980-03) → C (timestamp: 1980-06)
    - Case 2: A (timestamp: 1990-01) → B (timestamp: 1990-02) → D (timestamp: 1990-03)

    The returned dictionary will contain::

        {
            ('A', 'B'): (1.5 months, 0.5 months),
            ('A', 'C'): (5 months, 0),
            ('A', 'D'): (2 months, 0)
        }

    :param log: Event log or Pandas DataFrame.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A dictionary mapping each pair of activities to a tuple of (average time difference, standard deviation).
    :rtype: ``Dict[Tuple[str, str], Tuple[float, float]]``

    .. code-block:: python3

        import pm4py

        temporal_profile = pm4py.discover_temporal_profile(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )

    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )

    from pm4py.algo.discovery.temporal_profile import (
        algorithm as temporal_profile_discovery,
    )

    return temporal_profile_discovery.apply(log, parameters=properties)


def discover_log_skeleton(
        log: Union[EventLog, pd.DataFrame],
        noise_threshold: float = 0.0,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Dict[str, Any]:
    """
    Discovers a Log Skeleton from an event log.

    A Log Skeleton is a declarative model consisting of six different constraints:
    - **directly_follows**: Specifies strict bounds on activities that directly follow each other. Example: 'A should be directly followed by B' and 'B should be directly followed by C'.
    - **always_before**: Specifies that some activities may only be executed if certain other activities have been executed earlier in the case. Example: 'C should always be preceded by A'.
    - **always_after**: Specifies that certain activities should always trigger the execution of some other activities later in the case. Example: 'A should always be followed by C'.
    - **equivalence**: Specifies that a given pair of activities should occur the same number of times within a case. Example: 'B and C should always occur the same number of times'.
    - **never_together**: Specifies that a given pair of activities should never occur together in a case. Example: 'There should be no case containing both C and D'.
    - **activ_occurrences**: Specifies allowed numbers of occurrences per activity. Example: 'Activity A can occur 1 or 2 times, and Activity B can occur 1 to 4 times'.

    Reference paper:
    Verbeek, H. M. W., and R. Medeiros de Carvalho. "Log skeletons: A classification approach to process discovery." arXiv preprint arXiv:1806.08247 (2018).

    :param log: Event log or Pandas DataFrame.
    :param noise_threshold: Noise threshold influencing the strictness of constraints (default: 0.0).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A dictionary representing the Log Skeleton with various constraints.
    :rtype: ``Dict[str, Any]``

    .. code-block:: python3

        import pm4py

        log_skeleton = pm4py.discover_log_skeleton(
            dataframe,
            noise_threshold=0.1,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    properties["noise_threshold"] = noise_threshold

    from pm4py.algo.discovery.log_skeleton import (
        algorithm as log_skeleton_discovery,
    )

    return log_skeleton_discovery.apply(log, parameters=properties)


def discover_declare(
        log: Union[EventLog, pd.DataFrame],
        allowed_templates: Optional[Set[str]] = None,
        considered_activities: Optional[Set[str]] = None,
        min_support_ratio: Optional[float] = None,
        min_confidence_ratio: Optional[float] = None,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> Dict[str, Dict[Any, Dict[str, int]]]:
    """
    Discovers a DECLARE model from an event log.

    Reference paper:
    F. M. Maggi, A. J. Mooij and W. M. P. van der Aalst, "User-guided discovery of declarative process models," 2011 IEEE Symposium on Computational Intelligence and Data Mining (CIDM), Paris, France, 2011, pp. 192-199, doi: 10.1109/CIDM.2011.5949297.

    :param log: Event log or Pandas DataFrame.
    :param allowed_templates: (Optional) Set of DECLARE templates to consider for discovery.
    :param considered_activities: (Optional) Set of activities to consider for discovery.
    :param min_support_ratio: (Optional) Minimum percentage of cases for which the discovered rules apply.
    :param min_confidence_ratio: (Optional) Minimum percentage of cases for which the discovered rules are valid, based on the rule's support.
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A dictionary representing the discovered DECLARE model with constraints and their parameters.
    :rtype: ``Dict[str, Dict[Any, Dict[str, int]]]``

    .. code-block:: python3

        import pm4py

        declare_model = pm4py.discover_declare(log)
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
    )
    properties["allowed_templates"] = allowed_templates
    properties["considered_activities"] = considered_activities
    properties["min_support_ratio"] = min_support_ratio
    properties["min_confidence_ratio"] = min_confidence_ratio

    from pm4py.algo.discovery.declare import algorithm as declare_discovery

    return declare_discovery.apply(log, parameters=properties)


def discover_powl(
        log: Union[EventLog, pd.DataFrame],
        variant=None,
        filtering_weight_factor: float = 0.0,
        order_graph_filtering_threshold: float = None,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
) -> POWL:
    """
    Discovers a POWL (Partially Ordered Workflow Language) model from an event log.

    Reference paper:
    Kourani, Humam, and Sebastiaan J. van Zelst. "POWL: partially ordered workflow language." International Conference on Business Process Management. Cham: Springer Nature Switzerland, 2023.

    :param log: Event log or Pandas DataFrame.
    :param variant: Variant of the POWL discovery algorithm to use.
    :param filtering_weight_factor: Factoring threshold for filtering weights, accepts values 0 <= x < 1 (default: 0.0).
    :param order_graph_filtering_threshold: Filtering threshold for the order graph, valid for the DYNAMIC_CLUSTERING variant, accepts values 0.5 < x <= 1 (default: None).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :return: A POWL object representing the discovered POWL model.
    :rtype: ``POWL``

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/receipt.xes')
        powl_model = pm4py.discover_powl(
            log,
            activity_key='concept:name'
        )
        print(powl_model)
    """
    from pm4py.algo.discovery.powl.inductive.variants.dynamic_clustering_frequency.dynamic_clustering_frequency_partial_order_cut import (
        ORDER_FREQUENCY_RATIO, )
    from pm4py.algo.discovery.powl.inductive.variants.powl_discovery_varaints import (
        POWLDiscoveryVariant, )

    if variant is None:
        variant = POWLDiscoveryVariant.MAXIMAL

    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    # import pm4py
    # log = pm4py.convert_to_event_log(log, case_id_key=case_id_key)
    properties = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key)

    if order_graph_filtering_threshold is not None:
        if variant is POWLDiscoveryVariant.DYNAMIC_CLUSTERING:
            properties[ORDER_FREQUENCY_RATIO] = order_graph_filtering_threshold
        else:
            raise Exception(
                "The order graph filtering threshold can only be used for the DYNAMIC_CLUSTERING variant."
            )

    properties["filtering_threshold"] = filtering_weight_factor

    from pm4py.algo.discovery.powl import algorithm as powl_discovery

    return powl_discovery.apply(log, variant=variant, parameters=properties)


def discover_batches(
        log: Union[EventLog, pd.DataFrame],
        merge_distance: int = 15 * 60,
        min_batch_size: int = 2,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        resource_key: str = "org:resource",
) -> List[Tuple[Tuple[str, str], int, Dict[str, Any]]]:
    """
    Discovers batches from the provided log.

    An activity is executed in batches by a given resource when the resource performs the same activity multiple times in a short period.
    Identifying such activities may highlight repetitive tasks that could be automated.

    The following batch categories are detected:
    - **Simultaneous**: All events in the batch have identical start and end timestamps.
    - **Batching at Start**: All events in the batch have identical start timestamps.
    - **Batching at End**: All events in the batch have identical end timestamps.
    - **Sequential Batching**: Consecutive events have the end of the first equal to the start of the second.
    - **Concurrent Batching**: Consecutive events that do not match sequentially.

    Reference paper:
    Martin, N., Swennen, M., Depaire, B., Jans, M., Caris, A., & Vanhoof, K. (2015, December). Batch Processing: Definition and Event Log Identification. In SIMPDA (pp. 137-140).

    :param log: Event log or Pandas DataFrame.
    :param merge_distance: Maximum time distance (in seconds) between non-overlapping intervals to consider them part of the same batch (default: 900 seconds, i.e., 15 minutes).
    :param min_batch_size: Minimum number of events required to form a batch (default: 2).
    :param activity_key: Attribute to be used for the activity (default: "concept:name").
    :param timestamp_key: Attribute to be used for the timestamp (default: "time:timestamp").
    :param case_id_key: Attribute to be used as case identifier (default: "case:concept:name").
    :param resource_key: Attribute to be used as resource (default: "org:resource").
    :return: A sorted list of tuples, each containing:
             - The (activity, resource) pair.
             - The number of batches for the given activity-resource.
             - A dictionary with batch details.
    :rtype: ``List[Tuple[Tuple[str, str], int, Dict[str, Any]]]``

    .. code-block:: python3

        import pm4py

        batches = pm4py.discover_batches(
            dataframe,
            activity_key='concept:name',
            case_id_key='case:concept:name',
            timestamp_key='time:timestamp',
            resource_key='org:resource'
        )
    """
    __event_log_deprecation_warning(log)

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )

    properties = get_properties(
        log,
        activity_key=activity_key,
        timestamp_key=timestamp_key,
        case_id_key=case_id_key,
        resource_key=resource_key,
    )
    properties["merge_distance"] = merge_distance
    properties["min_batch_size"] = min_batch_size

    from pm4py.algo.discovery.batches import algorithm as batches_discovery

    return batches_discovery.apply(log, parameters=properties)


def correlation_miner(
        df: pd.DataFrame,
        annotation: str = "frequency",
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
) -> Tuple[dict, dict, dict]:
    """
    Applies the Correlation Miner to 'discover' the frequency/performance DFG from an event log without case ID.

    The approach is described in:
    Pourmirza, Shaya, Remco Dijkman, and Paul Grefen. "Correlation miner: mining business process models and event
    correlations without case identifiers." International Journal of Cooperative Information Systems 26.02 (2017):
    1742002.

    :param log: Pandas dataframe
    :param annotation: annotation ('frequency' for the frequency DFG, or 'performance' for the performance DFG)
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :rtype: ``Tuple[dict, dict, dict]``

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes("tests/input_data/running-example.xes")
        log = log[["concept:name", "time:timestamp"]]

        dfg, sa, ea = pm4py.correlation_miner(log)
        pm4py.view_dfg(dfg, sa, ea, format="svg")

        perf_dfg, sa, ea = pm4py.correlation_miner(log, annotation="performance")
        pm4py.view_performance_dfg(perf_dfg, sa, ea, format="svg")
    """
    properties = get_properties(
        df, activity_key=activity_key, timestamp_key=timestamp_key
    )

    if is_polars_lazyframe(df):
        if importlib.util.find_spec("polars") is None:
            raise RuntimeError(
                "Polars LazyFrame provided but 'polars' package is not installed."
            )

        import polars as pl  # type: ignore[import-untyped]

        if activity_key not in df.columns:
            raise Exception(
                f"Column '{activity_key}' is not present in the provided Polars LazyFrame."
            )

        first_row = (
            df.select(pl.col(activity_key))
            .head(1)
            .collect()
        )
        if first_row.height == 0:
            raise ValueError("The provided Polars LazyFrame must contain at least one event.")
        first_activity = first_row[activity_key].to_list()[0]

        last_row = (
            df.select(pl.col(activity_key))
            .tail(1)
            .collect()
        )
        last_activity = last_row[activity_key].to_list()[0]
    else:
        # code for Pandas dataframes
        first_activity = df[activity_key].iloc[0]
        last_activity = df[activity_key].iloc[-1]

    from pm4py.algo.discovery.correlation_mining import (
        algorithm as correlation_miner,
    )

    dfg, perf_dfg = correlation_miner.apply(df, parameters=properties)
    perf_dfg = {a: float(y) for a, y in perf_dfg.items()}

    activities_entering = Counter()
    activities_exiting = Counter()

    for edge, freq in dfg.items():
        activities_exiting[edge[0]] += freq
        activities_entering[edge[1]] += freq

    start_activities = {first_activity: activities_exiting[first_activity]}
    end_activities = {last_activity: activities_entering[last_activity]}

    if annotation == "frequency":
        return dfg, start_activities, end_activities
    else:
        return perf_dfg, start_activities, end_activities


def discover_otg(
        ocel: OCEL,
        variant=None,
        parameters: Optional[Dict[Any, Any]] = None,
) -> Tuple[Set[str], Dict[Tuple[str, str, str], int]]:
    """
    Discovers an Object-Type Graph (OTG) from an object-centric event log.

    Published in: https://publications.rwth-aachen.de/record/1014107

    An OTG summarizes how object types are related across different interaction graphs extracted from the OCEL.
    Specifically, an OTG is a tuple containing:
    - The set of object types
    - The edges along with the frequency, where each edge is (object_type1, relationship, object_type2).

    Relationship can be:
    * object_interaction (objects related in some event)
    * object_descendants (lifecycle of the first event starts before the other object)
    * object_inheritance (lifecycle of the first object ends exactly when the second one starts)
    * object_cobirth (objects start their lifecycle in the same event)
    * object_codeath (objects end their lifecycle in the sae event)

    :param ocel: Object-centric event log.
    :param variant: Variant of the OTG discovery algorithm to use (default: classic variant).
    :param parameters: Optional variant-specific parameters.
    :return: Tuple containing the set of object types and the OTG edges with their frequencies.
    :rtype: ``Tuple[Set[str], Dict[Tuple[str, str, str], int]]``

    .. code-block:: python3

        import pm4py

        otg = pm4py.discover_otg(ocel)
    """
    from pm4py.algo.discovery.ocel.otg import algorithm as otg_discovery

    if variant is None:
        variant = otg_discovery.Variants.CLASSIC

    return otg_discovery.apply(ocel, variant=variant, parameters=parameters)


def discover_etot(
        ocel: OCEL,
        variant=None,
        parameters: Optional[Dict[Any, Any]] = None,
) -> Tuple[
    Set[str],
    Set[str],
    Set[Tuple[str, str]],
    Dict[Tuple[str, str], int],
]:
    """
    Discovers the ET-OT (Event Type - Object Type) graph from an object-centric event log.

    Published in: https://publications.rwth-aachen.de/record/1014107

    The ET-OT graph captures the relationships between event types and object types along with their frequencies.
    Specifically, an ET-OT graph is a tuple consisting of:
    - Set of activities
    - Set of object types
    - Set of relationships, where an edge (a, ot) indicates that events of type a are associated with objects of type ot
    - A dictionary associating each relationship to a weight (frequency)

    :param ocel: Object-centric event log.
    :param variant: Variant of the ET-OT discovery algorithm to use (default: classic variant).
    :param parameters: Optional variant-specific parameters.
    :return: Tuple containing the set of activities, the set of object types, the ET-OT edges, and their frequencies.
    :rtype: ``Tuple[Set[str], Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], int]]``

    .. code-block:: python3

        import pm4py

        etot = pm4py.discover_etot(ocel)
    """
    from pm4py.algo.discovery.ocel.etot import algorithm as etot_discovery

    if variant is None:
        variant = etot_discovery.Variants.CLASSIC

    return etot_discovery.apply(ocel, variant=variant, parameters=parameters)
