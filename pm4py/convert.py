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
The ``pm4py.convert`` module contains the cross-conversions implemented in ``pm4py``
"""

from typing import Union, Tuple, Optional, Collection, List, Any, Dict

import pandas as pd
from copy import deepcopy

import pm4py
from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.powl.obj import POWL
from pm4py.objects.heuristics_net.obj import HeuristicsNet
from pm4py.objects.genetic_matrix.obj import GeneticMatrix
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.objects.petri_net.obj import Marking
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.util import constants, nx_utils
from pm4py.utils import get_properties, __event_log_deprecation_warning
from pm4py.objects.transition_system.obj import TransitionSystem
from pm4py.util.pandas_utils import (
    check_is_pandas_dataframe,
    check_pandas_dataframe_columns,
)
import networkx as nx


def convert_to_event_log(
        obj: Union[pd.DataFrame, EventStream],
        case_id_key: str = "case:concept:name",
        **kwargs,
) -> EventLog:
    """
    Converts a DataFrame or EventStream object to an event log object.

    :param obj: The DataFrame or EventStream object to convert.
    :param case_id_key: The attribute to be used as the case identifier. Defaults to "case:concept:name".
    :param kwargs: Additional keyword arguments to pass to the converter.
    :return: An ``EventLog`` object.

    .. code-block:: python3

       import pandas as pd
       import pm4py

       dataframe = pm4py.read_csv("tests/input_data/running-example.csv")
       dataframe = pm4py.format_dataframe(dataframe, case_id_column='case:concept:name', activity_column='concept:name', timestamp_column='time:timestamp')
       log = pm4py.convert_to_event_log(dataframe)
    """

    if check_is_pandas_dataframe(obj):
        check_pandas_dataframe_columns(obj, case_id_key=case_id_key)

    parameters = get_properties(obj, case_id_key=case_id_key)
    for k, v in kwargs.items():
        parameters[k] = v

    from pm4py.objects.conversion.log import converter

    log = converter.apply(
        obj, variant=converter.Variants.TO_EVENT_LOG, parameters=parameters
    )

    __event_log_deprecation_warning(log)

    return log


def convert_to_event_stream(
        obj: Union[EventLog, pd.DataFrame],
        case_id_key: str = "case:concept:name",
        **kwargs,
) -> EventStream:
    """
    Converts a log object or DataFrame to an event stream.

    :param obj: The log object (``EventLog``) or DataFrame to convert.
    :param case_id_key: The attribute to be used as the case identifier. Defaults to "case:concept:name".
    :param kwargs: Additional keyword arguments to pass to the converter.
    :return: An ``EventStream`` object.

    .. code-block:: python3

       import pm4py

       log = pm4py.read_xes("tests/input_data/running-example.xes")
       event_stream = pm4py.convert_to_event_stream(log)
    """
    if check_is_pandas_dataframe(obj):
        check_pandas_dataframe_columns(obj, case_id_key=case_id_key)

    parameters = get_properties(obj, case_id_key=case_id_key)
    for k, v in kwargs.items():
        parameters[k] = v

    from pm4py.objects.conversion.log import converter

    stream = converter.apply(
        obj, variant=converter.Variants.TO_EVENT_STREAM, parameters=parameters
    )

    __event_log_deprecation_warning(stream)

    return stream


def convert_to_dataframe(
        obj: Union[EventStream, EventLog], **kwargs
) -> pd.DataFrame:
    """
    Converts a log object (``EventStream`` or ``EventLog``) to a Pandas DataFrame.

    :param obj: The log object to convert.
    :param kwargs: Additional keyword arguments to pass to the converter.
    :return: A ``pd.DataFrame`` object.

    .. code-block:: python3

       import pm4py

       log = pm4py.read_xes("tests/input_data/running-example.xes")
       dataframe = pm4py.convert_to_dataframe(log)
    """
    if check_is_pandas_dataframe(obj):
        check_pandas_dataframe_columns(obj)

    parameters = get_properties(obj)
    for k, v in kwargs.items():
        parameters[k] = v

    from pm4py.objects.conversion.log import converter

    df = converter.apply(
        obj, variant=converter.Variants.TO_DATA_FRAME, parameters=parameters
    )
    return df


def convert_to_bpmn(
        *args: Union[Tuple[PetriNet, Marking, Marking], ProcessTree]
) -> BPMN:
    """
    Converts an object to a BPMN diagram.

    As input, either a Petri net (with corresponding initial and final markings) or a process tree can be provided.
    A process tree can always be converted into a BPMN model, ensuring the quality of the resulting object.
    For Petri nets, the quality of the conversion largely depends on the net provided (e.g., sound WF-nets are likely to produce reasonable BPMN models).

    :param args:
        - If converting a Petri net: a tuple of (``PetriNet``, ``Marking``, ``Marking``).
        - If converting a process tree: a single ``ProcessTree`` object.
    :return: A ``BPMN`` object.

    .. code-block:: python3

       import pm4py

       # Import a Petri net from a file
       net, im, fm = pm4py.read_pnml("tests/input_data/running-example.pnml")
       bpmn_graph = pm4py.convert_to_bpmn(net, im, fm)
    """
    from pm4py.objects.process_tree.obj import ProcessTree
    from pm4py.objects.bpmn.obj import BPMN

    if isinstance(args[0], BPMN):
        # the object is already a BPMN
        return args[0]
    elif isinstance(args[0], ProcessTree):
        from pm4py.objects.conversion.process_tree.variants import to_bpmn

        return to_bpmn.apply(args[0])
    else:
        # try to convert the object to a Petri net. Then, use the PM4Py PN-to-BPMN converter
        # to get the BPMN object
        try:
            net, im, fm = convert_to_petri_net(*args)
            from pm4py.objects.conversion.wf_net.variants import to_bpmn

            return to_bpmn.apply(net, im, fm)
        except BaseException:
            # don't do nothing and throw the following exception
            pass
    # if no conversion is done, then the format of the arguments is unsupported
    raise Exception("Unsupported conversion of the provided object to BPMN")


def convert_to_petri_net(
        *args: Union[BPMN, ProcessTree, HeuristicsNet, GeneticMatrix, POWL, dict]
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Converts an input model to an (accepting) Petri net.

    The input objects can be a process tree, BPMN model, Heuristic net, GeneticMatrix, POWL model, or a dictionary representing a Directly-Follows Graph (DFG).
    The output is a tuple containing the Petri net and the initial and final markings.
    The markings are only returned if they can be reasonably derived from the input model.

    :param args:
        - If converting from a BPMN, ProcessTree, HeuristicsNet, GeneticMatrix, or POWL: a single object of the respective type.
        - If converting from a DFG: a dictionary representing the DFG, followed by lists of start and end activities.
    :return: A tuple of (``PetriNet``, ``Marking``, ``Marking``).

    .. code-block:: python3

       import pm4py

       # Imports a process tree from a PTML file
       process_tree = pm4py.read_ptml("tests/input_data/running-example.ptml")
       net, im, fm = pm4py.convert_to_petri_net(process_tree)
    """
    if isinstance(args[0], PetriNet):
        # the object is already a Petri net
        return args[0], args[1], args[2]
    elif isinstance(args[0], ProcessTree):
        if isinstance(args[0], POWL):
            from pm4py.objects.conversion.powl import converter

            return converter.apply(args[0])
        from pm4py.objects.conversion.process_tree.variants import to_petri_net

        return to_petri_net.apply(args[0])
    elif isinstance(args[0], BPMN):
        from pm4py.objects.conversion.bpmn.variants import to_petri_net

        return to_petri_net.apply(args[0])
    elif isinstance(args[0], HeuristicsNet):
        from pm4py.objects.conversion.heuristics_net.variants import (
            to_petri_net,
        )

        return to_petri_net.apply(args[0])
    elif isinstance(args[0], GeneticMatrix):
        from pm4py.objects.conversion.genetic_matrix.variants import (
            to_petri_net,
        )

        return to_petri_net.apply(args[0])
    elif isinstance(args[0], dict):
        # DFG
        from pm4py.objects.conversion.dfg.variants import (
            to_petri_net_activity_defines_place,
        )

        return to_petri_net_activity_defines_place.apply(
            args[0],
            parameters={
                to_petri_net_activity_defines_place.Parameters.START_ACTIVITIES: args[1],
                to_petri_net_activity_defines_place.Parameters.END_ACTIVITIES: args[2],
            },
        )
    # if no conversion is done, then the format of the arguments is unsupported
    raise Exception(
        "Unsupported conversion of the provided object to Petri net"
    )


