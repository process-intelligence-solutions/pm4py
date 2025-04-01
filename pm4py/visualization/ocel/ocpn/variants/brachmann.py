import uuid
import numpy as np
import math
import copy
from typing import Optional, Dict, Any, List, Tuple, Set
from graphviz import Digraph
from enum import Enum
from pm4py.util import exec_utils, constants, vis_utils
from pm4py.util.lp import solver as lp_solver
from pm4py.objects.petri_net.obj import PetriNet  # For type hinting if needed

# --- Constants matching TypeScript OCPNLayout ---
PLACE_TYPE = "place"
TRANSITION_TYPE = "transition"
DUMMY_TYPE = "dummy"


# --- Helper Functions ---

def ot_to_color(ot: str) -> str:
    """Generates a deterministic hex color based on the object type string."""
    # Simple hash-based color generation (consistent with the original pm4py vis)
    ot_hash = int(hash(ot))
    num = []
    while len(num) < 6:
        num.insert(0, ot_hash % 16)
        ot_hash = ot_hash // 16
    ret = "#" + "".join([vis_utils.get_corr_hex(x) for x in num])
    return ret


def generate_dummy_id() -> str:
    """Generates a unique ID for a dummy node."""
    return "dummy_" + str(uuid.uuid4())


def generate_arc_id(source_id: str, target_id: str) -> str:
    """Generates a unique ID for an arc."""
    return f"arc_{source_id}_{target_id}_{uuid.uuid4()}"


def get_neighbors(vertex_id: str, layout_data: Dict, direction: str) -> List[str]:
    """Gets upper ('up') or lower ('down') neighbors of a vertex."""
    neighbors = set()
    arcs = layout_data.get("arcs", {})
    if direction == 'up':
        # Find arcs where the current vertex is the target
        for arc_id, arc_data in arcs.items():
            if arc_data['target'] == vertex_id:
                neighbors.add(arc_data['source'])
    elif direction == 'down':
        # Find arcs where the current vertex is the source
        for arc_id, arc_data in arcs.items():
            if arc_data['source'] == vertex_id:
                neighbors.add(arc_data['target'])
    return list(neighbors)


def get_arcs_between(u: str, v: str, layout_data: Dict) -> List[Dict]:
    """Gets arcs connecting vertex u and vertex v directly."""
    connecting_arcs = []
    for arc_id, arc_data in layout_data.get("arcs", {}).items():
        if (arc_data['source'] == u and arc_data['target'] == v) or \
                (arc_data['source'] == v and arc_data['target'] == u):
            connecting_arcs.append(arc_data)
    return connecting_arcs


def get_arcs_between_layers(layer_idx1: int, layer_idx2: int, layout_data: Dict) -> List[Dict]:
    """Gets all arcs connecting nodes between two specific layers."""
    arcs_between = []
    vertices = layout_data.get("vertices", {})
    layering = layout_data.get("layering", [])

    if layer_idx1 < 0 or layer_idx1 >= len(layering) or \
            layer_idx2 < 0 or layer_idx2 >= len(layering):
        return []

    layer1_nodes = set(layering[layer_idx1])
    layer2_nodes = set(layering[layer_idx2])

    for arc_id, arc_data in layout_data.get("arcs", {}).items():
        src = arc_data['source']
        tgt = arc_data['target']
        if (src in layer1_nodes and tgt in layer2_nodes) or \
                (src in layer2_nodes and tgt in layer1_nodes):
            # Ensure the arc direction aligns with layer indices for simplicity later
            # This assumes layer_idx2 > layer_idx1 typically represents downward flow
            # Let's return based on the layer index order passed in
            if src in layer1_nodes and tgt in layer2_nodes:
                arcs_between.append(arc_data)
            elif src in layer2_nodes and tgt in layer1_nodes:
                # Add but maybe flag directionality if needed by caller
                arcs_between.append(arc_data)

    return arcs_between


def is_incident_to_inner_segment(ocpn_layout: Dict, vertex_id: str) -> bool:
    """Checks if a vertex is a dummy node connected to another dummy node above it."""
    vertices = ocpn_layout.get("vertices", {})
    v = vertices.get(vertex_id)
    if v and v.get("type") == DUMMY_TYPE:
        upper_neighbor_id = v.get("upper_neighbor")  # Assuming upper_neighbor stores the ID
        if upper_neighbor_id:
            upper_neighbor = vertices.get(upper_neighbor_id)
            if upper_neighbor and upper_neighbor.get("type") == DUMMY_TYPE:
                return True
    return False


# --- Core Sugiyama Steps ---

def _build_initial_layout(ocpn: Dict[str, Any], parameters: Dict) -> Dict:
    """Creates the initial layout structure before applying Sugiyama steps."""
    layout_data = {
        "vertices": {},
        "arcs": {},
        "original_arcs": {},  # Store original connections before dummies
        "object_types": list(ocpn["object_types"]),
        "config": parameters  # Store config for easy access
    }
    vertex_map = {}  # Map (type, original_node) -> layout_id

    # 1. Create vertices for all places and transitions in the individual nets
    for ot, (net, im, fm) in ocpn.get("petri_nets", {}).items():
        # Create places
        for place in net.places:
            place_id = str(place)  # Use inherent ID if available, else generate
            if (PLACE_TYPE, place_id) not in vertex_map:
                layout_id = f"place_{ot}_{place.name}_{uuid.uuid4()}"  # Ensure uniqueness
                vertex_map[(PLACE_TYPE, place_id)] = layout_id
                is_source = place in im
                is_sink = place in fm
                layout_data["vertices"][layout_id] = {
                    "id": layout_id,
                    "original_id": place_id,
                    "name": place.name or f"p_{ot}",
                    "label": place.name or f"p_{ot}",  # Or maybe object type?
                    "objectType": ot,
                    "type": PLACE_TYPE,
                    "layer": -1,
                    "pos": -1,
                    "x": None,
                    "y": None,
                    "is_source": is_source,
                    "is_sink": is_sink,
                    # For positioning
                    "root": layout_id,
                    "align": layout_id,
                    "sink": layout_id,
                    "shift": float('inf'),
                    "upper_neighbor": None,  # For dummy tracking
                    "lower_neighbor": None,  # For dummy tracking
                }

        # Create transitions (link to activities if possible)
        for trans in net.transitions:
            trans_id = str(trans)  # Use inherent ID
            layout_id = None
            if trans.label:  # Visible transition corresponds to an activity
                # Check if an activity node already exists
                if (TRANSITION_TYPE, trans.label) in vertex_map:
                    layout_id = vertex_map[(TRANSITION_TYPE, trans.label)]
                    # Add this object type to the transition's knowledge
                    layout_data["vertices"][layout_id].setdefault("adjacentObjectTypes", set()).add(ot)
                else:
                    layout_id = f"trans_{trans.label}_{uuid.uuid4()}"
                    vertex_map[(TRANSITION_TYPE, trans.label)] = layout_id
                    layout_data["vertices"][layout_id] = {
                        "id": layout_id,
                        "original_id": trans_id,  # Keep track of original PNet transition ID too? Maybe needed?
                        "name": trans.label,
                        "label": trans.label,
                        "objectType": None,  # Transitions don't belong to one OT
                        "adjacentObjectTypes": {ot},  # OTs involved
                        "type": TRANSITION_TYPE,
                        "silent": False,
                        "layer": -1,
                        "pos": -1,
                        "x": None,
                        "y": None,
                        # For positioning
                        "root": layout_id,
                        "align": layout_id,
                        "sink": layout_id,
                        "shift": float('inf'),
                        "upper_neighbor": None,
                        "lower_neighbor": None,
                    }
            else:  # Silent transition
                layout_id = f"silent_{ot}_{trans.name}_{uuid.uuid4()}"
                vertex_map[(TRANSITION_TYPE, trans_id)] = layout_id  # Map original silent trans ID
                layout_data["vertices"][layout_id] = {
                    "id": layout_id,
                    "original_id": trans_id,
                    "name": trans.name or "silent",
                    "label": None,  # Or 'τ' ?
                    "objectType": ot,  # Silent transitions often tied to one net context
                    "adjacentObjectTypes": {ot},
                    "type": TRANSITION_TYPE,
                    "silent": True,
                    "layer": -1,
                    "pos": -1,
                    "x": None,
                    "y": None,
                    # For positioning
                    "root": layout_id,
                    "align": layout_id,
                    "sink": layout_id,
                    "shift": float('inf'),
                    "upper_neighbor": None,
                    "lower_neighbor": None,
                }

        # 2. Create arcs based on the Petri net structure
        for arc in net.arcs:
            source_node = arc.source
            target_node = arc.target
            source_id_orig = str(source_node)
            target_id_orig = str(target_node)

            source_type = PLACE_TYPE if isinstance(source_node, PetriNet.Place) else TRANSITION_TYPE
            target_type = PLACE_TYPE if isinstance(target_node, PetriNet.Place) else TRANSITION_TYPE

            # Need to map the Petri Net element to the correct layout ID
            # Handle visible transitions potentially shared across OTs
            if source_type == TRANSITION_TYPE and source_node.label:
                source_layout_id = vertex_map.get((source_type, source_node.label))
            else:
                source_layout_id = vertex_map.get((source_type, source_id_orig))

            if target_type == TRANSITION_TYPE and target_node.label:
                target_layout_id = vertex_map.get((target_type, target_node.label))
            else:
                target_layout_id = vertex_map.get((target_type, target_id_orig))

            if source_layout_id and target_layout_id:
                # Check if an arc (in either direction) already exists between these layout nodes
                # This handles cases where the same high-level connection appears in multiple OTs
                arc_exists = False
                existing_arc_id = None
                for arc_id_check, arc_data_check in layout_data["arcs"].items():
                    if (arc_data_check['source'] == source_layout_id and arc_data_check[
                        'target'] == target_layout_id) or \
                            (arc_data_check['source'] == target_layout_id and arc_data_check[
                                'target'] == source_layout_id):
                        arc_exists = True
                        existing_arc_id = arc_id_check
                        break

                if not arc_exists:
                    arc_id = generate_arc_id(source_layout_id, target_layout_id)
                    # Determine if it's a variable arc (double arc) - simplified check
                    is_variable = False
                    if ot in ocpn.get("double_arcs_on_activity", {}):
                        act_label = None
                        if source_type == TRANSITION_TYPE and source_node.label:
                            act_label = source_node.label
                        elif target_type == TRANSITION_TYPE and target_node.label:
                            act_label = target_node.label
                        if act_label and ocpn["double_arcs_on_activity"][ot].get(act_label, False):
                            is_variable = True  # Simplified: if *activity* has double arc for this OT

                    arc_data = {
                        "id": arc_id,
                        "source": source_layout_id,
                        "target": target_layout_id,
                        "objectType": ot,  # Associate arc with this OT's net initially
                        "original": True,  # Mark as an original arc from the PN
                        "reversed": False,  # For cycle breaking
                        "dummy_nodes": [],  # Path of dummies
                        "minLayer": -1,  # For dummy insertion
                        "maxLayer": -1,  # For dummy insertion
                        "type1": False,  # For positioning conflicts
                        "weight": arc.weight if hasattr(arc, 'weight') else 1,  # Use arc weight if available
                        "variable": is_variable,  # Mark variable arcs (e.g., double arcs in OCPN paper)
                    }
                    layout_data["arcs"][arc_id] = arc_data
                    layout_data["original_arcs"][arc_id] = copy.deepcopy(arc_data)  # Keep pristine copy
                else:
                    # Arc already exists, maybe update weight or mark as variable if needed?
                    # For now, just ensure the involved object types are tracked on the vertices
                    if source_type == TRANSITION_TYPE:
                        layout_data["vertices"][source_layout_id].setdefault("adjacentObjectTypes", set()).add(ot)
                    if target_type == TRANSITION_TYPE:
                        layout_data["vertices"][target_layout_id].setdefault("adjacentObjectTypes", set()).add(ot)
                    pass  # Don't add duplicate arc structure

            else:
                print(f"Warning: Could not find layout nodes for arc {source_id_orig} -> {target_id_orig} in OT {ot}")

    # Add global activities not represented in any Petri net transition?
    # This layout focuses on the discovered nets. Add activities might be needed if some are unconnected.
    all_activity_nodes = {v['name'] for v in layout_data['vertices'].values() if
                          v['type'] == TRANSITION_TYPE and not v['silent']}
    for act in ocpn.get("activities", set()):
        if act not in all_activity_nodes:
            # This activity wasn't part of any discovered Petri net transition
            layout_id = f"trans_{act}_unconnected_{uuid.uuid4()}"
            layout_data["vertices"][layout_id] = {
                "id": layout_id, "original_id": None, "name": act, "label": act,
                "objectType": None, "adjacentObjectTypes": set(), "type": TRANSITION_TYPE,
                "silent": False, "layer": -1, "pos": -1, "x": None, "y": None,
                "root": layout_id, "align": layout_id, "sink": layout_id, "shift": float('inf'),
                "upper_neighbor": None, "lower_neighbor": None,
            }
            print(f"Warning: Activity '{act}' not found in Petri net transitions, adding as unconnected node.")

    return layout_data


