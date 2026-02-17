"""
Test suite for the apply_partial_order_projection function.

These tests validate the observable behaviour of
pm4py.objects.conversion.wf_net.variants.to_powl.apply_partial_order_projection.

The tests are written in terms of functional requirements (contract-style behaviour),
not in terms of internal branch IDs. A separate instrumentation map is kept below for
coverage analysis only.
"""

import unittest

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.conversion.wf_net.variants.to_powl import apply_partial_order_projection

# Manual coverage instrumentation reference (apply_partial_order_projection).
# This is for coverage bookkeeping only and must not be treated as a behavioural specification.
# 0: start uniqueness violated (raise)
# 1: start uniqueness check passed (in uniqueness loop)
# 2: start_places == end_places
# 3: start_places != end_places
# 4: end uniqueness violated (raise)
# 5: end uniqueness check passed (in uniqueness loop)
# 6: arc touches subnet transitions (processed)
# 7: source found in node_map
# 8: source not in node_map
# 9: source is boundary and unmapped => continue (skip arc)
# 10: source is not boundary and unmapped => clone place
# 11: target found in node_map
# 12: target not in node_map
# 13: target is boundary and unmapped => continue (skip arc)
# 14: target is not boundary and unmapped => clone place
# 15: arc does not touch subnet transitions (ignored)
# 16: iterating over subnet_transitions
# 17: iterating start uniqueness loop (len(start_places) > 1)
# 18: iterating end uniqueness loop (len(end_places) > 1)
# 19: iterating over net.arcs


