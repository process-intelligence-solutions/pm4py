import datetime
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import ExitStack
from unittest import mock

import pandas as pd

import pm4py
from pm4py.objects.log.obj import Event, EventLog, Trace
from pm4py.objects.org.sna.obj import SNA


class VisualizationFacadeDeepCoverageTest(unittest.TestCase):
    def test_basic_powl_title_parameters(self):
        from pm4py.objects.powl.obj import Transition
        from pm4py.util import constants
        from pm4py.visualization.powl.variants import basic

        title = 'Review <A&B> "approval"'
        cases = (
            (False, {}, []),
            (True, {"enable_graph_title": False, "graph_title": "Hidden"}, []),
            (False, {basic.Parameters.ENABLE_GRAPH_TITLE: True}, ["POWL model"]),
            (False, {"enable_graph_title": True, "graph_title": title}, [title]),
            (True, {}, ["POWL model"]),
        )
        for default_enabled, parameters, expected in cases:
            with self.subTest(default=default_enabled, parameters=parameters):
                with mock.patch.object(constants, "DEFAULT_ENABLE_GRAPH_TITLES", default_enabled):
                    graph = basic.apply(Transition("A"), parameters=parameters)
                svg = ET.fromstring(graph.pipe(format="svg"))
                labels = svg.findall("./svg:g/svg:text", {"svg": "http://www.w3.org/2000/svg"})
                self.assertEqual(expected, ["".join(label.itertext()) for label in labels])

    def test_save_vis_powl_keeps_the_requested_title(self):
        from pm4py.objects.powl.obj import Transition

        title = 'Review <A&B> "approval"'
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "powl.svg")
            pm4py.save_vis_powl(Transition("A"), path, graph_title=title)
            svg = ET.parse(path).getroot()
        labels = svg.findall("./svg:g/svg:text", {"svg": "http://www.w3.org/2000/svg"})
        self.assertEqual([title], ["".join(label.itertext()) for label in labels])

    @staticmethod
    def _path(*parts):
        return os.path.join(os.path.dirname(__file__), 'input_data', *parts)

    @staticmethod
    def _log_data():
        base = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        rows, log = [], EventLog()
        for case_id, activities in (('1', ('A', 'B', 'C')), ('2', ('A', 'C', 'B'))):
            trace = Trace(attributes={'concept:name': case_id})
            for index, activity in enumerate(activities):
                event = Event({
                    'concept:name': activity,
                    'time:timestamp': base + datetime.timedelta(
                        days=int(case_id), hours=index * int(case_id)
                    ),
                    'org:resource': 'r' + str(index % 2),
                })
                trace.append(event)
                rows.append({'case:concept:name': case_id, **event})
            log.append(trace)
        return log, pd.DataFrame(rows)

    @staticmethod
    def _patch_visualizer_io(stack):
        from pm4py.visualization.align_table import visualizer as align_vis
        from pm4py.visualization.bpmn import visualizer as bpmn_vis
        from pm4py.visualization.dfg import visualizer as dfg_vis
        from pm4py.visualization.footprints import visualizer as fp_vis
        from pm4py.visualization.graphs import visualizer as graphs_vis
        from pm4py.visualization.heuristics_net import visualizer as heu_vis
        from pm4py.visualization.network_analysis import visualizer as network_vis
        from pm4py.visualization.ocel.object_graph import visualizer as object_vis
        from pm4py.visualization.ocel.ocdfg import visualizer as ocdfg_vis
        from pm4py.visualization.ocel.ocpn import visualizer as ocpn_vis
        from pm4py.visualization.performance_spectrum import visualizer as spectrum_vis
        from pm4py.visualization.powl import visualizer as powl_vis
        from pm4py.visualization.sna import visualizer as sna_vis
        from pm4py.visualization.transition_system import visualizer as ts_vis
        from pm4py.visualization.trie import visualizer as trie_vis

        for module in (
            align_vis, bpmn_vis, dfg_vis, fp_vis, graphs_vis, heu_vis,
            network_vis, object_vis, ocdfg_vis, ocpn_vis, spectrum_vis,
            powl_vis, sna_vis, ts_vis, trie_vis,
        ):
            if hasattr(module, 'view'):
                stack.enter_context(mock.patch.object(module, 'view', return_value='viewed'))
            if hasattr(module, 'save'):
                stack.enter_context(mock.patch.object(module, 'save', return_value='saved'))

    def test_graph_model_and_organizational_facades(self):
        log, dataframe = self._log_data()
        performance_dfg, starts, ends = pm4py.discover_performance_dfg(dataframe)
        heuristics = pm4py.discover_heuristics_net(dataframe)
        bpmn = pm4py.convert_to_bpmn(pm4py.parse_process_tree("->( 'A', X( 'B', 'C' ) )"))
        sna = SNA({('r0', 'r1'): 2.0}, True)

        with ExitStack() as stack, tempfile.TemporaryDirectory() as directory:
            self._patch_visualizer_io(stack)
            pm4py.view_performance_dfg(
                performance_dfg, starts, ends, format='svg', graph_title='Performance'
            )
            self.assertEqual('saved', pm4py.save_vis_performance_dfg(
                performance_dfg, starts, ends, os.path.join(directory, 'performance.svg'),
                graph_title='Performance'
            ))
            for variant in ('classic', 'dagrejs', 'bpmnio_auto_layout'):
                pm4py.view_bpmn(bpmn, variant_str=variant, graph_title='BPMN')
                self.assertEqual('saved', pm4py.save_vis_bpmn(
                    bpmn, os.path.join(directory, f'{variant}.svg'), variant_str=variant,
                    graph_title='BPMN'
                ))
            pm4py.view_heuristics_net(heuristics, format='svg', graph_title='Heuristics')
            self.assertEqual('saved', pm4py.save_vis_heuristics_net(
                heuristics, os.path.join(directory, 'heuristics.svg'), graph_title='Heuristics'
            ))
            for variant in ('networkx', 'pyvis'):
                # Avoid the optional pyvis backend while still checking facade routing.
                from pm4py.visualization.sna import visualizer as sna_visualizer
                with mock.patch.object(sna_visualizer, 'apply', return_value='sna'):
                    pm4py.view_sna(sna, variant_str=variant)
                    self.assertEqual('saved', pm4py.save_vis_sna(
                        sna, os.path.join(directory, f'sna-{variant}.png'), variant_str=variant
                    ))

    def test_statistical_graphs_spectrum_and_distributions(self):
        log, dataframe = self._log_data()
        with ExitStack() as stack, tempfile.TemporaryDirectory() as directory:
            self._patch_visualizer_io(stack)
            pm4py.view_case_duration_graph(log, format='svg', graph_title='Duration')
            self.assertEqual('saved', pm4py.save_vis_case_duration_graph(
                dataframe, os.path.join(directory, 'duration.svg'), graph_title='Duration'
            ))
            pm4py.view_events_per_time_graph(log, format='svg', graph_title='Events')
            self.assertEqual('saved', pm4py.save_vis_events_per_time_graph(
                dataframe, os.path.join(directory, 'events.svg'), graph_title='Events'
            ))
            pm4py.view_performance_spectrum(
                log, ['A', 'B'], format='svg', graph_title='Spectrum'
            )
            self.assertEqual('saved', pm4py.save_vis_performance_spectrum(
                dataframe, ['A', 'B'], os.path.join(directory, 'spectrum.svg'),
                graph_title='Spectrum'
            ))
            distribution_types = ('days_month', 'months', 'years', 'hours', 'days_week', 'weeks')
            for index, distribution in enumerate(distribution_types):
                source = log if index % 2 else dataframe
                pm4py.view_events_distribution_graph(
                    source, distr_type=distribution, format='svg', graph_title='Distribution'
                )
                self.assertEqual('saved', pm4py.save_vis_events_distribution_graph(
                    source,
                    os.path.join(directory, f'{distribution}.svg'),
                    distr_type=distribution,
                    graph_title='Distribution',
                ))
            with self.assertRaises(Exception):
                pm4py.view_events_distribution_graph(log, distr_type='unsupported')

    def test_ocel_elkjs_ocpn_and_remaining_model_facades(self):
        log, dataframe = self._log_data()
        ocel = pm4py.read_ocel2_json(self._path('ocel', 'ocel20_example.jsonocel'))
        ocdfg = pm4py.discover_ocdfg(ocel)
        # The ELK renderer expects empty edge dictionaries for isolated
        # object types as well as object types that have actual edges.
        for metric_content in ocdfg['edges'].values():
            for object_type in ocdfg['object_types']:
                metric_content.setdefault(object_type, {})
        for metric_content in ocdfg['edges_performance'].values():
            for object_type in ocdfg['object_types']:
                metric_content.setdefault(object_type, {})
        ocpn = pm4py.discover_oc_petri_net(ocel)
        transition_system = pm4py.discover_transition_system(dataframe)
        prefix_tree = pm4py.discover_prefix_tree(dataframe)
        process_tree = pm4py.parse_process_tree("->( 'A', X( 'B', 'C' ) )")
        powl = pm4py.convert_to_powl(process_tree)
        net, initial, final = pm4py.convert_to_petri_net(process_tree)
        aligned = pm4py.conformance_diagnostics_alignments(
            log, net, initial, final, return_diagnostics_dataframe=False
        )
        footprints = pm4py.discover_footprints(process_tree)
        object_ids = ocel.objects[ocel.object_id_column].to_list()[:2]
        object_graph = {(object_ids[0], object_ids[1])}
        frequency_network = {('alice', 'bob'): {'handover': 3}}
        performance_network = {('alice', 'bob'): {'handover': [1.0, 2.0, 3.0]}}

        with ExitStack() as stack, tempfile.TemporaryDirectory() as directory:
            self._patch_visualizer_io(stack)
            for annotation in ('frequency', 'performance'):
                pm4py.view_ocdfg(
                    ocdfg, annotation=annotation, variant_str='elkjs',
                    format='html', graph_title='OCDFG'
                )
                self.assertEqual('saved', pm4py.save_vis_ocdfg(
                    ocdfg, os.path.join(directory, f'ocdfg-{annotation}.html'),
                    annotation=annotation, variant_str='elkjs', graph_title='OCDFG'
                ))
            for variant in ('wo_decoration', 'brachmann'):
                pm4py.view_ocpn(ocpn, variant_str=variant, format='svg', graph_title='OCPN')
                self.assertEqual('saved', pm4py.save_vis_ocpn(
                    ocpn, os.path.join(directory, f'ocpn-{variant}.svg'),
                    variant_str=variant, graph_title='OCPN'
                ))
            pm4py.view_network_analysis(frequency_network, graph_title='Network')
            self.assertEqual('saved', pm4py.save_vis_network_analysis(
                performance_network, os.path.join(directory, 'network.svg'),
                variant='performance', graph_title='Network'
            ))
            pm4py.view_transition_system(transition_system, graph_title='TS')
            self.assertEqual('saved', pm4py.save_vis_transition_system(
                transition_system, os.path.join(directory, 'ts.svg'), graph_title='TS'
            ))
            pm4py.view_prefix_tree(prefix_tree, graph_title='Trie')
            self.assertEqual('saved', pm4py.save_vis_prefix_tree(
                prefix_tree, os.path.join(directory, 'trie.svg'), graph_title='Trie'
            ))
            pm4py.view_alignments(log, aligned, graph_title='Alignments')
            self.assertEqual('saved', pm4py.save_vis_alignments(
                log, aligned, os.path.join(directory, 'alignments.svg'), graph_title='Alignments'
            ))
            pm4py.view_footprints((footprints, footprints), graph_title='Footprints')
            self.assertEqual('saved', pm4py.save_vis_footprints(
                (footprints, footprints), os.path.join(directory, 'footprints.svg'),
                graph_title='Footprints'
            ))
            pm4py.view_powl(powl, variant_str='net', graph_title='POWL')
            self.assertEqual('saved', pm4py.save_vis_powl(
                powl, os.path.join(directory, 'powl.svg'), graph_title='POWL'
            ))
            pm4py.view_object_graph(ocel, object_graph, graph_title='Objects')
            self.assertEqual('saved', pm4py.save_vis_object_graph(
                ocel, object_graph, os.path.join(directory, 'objects.svg'), graph_title='Objects'
            ))


if __name__ == '__main__':
    unittest.main()
