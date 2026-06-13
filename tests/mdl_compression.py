import unittest

from pm4py.algo.discovery.mdl_compression.trace_compressor import TraceCompressor
from pm4py.algo.discovery.mdl_compression.compression_rules import rule_duplication


class MDLCompressionTest(unittest.TestCase):

    def _convert_to_tuple_log(self, list_of_lists):
        """Helper to convert test arrays into the {tuple: freq} format"""
        return {tuple(t): 1 for t in list_of_lists}

    def test_prefix_rule(self):
        """Tests that a prefix is absorbed and annotates a stop point."""
        log = self._convert_to_tuple_log([['a', 'b'], ['a', 'b', 'c', 'd']])
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        self.assertEqual(set(final_log.keys()), {('a', 'b', 'c', 'd')})
        self.assertIn('stop', annotations.get('b', set()))
        self.assertNotIn('start', annotations.get('b', set()))

    def test_suffix_rule(self):
        """Tests that a suffix is absorbed and annotates a start point."""
        log = self._convert_to_tuple_log([['c', 'd'], ['a', 'b', 'c', 'd']])
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        self.assertEqual(set(final_log.keys()), {('a', 'b', 'c', 'd')})
        self.assertIn('start', annotations.get('c', set()))

    def test_infix_rule(self):
        """Tests that an infix is absorbed and annotates both start and stop."""
        log = self._convert_to_tuple_log([['b', 'c'], ['a', 'b', 'c', 'd']])
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        self.assertEqual(set(final_log.keys()), {('a', 'b', 'c', 'd')})
        self.assertIn('start', annotations.get('b', set()))
        self.assertIn('stop', annotations.get('c', set()))

    def test_concatenation(self):
        """Tests fusing two traces with an edge-anchored overlap."""
        log = self._convert_to_tuple_log([['a', 'b', 'c', 'd'], ['d', 'e', 'f']])
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        self.assertEqual(set(final_log.keys()), {('a', 'b', 'c', 'd', 'e', 'f')})
        self.assertIn('stop', annotations.get('d', set()))
        self.assertIn('start', annotations.get('d', set()))

    def test_completion(self):
        """Tests completing a trace that ended prematurely but shares an internal pivot."""
        log = self._convert_to_tuple_log([['a', 'b', 'd'], ['x', 'y', 'd', 'e', 'f']])
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        expected_traces = {('a', 'b', 'd', 'e', 'f'), ('x', 'y', 'd', 'e', 'f')}
        self.assertEqual(set(final_log.keys()), expected_traces)
        self.assertIn('stop', annotations.get('d', set()))

    def test_skip_rule_concurrent_subsets(self):
        """Tests that subsets of an AND block are absorbed to create skip points."""
        raw_traces = [
            ['s', 'a', 'b', 'c', 'd', 'f', 'g', 'e'],
            ['s', 'c', 'd', 'e'],
        ]
        log = self._convert_to_tuple_log(raw_traces)
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        self.assertEqual(set(final_log.keys()), {('s', 'a', 'b', 'c', 'd', 'f', 'g', 'e')})
        self.assertIn('skip', annotations.get('d', set()))

    def test_duplication(self):
        """Tests cross-multiplying traces on a shared internal pivot."""
        raw_traces = [
            ['a', 'b', 'P', 'x', 'y'],
            ['m', 'n', 'P', 'u', 'v']
        ]
        log = self._convert_to_tuple_log(raw_traces)
        compressor = TraceCompressor(log)

        compressor.active_rules.append(rule_duplication)
        final_log, _ = compressor.run()

        expected_traces = {
            ('a', 'b', 'P', 'x', 'y'),
            ('m', 'n', 'P', 'u', 'v'),
            ('a', 'b', 'P', 'u', 'v'),
            ('m', 'n', 'P', 'x', 'y')
        }
        self.assertEqual(set(final_log.keys()), expected_traces)

    def test_emergent_rule(self):
        """
        Tests Emergent Unification.
        Proves that Prefix and Completion rules naturally chain together across
        multiple iterations to resolve complex multi-branching fragments.
        """
        raw_traces = [
            ['x', 'y'],
            ['x', 'y', 'd', 'e', 'f'],
            ['a', 'b'],
            ['a', 'b', 'd']
        ]
        log = self._convert_to_tuple_log(raw_traces)
        compressor = TraceCompressor(log)
        final_log, annotations = compressor.run()

        expected_traces = {('x', 'y', 'd', 'e', 'f'), ('a', 'b', 'd', 'e', 'f')}
        self.assertEqual(set(final_log.keys()), expected_traces)

        self.assertIn('stop', annotations.get('y', set()))
        self.assertIn('stop', annotations.get('b', set()))
        self.assertIn('stop', annotations.get('d', set()))


if __name__ == '__main__':
    unittest.main()