"""
Test suite for the apply_partial_order_projection function.

This module tests the apply_partial_order_projection function from
pm4py.objects.conversion.wf_net.variants.to_powl, which extracts a subnet
from a Petri net based on a set of transitions and boundary places.

The function has the following signature:
    apply_partial_order_projection(
        net: PetriNet,
        subnet_transitions: Set[PetriNet.Transition],
        start_places: Set[PetriNet.Place],
        end_places: Set[PetriNet.Place]
    ) -> Tuple[PetriNet, PetriNet.Place, PetriNet.Place]

Branch coverage tracking:
    The function contains 17 branches (IDs 0-16) that need to be tested.
    These 4 tests cover 11 out of 17 branches (65% coverage):
    - Branches covered: 2, 3, 6, 7, 8, 10, 11, 12, 14, 15, 16
    - Branches not covered: 0, 1, 4, 5, 9, 13
"""

import unittest

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.conversion.wf_net.variants.to_powl import apply_partial_order_projection
from assignment_utilities.manual_coverage_helper import init_function, report


class PartialOrderProjectionTest(unittest.TestCase):
    """Test cases for the apply_partial_order_projection function."""

    # @classmethod
    # def setUpClass(cls):
    #     init_function("apply_partial_order_projection", slots=20)
    #
    # @classmethod
    # def tearDownClass(cls):
    #     print("\n" + "="*80)
    #     print("COVERAGE REPORT FOR apply_partial_order_projection")
    #     print("="*80)
    #     print(report(only_hit=True))
    #     print("="*80)

    # Helper Methods

    def _create_simple_sequence_net(self) -> tuple[PetriNet, PetriNet.Place, PetriNet.Place]:
        """
        Create a simple sequential Petri net: p1 -> t1 -> p2 -> t2 -> p3

        Returns:
            Tuple of (net, start_place, end_place)
        """
        net = PetriNet("simple_sequence")

        # Create places
        p1 = PetriNet.Place("p1")
        p2 = PetriNet.Place("p2")
        p3 = PetriNet.Place("p3")
        net.places.add(p1)
        net.places.add(p2)
        net.places.add(p3)

        # Create transitions
        t1 = PetriNet.Transition("t1", "t1")
        t2 = PetriNet.Transition("t2", "t2")
        net.transitions.add(t1)
        net.transitions.add(t2)

        # Add arcs
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

        # Both transitions share p1 as input and p2 as output
        petri_utils.add_arc_from_to(p1, t1, net)
        petri_utils.add_arc_from_to(p1, t2, net)
        petri_utils.add_arc_from_to(t1, p2, net)
        petri_utils.add_arc_from_to(t2, p2, net)

        return net, p1, p2

    def _create_loop_net(self) -> tuple[PetriNet, PetriNet.Place]:
        """
        Create a loop: p1 -> t1 -> p2 -> t2 -> p1

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
        petri_utils.add_arc_from_to(t2, p1, net)  # Loop back!

        return net, p1

    def _create_net_for_internal_places(self) -> tuple[PetriNet, PetriNet.Place, PetriNet.Place, PetriNet.Place]:
        """
        Create: p_start -> t1 -> p_internal -> t2 -> p_end

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

    def _assert_subnet_structure(self, subnet: PetriNet, expected_transitions: int,
                                 expected_places: int, expected_arcs: int):
        """
        Assert that a subnet has the expected structure.

        Args:
            subnet: The Petri net to check
            expected_transitions: Expected number of transitions
            expected_places: Expected number of places
            expected_arcs: Expected number of arcs
        """
        self.assertEqual(len(subnet.transitions), expected_transitions,
                        f"Expected {expected_transitions} transitions, got {len(subnet.transitions)}")
        self.assertEqual(len(subnet.places), expected_places,
                        f"Expected {expected_places} places, got {len(subnet.places)}")
        self.assertEqual(len(subnet.arcs), expected_arcs,
                        f"Expected {expected_arcs} arcs, got {len(subnet.arcs)}")

    # Test Cases - Basic Functionality

    def test_simple_subnet_extraction(self):
        """
        Test basic subnet extraction with a simple sequence.

        This should cover:
        - Branch 3: start_places != end_places
        - Branch 6: arc considered
        - Branch 8: source not in node_map (first time)
        - Branch 12: target not in node_map (first time)
        - Branch 15: arc added
        - Branch 16: arc ignored (arcs from t2 don't touch subnet)
        """
        # Create test net: p1 -> t1 -> p2 -> t2 -> p3
        net, p1, p3 = self._create_simple_sequence_net()

        # Get specific nodes
        t1 = [t for t in net.transitions if t.label == "t1"][0]
        p2 = [p for p in net.places if p.name == "p2"][0]

        # Extract subnet containing only t1, with p1 as start and p2 as end
        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1},      # Only t1 in subnet
            {p1},      # Start boundary
            {p2}       # End boundary
        )

        # Assertions
        self._assert_subnet_structure(subnet,
                                      expected_transitions=1,
                                      expected_places=2,   # cloned p1 and p2 (boundaries)
                                      expected_arcs=2)     # p1->t1 and t1->p2

        # Verify start and end places are different (branch 3)
        self.assertIsNotNone(new_start)
        self.assertIsNotNone(new_end)
        self.assertIsNot(new_start, new_end)

        # Verify the transition is correctly cloned
        subnet_t1 = list(subnet.transitions)[0]
        self.assertEqual(subnet_t1.label, "t1")

        # Verify arcs exist (branches 6, 15)
        has_start_arc = any(arc.source == new_start and arc.target == subnet_t1
                           for arc in subnet.arcs)
        has_end_arc = any(arc.source == subnet_t1 and arc.target == new_end
                         for arc in subnet.arcs)
        self.assertTrue(has_start_arc, "Arc from start to t1 should exist")
        self.assertTrue(has_end_arc, "Arc from t1 to end should exist")

    def test_same_start_and_end_place(self):
        """
        Test projection when start_places == end_places (loop structure).

        This should cover:
        - Branch 2: start_places == end_places
        """
        # Create loop net: p1 -> t1 -> p2 -> t2 -> p1
        net, p1 = self._create_loop_net()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        t2 = [t for t in net.transitions if t.label == "t2"][0]

        # Extract subnet with both transitions, where p1 is both start and end
        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1, t2},   # Both transitions in the loop
            {p1},       # Start place
            {p1}        # End place (SAME as start!)
        )

        # Key assertion: start and end should be the same place (branch 2)
        self.assertIs(new_start, new_end,
                     "Start and end place should be identical when boundaries are the same")

        # Verify subnet structure
        self._assert_subnet_structure(subnet,
                                      expected_transitions=2,
                                      expected_places=2,   # p1 (start/end) and p2 (internal)
                                      expected_arcs=4)     # p1->t1, t1->p2, p2->t2, t2->p1

    def test_reuse_mapped_nodes(self):
        """
        Test that nodes already in node_map are reused correctly.

        This should cover:
        - Branch 7: source found in node_map
        - Branch 11: target found in node_map

        In a parallel structure where p1 feeds both t1 and t2, and both feed into p2:
        - First arc p1->t1: p1 is not in map (branch 8)
        - Second arc p1->t2: p1 is already mapped (branch 7)
        - First arc t1->p2: p2 is not in map (branch 12)
        - Second arc t2->p2: p2 is already mapped (branch 11)
        """
        # Create parallel net with shared places
        net, p1, p2 = self._create_parallel_net()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        t2 = [t for t in net.transitions if t.label == "t2"][0]

        # Extract subnet with both transitions
        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1, t2},   # Both transitions share p1 and p2
            {p1},       # Start boundary
            {p2}        # End boundary
        )

        # Verify structure
        self._assert_subnet_structure(subnet,
                                      expected_transitions=2,
                                      expected_places=2,   # p1 and p2 (both boundaries)
                                      expected_arcs=4)     # p1->t1, p1->t2, t1->p2, t2->p2

        # Verify that both transitions share the same start and end places
        # (this confirms node reuse worked correctly)
        arcs_from_start = [arc for arc in subnet.arcs if arc.source == new_start]
        arcs_to_end = [arc for arc in subnet.arcs if arc.target == new_end]

        self.assertEqual(len(arcs_from_start), 2, "Both transitions should connect from start")
        self.assertEqual(len(arcs_to_end), 2, "Both transitions should connect to end")

        # Verify only 2 places exist (not 4), confirming reuse
        self.assertEqual(len(subnet.places), 2,
                        "Should only have 2 places (boundaries), not duplicates")

    def test_projection_preserves_subnet_structure(self):
        """
        Test that the projected subnet preserves the structure of selected transitions.

        This specifically tests internal place cloning:
        - Branch 10: source not boundary => clone (p_internal as source)
        - Branch 14: target not boundary => clone (p_internal as target)

        Verify that:
        - All subnet transitions are cloned
        - Internal places are cloned
        - Arcs are correctly reconstructed
        - Boundary places are replaced with single start/end places
        """
        # Create: p_start -> t1 -> p_internal -> t2 -> p_end
        net, p_start, p_internal, p_end = self._create_net_for_internal_places()

        t1 = [t for t in net.transitions if t.label == "t1"][0]
        t2 = [t for t in net.transitions if t.label == "t2"][0]

        # Extract subnet with both transitions
        # p_start and p_end are boundaries, p_internal is internal and should be cloned
        subnet, new_start, new_end = apply_partial_order_projection(
            net,
            {t1, t2},       # Both transitions
            {p_start},      # Boundary start
            {p_end}         # Boundary end
        )

        # Verify structure
        self._assert_subnet_structure(subnet,
                                      expected_transitions=2,
                                      expected_places=3,   # start, internal (cloned), end
                                      expected_arcs=4)     # start->t1, t1->internal, internal->t2, t2->end

        # Find the internal place in the subnet (not start, not end)
        internal_places = [p for p in subnet.places
                          if p != new_start and p != new_end]
        self.assertEqual(len(internal_places), 1,
                        "Should have exactly one internal place")

        subnet_internal = internal_places[0]
        subnet_t1 = [t for t in subnet.transitions if t.label == "t1"][0]
        subnet_t2 = [t for t in subnet.transitions if t.label == "t2"][0]

        # Verify arc connectivity
        # start -> t1
        self.assertTrue(any(arc.source == new_start and arc.target == subnet_t1
                           for arc in subnet.arcs))

        # t1 -> internal (branch 14: target not boundary, clone it)
        self.assertTrue(any(arc.source == subnet_t1 and arc.target == subnet_internal
                           for arc in subnet.arcs))

        # internal -> t2 (branch 10: source not boundary, clone it)
        self.assertTrue(any(arc.source == subnet_internal and arc.target == subnet_t2
                           for arc in subnet.arcs))

        # t2 -> end
        self.assertTrue(any(arc.source == subnet_t2 and arc.target == new_end
                           for arc in subnet.arcs))


if __name__ == "__main__":
    unittest.main()

