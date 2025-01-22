from pm4py.algo.discovery.ocel.otg.variants import classic
from enum import Enum
from pm4py.util import exec_utils
from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any, Tuple, Set


class Variants(Enum):
    CLASSIC = classic


def apply(ocel: OCEL, variant=Variants.CLASSIC, parameters: Optional[Dict[Any, Any]] = None) -> Tuple[Set[str], Dict[Tuple[str, str, str], int]]:
    """
    Discovers an OTG (object-type-graph) from the provided OCEL

    Parameters
    -----------------
    ocel
        OCEL
    variant
        Variant to be used (available: Variants.CLASSIC)
    parameters
        Variant-specific parameters

    Returns
    -----------------
    otg
        Object-type-graph (tuple; the first element is the set of object types, the second element is the OTG)
    """
    if parameters is None:
        parameters = {}

    return exec_utils.get_variant(variant).apply(ocel, parameters)