# --- Graph representation for algorithms ---
class OCPNGraph:
    """Helper class to represent the graph for cycle breaking and layer assignment."""

    def __init__(self, layout_data: Dict):
        self.nodes = list(layout_data["vertices"].keys())
        self.arcs_data = layout_data["arcs"]  # Reference to main arc data
        self.adj = {n: [] for n in self.nodes}
        self.rev_adj = {n: [] for n in self.nodes}
        self.arc_list = []  # List of {'source': id, 'target': id, 'id': arc_id}

        for arc_id, arc in self.arcs_data.items():
            src, tgt = arc['source'], arc['target']
            # Skip self-loops if any exist for layout purposes
            if src == tgt:
                continue
            if src in self.nodes and tgt in self.nodes:
                self.adj[src].append(tgt)
                self.rev_adj[tgt].append(src)
                self.arc_list.append({'source': src, 'target': tgt, 'id': arc_id})

    def get_out_degree(self, node: str) -> int:
        return len(self.adj.get(node, []))

    def get_in_degree(self, node: str) -> int:
        return len(self.rev_adj.get(node, []))

    def remove_node(self, node: str):
        if node not in self.nodes:
            return

        # Remove from adjacency lists
        successors = self.adj.pop(node, [])
        predecessors = self.rev_adj.pop(node, [])

        for succ in successors:
            if succ in self.rev_adj:
                self.rev_adj[succ].remove(node)

        for pred in predecessors:
            if pred in self.adj:
                self.adj[pred].remove(node)

        # Remove from node list
        self.nodes.remove(node)

        # Remove related arcs from arc_list (inefficient, but simple for now)
        self.arc_list = [a for a in self.arc_list if a['source'] != node and a['target'] != node]

    def remove_nodes(self, nodes_to_remove: List[str]):
        # It's often more efficient to rebuild adjacencies if removing many nodes
        # But for simplicity, we call remove_node iteratively
        for node in nodes_to_remove:
            self.remove_node(node)

    def get_sink(self) -> Optional[str]:
        for node in self.nodes:
            if self.get_out_degree(node) == 0:
                return node
        return None

    def get_source(self) -> Optional[str]:
        for node in self.nodes:
            if self.get_in_degree(node) == 0:
                return node
        return None

    def get_max_out_degree_node(self) -> Optional[str]:
        max_degree = -1
        max_node = None
        for node in self.nodes:
            degree = self.get_out_degree(node) - self.get_in_degree(node)
            if degree > max_degree:
                max_degree = degree
                max_node = node
        return max_node


def _modified_greedy_fas(graph: OCPNGraph, sources: List[str], sinks: List[str]) -> List[str]:
    """Computes Feedback Arc Set using greedy algorithm considering sources/sinks."""
    s1 = list(sources)  # Nodes forced to the beginning
    s2 = list(sinks)  # Nodes forced to the end

    # Filter sources/sinks that might not be in the graph (e.g., unconnected activities)
    s1 = [n for n in s1 if n in graph.nodes]
    s2 = [n for n in s2 if n in graph.nodes]

    # Pre-sort sources/sinks based on degree difference (high out-degree first for sources)
    if s1:
        s1.sort(key=lambda n: graph.get_out_degree(n) - graph.get_in_degree(n), reverse=True)
        graph.remove_nodes(s1)  # Temporarily remove from graph

    if s2:
        # High in-degree first for sinks (or low (out-in) diff)
        s2.sort(key=lambda n: graph.get_out_degree(n) - graph.get_in_degree(n), reverse=True)  # Same sorting as TS
        graph.remove_nodes(s2)  # Temporarily remove

    # Main greedy loop
    temp_s1 = []
    temp_s2 = []
    while graph.nodes:
        # Remove all current sinks
        sink = graph.get_sink()
        while sink:
            temp_s2.insert(0, sink)  # Add to front of temp_s2
            graph.remove_node(sink)
            sink = graph.get_sink()

        # Remove all current sources
        source = graph.get_source()
        while source:
            temp_s1.append(source)  # Add to end of temp_s1
            graph.remove_node(source)
            source = graph.get_source()

        # If nodes remain, pick highest (out-degree - in-degree)
        if graph.nodes:
            node = graph.get_max_out_degree_node()
            if node:  # Should always find one if graph.nodes is not empty
                temp_s1.append(node)
                graph.remove_node(node)
            else:
                # Should not happen if graph.nodes is non-empty and graph was connected
                print("Warning: No node found in FAS loop, graph might be empty or disconnected unexpectedly.")
                break

    # Combine results: sources + temp_s1 + temp_s2 + sinks
    return s1 + temp_s1 + temp_s2 + s2