def convert_to_process_tree(
        *args: Union[Tuple[PetriNet, Marking, Marking], BPMN, ProcessTree, POWL]
) -> ProcessTree:
    """
    Converts an input model to a process tree.

    The input models can be Petri nets (with markings) or BPMN models.
    For both input types, the conversion is not guaranteed to work and may raise an exception.

    :param args:
        - If converting from a Petri net: a tuple of (``PetriNet``, ``Marking``, ``Marking``).
        - If converting from a BPMN or ProcessTree: a single object of the respective type.
    :return: A ``ProcessTree`` object.

    .. code-block:: python3

       import pm4py

       # Imports a BPMN file
       bpmn_graph = pm4py.read_bpmn("tests/input_data/running-example.bpmn")
       # Converts the BPMN to a process tree (through intermediate conversion to a Petri net)
       process_tree = pm4py.convert_to_process_tree(bpmn_graph)
    """
    from pm4py.objects.process_tree.obj import ProcessTree
    from pm4py.objects.petri_net.obj import PetriNet

    if isinstance(args[0], POWL):
        from pm4py.objects.conversion.powl.variants import to_process_tree
        return to_process_tree.apply(args[0])
    elif isinstance(args[0], ProcessTree):
        # the object is already a process tree
        return args[0]

    if isinstance(args[0], PetriNet):
        net, im, fm = args[0], args[1], args[2]
    else:
        net, im, fm = convert_to_petri_net(*args)

    from pm4py.objects.conversion.wf_net.variants import to_process_tree

    tree = to_process_tree.apply(net, im, fm)
    if tree is not None:
        return tree

    raise Exception(
        "The object represents a model that cannot be represented as a process tree!"
    )


