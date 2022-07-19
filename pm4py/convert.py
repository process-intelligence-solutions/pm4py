__doc__ = """
The ``pm4py.convert`` module contains the cross-conversions implemented in ``pm4py``
"""

from typing import Union, Tuple, Optional

import pandas as pd

from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.heuristics_net.obj import HeuristicsNet
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.utils import get_properties, __event_log_deprecation_warning
from pm4py.objects.transition_system.obj import TransitionSystem
from pm4py.util.pandas_utils import check_is_pandas_dataframe, check_pandas_dataframe_columns


def convert_to_event_log(obj: Union[pd.DataFrame, EventStream], case_id_key: str = "case:concept:name") -> EventLog:
    """
    Converts a log object to an event log

    Example:

    .. code-block:: python3

       import pandas as pd
       import pm4py

       dataframe = pm4py.read_csv("tests/input_data/running-example.csv")
       dataframe = pm4py.format_dataframe(dataframe, case_id_column='case:concept:name', activity_column='concept:name', timestamp_column='time:timestamp')
       log = pm4py.convert_to_event_log(dataframe)

    :param obj: log object
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``EventLog``
    """
    if type(obj) not in [pd.DataFrame, EventLog, EventStream]: raise Exception("the method can be applied only to a traditional event log!")

    if check_is_pandas_dataframe(obj):
        check_pandas_dataframe_columns(obj, case_id_key=case_id_key)

    from pm4py.objects.conversion.log import converter
    log = converter.apply(obj, variant=converter.Variants.TO_EVENT_LOG, parameters=get_properties(obj, case_id_key=case_id_key))

    __event_log_deprecation_warning(log)

    return log


def convert_to_event_stream(obj: Union[EventLog, pd.DataFrame], case_id_key: str = "case:concept:name") -> EventStream:
    """
    Converts a log object to an event stream

    Example:

    .. code-block:: python3

       import pm4py

       log = pm4py.read_xes("tests/input_data/running-example.xes")
       event_stream = pm4py.convert_to_event_stream(log)

    :param obj: log object
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``EventStream``
    """
    if type(obj) not in [pd.DataFrame, EventLog, EventStream]: raise Exception("the method can be applied only to a traditional event log!")

    if check_is_pandas_dataframe(obj):
        check_pandas_dataframe_columns(obj, case_id_key=case_id_key)

    from pm4py.objects.conversion.log import converter
    stream = converter.apply(obj, variant=converter.Variants.TO_EVENT_STREAM, parameters=get_properties(obj, case_id_key=case_id_key))

    __event_log_deprecation_warning(stream)

    return stream


def convert_to_dataframe(obj: Union[EventStream, EventLog]) -> pd.DataFrame:
    """
    Converts a log object to a dataframe

    Example:

    .. code-block:: python3

       import pm4py

       log = pm4py.read_xes("tests/input_data/running-example.xes")
       dataframe = pm4py.convert_to_dataframe(log)

    :param obj: log object
    :rtype: ``pd.DataFrame``
    """
    if type(obj) not in [pd.DataFrame, EventLog, EventStream]: raise Exception("the method can be applied only to a traditional event log!")

    if check_is_pandas_dataframe(obj):
        check_pandas_dataframe_columns(obj)

    from pm4py.objects.conversion.log import converter
    df = converter.apply(obj, variant=converter.Variants.TO_DATA_FRAME, parameters=get_properties(obj))
    return df