def _reverse_cycles(layout_data: Dict, config: Dict) -> int:
    """Reverses arcs based on FAS to break cycles."""
    print("Step 1: Cycle Breaking...")
    graph = OCPNGraph(layout_data)

    # Identify potential sources/sinks from layout data (places marked is_source/is_sink)
    # Note: The TS config allows arbitrary node IDs. Here we derive from Petri net markings.
    potential_sources = [vid for vid, vdata in layout_data["vertices"].items() if vdata.get("is_source")]
    potential_sinks = [vid for vid, vdata in layout_data["vertices"].items() if vdata.get("is_sink")]
    # Allow user override via parameters if needed
    sources = config.get("sources", potential_sources)
    sinks = config.get("sinks", potential_sinks)

    # Ensure sources/sinks provided in config actually exist
    sources = [s for s in sources if s in layout_data["vertices"]]
    sinks = [s for s in sinks if s in layout_data["vertices"]]

    fas_order = _modified_greedy_fas(graph, sources, sinks)
    fas_indices = {node_id: index for index, node_id in enumerate(fas_order)}

    reversed_count = 0
    for arc_id, arc in layout_data["arcs"].items():
        src = arc['source']
        tgt = arc['target']

        # Check if src and tgt are in the FAS order (they might have been removed if sources/sinks)
        src_index = fas_indices.get(src)
        tgt_index = fas_indices.get(tgt)

        if src_index is not None and tgt_index is not None:
            if src_index > tgt_index:
                # physically swap them
                arc['source'], arc['target'] = arc['target'], arc['source']
                # store the original direction so we can revert later
                arc['original_source'] = tgt
                arc['original_target'] = src
                # no need for arc['reversed'] at all
                reversed_count += 1
            else:
                arc['reversed'] = False
        else:
            # Arc involves a pre-defined source/sink, assume original direction is fine
            # Or handle edge cases if needed
            arc['reversed'] = False

    print(f"  Reversed {reversed_count} arcs.")
    return reversed_count


def _assign_layers(layout_data: Dict) -> bool:
    """Assigns layers to vertices using LP to minimize edge length."""
    print("Step 2: Layer Assignment (using LP)...")
    vertices = layout_data["vertices"]
    arcs = layout_data["arcs"]
    node_list = list(vertices.keys())
    node_to_index = {node_id: i for i, node_id in enumerate(node_list)}
    num_vars = len(node_list)

    # Objective: Minimize sum(weight * (layer[target] - layer[source]))
    # c vector (cost for each variable/node's layer)
    c = np.zeros(num_vars)
    active_arcs = []  # Arcs between nodes currently in the graph

    for arc_id, arc in arcs.items():
        src_orig, tgt_orig = arc['source'], arc['target']
        weight = arc.get('weight', 1)  # Consider arc weights

        # Use the 'reversed' flag to determine the direction for layering
        if arc['reversed']:
            src, tgt = tgt_orig, src_orig
        else:
            src, tgt = src_orig, tgt_orig

        if src in node_to_index and tgt in node_to_index:
            src_idx = node_to_index[src]
            tgt_idx = node_to_index[tgt]
            c[tgt_idx] += weight
            c[src_idx] -= weight
            active_arcs.append({'source': src, 'target': tgt, 'id': arc_id})

    # Constraints: layer[target] - layer[source] >= 1 (for non-reversed arcs)
    # Represented as: -layer[source] + layer[target] >= 1
    num_constraints = len(active_arcs)
    # Aub matrix for inequalities Aub * x <= bub
    # We have A * x >= b, so -A * x <= -b
    Aub = np.zeros((num_constraints, num_vars))
    bub = np.full(num_constraints, -1.0)  # Lower bound is 1, so upper bound for <= form is -1

    for i, arc in enumerate(active_arcs):
        src_idx = node_to_index[arc['source']]
        tgt_idx = node_to_index[arc['target']]
        Aub[i, src_idx] = 1.0  # Coefficient for -layer[source] becomes +1 in -A
        Aub[i, tgt_idx] = -1.0  # Coefficient for +layer[target] becomes -1 in -A

    # Constraints: layer[node] >= 0 (Implicit in some solvers, but can add)
    # -layer[node] <= 0
    num_positivity_constraints = num_vars
    Aub_pos = np.zeros((num_positivity_constraints, num_vars))
    bub_pos = np.zeros(num_positivity_constraints)
    for i in range(num_vars):
        Aub_pos[i, i] = -1.0  # -layer[i] <= 0

    # Combine constraints
    Aub_combined = np.vstack((Aub, Aub_pos))
    bub_combined = np.concatenate((bub, bub_pos))

    # Equality constraints (Aeq * x = beq) - None in this basic formulation
    Aeq = None  # np.zeros((0, num_vars)) # Or None
    beq = None  # np.zeros(0) # Or None

    # --- Solve LP using pm4py utility ---
    try:
        # Ensure integer solution - Requires a solver that supports MILP (e.g., Pulp, CBC, GLPK)
        # Check pm4py's default or specify one that supports integers if needed.
        # If the default ('scipy') doesn't support integers, this might yield float layers.
        # We can round them, but a true MILP solver is better.
        # Let's try first and see. SciPy's HiGHS might handle MILP.
        # TODO: Add parameter to specify integer variables if solver supports it

        print(f"  Setting up LP with {num_vars} variables and {Aub_combined.shape[0]} constraints.")
        sol = lp_solver.apply(c, Aub_combined, bub_combined, Aeq, beq,
                              parameters={"verbose": False})  # Add verbose=True for debugging

        if sol is None:
            print("  LP Solver did not return a solution.")
            # Fallback: Simple topological sort based layering? (Less optimal)
            # Or error out
            return False

        points = lp_solver.get_points_from_sol(sol)

        if points is None or len(points) != num_vars:
            print("  LP Solver failed to extract points or returned incorrect number.")
            # print("Solver status:", sol...) # Need specific solver's status info
            return False

        # Assign layers (rounding if necessary)
        max_layer = 0
        layering_dict = {}
        for i, node_id in enumerate(node_list):
            # Round to nearest integer. Add small epsilon for robustness?
            layer = int(round(points[i]))
            vertices[node_id]['layer'] = layer
            if layer not in layering_dict:
                layering_dict[layer] = []
            layering_dict[layer].append(node_id)
            max_layer = max(max_layer, layer)

        # Convert dictionary to sorted list of lists
        layout_data['layering'] = []
        for i in range(max_layer + 1):
            layout_data['layering'].append(layering_dict.get(i, []))

        print(f"  Assigned nodes to {max_layer + 1} layers.")
        return True

    except Exception as e:
        print(f"  Error during LP solving or layer assignment: {e}")
        import traceback
        traceback.print_exc()
        return False


