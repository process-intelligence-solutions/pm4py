from pm4py.util import exec_utils
from typing import Optional, Dict, Any, Union
from enum import Enum
from pm4py.objects.ocel.obj import OCEL


class Parameters(Enum):
    THETA_ACT = "theta_act"
    THETA_FLOW = "theta_flow"
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    DELTA = "delta"


def apply(real: Union[OCEL, Dict[str, Any]], normative: Dict[str, Any], parameters: Optional[Dict[Any, Any]] = None) -> Dict[str, Any]:
    """
    Applies object-centric conformance checking between the given real object (object-centric event log or DFG)
    and a normative OC-DFG.

    Parameters
    -----------------
    real
        Real entity (OCEL or OC-DFG)
    normative
        Normative entity (OC-DFG)
    parameters
        Variant-specific parameters:
        - Parameters.THETA_ACT
        - Parameters.THETA_FLOW
        - Parameters.ALPHA
        - Parameters.BETA
        - Parameters.GAMMA
        - Parameters.DELTA

    Returns
    -----------------
    conf_diagn_dict
        Dictionary with conformance diagnostics
    """
    if parameters is None:
        parameters = {}

    theta_act = exec_utils.get_param_value(Parameters.THETA_ACT, parameters, 0)
    theta_flow = exec_utils.get_param_value(Parameters.THETA_FLOW, parameters, 0)
    alpha = exec_utils.get_param_value(Parameters.ALPHA, parameters, 1)
    beta = exec_utils.get_param_value(Parameters.BETA, parameters, 1)
    gamma = exec_utils.get_param_value(Parameters.GAMMA, parameters, 1)
    delta = exec_utils.get_param_value(Parameters.DELTA, parameters, 1)

    if isinstance(real, OCEL):
        import pm4py
        real = pm4py.discover_ocdfg(real)

    return compare_ocdfgs(real, normative, theta_act, theta_flow, alpha, beta, gamma, delta)


def compare_ocdfgs(ocdfg1, ocdfg2, theta_act=0, theta_flow=0, alpha=1, beta=1, gamma=1, delta=1):
    """
    Compare two Object-Centric Directly-Follows Graphs (OCDFGs) and perform conformance checking.

    Parameters:
    - ocdfg1: The first OCDFG to compare.
    - ocdfg2: The second OCDFG to compare.
    - theta_act: Threshold for activity measure difference.
    - theta_flow: Threshold for flow measure difference.
    - alpha, beta, gamma, delta: Weighting factors for fitness calculation.

    Returns:
    - A dictionary containing conformance checking results.
    """

    # Extract components from OCDFG1
    A1 = set(ocdfg1.get('activities', set()))
    edges1 = ocdfg1.get('edges', {})
    activities_indep1 = ocdfg1.get('activities_indep', {})

    # Extract components from OCDFG2
    A2 = set(ocdfg2.get('activities', set()))
    edges2 = ocdfg2.get('edges', {})
    activities_indep2 = ocdfg2.get('activities_indep', {})

    # Union of activities
    all_activities = A1.union(A2)

    # Activity Conformance
    A_missing = A2 - A1  # Activities in ocdfg2 but not in ocdfg1
    A_additional = A1 - A2  # Activities in ocdfg1 but not in ocdfg2

    # Flow (Edge) Conformance
    # 'event_couples' is a parent of the object types
    F1_set = set()
    event_couples1 = edges1.get('event_couples', {})
    for ot in event_couples1:
        flows1 = event_couples1[ot]
        F1_set.update(flows1.keys())

    F2_set = set()
    event_couples2 = edges2.get('event_couples', {})
    for ot in event_couples2:
        flows2 = event_couples2[ot]
        F2_set.update(flows2.keys())

    F_missing = F2_set - F1_set  # Flows in ocdfg2 but not in ocdfg1
    F_additional = F1_set - F2_set  # Flows in ocdfg1 but not in ocdfg2

    # Measure Conformance for Activities
    Delta_act = {}
    delta_act = {}
    events1 = activities_indep1.get('events', {})
    events2 = activities_indep2.get('events', {})
    for a in all_activities:
        # Measure in ocdfg1
        measure1 = len(events1.get(a, []))
        # Measure in ocdfg2
        measure2 = len(events2.get(a, []))
        diff = abs(measure2 - measure1)
        Delta_act[a] = diff
        delta_act[a] = 1 if diff > theta_act else 0

    # Measure Conformance for Flows
    Delta_flow = {}
    delta_flow = {}
    all_flows = F1_set.union(F2_set)
    for flow in all_flows:
        measure1 = 0
        # Sum over all object types in event_couples1
        for ot in event_couples1:
            flows1 = event_couples1[ot]
            measure1 += len(flows1.get(flow, []))
        measure2 = 0
        # Sum over all object types in event_couples2
        for ot in event_couples2:
            flows2 = event_couples2[ot]
            measure2 += len(flows2.get(flow, []))
        diff = abs(measure2 - measure1)
        Delta_flow[flow] = diff
        delta_flow[flow] = 1 if diff > theta_flow else 0

    # Fitness Calculation
    N = alpha * len(all_activities) + beta * len(all_flows) + \
        gamma * len(all_activities) + delta * len(all_flows)

    # Calculate numerator components
    fitness_numerator = (alpha * len(A_missing) + beta * len(F_missing) +
                         gamma * sum(delta_act.values()) + delta * sum(delta_flow.values()))

    # To avoid division by zero
    if N == 0:
        fitness = 1.0
    else:
        fitness = 1 - (fitness_numerator / N)
        fitness = max(0.0, min(fitness, 1.0))  # Ensure fitness is within [0,1]

    # Prepare the result dictionary
    result = {
        'missing_activities': A_missing,
        'additional_activities': A_additional,
        'missing_flows': F_missing,
        'additional_flows': F_additional,
        'activity_measure_differences': Delta_act,
        'non_conforming_activities_in_measure': {a for a in Delta_act if Delta_act[a] > theta_act},
        'flow_measure_differences': Delta_flow,
        'non_conforming_flows_in_measure': {f for f in Delta_flow if Delta_flow[f] > theta_flow},
        'fitness': fitness
    }

    return result