def convert_to_powl(*args: Union[Tuple[PetriNet, Marking, Marking], BPMN, ProcessTree]) -> POWL:
    """
    Converts an input model to a POWL model.

    The input models can be Petri nets (with markings) or BPMN models or process trees.
    For both input types, the conversion is not guaranteed to work and may raise an exception.

    :param args:
        - If converting from a Petri net: a tuple of (``PetriNet``, ``Marking``, ``Marking``).
        - If converting from a BPMN or ProcessTree: a single object of the respective type.
    :return: A ``ProcessTree`` object.

    .. code-block:: python3

       import pm4py

       # Imports a BPMN file
       bpmn_graph = pm4py.read_bpmn("tests/input_data/running-example.bpmn")
       # Converts the BPMN to a POWL (through intermediate conversion to a Petri net)
       powl = pm4py.convert_to_powl(bpmn_graph)
       print(powl)
    """
    from pm4py.objects.process_tree.obj import ProcessTree
    from pm4py.objects.petri_net.obj import PetriNet

    if isinstance(args[0], ProcessTree):
        from pm4py.objects.conversion.process_tree.variants import to_powl
        return to_powl.apply(args[0])
    elif isinstance(args[0], PetriNet):
        from pm4py.objects.conversion.wf_net.variants import to_powl
        return to_powl.apply(args[0])
    elif isinstance(args[0], BPMN):
        from pm4py.objects.conversion.wf_net.variants import to_powl
        net, im, fm = pm4py.convert_to_petri_net(args[0])
        return to_powl.apply(net)

    raise Exception(
        "The object represents a model that cannot be directly represented as a POWL!"
    )