def _insert_dummy_vertices(layout_data: Dict):
    """Inserts dummy nodes for arcs spanning multiple layers."""
    print("Step 3: Dummy Vertex Insertion...")
    vertices = layout_data["vertices"]
    arcs = layout_data["arcs"]
    layering = layout_data["layering"]
    arcs_to_add = {}
    arcs_to_remove = []
    dummy_count = 0

    # Iterate over a copy of arc IDs as we modify the arcs dictionary
    original_arc_ids = list(arcs.keys())

    for arc_id in original_arc_ids:
        arc = arcs[arc_id]
        src_id_orig, tgt_id_orig = arc['source'], arc['target']

        # Use the 'reversed' flag to determine logical source/target for layering
        if arc['reversed']:
            src_id, tgt_id = tgt_id_orig, src_id_orig
        else:
            src_id, tgt_id = src_id_orig, tgt_id_orig

        if src_id not in vertices or tgt_id not in vertices:
            print(f"Warning: Skipping dummy insertion for arc {arc_id} - source or target not found.")
            continue

        src_node = vertices[src_id]
        tgt_node = vertices[tgt_id]

        src_layer = src_node.get('layer', -1)
        tgt_layer = tgt_node.get('layer', -1)

        if src_layer == -1 or tgt_layer == -1:
            print(f"Warning: Skipping dummy insertion for arc {arc_id} ({src_id} -> {tgt_id}) - layers not assigned.")
            continue

        arc['minLayer'] = min(src_layer, tgt_layer)  # Store original layer span
        arc['maxLayer'] = max(src_layer, tgt_layer)

        slack = tgt_layer - src_layer  # Based on non-reversed direction

        if slack > 1:
            # Remove original arc, will be replaced by segments
            arcs_to_remove.append(arc_id)
            dummies_in_path = []

            # Determine object type for dummies (use place's OT if exists)
            ot = arc.get("objectType")  # Initial guess
            if vertices[src_id_orig]["type"] == PLACE_TYPE:
                ot = vertices[src_id_orig]["objectType"]
            elif vertices[tgt_id_orig]["type"] == PLACE_TYPE:
                ot = vertices[tgt_id_orig]["objectType"]

            # Find rough horizontal position for inserting dummies
            src_pos = -1
            tgt_pos = -1
            if src_layer < len(layering) and src_id in layering[src_layer]:
                src_pos = layering[src_layer].index(src_id)
            if tgt_layer < len(layering) and tgt_id in layering[tgt_layer]:
                tgt_pos = layering[tgt_layer].index(tgt_id)

            median_pos = len(layering[src_layer + 1]) // 2  # Default if positions unknown
            if src_pos != -1 and tgt_pos != -1:
                # Simple median estimate based on original nodes' positions
                # More sophisticated placement could be done in vertex ordering/positioning
                median_pos = (src_pos + tgt_pos) // 2

            last_node_id = src_id  # Start from the source
            for i in range(1, slack):
                dummy_layer_idx = src_layer + i
                dummy_id = generate_dummy_id()
                dummy_count += 1
                dummies_in_path.append(dummy_id)

                dummy_node = {
                    "id": dummy_id,
                    "original_id": None,
                    "name": f"dummy_{dummy_count}",
                    "label": None,
                    "objectType": ot,  # Inherit OT for coloring/grouping
                    "type": DUMMY_TYPE,
                    "layer": dummy_layer_idx,
                    "pos": -1,  # Will be set by ordering
                    "x": None,
                    "y": None,
                    "dummy_of_arc": arc_id,  # Link back to the original arc ID
                    "root": dummy_id,  # Initialize positioning fields
                    "align": dummy_id,
                    "sink": dummy_id,
                    "shift": float('inf'),
                    "upper_neighbor": last_node_id,  # Track connectivity
                    "lower_neighbor": None,  # Will be set next iteration or by target
                }
                vertices[dummy_id] = dummy_node

                # Update previous dummy's lower neighbor
                if i > 1:
                    vertices[dummies_in_path[-2]]["lower_neighbor"] = dummy_id

                # Insert dummy into the layering structure (approximate position)
                if dummy_layer_idx < len(layering):
                    insert_pos = min(median_pos, len(layering[dummy_layer_idx]))
                    layering[dummy_layer_idx].insert(insert_pos, dummy_id)
                else:
                    # Should not happen if layers are contiguous
                    print(f"Warning: Dummy layer index {dummy_layer_idx} out of bounds.")
                    layering.append([dummy_id])  # Append as new layer?

                # Create arc segment: last_node -> dummy
                segment_arc_id = generate_arc_id(last_node_id, dummy_id)
                # New arcs inherit properties from the original arc they replace
                arcs_to_add[segment_arc_id] = {
                    "id": segment_arc_id,
                    "source": last_node_id,  # Actual source/target for segment
                    "target": dummy_id,
                    "objectType": ot,
                    "original": False,  # Not an original PN arc
                    "reversed": False,  # Segments follow layer order
                    "dummy_nodes": [],
                    "minLayer": dummy_layer_idx - 1,
                    "maxLayer": dummy_layer_idx,
                    "type1": False,
                    "weight": arc.get('weight', 1),  # Inherit weight
                    "variable": arc.get('variable', False),  # Inherit variability
                    "original_arc_id": arc_id  # Link back
                }

                last_node_id = dummy_id  # Move to the new dummy

            # Final segment: last_dummy -> target
            segment_arc_id = generate_arc_id(last_node_id, tgt_id)
            arcs_to_add[segment_arc_id] = {
                "id": segment_arc_id,
                "source": last_node_id,
                "target": tgt_id,
                "objectType": ot,
                "original": False,
                "reversed": False,
                "dummy_nodes": [],
                "minLayer": tgt_layer - 1,
                "maxLayer": tgt_layer,
                "type1": False,
                "weight": arc.get('weight', 1),
                "variable": arc.get('variable', False),
                "original_arc_id": arc_id
            }
            # Set lower neighbor for the last dummy
            vertices[last_node_id]["lower_neighbor"] = tgt_id

            # Store the path of dummies on the *original* arc data (useful later?)
            # Find the original arc in the pristine copy
            if arc_id in layout_data["original_arcs"]:
                layout_data["original_arcs"][arc_id]["dummy_nodes"] = dummies_in_path

            # Also add dummy path info somewhere accessible for drawing? Maybe not needed if segments are drawn.
            # Let's add it to the removed arc's data just in case
            arcs[arc_id]['dummy_nodes'] = dummies_in_path

    # Apply changes
    for arc_id in arcs_to_remove:
        del arcs[arc_id]
    arcs.update(arcs_to_add)

    print(f"  Inserted {dummy_count} dummy vertices.")


# --- Vertex Ordering (Barycenter Heuristic) ---

def _compute_barycenter(ocpn_layout: Dict, vertex_id: str, layer_idx: int, fixed_layer_idx: int, config: Dict) -> float:
    """Computes the barycenter value for a vertex based on neighbors in the fixed layer."""
    vertices = ocpn_layout["vertices"]
    layering = ocpn_layout["layering"]
    vertex = vertices[vertex_id]

    if fixed_layer_idx < 0 or fixed_layer_idx >= len(layering):
        return 0.0  # No fixed layer neighbors

    fixed_layer = layering[fixed_layer_idx]
    fixed_layer_positions = {node_id: pos for pos, node_id in enumerate(fixed_layer)}

    # Find neighbors in the fixed layer
    neighbors_in_fixed = []
    arcs = ocpn_layout.get("arcs", {})
    for arc_id, arc in arcs.items():
        # Consider original direction before reversal for neighborhood
        src_orig, tgt_orig = arc['source'], arc['target']
        other_node = None
        if src_orig == vertex_id and tgt_orig in fixed_layer_positions:
            other_node = tgt_orig
        elif tgt_orig == vertex_id and src_orig in fixed_layer_positions:
            other_node = src_orig

        if other_node:
            # Check if the arc actually connects the two layers of interest
            other_node_layer = vertices.get(other_node, {}).get('layer', -1)
            if other_node_layer == fixed_layer_idx:
                neighbors_in_fixed.append(other_node)

    if not neighbors_in_fixed:
        return -1.0  # Indicate no neighbors

    barycenter_sum = 0.0
    for neighbor in neighbors_in_fixed:
        barycenter_sum += fixed_layer_positions[neighbor]  # Use 0-based index

    avg_barycenter = barycenter_sum / len(neighbors_in_fixed)

    # --- Add Object Attraction component (for places) ---
    if vertex["type"] == PLACE_TYPE and config.get("object_attraction", 0) > 0:
        object_attraction = config.get("object_attraction", 0.5)  # Default weight
        obj_attr_min = config.get("object_attraction_range_min", 1)
        obj_attr_max = config.get("object_attraction_range_max", 1)
        current_ot = vertex["objectType"]

        object_neighbor_positions = []
        direction = 1 if fixed_layer_idx > layer_idx else -1  # +1 if fixed layer is below, -1 if above

        for i in range(obj_attr_min, obj_attr_max + 1):
            target_layer_idx = layer_idx + direction * (2 * i)  # Look 2*i layers away
            if 0 <= target_layer_idx < len(layering):
                target_layer = layering[target_layer_idx]
                for neighbor_pos, node_id in enumerate(target_layer):
                    if vertices[node_id]["type"] == PLACE_TYPE and vertices[node_id]["objectType"] == current_ot:
                        object_neighbor_positions.append(neighbor_pos)

        if object_neighbor_positions:
            avg_object_pos = sum(object_neighbor_positions) / len(object_neighbor_positions)
            # Weighted average: (1 - attraction) * neighbor_barycenter + attraction * object_barycenter
            return (1.0 - object_attraction) * avg_barycenter + object_attraction * avg_object_pos
        else:
            return avg_barycenter  # No object neighbors found, use only structural barycenter
    elif vertex["type"] == DUMMY_TYPE:
        # Dummy nodes strongly follow their single neighbor in the fixed layer
        # This simplifies things and keeps dummy chains straight
        # Note: TS code seems to average if multiple dummies connect, but a single connection is standard
        if neighbors_in_fixed:
            # Should only have one neighbor in the fixed layer by construction
            return fixed_layer_positions[neighbors_in_fixed[0]]
        else:
            return -1.0  # Should not happen for a connected dummy

    else:  # Standard transition
        return avg_barycenter


def _barycenter_ordering_pass(ocpn_layout: Dict, current_layering: List[List[str]], fixed_layer_idx: int,
                              sweep_down: bool, config: Dict) -> List[List[str]]:
    """Performs one pass of barycenter ordering for layers adjacent to fixed_layer_idx."""
    new_layering = copy.deepcopy(current_layering)  # Work on a copy
    layer_to_order_idx = fixed_layer_idx + 1 if sweep_down else fixed_layer_idx - 1

    if layer_to_order_idx < 0 or layer_to_order_idx >= len(new_layering):
        return new_layering  # Nothing to order

    layer_to_order = new_layering[layer_to_order_idx]
    if not layer_to_order:
        return new_layering  # Empty layer

    # Compute barycenters for all nodes in the layer_to_order based on fixed_layer_idx
    barycenters = {}
    for node_id in layer_to_order:
        bc_val = _compute_barycenter(ocpn_layout, node_id, layer_to_order_idx, fixed_layer_idx, config)
        barycenters[node_id] = bc_val

    # Adjust barycenters for nodes with no neighbors (-1)
    adjusted_barycenters = {}
    last_valid_bc = 0.0
    for i, node_id in enumerate(layer_to_order):  # Iterate in original order first
        bc = barycenters[node_id]
        if bc == -1.0:
            # Assign based on the left neighbor's adjusted value, or 0 if first
            # Add small offset to maintain original relative order among no-neighbor nodes
            adjusted_bc = last_valid_bc + i * 1e-6  # Add tiny offset based on original pos
            adjusted_barycenters[node_id] = adjusted_bc
            # Don't update last_valid_bc here, use the *actual* last valid one
        else:
            adjusted_barycenters[node_id] = bc
            last_valid_bc = bc  # Update the last *valid* barycenter found

    # Sort the layer based on adjusted barycenters
    # Stable sort: maintain original order for equal barycenters
    original_indices = {node_id: i for i, node_id in enumerate(layer_to_order)}

    def sort_key(node_id):
        # Primary key: adjusted barycenter
        # Secondary key: original index for stability
        return (adjusted_barycenters[node_id], original_indices[node_id])

    ordered_layer = sorted(layer_to_order, key=sort_key)

    new_layering[layer_to_order_idx] = ordered_layer
    return new_layering


