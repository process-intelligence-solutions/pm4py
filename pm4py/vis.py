'''
    PM4Py – A Process Mining Library for Python
Copyright (C) 2024 Process Intelligence Solutions UG (haftungsbeschränkt)

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
The `pm4py.vis` module contains the visualizations offered in pm4py.

**Note on Graphviz-based visualizations (e.g., Petri nets, DFGs, BPMN, process trees):**

Supported output formats include:

- **png**: Generates a PNG image.
- **svg**: Generates an SVG image, which can be scaled without loss of quality.
- **pdf**: Generates a PDF file, suitable for printing and embedding in documents.
- **gv**: Returns or saves the Dot source code of the Graphviz graph.
- **html**: When 'html' is provided as the format, the visualization is rendered in an HTML page using GraphvizJS. This allows interactive viewing of the graph directly in a web browser.

If `html` is used, an HTML file containing the GraphvizJS-based rendering is produced, enabling panning, zooming, and other interactive features.

In general, for Graphviz-based visualizations, if you provide a format extension, the visualization will be generated accordingly. For example:
- `format='png'` will produce a PNG file.
- `format='svg'` will produce an SVG file.
- `format='pdf'` will produce a PDF file.
- `format='gv'` will return/save the raw Dot code.
- `format='html'` will produce an interactive HTML visualization using GraphvizJS.
"""

import os
import sys
from typing import Optional, Union, List, Dict, Any, Tuple, Set

import pandas as pd

from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.powl.obj import POWL
from pm4py.objects.heuristics_net.obj import HeuristicsNet
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util.pandas_utils import check_is_pandas_dataframe, check_pandas_dataframe_columns
from pm4py.utils import get_properties
from pm4py.objects.transition_system.obj import TransitionSystem
from pm4py.objects.trie.obj import Trie
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.org.sna.obj import SNA
from pm4py.util import constants


def _extract_format(format_or_path: str) -> str:
    if '.' in format_or_path:
        return os.path.splitext(format_or_path)[1][1:].lower()
    return str(format_or_path).lower()


def _setup_parameters(fmt: str, bgcolor: str = "white", rankdir: str = None, graph_title: Optional[str] = None) -> Dict[str, Any]:
    parameters = {
        "format": fmt,
        "bgcolor": bgcolor,
        "enable_graph_title": constants.DEFAULT_ENABLE_GRAPH_TITLES
    }
    if rankdir is not None:
        parameters["rankdir"] = rankdir
        parameters["set_rankdir"] = rankdir
    if graph_title:
        parameters["enable_graph_title"] = True
        parameters["graph_title"] = graph_title
    return parameters


def _select_petri_net_variant(variant_str: str, pn_visualizer, log: Optional[Union[EventLog, pd.DataFrame]]) -> Any:
    variants_map = {
        "wo_decoration": pn_visualizer.Variants.WO_DECORATION,
        "token_decoration_frequency": pn_visualizer.Variants.FREQUENCY,
        "token_decoration_performance": pn_visualizer.Variants.PERFORMANCE,
        "greedy_decoration_frequency": pn_visualizer.Variants.FREQUENCY_GREEDY,
        "greedy_decoration_performance": pn_visualizer.Variants.PERFORMANCE_GREEDY,
        "alignments": pn_visualizer.Variants.ALIGNMENTS
    }
    variant = variants_map.get(variant_str, pn_visualizer.Variants.WO_DECORATION)
    if variant_str != "wo_decoration" and log is None:
        raise Exception("The 'log' parameter must be provided for decoration purposes.")
    return variant


def view_petri_net(petri_net: PetriNet, initial_marking: Optional[Marking] = None,
                   final_marking: Optional[Marking] = None, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white",
                   decorations: Dict[Any, Any] = None, debug: bool = False, rankdir: str = constants.DEFAULT_RANKDIR_GVIZ,
                   graph_title: Optional[str] = None, variant_str: str = "wo_decoration", log: Optional[Union[EventLog, pd.DataFrame]] = None):
    """
    Views a (composite) Petri net.

    :param petri_net: Petri net
    :param initial_marking: Initial marking
    :param final_marking: Final marking
    :param format: Format of the output picture (if 'html' is provided, GraphvizJS is used to render the visualization in an HTML page)
    :param bgcolor: Background color of the visualization (default: white)
    :param decorations: Decorations (color, label) associated with the elements of the Petri net
    :param debug: Boolean enabling/disabling debug mode (shows place and transition names)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param graph_title: Sets the title of the visualization (if provided)
    :param variant_str: The variant to be used (possible values:
        'wo_decoration', 'token_decoration_frequency', 'token_decoration_performance',
        'greedy_decoration_frequency', 'greedy_decoration_performance', 'alignments')
    :param log: The event log or Pandas dataframe that should be used, if decoration is required

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_inductive(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.view_petri_net(net, im, fm, format='svg')
    """
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    fmt = _extract_format(format)
    variant = _select_petri_net_variant(variant_str, pn_visualizer, log)
    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    parameters["decorations"] = decorations
    parameters["debug"] = debug
    gviz = pn_visualizer.apply(petri_net, initial_marking, final_marking,
                               log=log, variant=variant, parameters=parameters)
    pn_visualizer.view(gviz)


def save_vis_petri_net(petri_net: PetriNet, initial_marking: Marking, final_marking: Marking, file_path: str, bgcolor: str = "white",
                       decorations: Dict[Any, Any] = None, debug: bool = False, rankdir: str = constants.DEFAULT_RANKDIR_GVIZ,
                       graph_title: Optional[str] = None, variant_str: str = "wo_decoration", log: Optional[Union[EventLog, pd.DataFrame]] = None, **kwargs):
    """
    Saves a Petri net visualization to a file.

    :param petri_net: Petri net
    :param initial_marking: Initial marking
    :param final_marking: Final marking
    :param file_path: Destination path
    :param bgcolor: Background color of the visualization (default: white)
    :param decorations: Decorations (color, label) associated with the elements of the Petri net
    :param debug: Boolean enabling/disabling debug mode (shows place and transition names)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param graph_title: Sets the title of the visualization (if provided)
    :param variant_str: The variant to be used (possible values:
        'wo_decoration', 'token_decoration_frequency', 'token_decoration_performance',
        'greedy_decoration_frequency', 'greedy_decoration_performance', 'alignments')
    :param log: The event log or Pandas dataframe that should be used, if decoration is required

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.discover_petri_net_inductive(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_petri_net(net, im, fm, 'petri_net.png')
    """
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    fmt = _extract_format(file_path)
    variant = _select_petri_net_variant(variant_str, pn_visualizer, log)
    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    parameters["decorations"] = decorations
    parameters["debug"] = debug
    gviz = pn_visualizer.apply(petri_net, initial_marking, final_marking,
                               log=log, variant=variant, parameters=parameters)
    return pn_visualizer.save(gviz, file_path)


def view_performance_dfg(dfg: dict, start_activities: dict, end_activities: dict, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW,
                         aggregation_measure="mean", bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, serv_time: Optional[Dict[str, float]] = None,
                         graph_title: Optional[str] = None):
    """
    Views a performance DFG.

    :param dfg: DFG object
    :param start_activities: Start activities
    :param end_activities: End activities
    :param format: Format of the output picture (if 'html' is provided, GraphvizJS is used to render the visualization in an HTML page)
    :param aggregation_measure: Aggregation measure (default: mean), possible values: mean, median, min, max, sum, stdev
    :param bgcolor: Background color of the visualization (default: white)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param serv_time: (optional) Provides the activities' service times, used to decorate the graph
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        performance_dfg, start_activities, end_activities = pm4py.discover_performance_dfg(dataframe, case_id_key='case:concept:name', activity_key='concept:name', timestamp_key='time:timestamp')
        pm4py.view_performance_dfg(performance_dfg, start_activities, end_activities, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.dfg import visualizer as dfg_visualizer
    from pm4py.visualization.dfg.variants import performance as dfg_perf_visualizer
    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    dfg_parameters = dfg_perf_visualizer.Parameters
    parameters[dfg_parameters.START_ACTIVITIES] = start_activities
    parameters[dfg_parameters.END_ACTIVITIES] = end_activities
    parameters[dfg_parameters.AGGREGATION_MEASURE] = aggregation_measure
    gviz = dfg_perf_visualizer.apply(dfg, serv_time=serv_time, parameters=parameters)
    dfg_visualizer.view(gviz)


def save_vis_performance_dfg(dfg: dict, start_activities: dict, end_activities: dict, file_path: str,
                             aggregation_measure="mean", bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, serv_time: Optional[Dict[str, float]] = None,
                             graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of a performance DFG.

    :param dfg: DFG object
    :param start_activities: Start activities
    :param end_activities: End activities
    :param file_path: Destination path
    :param aggregation_measure: Aggregation measure (default: mean), possible values: mean, median, min, max, sum, stdev
    :param bgcolor: Background color of the visualization (default: white)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param serv_time: (optional) Provides the activities' service times, used to decorate the graph
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        performance_dfg, start_activities, end_activities = pm4py.discover_performance_dfg(dataframe, case_id_key='case:concept:name', activity_key='concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_performance_dfg(performance_dfg, start_activities, end_activities, 'perf_dfg.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.dfg import visualizer as dfg_visualizer
    from pm4py.visualization.dfg.variants import performance as dfg_perf_visualizer
    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    dfg_parameters = dfg_perf_visualizer.Parameters
    parameters[dfg_parameters.START_ACTIVITIES] = start_activities
    parameters[dfg_parameters.END_ACTIVITIES] = end_activities
    parameters[dfg_parameters.AGGREGATION_MEASURE] = aggregation_measure
    gviz = dfg_perf_visualizer.apply(dfg, serv_time=serv_time, parameters=parameters)
    return dfg_visualizer.save(gviz, file_path)


def view_dfg(dfg: dict, start_activities: dict, end_activities: dict, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", max_num_edges: int = sys.maxsize, rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, graph_title: Optional[str] = None):
    """
    Views a (composite) DFG.

    :param dfg: DFG object
    :param start_activities: Start activities
    :param end_activities: End activities
    :param format: Format of the output picture (if 'html' is provided, GraphvizJS is used to render the visualization in an HTML page)
    :param bgcolor: Background color of the visualization (default: white)
    :param max_num_edges: Maximum number of edges to represent in the graph
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        dfg, start_activities, end_activities = pm4py.discover_dfg(dataframe, case_id_key='case:concept:name', activity_key='concept:name', timestamp_key='time:timestamp')
        pm4py.view_dfg(dfg, start_activities, end_activities, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.dfg import visualizer as dfg_visualizer
    dfg_parameters = dfg_visualizer.Variants.FREQUENCY.value.Parameters
    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    parameters["maxNoOfEdgesInDiagram"] = max_num_edges
    parameters[dfg_parameters.START_ACTIVITIES] = start_activities
    parameters[dfg_parameters.END_ACTIVITIES] = end_activities
    gviz = dfg_visualizer.apply(dfg, variant=dfg_visualizer.Variants.FREQUENCY,
                                parameters=parameters)
    dfg_visualizer.view(gviz)


def save_vis_dfg(dfg: dict, start_activities: dict, end_activities: dict, file_path: str, bgcolor: str = "white", max_num_edges: int = sys.maxsize, rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, graph_title: Optional[str] = None, **kwargs):
    """
    Saves a DFG visualization to a file.

    :param dfg: DFG object
    :param start_activities: Start activities
    :param end_activities: End activities
    :param file_path: Destination path
    :param bgcolor: Background color of the visualization (default: white)
    :param max_num_edges: Maximum number of edges to represent in the graph
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        dfg, start_activities, end_activities = pm4py.discover_dfg(dataframe, case_id_key='case:concept:name', activity_key='concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_dfg(dfg, start_activities, end_activities, 'dfg.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.dfg import visualizer as dfg_visualizer
    dfg_parameters = dfg_visualizer.Variants.FREQUENCY.value.Parameters
    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    parameters["maxNoOfEdgesInDiagram"] = max_num_edges
    parameters[dfg_parameters.START_ACTIVITIES] = start_activities
    parameters[dfg_parameters.END_ACTIVITIES] = end_activities
    gviz = dfg_visualizer.apply(dfg, variant=dfg_visualizer.Variants.FREQUENCY,
                                parameters=parameters)
    return dfg_visualizer.save(gviz, file_path)


def view_process_tree(tree: ProcessTree, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, graph_title: Optional[str] = None):
    """
    Views a process tree.

    :param tree: Process tree
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used to render the visualization in an HTML page)
    :param bgcolor: Background color of the visualization (default: white)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        process_tree = pm4py.discover_process_tree_inductive(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.view_process_tree(process_tree, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.process_tree import visualizer as pt_visualizer
    parameters = pt_visualizer.Variants.WO_DECORATION.value.Parameters
    props = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = pt_visualizer.apply(tree, parameters={**props, **{parameters.FORMAT: fmt}})
    pt_visualizer.view(gviz)


def save_vis_process_tree(tree: ProcessTree, file_path: str, bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of a process tree.

    :param tree: Process tree
    :param file_path: Destination path
    :param bgcolor: Background color of the visualization (default: white)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        process_tree = pm4py.discover_process_tree_inductive(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_process_tree(process_tree, 'process_tree.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.process_tree import visualizer as pt_visualizer
    parameters = pt_visualizer.Variants.WO_DECORATION.value.Parameters
    props = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = pt_visualizer.apply(tree, parameters={**props, **{parameters.FORMAT: fmt}})
    return pt_visualizer.save(gviz, file_path)


def save_vis_bpmn(bpmn_graph: BPMN, file_path: str, bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, variant_str: str = "classic", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of a BPMN graph.

    :param bpmn_graph: BPMN graph
    :param file_path: Destination path
    :param bgcolor: Background color of the visualization (default: white)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param variant_str: Variant of the visualization to be used ("classic" or "dagrejs")
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        bpmn_graph = pm4py.discover_bpmn_inductive(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_bpmn(bpmn_graph, 'trial.bpmn')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
    variant = None
    if variant_str == "classic":
        variant = bpmn_visualizer.Variants.CLASSIC
    elif variant_str == "classic_v2":
        variant = bpmn_visualizer.Variants.CLASSIC_V2        
    elif variant_str == "dagrejs":
        variant = bpmn_visualizer.Variants.DAGREJS
    props = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = bpmn_visualizer.apply(bpmn_graph, variant=variant, parameters=props)
    return bpmn_visualizer.save(gviz, file_path, variant=variant)


def view_bpmn(bpmn_graph: BPMN, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, variant_str: str = "classic", graph_title: Optional[str] = None):
    """
    Views a BPMN graph.

    :param bpmn_graph: BPMN graph
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used to render the visualization in an HTML page)
    :param bgcolor: Background color of the visualization (default: white)
    :param rankdir: Sets the direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)
    :param variant_str: Variant of the visualization to be used ("classic" or "dagrejs")
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        bpmn_graph = pm4py.discover_bpmn_inductive(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.view_bpmn(bpmn_graph)
    """
    fmt = _extract_format(format)
    from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
    variant = None
    if variant_str == "classic":
        variant = bpmn_visualizer.Variants.CLASSIC
    elif variant_str == "classic_v2":
        variant = bpmn_visualizer.Variants.CLASSIC_V2
    elif variant_str == "dagrejs":
        variant = bpmn_visualizer.Variants.DAGREJS
    props = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = bpmn_visualizer.apply(bpmn_graph, variant=variant, parameters=props)
    bpmn_visualizer.view(gviz, variant=variant)


def view_heuristics_net(heu_net: HeuristicsNet, format: str = "png", bgcolor: str = "white", graph_title: Optional[str] = None):
    """
    Views a heuristics net.

    :param heu_net: Heuristics net
    :param format: Format of the visualization
    :param bgcolor: Background color of the visualization (default: white)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        heu_net = pm4py.discover_heuristics_net(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.view_heuristics_net(heu_net, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
    parameters = hn_visualizer.Variants.PYDOTPLUS.value.Parameters
    props = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = hn_visualizer.apply(heu_net, parameters={**props, **{parameters.FORMAT: fmt}})
    hn_visualizer.view(gviz)


def save_vis_heuristics_net(heu_net: HeuristicsNet, file_path: str, bgcolor: str = "white", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of a heuristics net.

    :param heu_net: Heuristics net
    :param file_path: Destination path
    :param bgcolor: Background color of the visualization (default: white)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        heu_net = pm4py.discover_heuristics_net(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_heuristics_net(heu_net, 'heu.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
    parameters = hn_visualizer.Variants.PYDOTPLUS.value.Parameters
    props = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = hn_visualizer.apply(heu_net, parameters={**props, **{parameters.FORMAT: fmt}})
    return hn_visualizer.save(gviz, file_path)


def __dotted_attribute_selection(log: Union[EventLog, pd.DataFrame], attributes):
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log)

    if attributes is None:
        from pm4py.util import xes_constants
        from pm4py.objects.log.util import sorting
        from pm4py.objects.conversion.log import converter
        log = converter.apply(log, variant=converter.Variants.TO_EVENT_LOG)
        log = sorting.sort_timestamp(log, xes_constants.DEFAULT_TIMESTAMP_KEY)
        for index, trace in enumerate(log):
            trace.attributes["@@index"] = index
        attributes = ["time:timestamp", "case:@@index", "concept:name"]
    return log, attributes


def view_dotted_chart(log: Union[EventLog, pd.DataFrame], format: str = "png", attributes=None, bgcolor: str = "white", show_legend: bool = True, graph_title: Optional[str] = None):
    """
    Displays the dotted chart.

    Each event in the log is represented as a point. Dimensions are:
    - X-axis: The value of the first selected attribute.
    - Y-axis: The value of the second selected attribute.
    - Color: The value of the third selected attribute.

    If attributes are not provided, a default dotted chart is shown:
    X-axis: time
    Y-axis: case index (in order of occurrence)
    Color: activity

    :param log: Event log
    :param format: Image format
    :param attributes: Attributes used to construct the dotted chart. If None, the default dotted chart is used. For custom attributes, use a list of the form [x-axis attribute, y-axis attribute, color attribute].
    :param bgcolor: Background color of the chart (default: white)
    :param show_legend: Boolean (enables/disables the legend)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.view_dotted_chart(dataframe, format='svg')
        pm4py.view_dotted_chart(dataframe, attributes=['time:timestamp', 'concept:name', 'org:resource'])
    """
    fmt = _extract_format(format)
    log, attributes = __dotted_attribute_selection(log, attributes)
    from pm4py.visualization.dotted_chart import visualizer as dotted_chart_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    params["show_legend"] = show_legend
    gviz = dotted_chart_visualizer.apply(log, attributes, parameters=params)
    dotted_chart_visualizer.view(gviz)


def save_vis_dotted_chart(log: Union[EventLog, pd.DataFrame], file_path: str, attributes=None, bgcolor: str = "white", show_legend: bool = True, graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of the dotted chart.

    Each event in the log is represented as a point. Dimensions are:
    - X-axis: The value of the first selected attribute.
    - Y-axis: The value of the second selected attribute.
    - Color: The value of the third selected attribute.

    If attributes are not provided, a default dotted chart is used:
    X-axis: time
    Y-axis: case index (in order of occurrence)
    Color: activity

    :param log: Event log
    :param file_path: Destination path
    :param attributes: Attributes for the dotted chart. For example, ["time:timestamp", "concept:name", "org:resource"].
    :param bgcolor: Background color of the chart (default: white)
    :param show_legend: Boolean (enables/disables the legend)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.save_vis_dotted_chart(dataframe, 'dotted.png', attributes=['time:timestamp', 'concept:name', 'org:resource'])
    """
    fmt = _extract_format(file_path)
    log, attributes = __dotted_attribute_selection(log, attributes)
    from pm4py.visualization.dotted_chart import visualizer as dotted_chart_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    params["show_legend"] = show_legend
    gviz = dotted_chart_visualizer.apply(log, attributes, parameters=params)
    return dotted_chart_visualizer.save(gviz, file_path)


def view_sna(sna_metric: SNA, variant_str: Optional[str] = None):
    """
    Represents a SNA metric (.html).

    :param sna_metric: Values of the metric
    :param variant_str: Variant to be used (default: pyvis)

    .. code-block:: python3

        import pm4py

        metric = pm4py.discover_subcontracting_network(dataframe, resource_key='org:resource', timestamp_key='time:timestamp', case_id_key='case:concept:name')
        pm4py.view_sna(metric)
    """
    if variant_str is None:
        if constants.DEFAULT_GVIZ_VIEW == "matplotlib_view":
            variant_str = "networkx"
        else:
            variant_str = "pyvis"

    from pm4py.visualization.sna import visualizer as sna_visualizer
    variant = sna_visualizer.Variants.PYVIS
    if variant_str == "networkx":
        variant = sna_visualizer.Variants.NETWORKX
    gviz = sna_visualizer.apply(sna_metric, variant=variant)
    sna_visualizer.view(gviz, variant=variant)


def save_vis_sna(sna_metric: SNA, file_path: str, variant_str: Optional[str] = None, **kwargs):
    """
    Saves the visualization of a SNA metric in a .html file.

    :param sna_metric: Values of the metric
    :param file_path: Destination path
    :param variant_str: Variant to be used (default: pyvis)

    .. code-block:: python3

        import pm4py

        metric = pm4py.discover_subcontracting_network(dataframe, resource_key='org:resource', timestamp_key='time:timestamp', case_id_key='case:concept:name')
        pm4py.save_vis_sna(metric, 'sna.png')
    """
    if variant_str is None:
        if constants.DEFAULT_GVIZ_VIEW == "matplotlib_view":
            variant_str = "networkx"
        else:
            variant_str = "pyvis"

    from pm4py.visualization.sna import visualizer as sna_visualizer
    variant = sna_visualizer.Variants.PYVIS
    if variant_str == "networkx":
        variant = sna_visualizer.Variants.NETWORKX

    gviz = sna_visualizer.apply(sna_metric, variant=variant)
    return sna_visualizer.save(gviz, file_path, variant=variant)


def view_case_duration_graph(log: Union[EventLog, pd.DataFrame], format: str = "png", activity_key="concept:name", timestamp_key="time:timestamp", case_id_key="case:concept:name", graph_title: Optional[str] = None):
    """
    Visualizes the case duration graph.

    :param log: Log object
    :param format: Format of the visualization (png, svg, ...)
    :param activity_key: Attribute to be used as activity
    :param case_id_key: Attribute to be used as case identifier
    :param timestamp_key: Attribute to be used as timestamp
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.view_case_duration_graph(dataframe, format='svg', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(format)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
        from pm4py.statistics.traces.generic.pandas import case_statistics
        graph = case_statistics.get_kde_caseduration(log, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    else:
        from pm4py.statistics.traces.generic.log import case_statistics
        graph = case_statistics.get_kde_caseduration(log, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    from pm4py.visualization.graphs import visualizer as graphs_visualizer
    properties = {"format": fmt}
    if graph_title is not None:
        properties["title"] = graph_title

    graph_vis = graphs_visualizer.apply(graph[0], graph[1], variant=graphs_visualizer.Variants.CASES,
                                        parameters=properties)
    graphs_visualizer.view(graph_vis)


def save_vis_case_duration_graph(log: Union[EventLog, pd.DataFrame], file_path: str, activity_key="concept:name", timestamp_key="time:timestamp", case_id_key="case:concept:name", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the case duration graph to the specified path.

    :param log: Log object
    :param file_path: Destination path
    :param activity_key: Attribute to be used as activity
    :param case_id_key: Attribute to be used as case identifier
    :param timestamp_key: Attribute to be used as timestamp
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.save_vis_case_duration_graph(dataframe, 'duration.png', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(file_path)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
        from pm4py.statistics.traces.generic.pandas import case_statistics
        graph = case_statistics.get_kde_caseduration(log, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    else:
        from pm4py.statistics.traces.generic.log import case_statistics
        graph = case_statistics.get_kde_caseduration(log, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    from pm4py.visualization.graphs import visualizer as graphs_visualizer
    properties = {"format": fmt}
    if graph_title is not None:
        properties["title"] = graph_title

    graph_vis = graphs_visualizer.apply(graph[0], graph[1], variant=graphs_visualizer.Variants.CASES,
                                        parameters=properties)
    return graphs_visualizer.save(graph_vis, file_path)


def view_events_per_time_graph(log: Union[EventLog, pd.DataFrame], format: str = "png", activity_key="concept:name", timestamp_key="time:timestamp", case_id_key="case:concept:name", graph_title: Optional[str] = None):
    """
    Visualizes the events per time graph.

    :param log: Log object
    :param format: Format of the visualization (png, svg, ...)
    :param activity_key: Attribute to be used as activity
    :param case_id_key: Attribute to be used as case identifier
    :param timestamp_key: Attribute to be used as timestamp
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.view_events_per_time_graph(dataframe, format='svg', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(format)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
        from pm4py.statistics.attributes.pandas import get as attributes_get
        graph = attributes_get.get_kde_date_attribute(log, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    else:
        from pm4py.statistics.attributes.log import get as attributes_get
        graph = attributes_get.get_kde_date_attribute(log, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    from pm4py.visualization.graphs import visualizer as graphs_visualizer
    properties = {"format": fmt}
    if graph_title is not None:
        properties["title"] = graph_title

    graph_vis = graphs_visualizer.apply(graph[0], graph[1], variant=graphs_visualizer.Variants.DATES,
                                        parameters=properties)
    graphs_visualizer.view(graph_vis)


def save_vis_events_per_time_graph(log: Union[EventLog, pd.DataFrame], file_path: str, activity_key="concept:name", timestamp_key="time:timestamp", case_id_key="case:concept:name", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the events per time graph to the specified path.

    :param log: Log object
    :param file_path: Destination path
    :param activity_key: Attribute to be used as activity
    :param case_id_key: Attribute to be used as case identifier
    :param timestamp_key: Attribute to be used as timestamp
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.save_vis_events_per_time_graph(dataframe, 'ev_time.png', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(file_path)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
        from pm4py.statistics.attributes.pandas import get as attributes_get
        graph = attributes_get.get_kde_date_attribute(log, attribute=timestamp_key, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    else:
        from pm4py.statistics.attributes.log import get as attributes_get
        graph = attributes_get.get_kde_date_attribute(log, attribute=timestamp_key, parameters=get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key))
    fmt = _extract_format(file_path)
    from pm4py.visualization.graphs import visualizer as graphs_visualizer
    properties = {"format": fmt}
    if graph_title is not None:
        properties["title"] = graph_title

    graph_vis = graphs_visualizer.apply(graph[0], graph[1], variant=graphs_visualizer.Variants.DATES,
                                        parameters=properties)

    return graphs_visualizer.save(graph_vis, file_path)


def view_performance_spectrum(log: Union[EventLog, pd.DataFrame], activities: List[str], format: str = "png", activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name", bgcolor: str = "white", graph_title: Optional[str] = None):
    """
    Displays the performance spectrum.

    The performance spectrum is a novel visualization of the performance of the process, showing time elapsed between different activities.
    Refer to:
    Denisov, Vadim, et al. "The Performance Spectrum Miner: Visual Analytics for Fine-Grained Performance Analysis of Processes."
    BPM (Dissertation/Demos/Industry). 2018.

    :param log: Event log
    :param activities: List of activities (in order) used to build the performance spectrum
    :param format: Format of the visualization (png, svg ...)
    :param activity_key: Attribute to be used for the activity
    :param timestamp_key: Attribute to be used for the timestamp
    :param case_id_key: Attribute to be used as case identifier
    :param bgcolor: Background color of the visualization (default: white)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.view_performance_spectrum(dataframe, ['Act. A', 'Act. C', 'Act. D'], format='svg', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(format)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)

    properties = get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    from pm4py.algo.discovery.performance_spectrum import algorithm as performance_spectrum
    perf_spectrum = performance_spectrum.apply(log, activities, parameters=properties)
    from pm4py.visualization.performance_spectrum import visualizer as perf_spectrum_visualizer
    from pm4py.visualization.performance_spectrum.variants import neato

    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = perf_spectrum_visualizer.apply(perf_spectrum, parameters={**params, **{neato.Parameters.FORMAT.value: fmt}})
    perf_spectrum_visualizer.view(gviz)


def save_vis_performance_spectrum(log: Union[EventLog, pd.DataFrame], activities: List[str], file_path: str, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp", case_id_key: str = "case:concept:name", bgcolor: str = "white", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of the performance spectrum to a file.

    Refer to:
    Denisov, Vadim, et al. "The Performance Spectrum Miner: Visual Analytics for Fine-Grained Performance Analysis of Processes."
    BPM (Dissertation/Demos/Industry). 2018.

    :param log: Event log
    :param activities: List of activities used to build the performance spectrum
    :param file_path: Destination path (including the extension)
    :param activity_key: Attribute to be used for the activity
    :param timestamp_key: Attribute to be used for the timestamp
    :param case_id_key: Attribute to be used as case identifier
    :param bgcolor: Background color of the visualization (default: white)
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.save_vis_performance_spectrum(dataframe, ['Act. A', 'Act. C', 'Act. D'], 'perf_spec.png', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(file_path)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)

    properties = get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    from pm4py.algo.discovery.performance_spectrum import algorithm as performance_spectrum
    perf_spectrum = performance_spectrum.apply(log, activities, parameters=properties)
    from pm4py.visualization.performance_spectrum import visualizer as perf_spectrum_visualizer
    from pm4py.visualization.performance_spectrum.variants import neato

    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = perf_spectrum_visualizer.apply(perf_spectrum, parameters={**params, **{neato.Parameters.FORMAT.value: fmt}})
    return perf_spectrum_visualizer.save(gviz, file_path)


def __builds_events_distribution_graph(log: Union[EventLog, pd.DataFrame], parameters, distr_type: str = "days_week"):
    if distr_type == "days_month":
        title = "Distribution of the Events over the Days of a Month"; x_axis = "Day of month"; y_axis = "Number of Events"
    elif distr_type == "months":
        title = "Distribution of the Events over the Months"; x_axis = "Month"; y_axis = "Number of Events"
    elif distr_type == "years":
        title = "Distribution of the Events over the Years"; x_axis = "Year"; y_axis = "Number of Events"
    elif distr_type == "hours":
        title = "Distribution of the Events over the Hours"; x_axis = "Hour (of day)"; y_axis = "Number of Events"
    elif distr_type == "days_week":
        title = "Distribution of the Events over the Days of a Week"; x_axis = "Day of the Week"; y_axis = "Number of Events"
    elif distr_type == "weeks":
        title = "Distribution of the Events over the Weeks of a Year"; x_axis = "Week of the Year"; y_axis = "Number of Events"
    else:
        raise Exception("Unsupported distribution specified.")

    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log)
        from pm4py.statistics.attributes.pandas import get as attributes_get
        x, y = attributes_get.get_events_distribution(log, distr_type=distr_type, parameters=parameters)
    else:
        from pm4py.statistics.attributes.log import get as attributes_get
        x, y = attributes_get.get_events_distribution(log, distr_type=distr_type, parameters=parameters)

    return title, x_axis, y_axis, x, y


def view_events_distribution_graph(log: Union[EventLog, pd.DataFrame], distr_type: str = "days_week", format="png", activity_key="concept:name", timestamp_key="time:timestamp", case_id_key="case:concept:name", graph_title: Optional[str] = None):
    """
    Shows the distribution of the events in the specified dimension.

    This allows identifying work shifts, busy days, and busy periods of the year.

    :param log: Event log
    :param distr_type: Type of distribution (default: days_week):
        - days_month: Distribution of events among days of a month (1-31)
        - months: Distribution of events among months (1-12)
        - years: Distribution of events among years
        - hours: Distribution of events among hours of a day (0-23)
        - days_week: Distribution of events among days of the week (Mon-Sun)
        - weeks: Distribution of events among weeks of a year (0-52)
    :param format: Format of the visualization (default: png)
    :param activity_key: Attribute to be used as activity
    :param case_id_key: Attribute to be used as case identifier
    :param timestamp_key: Attribute to be used as timestamp
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.view_events_distribution_graph(dataframe, format='svg', distr_type='days_week', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(format)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)

    parameters = get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    title, x_axis, y_axis, x, y = __builds_events_distribution_graph(log, parameters, distr_type)
    parameters["title"] = graph_title if graph_title else title
    parameters["x_axis"] = x_axis
    parameters["y_axis"] = y_axis
    parameters["format"] = fmt

    from pm4py.visualization.graphs import visualizer as graphs_visualizer
    gviz = graphs_visualizer.apply(x, y, variant=graphs_visualizer.Variants.BARPLOT, parameters=parameters)
    graphs_visualizer.view(gviz)


def save_vis_events_distribution_graph(log: Union[EventLog, pd.DataFrame], file_path: str,
                                       distr_type: str = "days_week", activity_key="concept:name", timestamp_key="time:timestamp", case_id_key="case:concept:name", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the distribution of the events in a picture file.

    Observing the distribution of events over time helps infer work shifts, working days, and busy periods of the year.

    :param log: Event log
    :param file_path: Destination path (including the extension)
    :param distr_type: Type of distribution (default: days_week):
        - days_month: Events distribution among days of a month (1-31)
        - months: Events distribution among months (1-12)
        - years: Events distribution among years
        - hours: Events distribution among hours of a day (0-23)
        - days_week: Events distribution among days of a week (Mon-Sun)
        - weeks: Events distribution among weeks of a year (0-52)
    :param activity_key: Attribute to be used as activity
    :param case_id_key: Attribute to be used as case identifier
    :param timestamp_key: Attribute to be used as timestamp
    :param graph_title: Sets the title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        pm4py.save_vis_events_distribution_graph(dataframe, 'ev_distr_graph.png', distr_type='days_week', activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
    """
    fmt = _extract_format(file_path)
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)

    parameters = get_properties(log, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    title, x_axis, y_axis, x, y = __builds_events_distribution_graph(log, parameters, distr_type)
    parameters["title"] = graph_title if graph_title else title
    parameters["x_axis"] = x_axis
    parameters["y_axis"] = y_axis
    parameters["format"] = fmt

    from pm4py.visualization.graphs import visualizer as graphs_visualizer
    gviz = graphs_visualizer.apply(x, y, variant=graphs_visualizer.Variants.BARPLOT, parameters=parameters)
    return graphs_visualizer.save(gviz, file_path)


def view_ocdfg(
    ocdfg: Dict[str, Any],
    annotation: str = "frequency",
    act_metric: str = "events",
    edge_metric="event_couples",
    act_threshold: int = 0,
    edge_threshold: int = 0,
    performance_aggregation: str = "mean",
    format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW,
    bgcolor: str = "white",
    rankdir: str = constants.DEFAULT_RANKDIR_GVIZ,
    graph_title: Optional[str] = None,
    variant_str: str = "classic",
):
    """
    Views an OC-DFG (object-centric directly-follows graph).

    :param ocdfg: Object-centric directly-follows graph
    :param annotation: The annotation to use ("frequency" or "performance")
    :param act_metric: The metric for activities ("events", "unique_objects", "total_objects")
    :param edge_metric: The metric for edges ("event_couples", "unique_objects", "total_objects")
    :param act_threshold: Threshold on activities frequency (default: 0)
    :param edge_threshold: Threshold on edges frequency (default: 0)
    :param performance_aggregation: Aggregation measure for performance: mean, median, min, max, sum
    :param format: Format of the output (if 'html' is provided, GraphvizJS is used)
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)
    :param variant_str: Variant of the visualization ("classic" or "elkjs")

    .. code-block:: python3

        import pm4py

        ocdfg = pm4py.discover_ocdfg(ocel)
        pm4py.view_ocdfg(ocdfg, annotation='frequency', format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.ocel.ocdfg import visualizer

    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    parameters["annotation"] = annotation
    parameters["act_metric"] = act_metric
    parameters["edge_metric"] = edge_metric
    parameters["act_threshold"] = act_threshold
    parameters["edge_threshold"] = edge_threshold
    parameters["aggregation_measure"] = performance_aggregation

    variant = (
        visualizer.Variants.CLASSIC
        if variant_str == "classic"
        else visualizer.Variants.ELKJS
    )

    gviz = visualizer.apply(ocdfg, variant=variant, parameters=parameters)
    visualizer.view(gviz, variant=variant)


def save_vis_ocdfg(
    ocdfg: Dict[str, Any],
    file_path: str,
    annotation: str = "frequency",
    act_metric: str = "events",
    edge_metric="event_couples",
    act_threshold: int = 0,
    edge_threshold: int = 0,
    performance_aggregation: str = "mean",
    bgcolor: str = "white",
    rankdir: str = constants.DEFAULT_RANKDIR_GVIZ,
    graph_title: Optional[str] = None,
    variant_str: str = "classic",
    **kwargs
):
    """
    Saves the visualization of an OC-DFG.

    :param ocdfg: Object-centric directly-follows graph
    :param file_path: Destination path
    :param annotation: "frequency" or "performance"
    :param act_metric: Metric for activities ("events", "unique_objects", "total_objects")
    :param edge_metric: Metric for edges ("event_couples", "unique_objects", "total_objects")
    :param act_threshold: Threshold on activities frequency
    :param edge_threshold: Threshold on edges frequency
    :param performance_aggregation: Aggregation measure for performance: mean, median, min, max, sum
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)
    :param variant_str: Variant ("classic" or "elkjs")

    .. code-block:: python3

        import pm4py

        ocdfg = pm4py.discover_ocdfg(ocel)
        pm4py.save_vis_ocdfg(ocdfg, 'ocdfg.png', annotation='frequency')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.ocel.ocdfg import visualizer

    parameters = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    parameters["annotation"] = annotation
    parameters["act_metric"] = act_metric
    parameters["edge_metric"] = edge_metric
    parameters["act_threshold"] = act_threshold
    parameters["edge_threshold"] = edge_threshold
    parameters["aggregation_measure"] = performance_aggregation

    variant = (
        visualizer.Variants.CLASSIC
        if variant_str == "classic"
        else visualizer.Variants.ELKJS
    )
    gviz = visualizer.apply(ocdfg, variant=variant, parameters=parameters)
    return visualizer.save(gviz, file_path, variant=variant)


def view_ocpn(
    ocpn: Dict[str, Any],
    format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW,
    bgcolor: str = "white",
    rankdir: str = constants.DEFAULT_RANKDIR_GVIZ,
    graph_title: Optional[str] = None,
    variant_str: str = "wo_decoration"
):
    """
    Visualizes the object-centric Petri net.

    :param ocpn: Object-centric Petri net
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used)
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)
    :param variant_str: Variant to be used ("wo_decoration" or "brachmann")

    .. code-block:: python3

        import pm4py

        ocpn = pm4py.discover_oc_petri_net(ocel)
        pm4py.view_ocpn(ocpn, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.ocel.ocpn import visualizer as ocpn_visualizer

    props = _setup_parameters(fmt, bgcolor, rankdir, graph_title)

    variant = (
        ocpn_visualizer.Variants.WO_DECORATION
        if variant_str == "wo_decoration"
        else ocpn_visualizer.Variants.BRACHMANN
    )

    gviz = ocpn_visualizer.apply(ocpn, variant=variant, parameters=props)
    ocpn_visualizer.view(gviz)


def save_vis_ocpn(
    ocpn: Dict[str, Any],
    file_path: str,
    bgcolor: str = "white",
    rankdir: str = constants.DEFAULT_RANKDIR_GVIZ,
    graph_title: Optional[str] = None,
    variant_str: str = "wo_decoration",
    **kwargs
):
    """
    Saves the visualization of the object-centric Petri net into a file.

    :param ocpn: Object-centric Petri net
    :param file_path: Target path
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)
    :param variant_str: Variant to be used ("wo_decoration" or "brachmann")

    .. code-block:: python3

        import pm4py

        ocpn = pm4py.discover_oc_petri_net(ocel)
        pm4py.save_vis_ocpn(ocpn, 'ocpn.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.ocel.ocpn import visualizer as ocpn_visualizer

    props = _setup_parameters(fmt, bgcolor, rankdir, graph_title)

    variant = (
        ocpn_visualizer.Variants.WO_DECORATION
        if variant_str == "wo_decoration"
        else ocpn_visualizer.Variants.BRACHMANN
    )

    gviz = ocpn_visualizer.apply(ocpn, variant=variant, parameters=props)
    return ocpn_visualizer.save(gviz, file_path)


def view_network_analysis(network_analysis: Dict[Tuple[str, str], Dict[str, Any]], variant: str = "frequency", format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, activity_threshold: int = 1, edge_threshold: int = 1, bgcolor: str = "white", graph_title: Optional[str] = None):
    """
    Visualizes the network analysis.

    :param network_analysis: Network analysis
    :param variant: "frequency" or "performance"
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used)
    :param activity_threshold: Minimum occurrences of an activity to be included
    :param edge_threshold: Minimum occurrences of an edge to be included
    :param bgcolor: Background color (default: white)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        net_ana = pm4py.discover_network_analysis(dataframe, out_column='case:concept:name', in_column='case:concept:name', node_column_source='org:resource', node_column_target='org:resource', edge_column='concept:name')
        pm4py.view_network_analysis(net_ana, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.network_analysis import visualizer as network_analysis_visualizer
    chosen_variant = network_analysis_visualizer.Variants.PERFORMANCE if variant == "performance" else network_analysis_visualizer.Variants.FREQUENCY
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    params["activity_threshold"] = activity_threshold
    params["edge_threshold"] = edge_threshold

    gviz = network_analysis_visualizer.apply(network_analysis, variant=chosen_variant, parameters=params)
    network_analysis_visualizer.view(gviz)


def save_vis_network_analysis(network_analysis: Dict[Tuple[str, str], Dict[str, Any]], file_path: str, variant: str = "frequency", activity_threshold: int = 1, edge_threshold: int = 1, bgcolor: str = "white", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of the network analysis.

    :param network_analysis: Network analysis
    :param file_path: Target path
    :param variant: "frequency" or "performance"
    :param activity_threshold: Minimum occurrences of an activity
    :param edge_threshold: Minimum occurrences of an edge
    :param bgcolor: Background color (default: white)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        net_ana = pm4py.discover_network_analysis(dataframe, out_column='case:concept:name', in_column='case:concept:name', node_column_source='org:resource', node_column_target='org:resource', edge_column='concept:name')
        pm4py.save_vis_network_analysis(net_ana, 'net_ana.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.network_analysis import visualizer as network_analysis_visualizer
    chosen_variant = network_analysis_visualizer.Variants.PERFORMANCE if variant == "performance" else network_analysis_visualizer.Variants.FREQUENCY
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    params["activity_threshold"] = activity_threshold
    params["edge_threshold"] = edge_threshold

    gviz = network_analysis_visualizer.apply(network_analysis, variant=chosen_variant, parameters=params)
    return network_analysis_visualizer.save(gviz, file_path)


def view_transition_system(transition_system: TransitionSystem, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", graph_title: Optional[str] = None):
    """
    Views a transition system.

    :param transition_system: Transition system
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used)
    :param bgcolor: Background color (default: white)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        transition_system = pm4py.discover_transition_system(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.view_transition_system(transition_system, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.transition_system import visualizer as ts_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = ts_visualizer.apply(transition_system, parameters=params)
    ts_visualizer.view(gviz)


def save_vis_transition_system(transition_system: TransitionSystem, file_path: str, bgcolor: str = "white", graph_title: Optional[str] = None, **kwargs):
    """
    Persists the visualization of a transition system.

    :param transition_system: Transition system
    :param file_path: Destination path
    :param bgcolor: Background color (default: white)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        transition_system = pm4py.discover_transition_system(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_transition_system(transition_system, 'trans_system.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.transition_system import visualizer as ts_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = ts_visualizer.apply(transition_system, parameters=params)
    return ts_visualizer.save(gviz, file_path)


def view_prefix_tree(trie: Trie, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", graph_title: Optional[str] = None):
    """
    Views a prefix tree.

    :param trie: Prefix tree
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used)
    :param bgcolor: Background color (default: white)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        prefix_tree = pm4py.discover_prefix_tree(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.view_prefix_tree(prefix_tree, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.trie import visualizer as trie_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = trie_visualizer.apply(trie, parameters=params)
    trie_visualizer.view(gviz)


def save_vis_prefix_tree(trie: Trie, file_path: str, bgcolor: str = "white", graph_title: Optional[str] = None, **kwargs):
    """
    Persists the visualization of a prefix tree.

    :param trie: Prefix tree
    :param file_path: Destination path
    :param bgcolor: Background color (default: white)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        prefix_tree = pm4py.discover_prefix_tree(dataframe, activity_key='concept:name', case_id_key='case:concept:name', timestamp_key='time:timestamp')
        pm4py.save_vis_prefix_tree(prefix_tree, 'trie.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.trie import visualizer as trie_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = trie_visualizer.apply(trie, parameters=params)
    return trie_visualizer.save(gviz, file_path)


def view_alignments(log: Union[EventLog, pd.DataFrame], aligned_traces: List[Dict[str, Any]], format: str = "png", graph_title: Optional[str] = None):
    """
    Views the alignment table as a figure.

    :param log: Event log
    :param aligned_traces: Results of an alignment
    :param format: Format of the visualization (default: png)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/running-example.xes')
        net, im, fm = pm4py.discover_petri_net_inductive(log)
        aligned_traces = pm4py.conformance_diagnostics_alignments(log, net, im, fm)
        pm4py.view_alignments(log, aligned_traces, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.align_table import visualizer
    properties = {"format": fmt, "enable_graph_title": constants.DEFAULT_ENABLE_GRAPH_TITLES}
    if graph_title:
        properties["enable_graph_title"] = True
        properties["graph_title"] = graph_title
    gviz = visualizer.apply(log, aligned_traces, parameters=properties)
    visualizer.view(gviz)


def save_vis_alignments(log: Union[EventLog, pd.DataFrame], aligned_traces: List[Dict[str, Any]], file_path: str, graph_title: Optional[str] = None, **kwargs):
    """
    Saves an alignment table's figure on disk.

    :param log: Event log
    :param aligned_traces: Results of an alignment
    :param file_path: Target path
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/running-example.xes')
        net, im, fm = pm4py.discover_petri_net_inductive(log)
        aligned_traces = pm4py.conformance_diagnostics_alignments(log, net, im, fm)
        pm4py.save_vis_alignments(log, aligned_traces, 'output.svg')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.align_table import visualizer
    properties = {"format": fmt, "enable_graph_title": constants.DEFAULT_ENABLE_GRAPH_TITLES}
    if graph_title:
        properties["enable_graph_title"] = True
        properties["graph_title"] = graph_title

    gviz = visualizer.apply(log, aligned_traces, parameters=properties)
    return visualizer.save(gviz, file_path)


def view_footprints(footprints: Union[Tuple[Dict[str, Any], Dict[str, Any]], Dict[str, Any]], format: str = "png", graph_title: Optional[str] = None):
    """
    Views the footprints as a figure.

    :param footprints: Footprints
    :param format: Format of the visualization (default: png)
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/running-example.xes')
        fp_log = pm4py.discover_footprints(log)
        pm4py.view_footprints(fp_log, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.footprints import visualizer as fps_visualizer
    properties = {"format": fmt, "enable_graph_title": constants.DEFAULT_ENABLE_GRAPH_TITLES}
    if graph_title:
        properties["enable_graph_title"] = True
        properties["graph_title"] = graph_title

    if isinstance(footprints, dict):
        gviz = fps_visualizer.apply(footprints, parameters=properties)
    else:
        gviz = fps_visualizer.apply(footprints[0], footprints[1], variant=fps_visualizer.Variants.COMPARISON_SYMMETRIC, parameters=properties)

    fps_visualizer.view(gviz)


def save_vis_footprints(footprints: Union[Tuple[Dict[str, Any], Dict[str, Any]], Dict[str, Any]], file_path: str, graph_title: Optional[str] = None, **kwargs):
    """
    Saves the footprints' visualization on disk.

    :param footprints: Footprints
    :param file_path: Target path
    :param graph_title: Title of the visualization (if provided)

     .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/running-example.xes')
        fp_log = pm4py.discover_footprints(log)
        pm4py.save_vis_footprints(fp_log, 'output.svg')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.footprints import visualizer as fps_visualizer
    properties = {"format": fmt, "enable_graph_title": constants.DEFAULT_ENABLE_GRAPH_TITLES}
    if graph_title:
        properties["enable_graph_title"] = True
        properties["graph_title"] = graph_title

    if isinstance(footprints, dict):
        gviz = fps_visualizer.apply(footprints, parameters=properties)
    else:
        gviz = fps_visualizer.apply(footprints[0], footprints[1], variant=fps_visualizer.Variants.COMPARISON_SYMMETRIC, parameters=properties)

    return fps_visualizer.save(gviz, file_path)


def view_powl(powl: POWL, format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", variant_str: str = "basic", graph_title: Optional[str] = None):
    """
    Performs a visualization of a POWL model.

    Reference:
    Kourani, Humam, and Sebastiaan J. van Zelst.
    "POWL: partially ordered workflow language."
    International Conference on Business Process Management. Cham: Springer Nature Switzerland, 2023.

    :param powl: POWL model
    :param format: Format of the visualization (default: png)
    :param bgcolor: Background color (default: white)
    :param variant_str: Variant of the visualization to be used ("basic" or "net")
    :param graph_title: Title of the visualization (if provided)

     .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/running-example.xes')
        powl_model = pm4py.discover_powl(log)
        pm4py.view_powl(powl_model, format='svg', variant_str='basic')
        pm4py.view_powl(powl_model, format='svg', variant_str='net')
    """
    from pm4py.visualization.powl.visualizer import POWLVisualizationVariants
    variant = POWLVisualizationVariants.BASIC

    if variant_str == "basic":
        variant = POWLVisualizationVariants.BASIC
    elif variant_str == "net":
        variant = POWLVisualizationVariants.NET

    fmt = _extract_format(format)
    from pm4py.visualization.powl import visualizer as powl_visualizer
    params = _setup_parameters(fmt, bgcolor, graph_title=graph_title)
    gviz = powl_visualizer.apply(powl, variant=variant, parameters=params)

    powl_visualizer.view(gviz, parameters=params)


def save_vis_powl(powl: POWL, file_path: str, bgcolor: str = "white", rankdir: str = "TB", graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of a POWL model.

    Reference:
    Kourani, Humam, and Sebastiaan J. van Zelst.
    "POWL: partially ordered workflow language."
    International Conference on Business Process Management. Cham: Springer Nature Switzerland, 2023.

    :param powl: POWL model
    :param file_path: Target path
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)

     .. code-block:: python3

        import pm4py

        log = pm4py.read_xes('tests/input_data/running-example.xes')
        powl_model = pm4py.discover_powl(log)
        pm4py.save_vis_powl(powl_model, 'powl.png')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.powl import visualizer as powl_visualizer
    params = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = powl_visualizer.apply(powl, parameters=params)

    return powl_visualizer.save(gviz, file_path, parameters=params)


def view_object_graph(ocel: OCEL, graph: Set[Tuple[str, str]], format: str = constants.DEFAULT_FORMAT_GVIZ_VIEW, bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, graph_title: Optional[str] = None):
    """
    Visualizes an object graph on the screen.

    :param ocel: Object-centric event log
    :param graph: Object graph
    :param format: Format of the visualization (if 'html' is provided, GraphvizJS is used)
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('trial.ocel')
        obj_graph = pm4py.ocel_discover_objects_graph(ocel, graph_type='object_interaction')
        pm4py.view_object_graph(ocel, obj_graph, format='svg')
    """
    fmt = _extract_format(format)
    from pm4py.visualization.ocel.object_graph import visualizer as obj_graph_vis
    properties = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = obj_graph_vis.apply(ocel, graph, parameters=properties)
    obj_graph_vis.view(gviz)


def save_vis_object_graph(ocel: OCEL, graph: Set[Tuple[str, str]], file_path: str, bgcolor: str = "white", rankdir: str = constants.DEFAULT_RANKDIR_GVIZ, graph_title: Optional[str] = None, **kwargs):
    """
    Saves the visualization of an object graph.

    :param ocel: Object-centric event log
    :param graph: Object graph
    :param file_path: Destination path
    :param bgcolor: Background color (default: white)
    :param rankdir: Graph direction ("LR" or "TB")
    :param graph_title: Title of the visualization (if provided)

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel('trial.ocel')
        obj_graph = pm4py.ocel_discover_objects_graph(ocel, graph_type='object_interaction')
        pm4py.save_vis_object_graph(ocel, obj_graph, 'trial.pdf')
    """
    fmt = _extract_format(file_path)
    from pm4py.visualization.ocel.object_graph import visualizer as obj_graph_vis
    properties = _setup_parameters(fmt, bgcolor, rankdir, graph_title)
    gviz = obj_graph_vis.apply(ocel, graph, parameters=properties)
    return obj_graph_vis.save(gviz, file_path)
