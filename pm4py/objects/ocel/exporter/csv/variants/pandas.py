from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any
from pm4py.objects.ocel.util import ocel_consistency
from pm4py.objects.ocel.util import filtering_utils
from enum import Enum
from pm4py.util import exec_utils, constants as pm4_constants


class Parameters(Enum):
    ENCODING = "encoding"


def apply(ocel: OCEL, output_path: str, objects_path=None, parameters: Optional[Dict[Any, Any]] = None):
    """
    Exports an object-centric event log in a CSV file, using Pandas as backend

    Parameters
    -----------------
    ocel
        Object-centric event log
    output_path
        Destination file
    objects_path
        Optional path, where the objects dataframe is stored
    parameters
        Parameters of the algorithm
    """
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, pm4_constants.DEFAULT_ENCODING)

    ocel = ocel_consistency.apply(ocel, parameters=parameters)
    ocel = filtering_utils.propagate_relations_filtering(ocel, parameters=parameters)

    ocel.get_extended_table().to_csv(output_path, index=False, na_rep="", encoding=encoding)

    if objects_path is not None:
        ocel.objects.to_csv(objects_path, index=False, na_rep="", encoding=encoding)