def _count_crossings(ocpn_layout: Dict, layering: List[List[str]]) -> int:
    """Counts the number of edge crossings in the current layering."""
    crossings = 0
    vertices = ocpn_layout["vertices"]
    arcs_data = ocpn_layout.get("arcs", {})

    # Build a map of node_id to its position within its layer
    node_positions = {}
    for r, layer in enumerate(layering):
        for c, node_id in enumerate(layer):
            node_positions[node_id] = (r, c)

    # Iterate through pairs of layers
    for r in range(len(layering) - 1):
        layer1 = layering[r]
        layer2 = layering[r + 1]

        # Get all arcs between layer r and layer r+1
        # Need arcs considering dummy nodes represent segments
        arcs_between = []
        for arc_id, arc in arcs_data.items():
            src, tgt = arc['source'], arc['target']
            pos_src = node_positions.get(src)
            pos_tgt = node_positions.get(tgt)
            if pos_src and pos_tgt:
                # Check if layers match r and r+1 (in either direction)
                if (pos_src[0] == r and pos_tgt[0] == r + 1):
                    arcs_between.append(
                        {'source': src, 'target': tgt, 'source_pos': pos_src[1], 'target_pos': pos_tgt[1]})
                elif (pos_src[0] == r + 1 and pos_tgt[0] == r):
                    arcs_between.append(
                        {'source': tgt, 'target': src, 'source_pos': pos_tgt[1], 'target_pos': pos_src[1]})

        # Bilayer crossing counting (simplified - optimal is complex)
        # This uses the standard pairwise comparison method
        for i in range(len(arcs_between)):
            for j in range(i + 1, len(arcs_between)):
                arc1 = arcs_between[i]
                arc2 = arcs_between[j]

                # Check if endpoints cross
                if (arc1['source_pos'] < arc2['source_pos'] and arc1['target_pos'] > arc2['target_pos']) or \
                        (arc1['source_pos'] > arc2['source_pos'] and arc1['target_pos'] < arc2['target_pos']):
                    crossings += 1

    return crossings


def _order_vertices(layout_data: Dict, config: Dict):
    """Orders vertices within layers using the barycenter method."""
    print("Step 4: Vertex Ordering (Barycenter Heuristic)...")

    max_iterations = config.get("max_barycenter_iterations", 24)  # Max iterations without improvement

    current_layering = layout_data["layering"]
    best_layering = copy.deepcopy(current_layering)
    best_score = _count_crossings(layout_data, best_layering)
    print(f"  Initial crossing score: {best_score}")

    no_improvement_counter = 0
    iter_count = 0

    # Initial adjustment based on object centrality (if provided) - simplified
    # TODO: Implement object centrality pre-sorting if needed, TS version does this.

    while no_improvement_counter < max_iterations:
        iter_count += 1
        layering_before_sweep = copy.deepcopy(current_layering)

        # Downward sweep (fix layer i, order layer i+1)
        for i in range(len(current_layering) - 1):
            current_layering = _barycenter_ordering_pass(layout_data, current_layering, fixed_layer_idx=i,
                                                         sweep_down=True, config=config)

        # Upward sweep (fix layer i, order layer i-1)
        for i in range(len(current_layering) - 1, 0, -1):
            current_layering = _barycenter_ordering_pass(layout_data, current_layering, fixed_layer_idx=i,
                                                         sweep_down=False, config=config)

        current_score = _count_crossings(layout_data, current_layering)

        if current_score < best_score:
            best_score = current_score
            best_layering = copy.deepcopy(current_layering)
            no_improvement_counter = 0
            print(f"  Iteration {iter_count}: Improved score to {best_score}")
        else:
            no_improvement_counter += 1
            print(f"  Iteration {iter_count}: Score {current_score} (no improvement)")

        # Check for convergence (layering didn't change)
        if current_layering == layering_before_sweep:
            print(f"  Converged after {iter_count} iterations.")
            break

        # Check for oscillations (revisiting a previous state)? More complex to track.

    print(f"  Final crossing score: {best_score} after {iter_count} iterations.")
    layout_data["layering"] = best_layering

    # Update the 'pos' attribute in the vertex data
    for r, layer in enumerate(best_layering):
        for c, node_id in enumerate(layer):
            layout_data["vertices"][node_id]['pos'] = c


# --- Vertex Positioning (Brandes & Köpf Heuristic Variant) ---

def _mark_type1_conflicts(layout_data: Dict):
    """Marks arcs that cross 'inner segments' (dummy-dummy connections)."""
    vertices = layout_data["vertices"]
    arcs = layout_data["arcs"]
    layering = layout_data["layering"]

    for arc_id, arc in arcs.items():
        arc['type1'] = False  # Reset

    # Iterate through layers where conflicts can occur
    for i in range(len(layering) - 2):  # Need layers i, i+1, i+2
        layer_i = layering[i]
        layer_i1 = layering[i + 1]
        layer_i2 = layering[i + 2]

        pos_i1 = {node_id: pos for pos, node_id in enumerate(layer_i1)}
        pos_i = {node_id: pos for pos, node_id in enumerate(layer_i)}

        inner_segments = []  # Tuples (upper_dummy_pos, lower_dummy_pos) in layers i, i+1
        # Find inner segments between layer i and i+1
        for k, v_i1 in enumerate(layer_i1):
            node_i1_data = vertices[v_i1]
            if node_i1_data['type'] == DUMMY_TYPE:
                upper_neighbor_id = node_i1_data.get("upper_neighbor")
                if upper_neighbor_id and upper_neighbor_id in pos_i:
                    upper_neighbor_data = vertices[upper_neighbor_id]
                    if upper_neighbor_data['type'] == DUMMY_TYPE:
                        # Found inner segment (dummy -> dummy)
                        inner_segments.append((pos_i[upper_neighbor_id], k))

        if not inner_segments: continue  # No conflicts possible if no inner segments

        inner_segments.sort()  # Sort by position in layer i

        k0 = 0
        current_inner_idx = 0
        # Check non-inner segments between i and i+1 for crossings
        for l1, v_i1 in enumerate(layer_i1):  # Iterate through nodes in layer i+1
            k1 = len(layer_i) - 1  # Default right boundary
            is_lower_end_of_inner = False

            # Find the right boundary k1 defined by the next inner segment starting at or after v_i1
            while current_inner_idx < len(inner_segments) and inner_segments[current_inner_idx][1] <= l1:
                k1 = inner_segments[current_inner_idx][0]
                is_lower_end_of_inner = (inner_segments[current_inner_idx][1] == l1)
                current_inner_idx += 1

            if not is_lower_end_of_inner:  # Only check non-inner segments
                # Get upper neighbors in layer i for v_i1
                upper_neighbors_i = []
                for arc_id, arc_data in arcs.items():
                    if arc_data['target'] == v_i1 and arc_data['source'] in pos_i:
                        upper_neighbors_i.append(arc_data['source'])
                    elif arc_data['source'] == v_i1 and arc_data[
                        'target'] in pos_i:  # Should not happen if directed correctly
                        pass

                for u_i in upper_neighbors_i:
                    k = pos_i[u_i]
                    # Check if upper neighbor u_i is outside the bounds [k0, k1] defined by inner segments
                    if k < k0 or k > k1:
                        # This non-inner segment crosses an inner segment - mark as type 1
                        connecting_arcs = get_arcs_between(u_i, v_i1, layout_data)
                        for conn_arc in connecting_arcs:
                            # Ensure we only mark non-inner segments
                            is_seg_inner = (
                                        vertices[u_i]['type'] == DUMMY_TYPE and vertices[v_i1]['type'] == DUMMY_TYPE)
                            if not is_seg_inner:
                                conn_arc['type1'] = True

            # Update left boundary for next iteration
            if is_lower_end_of_inner:
                k0 = k1


