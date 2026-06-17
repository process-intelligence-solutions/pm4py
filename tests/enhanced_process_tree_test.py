import unittest
import pandas as pd
from pm4py.algo.discovery.log_refinement import algorithm as log_refinement_discovery
from pm4py.objects.conversion.process_tree.variants import to_petri_net
from pm4py.objects.petri_net.obj import ResetNet
from pm4py.objects.process_tree.obj import EnhancedProcessTree, Operator


class EnhancedProcessTreeTest(unittest.TestCase):

    def _build_stop_tree(self):
        """Builds the sequence ->( 'A', stop('B'), 'C' )"""
        root = EnhancedProcessTree(operator=Operator.SEQUENCE)
        node_a = EnhancedProcessTree(label='A', parent=root)
        node_b = EnhancedProcessTree(label='B', stop=True, parent=root)
        node_c = EnhancedProcessTree(label='C', parent=root)
        root.children = [node_a, node_b, node_c]
        return root

    def _build_start_tree(self):
        """Builds the sequence ->( 'A', start('B'), 'C' )"""
        root = EnhancedProcessTree(operator=Operator.SEQUENCE)
        node_a = EnhancedProcessTree(label='A', parent=root)
        node_b = EnhancedProcessTree(label='B', start=True, parent=root)
        node_c = EnhancedProcessTree(label='C', parent=root)
        root.children = [node_a, node_b, node_c]
        return root

    def _build_skip_tree(self):
        """Builds the sequence ->( 'A', skip('B'), 'C' )"""
        root = EnhancedProcessTree(operator=Operator.SEQUENCE)
        node_a = EnhancedProcessTree(label='A', parent=root)
        node_b = EnhancedProcessTree(label='B', skip=True, parent=root)
        node_c = EnhancedProcessTree(label='C', parent=root)
        root.children = [node_a, node_b, node_c]
        return root

    def _build_parallel_skip_tree(self):
        """Builds: ->( 'A', +( 'B', skip('C') ), 'D' )"""
        root = EnhancedProcessTree(operator=Operator.SEQUENCE)
        node_a = EnhancedProcessTree(label='A', parent=root)

        and_node = EnhancedProcessTree(operator=Operator.PARALLEL, parent=root)
        node_b = EnhancedProcessTree(label='B', parent=and_node)
        node_c = EnhancedProcessTree(label='C', skip=True, parent=and_node)
        and_node.children = [node_b, node_c]

        node_d = EnhancedProcessTree(label='D', parent=root)
        root.children = [node_a, and_node, node_d]
        return root

    def _build_parallel_stop_tree(self):
        """Builds: ->( 'A', +( 'B', stop('C') ), 'D' )"""
        root = EnhancedProcessTree(operator=Operator.SEQUENCE)
        node_a = EnhancedProcessTree(label='A', parent=root)

        and_node = EnhancedProcessTree(operator=Operator.PARALLEL, parent=root)
        node_b = EnhancedProcessTree(label='B', parent=and_node)
        node_c = EnhancedProcessTree(label='C', stop=True, parent=and_node)
        and_node.children = [node_b, node_c]

        node_d = EnhancedProcessTree(label='D', parent=root)
        root.children = [node_a, and_node, node_d]
        return root

    def _build_parallel_start_tree(self):
        """Builds: ->( 'A', +( 'B', start('C') ), 'D' )"""
        root = EnhancedProcessTree(operator=Operator.SEQUENCE)
        node_a = EnhancedProcessTree(label='A', parent=root)

        and_node = EnhancedProcessTree(operator=Operator.PARALLEL, parent=root)
        node_b = EnhancedProcessTree(label='B', parent=and_node)
        node_c = EnhancedProcessTree(label='C', start=True, parent=and_node)
        and_node.children = [node_b, node_c]

        node_d = EnhancedProcessTree(label='D', parent=root)
        root.children = [node_a, and_node, node_d]
        return root

    def _generate_mock_log(self):
        """Helper method to generate a fragmented log for testing."""
        traces = [
            ['a', 'b', 'c', 'd', 'e'],
            ['c', 'd', 'e']
        ]
        data = []
        for case_id, trace in enumerate(traces):
            for i, activity in enumerate(trace):
                data.append({
                    "case:concept:name": str(case_id),
                    "concept:name": activity,
                    "time:timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=i)
                })
        return pd.DataFrame(data)

    def test_discovery_annotations(self):
        """Tests if the discovery successfully injects the point properties."""
        log = self._generate_mock_log()
        enhanced_tree = log_refinement_discovery.apply(log)

        c_node_found = False
        for node in enhanced_tree.children:
            if node.label == 'c':
                c_node_found = True
                self.assertTrue(node.start, "Node 'c' should be annotated as a START point.")
                self.assertFalse(node.skip, "Node 'c' should NOT have a skip annotation.")

        self.assertTrue(c_node_found, "Node 'c' was lost during discovery.")

    def test_print_compatibility(self):
        """Tests if the custom tree still works with standard PM4Py base functions."""
        log = self._generate_mock_log()
        enhanced_tree = log_refinement_discovery.apply(log)

        tree_string = enhanced_tree.to_string()
        self.assertIn("(start)'c'", tree_string, "The to_string override failed to print the annotation.")

    def test_sequence_stop_annotation(self):
        """
        Tests if a 'stop' annotation on the middle node of a sequence
        correctly generates a path to the final place.
        """
        tree = self._build_stop_tree()
        net, im, fm = to_petri_net.apply(tree)

        final_places = list(fm.keys())
        self.assertEqual(len(final_places), 1, "There should be exactly one final place in the network.")
        p_final = final_places[0]

        b_transitions = [t for t in net.transitions if t.label == 'B']
        self.assertEqual(len(b_transitions), 1, "Transition 'B' was lost or duplicated during conversion.")
        t_b = b_transitions[0]

        b_out_arcs = list(t_b.out_arcs)
        self.assertEqual(len(b_out_arcs), 1, "Transition 'B' should output to exactly one place in a sequence.")
        p_after_b = b_out_arcs[0].target

        stop_path_created = False

        for arc in p_after_b.out_arcs:
            target_trans = arc.target

            # Check if this is a silent transition (label is None)
            if target_trans.label is None:
                # Check if this silent transition points to our global final place
                for out_arc in target_trans.out_arcs:
                    if out_arc.target == p_final:
                        stop_path_created = True
                        break

        self.assertTrue(stop_path_created,
                        "The converter failed to create a silent routing transition from 'B' to the final place.")

    def test_sequence_start_annotation(self):
        """
        Tests if a 'start' annotation on the middle node of a sequence
        correctly generates a path from the global initial place.
        """
        tree = self._build_start_tree()
        net, im, fm = to_petri_net.apply(tree)

        initial_places = list(im.keys())
        self.assertEqual(len(initial_places), 1, "There should be exactly one initial place in the network.")
        p_source = initial_places[0]

        b_transitions = [t for t in net.transitions if t.label == 'B']
        self.assertEqual(len(b_transitions), 1, "Transition 'B' was lost or duplicated during conversion.")
        t_b = b_transitions[0]

        b_in_arcs = list(t_b.in_arcs)
        self.assertEqual(len(b_in_arcs), 1, "Transition 'B' should have exactly one input place in a sequence.")
        p_before_b = b_in_arcs[0].source

        start_path_created = False

        for arc in p_source.out_arcs:
            target_trans = arc.target

            # Check if this is a silent transition with our custom 'tau_start' name
            if target_trans.label is None and "tau_start" in target_trans.name:
                # Check if this silent transition points directly to the place before B
                for out_arc in target_trans.out_arcs:
                    if out_arc.target == p_before_b:
                        start_path_created = True
                        break

        self.assertTrue(
            start_path_created,
            "The converter failed to create a silent routing transition from the global source to 'B'."
        )

    def test_sequence_skip_annotation(self):
        """
        Tests if a 'skip' annotation on the middle node of a sequence
        correctly generates a path to the parent's final place, bypassing C.
        """
        tree = self._build_skip_tree()

        net, im, fm = to_petri_net.apply(tree)

        b_transitions = [t for t in net.transitions if t.label == 'B']
        c_transitions = [t for t in net.transitions if t.label == 'C']

        self.assertEqual(len(b_transitions), 1, "Transition 'B' was not found.")
        self.assertEqual(len(c_transitions), 1, "Transition 'C' was not found.")

        t_b = b_transitions[0]
        t_c = c_transitions[0]

        b_out_arcs = list(t_b.out_arcs)
        self.assertEqual(len(b_out_arcs), 1, "Transition 'B' should output to exactly one place.")
        p_after_b = b_out_arcs[0].target

        c_out_arcs = list(t_c.out_arcs)
        self.assertEqual(len(c_out_arcs), 1, "Transition 'C' should output to exactly one place.")
        p_after_c = c_out_arcs[0].target

        skip_path_created = False

        for arc in p_after_b.out_arcs:
            target_trans = arc.target

            # Check if this is a silent transition with our custom 'tau_skip' name
            if target_trans.label is None and target_trans.name and "tau_skip" in target_trans.name:
                # Check if this silent transition points directly to the place after C
                for out_arc in target_trans.out_arcs:
                    if out_arc.target == p_after_c:
                        skip_path_created = True
                        break

        self.assertTrue(
            skip_path_created,
            "The converter failed to create a silent routing transition from 'B' to the parent's end place."
        )

    def test_parallel_skip_reset_arcs(self):
        """
        Tests if a 'skip' inside an AND block correctly generates Reset Arcs
        to clear tokens from concurrent branches.
        """
        tree = self._build_parallel_skip_tree()
        net, im, fm = to_petri_net.apply(tree)

        skip_transitions = [t for t in net.transitions if t.label is None and t.name and "tau_skip" in t.name]
        self.assertEqual(len(skip_transitions), 1, "The tau_skip bypass was not created inside the AND block.")
        t_skip = skip_transitions[0]

        reset_arcs = [arc for arc in t_skip.in_arcs if isinstance(arc, ResetNet.ResetArc)]

        self.assertGreater(
            len(reset_arcs), 0,
            "No Reset Arcs found! The skip bypass will deadlock the Petri net because concurrent tokens are left behind."
        )

    def test_parallel_stop_reset_arcs(self):
        """
        Tests if a 'stop' inside an AND block correctly generates Reset Arcs
        and routes directly to the global sink.
        """
        tree = self._build_parallel_stop_tree()
        net, im, fm = to_petri_net.apply(tree)

        p_final = list(fm.keys())[0]

        stop_transitions = [t for t in net.transitions if t.label is None and t.name and "tau_stop" in t.name]
        self.assertEqual(len(stop_transitions), 1, "The tau_stop bypass was not created inside the AND block.")
        t_stop = stop_transitions[0]

        reset_arcs = [arc for arc in t_stop.in_arcs if isinstance(arc, ResetNet.ResetArc)]
        self.assertGreater(len(reset_arcs), 0, "No Reset Arcs found for the stop bypass.")

        routes_to_sink = any(arc.target == p_final for arc in t_stop.out_arcs)
        self.assertTrue(routes_to_sink, "The stop bypass inside the AND block does not route to the global sink.")

    def test_parallel_start_split(self):
        """
        Tests if a 'start' inside an AND block correctly triggers the creation of
        a tau_start_split transition from the global source to prime all branches.
        """
        tree = self._build_parallel_start_tree()
        net, im, fm = to_petri_net.apply(tree)

        p_source = list(im.keys())[0]

        start_split_transitions = [t for t in net.transitions if
                                   t.label is None and t.name and "tau_start_split" in t.name]
        self.assertEqual(len(start_split_transitions), 1,
                         "The AND block failed to generate the tau_start_split transition.")
        t_start_split = start_split_transitions[0]

        takes_input_from_source = any(arc.source == p_source for arc in t_start_split.in_arcs)
        self.assertTrue(takes_input_from_source, "The tau_start_split is not connected to the global source.")

        self.assertGreaterEqual(len(t_start_split.out_arcs), 2,
                                "The tau_start_split did not split to power the concurrent branches.")


if __name__ == "__main__":
    unittest.main()
