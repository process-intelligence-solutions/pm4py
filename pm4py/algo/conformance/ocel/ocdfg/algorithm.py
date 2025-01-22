from pm4py.algo.conformance.ocel.ocdfg.variants import graph_comparison
from pm4py.util import exec_utils
from typing import Optional, Dict, Any, Union
from enum import Enum
from pm4py.objects.ocel.obj import OCEL


class Variants(Enum):
    GRAPH_COMPARISON = graph_comparison


def apply(real: Union[OCEL, Dict[str, Any]], normative: Dict[str, Any], variant=Variants.GRAPH_COMPARISON, parameters: Optional[Dict[Any, Any]] = None) -> Dict[str, Any]:
    """
    Applies object-centric conformance checking between the given real object (object-centric event log or DFG)
    and a normative OC-DFG.

    Parameters
    -----------------
    real
        Real entity (OCEL or OC-DFG)
    normative
        Normative entity (OC-DFG)
    variant
        Variant of the algorithm to be used (default: Variants.GRAPH_COMPARISON)
    parameters
        Variant-specific parameters

    Returns
    -----------------
    conf_diagn_dict
        Dictionary with conformance diagnostics
    """
    return exec_utils.get_variant(variant).apply(real, normative, parameters)