def _vertical_alignment(ocpn_layout: Dict, current_layering: List[List[str]], pos: Dict[str, int], sweep_down: bool) -> \
Tuple[Dict[str, str], Dict[str, str]]:
    """Aligns vertices vertically with median neighbors."""
    root = {vid: vid for vid in ocpn_layout["vertices"]}
    align = {vid: vid for vid in ocpn_layout["vertices"]}
    vertices = ocpn_layout["vertices"]

    # Iterate through layers in sweep direction
    layer_indices = range(len(current_layering)) if sweep_down else range(len(current_layering) - 1, -1, -1)

    for i in layer_indices:
        fixed_layer_idx = i - 1 if sweep_down else i + 1
        if fixed_layer_idx < 0 or fixed_layer_idx >= len(current_layering):
            continue  # Boundary layer

        layer_k = current_layering[i]
        r = -1  # Tracks the position of the rightmost aligned node in fixed layer

        for vk in layer_k:  # Iterate through nodes vk in current layer i
            # Get neighbors in the fixed layer (upper if sweep_down, lower otherwise)
            neighbors = []
            neighbor_dir = 'up' if sweep_down else 'down'

            # Find neighbors based on arc directionality *relative to the layers*
            arcs_data = ocpn_layout.get("arcs", {})
            fixed_layer_nodes = set(current_layering[fixed_layer_idx])

            for arc_id, arc in arcs_data.items():
                src, tgt = arc['source'], arc['target']
                if sweep_down:  # Looking for upper neighbors (in fixed_layer_idx = i-1)
                    if tgt == vk and src in fixed_layer_nodes:
                        neighbors.append(src)
                else:  # Looking for lower neighbors (in fixed_layer_idx = i+1)
                    if src == vk and tgt in fixed_layer_nodes:
                        neighbors.append(tgt)

            if not neighbors: continue

            # Sort neighbors by position in their layer
            neighbors.sort(key=lambda n: pos[n])

            # Get median neighbor(s) indices
            m_low = math.floor((len(neighbors) - 1) / 2)
            m_high = math.ceil((len(neighbors) - 1) / 2)
            median_indices = list(set([m_low, m_high]))  # Use set to handle single median case

            for m_idx in median_indices:
                median_neighbor = neighbors[m_idx]

                # Check if vk can be aligned with this median neighbor
                if align[vk] == vk:  # If vk is not already aligned
                    # Check if the edge is marked as type 1 conflict
                    connecting_arcs = get_arcs_between(median_neighbor, vk, ocpn_layout)
                    is_marked = any(a.get('type1', False) for a in connecting_arcs)

                    if not is_marked and pos[median_neighbor] > r:
                        # Align vk to median_neighbor
                        align[median_neighbor] = vk
                        root[vk] = root[median_neighbor]
                        align[vk] = root[vk]  # Point vk to the root of the block
                        r = pos[median_neighbor]  # Update rightmost position

    return root, align


def _place_block(ocpn_layout: Dict, layering: List[List[str]], v: str, x: Dict[str, Optional[float]],
                 pos: Dict[str, int], roots: Dict[str, str], sink: Dict[str, str], shift: Dict[str, float],
                 aligns: Dict[str, str], config: Dict):
    """Recursive part of horizontal compaction."""
    if x.get(v) is None:  # If x[v] is not yet defined
        x[v] = 0.0
        w = v
        while True:
            w_pos = pos[w]
            # Find layer index for w
            w_layer_idx = -1
            for idx, l in enumerate(layering):
                if w in l:
                    w_layer_idx = idx
                    break

            if w_pos > 0 and w_layer_idx != -1:  # If w has a predecessor in its layer
                predecessor = layering[w_layer_idx][w_pos - 1]
                u = roots[predecessor]  # Root of the predecessor block
                # Recursively place the predecessor block
                _place_block(ocpn_layout, layering, u, x, pos, roots, sink, shift, aligns, config)

                # Update sink relationship
                if sink[v] == v:
                    sink[v] = sink[u]

                # Calculate separation delta
                # Use max dimension based on rankdir
                place_dim = config.get("place_radius", 10) * 2
                trans_h = config.get("transition_height", 20)
                trans_w = config.get("transition_width", 50)
                silent_w = config.get("silent_transition_width", 10)
                max_trans_dim = max(trans_h, trans_w, silent_w)  # Simplified max size

                delta = config.get("vertex_sep", 20) + max(place_dim, max_trans_dim)  # Use a generic max size estimate

                if sink[v] != sink[u]:
                    # Blocks have different sinks, calculate required shift
                    current_shift = (x.get(v, 0.0) or 0.0) - (x.get(u, 0.0) or 0.0) - delta
                    shift[sink[u]] = min(shift.get(sink[u], float('inf')), current_shift)
                else:
                    # Blocks have the same sink, update position directly
                    new_x = (x.get(u, 0.0) or 0.0) + delta
                    x[v] = max(x.get(v, 0.0) or 0.0, new_x)

            # Move to the next node in the alignment block
            w = aligns[w]
            if w == v:  # Completed the block cycle
                break


def _horizontal_compaction(ocpn_layout: Dict, layering: List[List[str]], roots: Dict[str, str], aligns: Dict[str, str],
                           pos: Dict[str, int], config: Dict) -> Tuple[Dict[str, Optional[float]], float]:
    """Assigns preliminary x-coordinates based on vertical alignment."""
    x: Dict[str, Optional[float]] = {vid: None for vid in ocpn_layout["vertices"]}
    sink: Dict[str, str] = {vid: vid for vid in ocpn_layout["vertices"]}
    shift: Dict[str, float] = {vid: float('inf') for vid in ocpn_layout["vertices"]}

    # Place blocks rooted at v
    for layer in layering:
        for v in layer:
            if roots[v] == v:  # If v is a root
                _place_block(ocpn_layout, layering, v, x, pos, roots, sink, shift, aligns, config)

    # Calculate absolute coordinates
    abs_x: Dict[str, Optional[float]] = {}
    max_coord = 0.0
    min_coord = float('inf')

    for layer in layering:
        for v in layer:
            root_v = roots[v]
            if x.get(root_v) is not None:
                current_x = x[root_v]
                sink_root_v = sink[root_v]
                # Apply shift if the sink has a finite shift value
                if shift.get(sink_root_v, float('inf')) != float('inf'):
                    current_x += shift[sink_root_v]
                abs_x[v] = current_x
                max_coord = max(max_coord, current_x)
                min_coord = min(min_coord, current_x)
            else:
                abs_x[v] = None  # Should not happen if graph is connected

    # Normalize coordinates to start from 0 (or config.borderPadding)
    border = config.get("border_padding", 20)
    shift_val = border - min_coord if min_coord != float('inf') else border
    final_x = {}
    final_max = 0.0
    for v, val in abs_x.items():
        if val is not None:
            final_x[v] = val + shift_val
            final_max = max(final_max, final_x[v])
        else:
            final_x[v] = None

    # Add padding to the max coordinate as well
    final_max += border

    return final_x, final_max


def _position_vertices(layout_data: Dict, config: Dict):
    """Assigns final X/Y coordinates using 4-pass heuristic."""
    print("Step 5: Vertex Positioning...")

    # Mark type 1 conflicts first
    _mark_type1_conflicts(layout_data)

    layouts = []  # Store results of 4 passes {vertex_id: coord}

    original_layering = copy.deepcopy(layout_data["layering"])

    # --- Perform 4 passes ---
    for vert_dir in [0, 1]:  # 0: Down, 1: Up
        for horz_dir in [0, 1]:  # 0: Left->Right, 1: Right->Left

            print(f"  Running positioning pass (vert_dir={vert_dir}, horz_dir={horz_dir})...")
            current_layering = copy.deepcopy(original_layering)

            # 1. Transform layering based on direction
            if vert_dir == 1:  # Up
                current_layering.reverse()
            if horz_dir == 1:  # Right->Left
                for layer in current_layering:
                    layer.reverse()

            # Create position map for this transformed layering
            pos = {}
            for r, layer in enumerate(current_layering):
                for c, node_id in enumerate(layer):
                    pos[node_id] = c

            # 2. Vertical Alignment
            roots, aligns = _vertical_alignment(layout_data, current_layering, pos, sweep_down=(vert_dir == 0))

            # 3. Horizontal Compaction
            coords, max_coord = _horizontal_compaction(layout_data, current_layering, roots, aligns, pos, config)

            # 4. Undo horizontal transformation if needed
            if horz_dir == 1:
                final_coords = {}
                for v, c in coords.items():
                    if c is not None:
                        final_coords[v] = max_coord - c
                    else:
                        final_coords[v] = None
                layouts.append(final_coords)
            else:
                layouts.append(coords)

    # --- Combine results ---
    final_coords_x = {}
    final_coords_y = {}
    vertices = layout_data["vertices"]
    layering = layout_data["layering"]  # Use original layering for Y-coord calc
    border_padding = config.get("border_padding", 20)
    layer_sep = config.get("layer_sep", 50)
    direction = config.get("rankdir", "TB")  # TB or LR

    # 1. Calculate final X coordinate (median of 4 passes)
    for v_id in vertices.keys():
        candidate_coords = []
        for layout_pass in layouts:
            coord = layout_pass.get(v_id)
            if coord is not None:
                candidate_coords.append(coord)

        if candidate_coords:
            candidate_coords.sort()
            # Use median (average of middle two for even number)
            if len(candidate_coords) > 0:
                median_idx1 = math.floor((len(candidate_coords) - 1) / 2)
                median_idx2 = math.ceil((len(candidate_coords) - 1) / 2)
                median_coord = (candidate_coords[median_idx1] + candidate_coords[median_idx2]) / 2
                final_coords_x[v_id] = median_coord
        else:
            final_coords_x[v_id] = border_padding  # Default if no coord found?

    # 2. Calculate Y coordinate based on layer and layer sizes
    layer_sizes = []  # Store { 'layer': idx, 'size': height/width }
    max_layer_dim = 0
    for i, layer in enumerate(layering):
        max_dim = 0
        for node_id in layer:
            node = vertices[node_id]
            node_h, node_w = 0, 0
            if node['type'] == PLACE_TYPE:
                r = config.get("place_radius", 10)
                node_h, node_w = r * 2, r * 2
            elif node['type'] == TRANSITION_TYPE:
                node_h = config.get("transition_height", 20)
                if node['silent']:
                    node_w = config.get("silent_transition_width", 10)
                else:
                    node_w = config.get("transition_width", 50)
            elif node['type'] == DUMMY_TYPE:
                # Give dummies minimal size for separation calculation
                node_h, node_w = 1, 1

            if direction == "TB":
                max_dim = max(max_dim, node_h)
            else:  # LR
                max_dim = max(max_dim, node_w)
        layer_sizes.append({'layer': i, 'size': max_dim})
        max_layer_dim = max(max_layer_dim, max_dim)

    current_pos = border_padding
    layer_centers = {}
    for i in range(len(layering)):
        layer_size = layer_sizes[i]['size'] if i < len(layer_sizes) else max_layer_dim  # Use max if missing
        layer_center = current_pos + layer_size / 2.0
        layer_centers[i] = layer_center
        current_pos += layer_size + layer_sep

    # Assign coordinates based on rankdir
    max_x, max_y = 0.0, 0.0
    for v_id, node in vertices.items():
        x_coord = final_coords_x.get(v_id, border_padding)  # Horizontal position from passes
        y_coord = layer_centers.get(node['layer'], border_padding)  # Vertical position from layer

        if direction == "TB":
            node['x'] = x_coord
            node['y'] = y_coord  # Graphviz Y is often inverted, handle during drawing
            max_x = max(max_x, x_coord)
            max_y = max(max_y, y_coord)
        else:  # LR
            node['x'] = y_coord  # Layer position becomes X
            node['y'] = x_coord  # Calculated position becomes Y
            max_x = max(max_x, y_coord)
            max_y = max(max_y, x_coord)

    layout_data["max_x"] = max_x + border_padding
    layout_data["max_y"] = max_y + border_padding  # Store bounds for SVG sizing?

    print(f"  Assigned final coordinates (max_x={max_x:.2f}, max_y={max_y:.2f}).")


