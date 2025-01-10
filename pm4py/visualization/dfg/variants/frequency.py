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

from pm4py.statistics.attributes.log import get as attr_get
from pm4py.objects.dfg.utils import dfg_utils
from pm4py.util import xes_constants as xes
from pm4py.util import exec_utils
from pm4py.statistics.service_time.log import get as serv_time_get
from enum import Enum
from pm4py.util import constants
from typing import Optional, Dict, Any, Tuple
import graphviz
from pm4py.objects.log.obj import EventLog
from collections import Counter
from pm4py.visualization.dfg.util import dfg_gviz


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    FORMAT = "format"
    MAX_NO_EDGES_IN_DIAGRAM = "maxNoOfEdgesInDiagram"
    START_ACTIVITIES = "start_activities"
    END_ACTIVITIES = "end_activities"
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    FONT_SIZE = "font_size"
    RANKDIR = "rankdir"
    BGCOLOR = "bgcolor"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def apply(dfg: Dict[Tuple[str, str], int], log: EventLog = None, parameters: Optional[Dict[Any, Any]] = None, activities_count : Dict[str, int] = None, serv_time: Dict[str, float] = None) -> graphviz.Digraph:
    """
    Visualize a frequency directly-follows graph

    Parameters
    -----------------
    dfg
        Frequency Directly-follows graph
    log
        (if provided) Event log for the calculation of statistics
    activities_count
        (if provided) Dictionary associating to each activity the number of occurrences in the log.
    serv_time
        (if provided) Dictionary associating to each activity the average service time
    parameters
        Variant-specific parameters

    Returns
    -----------------
    gviz
        Graphviz digraph
    """
    if parameters is None:
        parameters = {}

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes.DEFAULT_NAME_KEY)
    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    max_no_of_edges_in_diagram = exec_utils.get_param_value(Parameters.MAX_NO_EDGES_IN_DIAGRAM, parameters, 100000)
    start_activities = exec_utils.get_param_value(Parameters.START_ACTIVITIES, parameters, {})
    end_activities = exec_utils.get_param_value(Parameters.END_ACTIVITIES, parameters, {})
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 12)
    font_size = str(font_size)

    if start_activities is None:
        start_activities = dict()
    if end_activities is None:
        end_activities = dict()
    activities = sorted(list(set(dfg_utils.get_activities_from_dfg(dfg)).union(set(start_activities)).union(set(end_activities))))

    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ)
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Frequency Directly-Follows Graph")

    if activities_count is None:
        if log is not None:
            activities_count = attr_get.get_attribute_values(log, activity_key, parameters=parameters)
        else:
            # the frequency of an activity in the log is at least the number of occurrences of
            # incoming arcs in the DFG.
            # if the frequency of the start activities nodes is also provided, use also that.
            activities_count = Counter({key: 0 for key in activities})
            for el in dfg:
                activities_count[el[1]] += dfg[el]
            if isinstance(start_activities, dict):
                for act in start_activities:
                    activities_count[act] += start_activities[act]

    if serv_time is None:
        if log is not None:
            serv_time = serv_time_get.apply(log, parameters=parameters)
        else:
            serv_time = {key: 0 for key in activities}

    return dfg_gviz.graphviz_visualization(activities_count, dfg, image_format=image_format, measure="frequency",
                                           max_no_of_edges_in_diagram=max_no_of_edges_in_diagram,
                                           start_activities=start_activities, end_activities=end_activities, serv_time=serv_time,
                                           font_size=font_size, bgcolor=bgcolor, rankdir=rankdir,
                                           enable_graph_title=enable_graph_title, graph_title=graph_title)
