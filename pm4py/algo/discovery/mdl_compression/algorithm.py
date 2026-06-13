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

from pm4py import util as pmutil
from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util import constants, exec_utils
from pm4py.util import xes_constants as xes_util
from pm4py.util.compression import util as comut
from pm4py.util.compression.dtypes import UVCL
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.mdl_compression.trace_compressor import TraceCompressor


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    NOISE_THRESHOLD = "noise_threshold"


def apply(
        obj: Union[EventLog, pd.DataFrame, UVCL],
        parameters: Optional[Dict[Any, Any]] = None,
) -> ProcessTree:
    """
    Applies the Minimum Description Length (MDL) Compression discovery algorithm.
    """
    if parameters is None:
        parameters = {}

    ack = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, parameters, xes_util.DEFAULT_NAME_KEY
    )
    tk = exec_utils.get_param_value(
        Parameters.TIMESTAMP_KEY, parameters, xes_util.DEFAULT_TIMESTAMP_KEY
    )
    cidk = exec_utils.get_param_value(
        Parameters.CASE_ID_KEY, parameters, pmutil.constants.CASE_CONCEPT_NAME
    )

    if type(obj) is UVCL:
        uvcl = obj
    else:
        uvcl = comut.get_variants(
            comut.project_univariate(
                obj, key=ack, df_glue=cidk, df_sorting_criterion_key=tk
            )
        )

    compressor = TraceCompressor(uvcl)
    compressed_uvcl, annotations = compressor.run()

    tree = inductive_miner.apply(compressed_uvcl, parameters=parameters)

    # TODO: Add the annotations (start, stop, skip) to the ProcessTree nodes.
    # We will build an annotator script later that traverses 'tree' and uses 'annotations'

    return tree