def convert_to_bpmn(*args: Union[Tuple[PetriNet, Marking, Marking], ProcessTree]) -> BPMN:
    """
    Converts an object to a BPMN diagram.
    As an input, either a Petri net (with corresponding initial and final marking) or a process tree can be provided.
    A process tree can always be converted into a BPMN model and thus quality of the result object is guaranteed.
    For Petri nets, the quality of the converison largely depends on the net provided (e.g., sound WF-nets are likely to produce reasonable BPMN models)    

    Example:

    .. code-block:: python3

       import pm4py

       # import a Petri net from a file
       net, im, fm = pm4py.read_pnml("tests/input_data/running-example.pnml")
       bpmn_graph = pm4py.convert_to_bpmn(net, im, fm)

    :param args: petri net (with initial and final marking) or process tree
    :rtype: ``BPMN``
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
        except:
            # don't do nothing and throw the following exception
            pass
    # if no conversion is done, then the format of the arguments is unsupported
    raise Exception("unsupported conversion of the provided object to BPMN")


def convert_to_petri_net(*args: Union[BPMN, ProcessTree, HeuristicsNet, dict]) -> Tuple[PetriNet, Marking, Marking]:
    """
    Converts an input model to an (accepting) Petri net.
    The input objects can either be a process tree, BPMN model or a Heuristic net.
    The output is a triple, containing the Petri net and the initial and final markings. The markings are only returned if they can be reasonable derived from the input model.

    Example:

    .. code-block:: python3

       import pm4py

       # imports a process tree from a PTML file
       process_tree = pm4py.read_ptml("tests/input_data/running-example.ptml")
       net, im, fm = pm4py.convert_to_petri_net(process_tree)

    :param args: process tree or BPMN
    :rtype: ``Tuple[PetriNet, Marking, Marking]``
    """
    if isinstance(args[0], PetriNet):
        # the object is already a Petri net
        return args[0], args[1], args[2]
    elif isinstance(args[0], ProcessTree):
        from pm4py.objects.conversion.process_tree.variants import to_petri_net
        return to_petri_net.apply(args[0])
    elif isinstance(args[0], BPMN):
        from pm4py.objects.conversion.bpmn.variants import to_petri_net
        return to_petri_net.apply(args[0])
    elif isinstance(args[0], HeuristicsNet):
        from pm4py.objects.conversion.heuristics_net.variants import to_petri_net
        return to_petri_net.apply(args[0])
    elif isinstance(args[0], dict):
        # DFG
        from pm4py.objects.conversion.dfg.variants import to_petri_net_activity_defines_place
        return to_petri_net_activity_defines_place.apply(args[0], parameters={
            to_petri_net_activity_defines_place.Parameters.START_ACTIVITIES: args[1],
            to_petri_net_activity_defines_place.Parameters.END_ACTIVITIES: args[2]})
    # if no conversion is done, then the format of the arguments is unsupported
    raise Exception("unsupported conversion of the provided object to Petri net")


def convert_to_process_tree(*args: Union[Tuple[PetriNet, Marking, Marking], BPMN]) -> ProcessTree:
    """
    Converts an input model to a process tree.
    The input models can either be Petri nets (marked) or BPMN models.
    For both input types, the conversion is not guaranteed to work, hence, invocation of the method can yield an Exception.

    Example:

    .. code-block:: python3

       import pm4py

       # imports a BPMN file
       bpmn_graph = pm4py.read_bpmn("tests/input_data/running-example.bpmn")
       # converts the BPMN to a process tree (through intermediate conversion to a Petri net)
       process_tree = pm4py.convert_to_process_tree(bpmn_graph)

    :param args: petri net (along with initial and final marking) or BPMN
    :rtype: ``ProcessTree``
    """
    from pm4py.objects.process_tree.obj import ProcessTree
    from pm4py.objects.petri_net.obj import PetriNet
    if isinstance(args[0], ProcessTree):
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

    raise Exception("the object represents a model that cannot be represented as a process tree!")


def convert_to_reachability_graph(*args: Union[Tuple[PetriNet, Marking, Marking], BPMN, ProcessTree]) -> TransitionSystem:
    """
    Converts an input model to a reachability graph (transition system)
    The input models can either be Petri nets (with markings), BPMN models or process trees.
    The output is the state-space of the model (i.e., the reachability graph), enocdoed as a ``TransitionSystem`` object.

    Example:

    .. code-block:: python3

       import pm4py

       # reads a Petri net from a file
       net, im, fm = pm4py.read_pnml("tests/input_data/running-example.pnml")
       # converts it to reachability graph
       reach_graph = pm4py.convert_to_reachability_graph(net, im, fm)

    :param args: petri net (along with initial and final marking), process tree or BPMN
    :rtype: ``TransitionSystem``
    """
    if isinstance(args[0], PetriNet):
        net, im, fm = args[0], args[1], args[2]
    else:
        net, im, fm = convert_to_petri_net(*args)

    from pm4py.objects.petri_net.utils import reachability_graph
    return reachability_graph.construct_reachability_graph(net, im)