# --- Graphviz Drawing ---

def _create_graphviz_digraph(ocpn: Dict, layout_data: Dict, parameters: Dict) -> Digraph:
    """Generates the Graphviz Digraph object from the layout with separate handling for direct edges and waypoint edges."""
    print("Step 6: Generating Graphviz output...")

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)
    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, "TB")
    engine = exec_utils.get_param_value(Parameters.ENGINE, parameters, "dot")
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Object-Centric Petri Net (Sugiyama Layout)")

    viz = Digraph(
        "ocpn_sugiyama",
        engine=engine,
        graph_attr={
            "bgcolor": bgcolor,
            "rankdir": rankdir,
            "splines": "line",  # Default to straight lines, adjust per edge type if needed
        },
        node_attr={'shape': 'box'},
    )

    if enable_graph_title:
        viz.attr(label=f'<<FONT POINT-SIZE="20">{graph_title}</FONT>>', labelloc="t")

    vertices = layout_data["vertices"]
    max_y = layout_data.get("max_y", 600)

    # Add Nodes (unchanged)
    for node_id, node in vertices.items():
        if node.get('x') is None or node.get('y') is None:
            print(f"Warning: Node {node_id} has no coordinates, skipping.")
            continue

        pos_x = node['x']
        pos_y = node['y']
        pos_str = f"{pos_x:.2f},{pos_y:.2f}!"

        attrs = {
            "pos": pos_str,
            "label": node['label'] if node['label'] else "",
            "id": node_id
        }

        if node['type'] == PLACE_TYPE:
            ot_color = ot_to_color(node['objectType'])
            radius_gv = parameters.get("place_radius", 10) / 72.0
            if node.get("is_source"):
                ot_label = f"{node['objectType']}"
                attrs.update({
                    "shape": "ellipse",
                    "fillcolor": ot_color,
                    "style": "filled",
                    "fontcolor": "black",
                    "width": f"{radius_gv * 2.5:.2f}",
                    "height": f"{radius_gv * 1.5:.2f}",
                    "fixedsize": "true",
                    "label": f"<{ot_label}<FONT POINT-SIZE='6'><BR/> </FONT>>",
                    "labelloc": "c",
                })
                if node.get("is_source") and node.get("is_sink"):
                    attrs["peripheries"] = "2"
            else:
                attrs.update({
                    "shape": "circle",
                    "fillcolor": ot_color,
                    "style": "filled",
                    "fontcolor": "black",
                    "width": f"{radius_gv * 2:.2f}",
                    "height": f"{radius_gv * 2:.2f}",
                    "fixedsize": "true",
                    "label": "",
                })
                if node.get("is_sink"):
                    attrs["peripheries"] = "2"

        elif node['type'] == TRANSITION_TYPE:
            height_gv = parameters.get("transition_height", 20) / 72.0
            if node['silent']:
                width_gv = parameters.get("silent_transition_width", 10) / 72.0
                attrs.update({
                    "shape": "box",
                    "fillcolor": parameters.get("transition_fill_color", "black"),
                    "style": "filled",
                    "width": f"{width_gv:.2f}",
                    "height": f"{height_gv:.2f}",
                    "fixedsize": "true",
                    "label": "",
                })
            else:
                base_width_gv = parameters.get("transition_width", 40) / 72.0
                width_gv = base_width_gv * 1.5
                font_size = parameters.get("font_size", 10) - 2
                label = node['label']
                max_label_width = 10
                if len(label) > max_label_width:
                    wrapped_label = "<BR/>".join([label[i:i+max_label_width] for i in range(0, len(label), max_label_width)])
                    attrs["label"] = f"<{wrapped_label}>"
                else:
                    attrs["label"] = label
                attrs.update({
                    "shape": "box",
                    "fillcolor": parameters.get("transition_fill_color", "white"),
                    "style": "filled",
                    "color": parameters.get("transition_color", "black"),
                    "width": f"{width_gv:.2f}",
                    "height": f"{height_gv:.2f}",
                    "fixedsize": "true",
                    "fontname": parameters.get("font_name", "Arial"),
                    "fontsize": str(font_size),
                    "fontcolor": parameters.get("transition_textcolor", "black"),
                })

        elif node['type'] == DUMMY_TYPE:
            attrs.update({
                "shape": "point",
                "width": "0.01",
                "height": "0.01",
                "label": "",
                "fixedsize": "true",
                "style": "invis",
            })

        viz.node(node_id, **attrs)

    # Add Edges with separate handling
    arcs = layout_data["arcs"]
    original_arcs = layout_data["original_arcs"]

    # First, categorize arcs
    direct_edges = []  # Arcs with no dummy nodes between non-dummy source and target
    waypoint_edges = {}  # Original arcs that pass through dummies, keyed by original arc_id

    for arc_id, arc in arcs.items():
        src = arc['source']
        tgt = arc['target']

        if src not in vertices or tgt not in vertices or \
                vertices[src].get('x') is None or vertices[tgt].get('x') is None:
            continue

        src_type = vertices[src]['type']
        tgt_type = vertices[tgt]['type']

        # Check if this arc is part of an original arc with dummies
        original_arc_id = arc.get('original_arc_id', arc_id)
        original_arc = original_arcs.get(original_arc_id, arc)

        # If both source and target are non-dummy and no dummies in original arc
        if src_type != DUMMY_TYPE and tgt_type != DUMMY_TYPE and not original_arc.get('dummy_nodes'):
            direct_edges.append(arc)
        else:
            # Collect all segments of waypoint edges under their original arc
            if original_arc_id not in waypoint_edges:
                # Find the ultimate source and target (non-dummy nodes)
                dummy_nodes = original_arc.get('dummy_nodes', [])
                ultimate_src = original_arc.get('source')
                ultimate_tgt = original_arc.get('target')
                waypoint_edges[original_arc_id] = {
                    'original_arc': original_arc,
                    'segments': [],
                    'ultimate_source': ultimate_src,
                    'ultimate_target': ultimate_tgt,
                    'dummy_nodes': dummy_nodes
                }
            waypoint_edges[original_arc_id]['segments'].append(arc)

    # 1. Draw Direct Edges
    for arc in direct_edges:
        src = arc['source']
        tgt = arc['target']
        ot = arc.get("objectType", layout_data["object_types"][0] if layout_data["object_types"] else "unknown")
        ot_color = ot_to_color(ot)

        edge_attrs = {
            "color": ot_color,
            "penwidth": str(parameters.get("arc_size", 1.0) * arc.get("weight", 1.0)),
            "arrowsize": str(parameters.get("arrowhead_size", 0.7)),
            "id": arc['id'],
            "splines": "line",  # Direct edges as straight lines
        }

        if arc.get('variable'):
            edge_attrs["penwidth"] = str(float(edge_attrs["penwidth"]) * 1.5)
            edge_attrs["style"] = "dashed"

        # Direct edges always have an arrow unless reversed
        if arc.get('reversed', False):
            edge_attrs['dir'] = 'back'
        else:
            edge_attrs['dir'] = 'forward'

        viz.edge(src, tgt, **edge_attrs)

    # 2. Draw Waypoint Edges (edges passing through dummies)
    for orig_arc_id, wp_data in waypoint_edges.items():
        orig_arc = wp_data['original_arc']
        segments = wp_data['segments']
        ultimate_src = wp_data['ultimate_source']
        ultimate_tgt = wp_data['ultimate_target']
        dummy_nodes = wp_data['dummy_nodes']

        ot = orig_arc.get("objectType", layout_data["object_types"][0] if layout_data["object_types"] else "unknown")
        ot_color = ot_to_color(ot)

        # Base attributes for all segments of this arc
        base_edge_attrs = {
            "color": ot_color,
            "penwidth": str(parameters.get("arc_size", 1.0) * orig_arc.get("weight", 1.0)),
            "arrowsize": str(parameters.get("arrowhead_size", 0.7)),
            "splines": "polyline",  # Allow bending at dummy nodes
        }

        if orig_arc.get('variable'):
            base_edge_attrs["penwidth"] = str(float(base_edge_attrs["penwidth"]) * 1.5)
            base_edge_attrs["style"] = "dashed"

        # Add each segment
        for segment in segments:
            src = segment['source']
            tgt = segment['target']
            segment_attrs = base_edge_attrs.copy()
            segment_attrs['id'] = segment['id']

            # Adjust arrowheads: no arrow if target is a dummy, full arrow only at ultimate target
            if tgt == ultimate_tgt:
                segment_attrs['arrowhead'] = 'normal'
                segment_attrs['dir'] = 'foward'
            elif src == ultimate_tgt:
                segment_attrs['arrowhead'] = 'normal'
                segment_attrs['dir'] = 'back'
            else:
                segment_attrs['arrowhead'] = 'none'

            viz.edge(src, tgt, **segment_attrs)

    viz.format = image_format.replace("html", "plain-ext")
    return viz


