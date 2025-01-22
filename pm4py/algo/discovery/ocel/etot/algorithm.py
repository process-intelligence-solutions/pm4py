from collections import defaultdict
from typing import Optional, Dict, Any, Tuple, Set
from pm4py.objects.ocel.obj import OCEL
from enum import Enum
from pm4py.util import exec_utils
from pm4py.algo.discovery.ocel.etot.variants import classic


class Variants(Enum):
    CLASSIC = classic


def apply(ocel: OCEL, variant=Variants.CLASSIC, parameters: Optional[Dict[Any, Any]] = None) -> Tuple[Set[str], Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], int]]:
    """
    Discovers the ET-OT graph from an OCEL

    Parameters
    ---------------
    ocel
        Object-centric event log
    variant
        Variant of the algorithm to be used (available: Variants.CLASSIC)
    parameters
        Variant-specific parameters

    Returns
    ----------------
    activities
        Set of activities
    object_types
        Set of object types
    edges
        Set of edges
    edges_frequency
        Dictionary associating to each edge a frequency
    """
    return exec_utils.get_variant(variant).apply(ocel, parameters)