def convert_to_reachability_graph(
        *args: Union[Tuple[PetriNet, Marking, Marking], BPMN, ProcessTree]
) -> TransitionSystem:
    """
    Converts an input model to a reachability graph (transition system).

    The input models can be Petri nets (with markings), BPMN models, or process trees.
    The output is the state-space of the model, encoded as a ``TransitionSystem`` object.

    :param args:
        - If converting from a Petri net: a tuple of (``PetriNet``, ``Marking``, ``Marking``).
        - If converting from a BPMN or ProcessTree: a single object of the respective type.
    :return: A ``TransitionSystem`` object.

    .. code-block:: python3

        import pm4py

        # Reads a Petri net from a file
        net, im, fm = pm4py.read_pnml("tests/input_data/running-example.pnml")
        # Converts it to a reachability graph
        reach_graph = pm4py.convert_to_reachability_graph(net, im, fm)
    """
    if isinstance(args[0], PetriNet):
        net, im, fm = args[0], args[1], args[2]
    else:
        net, im, fm = convert_to_petri_net(*args)

    from pm4py.objects.petri_net.utils import reachability_graph

    return reachability_graph.construct_reachability_graph(net, im)


def convert_log_to_ocel(
        log: Union[EventLog, EventStream, pd.DataFrame],
        activity_column: str = "concept:name",
        timestamp_column: str = "time:timestamp",
        object_types: Optional[Collection[str]] = None,
        obj_separator: str = " AND ",
        additional_event_attributes: Optional[Collection[str]] = None,
        additional_object_attributes: Optional[Dict[str, Collection[str]]] = None,
) -> OCEL:
    """
    Converts an event log to an object-centric event log (OCEL) with one or more object types.

    :param log: The log object to convert.
    :param activity_column: The name of the column representing activities.
    :param timestamp_column: The name of the column representing timestamps.
    :param object_types: A collection of column names to consider as object types. If None, defaults are used.
    :param obj_separator: The separator used between different objects in the same column. Defaults to " AND ".
    :param additional_event_attributes: Additional attribute names to include as event attributes in the OCEL.
    :param additional_object_attributes: Additional attributes per object type to include as object attributes in the OCEL. Should be a dictionary mapping object types to lists of attribute names.
    :return: An ``OCEL`` object.

    .. code-block:: python3

        import pm4py

        ocel = pm4py.convert_log_to_ocel(
            log,
            activity_column='concept:name',
            timestamp_column='time:timestamp',
            object_types=['case:concept:name']
        )
    """
    __event_log_deprecation_warning(log)

    if isinstance(log, EventStream):
        log = convert_to_dataframe(log)

    if object_types is None:
        object_types = list(
            set(
                x
                for x in log.columns
                if x == "case:concept:name" or x.startswith("ocel:type")
            )
        )

    from pm4py.objects.ocel.util import log_ocel

    return log_ocel.log_to_ocel_multiple_obj_types(
        log,
        activity_column,
        timestamp_column,
        object_types,
        obj_separator,
        additional_event_attributes=additional_event_attributes,
        additional_object_attributes=additional_object_attributes,
    )


def convert_ocel_to_networkx(
        ocel: OCEL, variant: str = "ocel_to_nx"
) -> nx.DiGraph:
    """
    Converts an OCEL to a NetworkX DiGraph object.

    :param ocel: The object-centric event log to convert.
    :param variant: The variant of the conversion to use.
                    Options:
                    - "ocel_to_nx": Graph containing event and object IDs and two types of relations (REL=related objects, DF=directly-follows).
                    - "ocel_features_to_nx": Graph containing different types of interconnections at the object level.
    :return: A ``nx.DiGraph`` object representing the OCEL.

    .. code-block:: python3

        import pm4py

        nx_digraph = pm4py.convert_ocel_to_networkx(ocel, variant='ocel_to_nx')
    """
    from pm4py.objects.conversion.ocel import converter

    variant1 = None
    if variant == "ocel_to_nx":
        variant1 = converter.Variants.OCEL_TO_NX
    elif variant == "ocel_features_to_nx":
        variant1 = converter.Variants.OCEL_FEATURES_TO_NX
    else:
        raise ValueError(
            f"Unsupported variant '{variant}'. Supported variants are 'ocel_to_nx' and 'ocel_features_to_nx'.")

    return converter.apply(ocel, variant=variant1)