# --- Main Apply Function ---

class Parameters(Enum):
    """ Parameters for the Sugiyama OCPN visualization """
    FORMAT = "format"
    BGCOLOR = "bgcolor"
    RANKDIR = "rankdir"  # TB or LR
    ENGINE = "engine"  # dot, neato, fdp
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"

    # Sugiyama specific parameters (matching TS config where possible)
    SOURCES = "sources"  # List of node IDs to force as sources
    SINKS = "sinks"  # List of node IDs to force as sinks
    VERTEX_SEP = "vertex_sep"  # Minimum horizontal distance between nodes
    LAYER_SEP = "layer_sep"  # Minimum vertical distance between layers
    EDGE_SEP = "edge_sep"  # (Not directly used here, vertex_sep dominates)
    BORDER_PADDING = "border_padding"  # Padding around the graph
    OBJECT_CENTRALITY = "object_centrality"  # Dict {ot: centrality_value} (Lower value = more central/left)
    OBJECT_ATTRACTION = "object_attraction"  # Weight (0-1) for place attraction in barycenter
    OBJECT_ATTRACTION_RANGE_MIN = "object_attraction_range_min"  # Min layers distance for attraction
    OBJECT_ATTRACTION_RANGE_MAX = "object_attraction_range_max"  # Max layers distance for attraction
    MAX_BARYCENTER_ITERATIONS = "max_barycenter_iterations"  # Max iterations for ordering

    # Visual element sizes (in points, roughly 1/72 inch)
    PLACE_RADIUS = "place_radius"
    TRANSITION_WIDTH = "transition_width"
    TRANSITION_HEIGHT = "transition_height"
    SILENT_TRANSITION_WIDTH = "silent_transition_width"
    ARC_SIZE = "arc_size"  # Base thickness
    ARROWHEAD_SIZE = "arrowhead_size"
    INDICATE_ARC_WEIGHT = "indicate_arc_weight"  # Boolean
    INDICATE_VARIABLE_ARCS = "indicate_variable_arcs"  # Boolean
    VARIABLE_ARC_INDICATOR_COLOR = "variable_arc_indicator_color"
    VARIABLE_ARC_INDICATOR_SIZE = "variable_arc_indicator_size"  # Multiplier for thickness

    # Colors
    TRANSITION_COLOR = "transition_color"  # Border
    TRANSITION_FILL_COLOR = "transition_fill_color"
    TRANSITION_TEXT_COLOR = "transition_text_color"
    DEFAULT_PLACE_COLOR = "default_place_color"  # Fallback if OT color fails
    ARC_DEFAULT_COLOR = "arc_default_color"
    TYPE_COLOR_MAPPING = "type_color_mapping"  # Optional dict {ot: color} override

    # Font
    FONT_NAME = "font_name"
    FONT_SIZE = "font_size"


def apply(ocpn: Dict[str, Any], parameters: Optional[Dict[Any, Any]] = None) -> Digraph:
    """
    Obtains a visualization of the provided object-centric Petri net using
    a Sugiyama-based layout algorithm.

    Args:
        ocpn (Dict[str, Any]): Object-centric Petri net structure.
        parameters (Optional[Dict[Any, Any]], optional): Algorithm parameters.

    Returns:
        Digraph: A Graphviz digraph object representing the layout.
    """
    if parameters is None:
        parameters = {}

    # --- Set default configuration parameters ---
    config = {
        # Basic viz
        Parameters.FORMAT.value: "png",
        Parameters.BGCOLOR.value: constants.DEFAULT_BGCOLOR,
        Parameters.RANKDIR.value: "TB",
        Parameters.ENGINE.value: "dot",
        Parameters.ENABLE_GRAPH_TITLE.value: True,
        Parameters.GRAPH_TITLE.value: "Object-Centric Petri Net (Sugiyama Layout)",
        # Sugiyama layout params
        Parameters.SOURCES.value: [],
        Parameters.SINKS.value: [],
        Parameters.VERTEX_SEP.value: 30,  # Adjusted default based on typical node sizes
        Parameters.LAYER_SEP.value: 50,
        Parameters.BORDER_PADDING.value: 20,
        Parameters.OBJECT_CENTRALITY.value: {},
        Parameters.OBJECT_ATTRACTION.value: 0.2,  # Moderate attraction
        Parameters.OBJECT_ATTRACTION_RANGE_MIN.value: 1,
        Parameters.OBJECT_ATTRACTION_RANGE_MAX.value: 2,  # Look 1 or 2 place-layers away
        Parameters.MAX_BARYCENTER_ITERATIONS.value: 24,
        # Visual sizes (points)
        Parameters.PLACE_RADIUS.value: 10.0,
        Parameters.TRANSITION_WIDTH.value: 40.0,
        Parameters.TRANSITION_HEIGHT.value: 20.0,
        Parameters.SILENT_TRANSITION_WIDTH.value: 8.0,
        Parameters.ARC_SIZE.value: 1.0,
        Parameters.ARROWHEAD_SIZE.value: 0.7,
        Parameters.INDICATE_ARC_WEIGHT.value: False,
        Parameters.INDICATE_VARIABLE_ARCS.value: True,
        Parameters.VARIABLE_ARC_INDICATOR_COLOR.value: "#FF0000",  # Red indicator for testing
        Parameters.VARIABLE_ARC_INDICATOR_SIZE.value: 1.5,  # Multiplier
        # Colors
        Parameters.TRANSITION_COLOR.value: "black",
        Parameters.TRANSITION_FILL_COLOR.value: "white",
        Parameters.TRANSITION_TEXT_COLOR.value: "black",
        Parameters.DEFAULT_PLACE_COLOR.value: "#D3D3D3",  # Light gray
        Parameters.ARC_DEFAULT_COLOR.value: "black",
        Parameters.TYPE_COLOR_MAPPING.value: {},
        # Font
        Parameters.FONT_NAME.value: "Arial",
        Parameters.FONT_SIZE.value: 10,
    }
    # Update defaults with user-provided parameters
    config.update({param.value: val for param, val in parameters.items() if isinstance(param, Parameters)})
    # Also allow string keys from user parameters
    config.update({k: v for k, v in parameters.items() if isinstance(k, str) and k in [p.value for p in Parameters]})

    # --- Build initial layout structure ---
    layout_data = _build_initial_layout(ocpn, config)
    if not layout_data["vertices"]:
        print("Error: No vertices found in OCPN structure.")
        return Digraph()  # Return empty graph

    # --- Run Sugiyama Steps ---
    _reverse_cycles(layout_data, config)

    if not _assign_layers(layout_data):
        print("Error: Layer assignment failed. Cannot proceed.")
        # Optionally: return a basic graphviz layout without positions?
        # For now, return empty.
        return Digraph()  # Or maybe the original non-sugiyama viz?

    _insert_dummy_vertices(layout_data)

    _order_vertices(layout_data, config)

    _position_vertices(layout_data, config)

    # --- Generate Graphviz Output ---
    gviz_graph = _create_graphviz_digraph(ocpn, layout_data, config)

    return gviz_graph
