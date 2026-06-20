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
from enum import Enum
from typing import Optional, Dict, Any, Union

import pandas as pd

from pm4py import util as pmutil, discover_process_tree_inductive
from pm4py.algo.discovery.log_refinement.log_refinement import LogRefinement
from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import EnhancedProcessTree
from pm4py.util import constants, exec_utils
from pm4py.util import xes_constants as xes_util
from pm4py.util.compression import util as comut
from pm4py.util.compression.dtypes import UVCL


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    NOISE_THRESHOLD = "noise_threshold"
    LIMIT = "limit"


def _dict_to_event_log(tuple_log: dict, activity_key="concept:name", timestamp_key="time:timestamp"):
    """
    Converts the internal compressed dictionary back into a standard PM4Py EventLog.
    This ensures the output is 100% compatible with top-level PM4Py algorithms.
    """
    from pm4py.objects.log.obj import EventLog, Trace, Event
    from datetime import datetime

    new_log = EventLog()
    for trace_tuple, frequency in tuple_log.items():
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


def apply(
        obj: Union[EventLog, pd.DataFrame, UVCL],
        parameters: Optional[Dict[Any, Any]] = None,
) -> EnhancedProcessTree:
    """
    Applies the Log Refinement discovery algorithm.
    """
    if parameters is None:
        parameters = {}

    ack = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_util.DEFAULT_NAME_KEY)
    tk = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters, xes_util.DEFAULT_TIMESTAMP_KEY)
    cidk = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, pmutil.constants.CASE_CONCEPT_NAME)
    noise_threshold = exec_utils.get_param_value(Parameters.NOISE_THRESHOLD, parameters, 0.0)
    limit = Parameters.LIMIT

    if isinstance(obj, dict):
        uvcl = obj
    else:
        uvcl = comut.get_variants(comut.project_univariate(obj, key=ack, df_glue=cidk, df_sorting_criterion_key=tk))

    log_refinement = LogRefinement(uvcl)
    revined_dict, annotations = log_refinement.run(limit=limit)

    refined_event_log = _dict_to_event_log(revined_dict)

    standard_tree = discover_process_tree_inductive(
        refined_event_log,
        noise_threshold=noise_threshold,
        activity_key=ack,
        timestamp_key=tk,
        case_id_key=cidk
    )

    from pm4py.objects.process_tree.utils.enhanced import convert_to_enhanced_tree
    enhanced_tree = convert_to_enhanced_tree(standard_tree, annotations)

    return enhanced_tree