def convert_log_to_networkx(
        log: Union[EventLog, EventStream, pd.DataFrame],
        include_df: bool = True,
        case_id_key: str = "concept:name",
        other_case_attributes_as_nodes: Optional[Collection[str]] = None,
        event_attributes_as_nodes: Optional[Collection[str]] = None,
) -> nx.DiGraph:
    """
    Converts an event log to a NetworkX DiGraph object.

    The nodes of the graph include events, cases, and optionally log attributes.
    The edges represent:
    - BELONGS_TO: Connecting each event to its corresponding case.
    - DF: Connecting events that directly follow each other (if enabled).
    - ATTRIBUTE_EDGE: Connecting cases/events to their attribute values.

    :param log: The log object to convert (``EventLog``, ``EventStream``, or Pandas DataFrame).
    :param include_df: Whether to include the directly-follows relation in the graph. Defaults to True.
    :param case_id_key: The attribute to be used as the case identifier. Defaults to "concept:name".
    :param other_case_attributes_as_nodes: Attributes at the case level to include as nodes, excluding the case ID.
    :param event_attributes_as_nodes: Attributes at the event level to include as nodes.
    :return: A ``nx.DiGraph`` object representing the event log.

    .. code-block:: python3

        import pm4py

        nx_digraph = pm4py.convert_log_to_networkx(
            log,
            other_case_attributes_as_nodes=['responsible', 'department'],
            event_attributes_as_nodes=['concept:name', 'org:resource']
        )
    """
    from pm4py.objects.conversion.log import converter

    return converter.apply(
        log,
        variant=converter.Variants.TO_NX,
        parameters={
            "include_df": include_df,
            "case_id_attribute": case_id_key,
            "other_case_attributes_as_nodes": other_case_attributes_as_nodes,
            "event_attributes_as_nodes": event_attributes_as_nodes,
        },
    )


def convert_log_to_time_intervals(
        log: Union[EventLog, pd.DataFrame],
        filter_activity_couple: Optional[Tuple[str, str]] = None,
        activity_key: str = "concept:name",
        timestamp_key: str = "time:timestamp",
        case_id_key: str = "case:concept:name",
        start_timestamp_key: str = "time:timestamp",
) -> List[List[Any]]:
    """
    Extracts a list of time intervals from an event log.

    Each interval contains two temporally consecutive events within the same case and measures the time between them
    (complete timestamp of the first event against the start timestamp of the second event).

    :param log: The log object to convert.
    :param filter_activity_couple: Optional tuple to filter intervals by a specific pair of activities.
    :param activity_key: The attribute to be used as the activity identifier. Defaults to "concept:name".
    :param timestamp_key: The attribute to be used as the timestamp. Defaults to "time:timestamp".
    :param case_id_key: The attribute to be used as the case identifier. Defaults to "case:concept:name".
    :param start_timestamp_key: The attribute to be used as the start timestamp in the interval. Defaults to "time:timestamp".
    :return: A list of intervals, where each interval is a list containing relevant information about the time gap.

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/receipt.xes')
        time_intervals = pm4py.convert_log_to_time_intervals(log)
        print(len(time_intervals))
        time_intervals = pm4py.convert_log_to_time_intervals(
            log,
            filter_activity_couple=('Confirmation of receipt', 'T02 Check confirmation of receipt')
        )
        print(len(time_intervals))
    """
    __event_log_deprecation_warning(log)

    properties = get_properties(
        log,
        activity_key=activity_key,
        case_id_key=case_id_key,
        timestamp_key=timestamp_key,
    )
    properties["filter_activity_couple"] = filter_activity_couple
    properties[constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY] = (
        start_timestamp_key
    )

    from pm4py.algo.transformation.log_to_interval_tree.variants import (
        open_paths,
    )

    return open_paths.log_to_intervals(log, parameters=properties)