class PartialOrderProjectionTest(unittest.TestCase):
    # Helper Methods

    def _create_simple_sequence_net(self) -> tuple[PetriNet, PetriNet.Place, PetriNet.Place]:
        """
        Create a simple sequential Petri net: p1 -> t1 -> p2 -> t2 -> p3.

        Returns:
            Tuple of (net, start_place, end_place)
        """
        net = PetriNet("simple_sequence")

        p1 = PetriNet.Place("p1")
        p2 = PetriNet.Place("p2")
        p3 = PetriNet.Place("p3")
        net.places.add(p1)
        net.places.add(p2)
        net.places.add(p3)

        t1 = PetriNet.Transition("t1", "t1")
        t2 = PetriNet.Transition("t2", "t2")
        net.transitions.add(t1)
        net.transitions.add(t2)

        petri_utils.add_arc_from_to(p1, t1, net)
        petri_utils.add_arc_from_to(t1, p2, net)
        petri_utils.add_arc_from_to(p2, t2, net)
        petri_utils.add_arc_from_to(t2, p3, net)

        return net, p1, p3

    def _create_parallel_net(self) -> tuple[PetriNet, PetriNet.Place, PetriNet.Place]:
        """
        Create a Petri net with parallel branches.

        Structure:
            p1 -> t1 -> p2
            p1 -> t2 -> p2

        Returns:
            Tuple of (net, start_place, end_place)
        """
        net = PetriNet("parallel_net")

        p1 = PetriNet.Place("p1")
        p2 = PetriNet.Place("p2")
        net.places.add(p1)
        net.places.add(p2)

        t1 = PetriNet.Transition("t1", "t1")
        t2 = PetriNet.Transition("t2", "t2")
        net.transitions.add(t1)
        net.transitions.add(t2)

        petri_utils.add_arc_from_to(p1, t1, net)
        petri_utils.add_arc_from_to(p1, t2, net)
        petri_utils.add_arc_from_to(t1, p2, net)
        petri_utils.add_arc_from_to(t2, p2, net)

        return net, p1, p2

    def _create_loop_net(self) -> tuple[PetriNet, PetriNet.Place]:
        """
        Create a loop: p1 -> t1 -> p2 -> t2 -> p1.

        Returns:
            Tuple of (net, loop_place)
        """
        net = PetriNet("loop_net")

        p1 = PetriNet.Place("p1")
        p2 = PetriNet.Place("p2")
        net.places.add(p1)
        net.places.add(p2)

        t1 = PetriNet.Transition("t1", "t1")
        t2 = PetriNet.Transition("t2", "t2")
        net.transitions.add(t1)
        net.transitions.add(t2)

        petri_utils.add_arc_from_to(p1, t1, net)
        petri_utils.add_arc_from_to(t1, p2, net)
        petri_utils.add_arc_from_to(p2, t2, net)
        petri_utils.add_arc_from_to(t2, p1, net)

        return net, p1

    def _create_net_for_internal_places(self) -> tuple[PetriNet, PetriNet.Place, PetriNet.Place, PetriNet.Place]:
        """
        Create: p_start -> t1 -> p_internal -> t2 -> p_end.

        Returns:
            Tuple of (net, p_start, p_internal, p_end)
        """
        net = PetriNet("internal_places_net")

        p_start = PetriNet.Place("p_start")
        p_internal = PetriNet.Place("p_internal")
        p_end = PetriNet.Place("p_end")
        net.places.add(p_start)
        net.places.add(p_internal)
        net.places.add(p_end)

        t1 = PetriNet.Transition("t1", "t1")
        t2 = PetriNet.Transition("t2", "t2")
        net.transitions.add(t1)
        net.transitions.add(t2)

        petri_utils.add_arc_from_to(p_start, t1, net)
        petri_utils.add_arc_from_to(t1, p_internal, net)
        petri_utils.add_arc_from_to(p_internal, t2, net)
        petri_utils.add_arc_from_to(t2, p_end, net)

        return net, p_start, p_internal, p_end

    def _assert_subnet_structure(
            self,
            subnet: PetriNet,
            expected_transitions: int,
            expected_places: int,
            expected_arcs: int,
    ) -> None:
        """
        Assert that a subnet has the expected structure.

        Args:
            subnet: The Petri net to check
            expected_transitions: Expected number of transitions
            expected_places: Expected number of places
            expected_arcs: Expected number of arcs
        """
        self.assertEqual(
            len(subnet.transitions),
            expected_transitions,
            f"Expected {expected_transitions} transitions, got {len(subnet.transitions)}",
        )
        self.assertEqual(
            len(subnet.places),
            expected_places,
            f"Expected {expected_places} places, got {len(subnet.places)}",
        )
        self.assertEqual(
            len(subnet.arcs),
            expected_arcs,
            f"Expected {expected_arcs} arcs, got {len(subnet.arcs)}",
        )

    # Test Cases - Behavioural requirements

    def test_simple_subnet_extraction(self) -> None:
        """
        REQ-PROJECT-SUBNET:
            Given a Petri net and a set of subnet transitions, the function returns a new Petri net
            containing exactly those transitions and the required places/arcs to preserve their connectivity.

        REQ-BOUNDARIES-DISTINCT:
            If start_places and end_places differ, the returned start and end places must be different objects.

        REQ-IGNORE-NON-SUBNET-ARCS:
            Arcs that do not touch any subnet transition must not appear in the projected subnet.

        This test uses a simple sequence and projects only the first transition.
        """

        net, p1, _p3 = self._create_simple_sequence_net()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        p2 = [p for p in net.places if p.name == "p2"][0]

        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1},
            {p1},
            {p2},
        )

        self._assert_subnet_structure(
            subnet,
            expected_transitions=1,
            expected_places=2,
            expected_arcs=2,
        )

        self.assertIsNotNone(new_start)
        self.assertIsNotNone(new_end)
        self.assertIsNot(
            new_start,
            new_end,
            "Start and end place must be distinct when boundary sets differ.",
        )

        subnet_t1 = list(subnet.transitions)[0]
        self.assertEqual(subnet_t1.label, "t1")

        has_start_arc = any(arc.source == new_start and arc.target == subnet_t1 for arc in subnet.arcs)
        has_end_arc = any(arc.source == subnet_t1 and arc.target == new_end for arc in subnet.arcs)
        self.assertTrue(has_start_arc, "Projected subnet must contain arc from start place to t1.")
        self.assertTrue(has_end_arc, "Projected subnet must contain arc from t1 to end place.")

    def test_same_start_and_end_place(self) -> None:
        """
        REQ-BOUNDARIES-SAME:
            If start_places == end_places, the returned start and end places must be the same object.

        This test projects a loop fragment where the boundary place is both the start and end.
        """

        net, p1 = self._create_loop_net()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        t2 = [t for t in net.transitions if t.label == "t2"][0]

        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1, t2},
            {p1},
            {p1},
        )

        self.assertIs(
            new_start,
            new_end,
            "Start and end must be identical when boundary sets are the same.",
        )

        self._assert_subnet_structure(
            subnet,
            expected_transitions=2,
            expected_places=2,
            expected_arcs=4,
        )

    def test_reuse_mapped_nodes(self) -> None:
        """
        REQ-NODE-REUSE:
            When multiple subnet transitions share the same boundary places, the projected subnet must not
            duplicate those places (i.e., the shared boundary is represented by a single place instance).

        This test uses a parallel structure where both transitions share the same start and end places.
        """

        net, p1, p2 = self._create_parallel_net()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        t2 = [t for t in net.transitions if t.label == "t2"][0]

        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1, t2},
            {p1},
            {p2},
        )

        self._assert_subnet_structure(
            subnet,
            expected_transitions=2,
            expected_places=2,
            expected_arcs=4,
        )

        arcs_from_start = [arc for arc in subnet.arcs if arc.source == new_start]
        arcs_to_end = [arc for arc in subnet.arcs if arc.target == new_end]

        self.assertEqual(len(arcs_from_start), 2, "Both transitions must connect from the single start place.")
        self.assertEqual(len(arcs_to_end), 2, "Both transitions must connect to the single end place.")
        self.assertEqual(
            len(subnet.places),
            2,
            "Shared boundary places must not be duplicated in the projected subnet.",
        )

    def test_projection_preserves_subnet_structure(self) -> None:
        """
        REQ-INTERNAL-PLACE-CLONING:
            If a selected subnet requires internal (non-boundary) places to preserve connectivity, those
            places must be created in the projected subnet.

        REQ-ARC-RECONSTRUCTION:
            The projected subnet must preserve the order/flow between the selected transitions via the
            internal place(s).

        This test projects a two-transition sequence with one internal place.
        """

        net, p_start, _p_internal, p_end = self._create_net_for_internal_places()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        t2 = [t for t in net.transitions if t.label == "t2"][0]

        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1, t2},
            {p_start},
            {p_end},
        )

        self._assert_subnet_structure(
            subnet,
            expected_transitions=2,
            expected_places=3,
            expected_arcs=4,
        )

        internal_places = [p for p in subnet.places if p != new_start and p != new_end]
        self.assertEqual(len(internal_places), 1, "Projected subnet must contain exactly one internal place.")
        subnet_internal = internal_places[0]

        subnet_t1 = [t for t in subnet.transitions if t.label == "t1"][0]
        subnet_t2 = [t for t in subnet.transitions if t.label == "t2"][0]

        self.assertTrue(any(arc.source == new_start and arc.target == subnet_t1 for arc in subnet.arcs))
        self.assertTrue(any(arc.source == subnet_t1 and arc.target == subnet_internal for arc in subnet.arcs))
        self.assertTrue(any(arc.source == subnet_internal and arc.target == subnet_t2 for arc in subnet.arcs))
        self.assertTrue(any(arc.source == subnet_t2 and arc.target == new_end for arc in subnet.arcs))


if __name__ == "__main__":
    unittest.main()