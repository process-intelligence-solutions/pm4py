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
from enum import Enum

from pm4py.util import constants, exec_utils
from pm4py.util import xes_constants as xes_util
from pm4py.util.business_hours import (
    BusinessHours,
    _as_utc_datetime,
    _prepare_scheduled_business_hours,
    soj_time_business_hours_diff,
)
from typing import Optional, Dict, Any, Union, Tuple
from pm4py.objects.log.obj import EventLog, EventStream


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    AGGREGATION_MEASURE = "aggregationMeasure"
    BUSINESS_HOURS = "business_hours"
    BUSINESS_HOUR_SLOTS = "business_hour_slots"
    WORKCALENDAR = "workcalendar"
    BUSINESS_TIMEZONE = "business_timezone"


def apply(
    log: Union[EventLog, EventStream],
    parameters: Optional[Dict[Union[str, Parameters], Any]] = None,
) -> Dict[Tuple[str, str], float]:
    return performance(log, parameters=parameters)


def performance(
    log: Union[EventLog, EventStream],
    parameters: Optional[Dict[Union[str, Parameters], Any]] = None,
) -> Dict[Tuple[str, str], float]:
    """
    Measure performance between couples of attributes in the DFG graph.

    Parameters
    ----------
    log
        Log
    parameters
        Possible parameters passed to the algorithms:
            aggregationMeasure -> performance aggregation measure (min, max, mean, median)
            activity_key -> Attribute to use as activity
            timestamp_key -> Attribute to use as timestamp

        - Parameters.BUSINESS_HOURS => calculates the difference of time based on the business hours, not the total time. Default: False
        - Parameters.BUSINESS_TIMEZONE => optional IANA timezone selecting
          scheduled elapsed seconds with valid aware timestamps. Requires
          business hours and microsecond precision.
        - Parameters.BUSINESS_HOURS_SLOTS => work schedule of the company.
          The following list defines that business hours are Mondays 07:00 - 17:00
          and Tuesdays 07:00 - 12:00 and 13:00 - 17:00::

            [
                (7 * 60 * 60, 17 * 60 * 60),
                ((24 + 7) * 60 * 60, (24 + 12) * 60 * 60),
                ((24 + 13) * 60 * 60, (24 + 17) * 60 * 60),
            ]
    Returns
    -------
    dfg : dict
        DFG graph

    """

    if parameters is None:
        parameters = {}

    from statistics import mean, median, stdev

    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, parameters, xes_util.DEFAULT_NAME_KEY
    )
    start_timestamp_key = exec_utils.get_param_value(
        Parameters.START_TIMESTAMP_KEY,
        parameters,
        xes_util.DEFAULT_TIMESTAMP_KEY,
    )
    timestamp_key = exec_utils.get_param_value(
        Parameters.TIMESTAMP_KEY, parameters, xes_util.DEFAULT_TIMESTAMP_KEY
    )
    aggregation_measure = exec_utils.get_param_value(
        Parameters.AGGREGATION_MEASURE, parameters, "mean"
    )

    business_hours = exec_utils.get_param_value(
        Parameters.BUSINESS_HOURS, parameters, False
    )
    business_hours_slots = exec_utils.get_param_value(
        Parameters.BUSINESS_HOUR_SLOTS,
        parameters,
        constants.DEFAULT_BUSINESS_HOUR_SLOTS,
    )

    workcalendar = exec_utils.get_param_value(
        Parameters.WORKCALENDAR,
        parameters,
        constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
    )

    business_timezone = exec_utils.get_param_value(
        Parameters.BUSINESS_TIMEZONE, parameters, None
    )
    if business_timezone is not None:
        if not business_hours:
            raise ValueError("business_timezone requires business_hours=True")
        business_hours_slots = tuple(
            tuple(slot) for slot in business_hours_slots
        )
        _prepare_scheduled_business_hours(
            business_hours_slots, business_timezone
        )
        for trace in log:
            for event in trace:
                for key in {timestamp_key, start_timestamp_key}:
                    _as_utc_datetime(event[key])
        dfgs0 = map(
            lambda trace: [
                (
                    (trace[i - 1][activity_key], trace[i][activity_key]),
                    soj_time_business_hours_diff(
                        trace[i - 1][timestamp_key],
                        trace[i][start_timestamp_key],
                        business_hours_slots,
                        workcalendar,
                        business_timezone=business_timezone,
                    ),
                )
                for i in range(1, len(trace))
            ],
            log,
        )
    elif business_hours:
        dfgs0 = map(
            (
                lambda t: [
                    (
                        (t[i - 1][activity_key], t[i][activity_key]),
                        max(
                            0,
                            BusinessHours(
                                t[i - 1][timestamp_key],
                                t[i][start_timestamp_key],
                                business_hour_slots=business_hours_slots,
                                workcalendar=workcalendar,
                            ).get_seconds(),
                        ),
                    )
                    for i in range(1, len(t))
                ]
            ),
            log,
        )
    else:
        dfgs0 = map(
            (
                lambda t: [
                    (
                        (t[i - 1][activity_key], t[i][activity_key]),
                        max(
                            0,
                            (
                                t[i][start_timestamp_key]
                                - t[i - 1][timestamp_key]
                            ).total_seconds(),
                        ),
                    )
                    for i in range(1, len(t))
                ]
            ),
            log,
        )
    ret0 = {}
    for el in dfgs0:
        for couple in el:
            if couple[0] not in ret0:
                ret0[couple[0]] = []
            ret0[couple[0]].append(couple[1])
    ret = Counter()
    for key in ret0:
        if aggregation_measure == "median":
            ret[key] = median(ret0[key])
        elif aggregation_measure == "min":
            ret[key] = min(ret0[key])
        elif aggregation_measure == "max":
            ret[key] = max(ret0[key])
        elif aggregation_measure == "stdev":
            ret[key] = stdev(ret0[key]) if len(ret0[key]) > 1 else 0
        elif aggregation_measure == "sum":
            ret[key] = sum(ret0[key])
        elif aggregation_measure == "raw_values":
            ret[key] = ret0[key]
        elif aggregation_measure == "all":
            ret[key] = {
                "median": median(ret0[key]),
                "min": min(ret0[key]),
                "max": max(ret0[key]),
                "stdev": stdev(ret0[key]) if len(ret0[key]) > 1 else 0,
                "sum": sum(ret0[key]),
                "mean": mean(ret0[key]),
            }
        else:
            ret[key] = mean(ret0[key])

    return ret