def convert_petri_net_to_networkx(
        net: PetriNet, im: Marking, fm: Marking
) -> nx.DiGraph:
    """
    Converts a Petri net to a NetworkX DiGraph.

    Each place and transition in the Petri net is represented as a node in the graph.

    :param net: The Petri net to convert.
    :param im: The initial marking of the Petri net.
    :param fm: The final marking of the Petri net.
    :return: A ``nx.DiGraph`` object representing the Petri net.

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.read_pnml('tests/input_data/running-example.pnml')
        nx_digraph = pm4py.convert_petri_net_to_networkx(net, im, fm)
    """
    G = nx_utils.DiGraph()
    for place in net.places:
        G.add_node(
            place.name,
            attr={
                "name": place.name,
                "is_in_im": place in im,
                "is_in_fm": place in fm,
                "type": "place",
            },
        )
    for trans in net.transitions:
        G.add_node(
            trans.name,
            attr={
                "name": trans.name,
                "label": trans.label,
                "type": "transition",
            },
        )
    for arc in net.arcs:
        G.add_edge(
            arc.source.name,
            arc.target.name,
            attr={"weight": arc.weight, "properties": arc.properties},
        )
    return G


def convert_petri_net_type(
        net: PetriNet, im: Marking, fm: Marking, type: str = "classic"
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Changes the internal type of a Petri net.

    Supports conversion to different Petri net types such as classic, reset, inhibitor, and reset_inhibitor nets.

    :param net: The Petri net to convert.
    :param im: The initial marking of the Petri net.
    :param fm: The final marking of the Petri net.
    :param type: The target Petri net type. Options are "classic", "reset", "inhibitor", "reset_inhibitor". Defaults to "classic".
    :return: A tuple of the converted (``PetriNet``, ``Marking``, ``Marking``).

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.read_pnml('tests/input_data/running-example.pnml')
        reset_net, new_im, new_fm = pm4py.convert_petri_net_type(net, im, fm, type='reset_inhibitor')
    """
    from pm4py.objects.petri_net.utils import petri_utils

    [net, im, fm] = deepcopy([net, im, fm])
    new_net = None
    if type == "classic":
        from pm4py.objects.petri_net.obj import PetriNet

        new_net = PetriNet(net.name)
    elif type == "reset":
        from pm4py.objects.petri_net.obj import ResetNet

        new_net = ResetNet(net.name)
    elif type == "inhibitor":
        from pm4py.objects.petri_net.obj import InhibitorNet

        new_net = InhibitorNet(net.name)
    elif type == "reset_inhibitor":
        from pm4py.objects.petri_net.obj import ResetInhibitorNet

        new_net = ResetInhibitorNet(net.name)
    else:
        raise ValueError(
            f"Unsupported Petri net type '{type}'. Supported types are 'classic', 'reset', 'inhibitor', 'reset_inhibitor'.")

    for place in net.places:
        new_net.places.add(place)
        in_arcs = set(place.in_arcs)
        out_arcs = set(place.out_arcs)
        for arc in in_arcs:
            place.in_arcs.remove(arc)
        for arc in out_arcs:
            place.out_arcs.remove(arc)
    for trans in net.transitions:
        new_net.transitions.add(trans)
        in_arcs = set(trans.in_arcs)
        out_arcs = set(trans.out_arcs)
        for arc in in_arcs:
            trans.in_arcs.remove(arc)
        for arc in out_arcs:
            trans.out_arcs.remove(arc)
    for arc in net.arcs:
        arc_type = (
            arc.properties["arctype"] if "arctype" in arc.properties else None
        )
        new_arc = petri_utils.add_arc_from_to(
            arc.source, arc.target, new_net, weight=arc.weight, type=arc_type
        )
    return new_net, im, fm
