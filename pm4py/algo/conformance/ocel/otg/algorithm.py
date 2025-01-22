from enum import Enum
from pm4py.util import exec_utils
from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any, Union, Tuple, Set
from pm4py.algo.conformance.ocel.otg.variants import graph_comparison


class Variants(Enum):
    GRAPH_COMPARISON = graph_comparison


def apply(real: Union[OCEL, Tuple[Set[str], Dict[Tuple[str, str, str], int]]], normative: Tuple[Set[str], Dict[Tuple[str, str, str], int]], variant=Variants.GRAPH_COMPARISON, parameters: Optional[Dict[Any, Any]] = None) -> Dict[str, Any]:
    """
    Applies OTG-based conformance checking between a 'real' object (OCEL or OTG) and a 'normative' OTG.

    Parameters
    -----------------
    real
        Real object (OCEL or OTG)
    normative
        Normative OTG
    variant
        Variant of the algorithm to be used (default: Variants.GRAPH_COMPARISON)
    parameters
        Variant-specific parameters

    Returns
    -----------------
    conf_diagn
        Diagnostics dictionary
    """
    return exec_utils.get_variant(variant).apply(real, normative, parameters)
