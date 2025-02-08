from collections import defaultdict
from typing import Optional, Dict, Any, Tuple, Set
from pm4py.objects.ocel.obj import OCEL


def apply(ocel: OCEL, parameters: Optional[Dict[Any, Any]] = None) -> Tuple[Set[str], Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], int]]:
    """
    Discovers the ET-OT graph from an OCEL

    Parameters
    ---------------
    ocel
        Object-centric event log
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
    if parameters is None:
        parameters = {}

    A = set()
    OT = set()
    R = set()
    w = defaultdict(int)

    # Iterate over the relations to build the ETOT Graph
    for index, row in ocel.relations.iterrows():
        a = row['ocel:activity']
        ot = row['ocel:type']
        A.add(a)
        OT.add(ot)
        R.add((a, ot))
        w[(a, ot)] += 1

    return A, OT, R, w
