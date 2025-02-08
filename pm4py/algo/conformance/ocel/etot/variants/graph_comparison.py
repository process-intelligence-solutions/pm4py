from enum import Enum
from pm4py.util import exec_utils
from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any, Union, Tuple, Set


class Parameters(Enum):
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    THETA_REL = "theta_real"


def apply(real: Union[OCEL, Tuple[Set[str], Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], int]]], normative: Tuple[Set[str], Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], int]], parameters: Optional[Dict[Any, Any]] = None) -> Dict[str, Any]:
    """
    Applies ET-OT-based conformance checking between a 'real' object (either an OCEL or an ET-OT graph),
    and a normative ET-OT graph.

    Parameters
    -------------------
    real
        Real object (OCEL, or ET-OT graph)
    normative
        Normative object (ET-OT graph)
    parameters
        Variant-specific parameters, including:
        - Parameters.ALPHA
        - Parameters.BETA
        - Parameters.GAMMA
        - Parameters.THETA_REAL

    Returns
    ------------------
    diagn_dict
        Diagnostics dictionary
    """
    if parameters is None:
        parameters = {}

    alpha = exec_utils.get_param_value(Parameters.ALPHA, parameters, 1)
    beta = exec_utils.get_param_value(Parameters.BETA, parameters, 1)
    gamma = exec_utils.get_param_value(Parameters.GAMMA, parameters, 1)
    theta_rel = exec_utils.get_param_value(Parameters.THETA_REL, parameters, 0.1)

    if isinstance(real, OCEL):
        from pm4py.algo.discovery.ocel.etot import algorithm as etot_discovery
        real = etot_discovery.apply(real, parameters=parameters)

    return compute_conformance(real, normative, alpha=alpha, beta=beta, gamma=gamma, theta_rel=theta_rel)


def compute_conformance(G_L, G_M, alpha=1, beta=1, gamma=1, theta_rel=0.1):
    A_L, OT_L, R_L, w_L = G_L
    A_M, OT_M, R_M, w_M = G_M

    # Node Conformance
    A_missing = A_M - A_L
    A_additional = A_L - A_M
    OT_missing = OT_M - OT_L
    OT_additional = OT_L - OT_M

    # Edge Conformance
    R_missing = R_M - R_L
    R_additional = R_L - R_M

    # Edge Frequency Conformance
    delta_rel_total = 0
    delta_rel = {}
    for r in R_M.intersection(R_L):
        w_M_r = w_M[r]
        w_L_r = w_L[r]
        delta = abs(w_L_r - w_M_r) / w_M_r
        delta_rel[r] = delta
        if delta > theta_rel:
            delta_rel_total += 1

    # Normalization constant
    N = alpha * (len(A_M) + len(OT_M)) + beta * len(R_M) + gamma * len(R_M)

    # Compute numerator
    numerator = alpha * (len(A_missing) + len(OT_missing)) + beta * len(R_missing) + gamma * delta_rel_total

    # Fitness value
    phi = 1 - (numerator / N)

    # Details dictionary
    details = {
        'A_missing': A_missing,
        'A_additional': A_additional,
        'OT_missing': OT_missing,
        'OT_additional': OT_additional,
        'R_missing': R_missing,
        'R_additional': R_additional,
        'delta_rel': delta_rel
    }

    return {"fitness": phi, "details": details}
