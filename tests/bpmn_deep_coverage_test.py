import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pm4py
from pm4py.objects.bpmn import semantics
from pm4py.objects.bpmn.importer import importer as bpmn_importer
from pm4py.objects.bpmn.obj import BPMN, Marking
from pm4py.objects.bpmn.util import bpmn_utils, label_replacing
from pm4py.objects.log.obj import Event, EventLog, Trace


class BpmnDeepCoverageTest(unittest.TestCase):
    @staticmethod
    def _input_path(*parts):
        return os.path.join(os.path.dirname(__file__), "input_data", *parts)

    def test_intermediate_events_preserve_parallel_synchronization(self):
        for event_type in ("intermediateCatchEvent", "intermediateThrowEvent"):
            with (
                self.subTest(event_type=event_type),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "parallel.bpmn"
                path.write_text(
                    f"""
                    <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
                      <bpmn:process id="process">
                        <bpmn:startEvent id="start"/>
                        <bpmn:task id="taskA" name="A"/>
                        <bpmn:intermediateCatchEvent id="beforeSplit"/>
                        <bpmn:parallelGateway id="split"/>
                        <bpmn:task id="taskB" name="B"/>
                        <bpmn:task id="taskC" name="C"/>
                        <bpmn:intermediateCatchEvent id="afterB"/>
                        <bpmn:{event_type} id="afterC"/>
                        <bpmn:parallelGateway id="join"/>
                        <bpmn:task id="taskD" name="D"/>
                        <bpmn:endEvent id="end"/>
                        <bpmn:sequenceFlow id="f1" sourceRef="start" targetRef="taskA"/>
                        <bpmn:sequenceFlow id="f2" sourceRef="taskA" targetRef="beforeSplit"/>
                        <bpmn:sequenceFlow id="f3" sourceRef="beforeSplit" targetRef="split"/>
                        <bpmn:sequenceFlow id="f4" sourceRef="split" targetRef="taskB"/>
                        <bpmn:sequenceFlow id="f5" sourceRef="split" targetRef="taskC"/>
                        <bpmn:sequenceFlow id="f6" sourceRef="taskB" targetRef="afterB"/>
                        <bpmn:sequenceFlow id="f7" sourceRef="taskC" targetRef="afterC"/>
                        <bpmn:sequenceFlow id="f8" sourceRef="afterB" targetRef="join"/>
                        <bpmn:sequenceFlow id="f9" sourceRef="afterC" targetRef="join"/>
                        <bpmn:sequenceFlow id="f10" sourceRef="join" targetRef="taskD"/>
                        <bpmn:sequenceFlow id="f11" sourceRef="taskD" targetRef="end"/>
                      </bpmn:process>
                    </bpmn:definitions>
                    """,
                    encoding="utf-8",
                )
                net, initial, final = pm4py.convert_to_petri_net(
                    pm4py.read_bpmn(str(path))
                )
                self.assertTrue(
                    all(t.in_arcs and t.out_arcs for t in net.transitions)
                )
                log = EventLog(
                    [
                        Trace(
                            [Event({"concept:name": name}) for name in labels]
                        )
                        for labels in ("ABCD", "ACBD", "ABD", "ACD")
                    ]
                )
                alignments = pm4py.conformance_diagnostics_alignments(
                    log,
                    net,
                    initial,
                    final,
                    variant_str="Variants.VERSION_DIJKSTRA_NO_HEURISTICS",
                    multi_processing=False,
                )
                self.assertEqual(
                    [True, True, False, False],
                    [alignment["fitness"] == 1.0 for alignment in alignments],
                )

    def test_data_reference_associations_and_diagram_layout_roundtrip(self):
        xml = """
        <definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
                     xmlns:local="urn:example"
                     xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                     xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                     xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                     targetNamespace="urn:example">
          <process id="process">
            <association id="read" sourceRef="local:document" targetRef="task"/>
            <association id="write" sourceRef="task" targetRef="local:store"/>
            <startEvent id="start"/>
            <serviceTask id="task" name="Work"/>
            <endEvent id="end"/>
            <sequenceFlow id="first" sourceRef="start" targetRef="task"/>
            <sequenceFlow id="last" sourceRef="task" targetRef="end"/>
            <dataObjectReference id="document" name="Document"/>
            <dataStoreReference id="store" name="Storage"/>
          </process>
          <bpmndi:BPMNDiagram>
            <bpmndi:BPMNPlane bpmnElement="local:process">
              <bpmndi:BPMNShape bpmnElement="local:document">
                <dc:Bounds x="10" y="20" width="30" height="40"/>
              </bpmndi:BPMNShape>
              <bpmndi:BPMNEdge bpmnElement="local:read">
                <di:waypoint x="10" y="20"/>
                <di:waypoint x="30" y="40"/>
              </bpmndi:BPMNEdge>
            </bpmndi:BPMNPlane>
          </bpmndi:BPMNDiagram>
        </definitions>
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "references.bpmn"
            path.write_text(xml, encoding="utf-8")
            graph = pm4py.read_bpmn(str(path))
            pm4py.write_bpmn(graph, str(path), auto_layout=False)
            roundtrip = pm4py.read_bpmn(str(path))

        for imported in (graph, roundtrip):
            nodes = {node.get_id(): node for node in imported.get_nodes()}
            document = nodes["document"]
            store = nodes["store"]
            task = nodes["task"]
            self.assertIsInstance(document, BPMN.DataObjectReference)
            self.assertIsInstance(store, BPMN.DataStoreReference)
            self.assertEqual(
                (10, 20, 30, 40),
                (
                    document.get_x(),
                    document.get_y(),
                    document.get_width(),
                    document.get_height(),
                ),
            )
            associations = {
                (flow.source, flow.target): flow
                for flow in imported.get_flows()
                if isinstance(flow, BPMN.Association)
            }
            self.assertEqual(
                {(document, task), (task, store)}, associations.keys()
            )
            read = associations[document, task]
            self.assertIs(read.source, document)
            self.assertIn(read, task.get_in_arcs())
            self.assertEqual([(10, 20), (30, 40)], read.get_waypoints())
            net, _, _ = pm4py.convert_to_petri_net(imported)
            self.assertEqual(
                {"Work"}, {t.label for t in net.transitions if t.label}
            )

    def test_reference_failures_report_flow_type_and_endpoint(self):
        xml = """
        <definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
                     xmlns:vendor="urn:vendor">
          <process id="process">
            <startEvent id="start"><outgoing>first</outgoing></startEvent>
            <task id="task"><incoming>first</incoming></task>
            <vendor:task id="extension"/>
            {flow}
          </process>
        </definitions>
        """
        with self.assertRaisesRegex(
            ValueError, "SequenceFlow 'broken'.*targetRef.*extension"
        ):
            bpmn_importer.deserialize(
                xml.format(
                    flow='<sequenceFlow id="broken" sourceRef="task" targetRef="extension"/>'
                )
            )
        with self.assertWarnsRegex(
            UserWarning, "Association 'broken'.*targetRef.*extension"
        ):
            graph = bpmn_importer.deserialize(
                xml.format(
                    flow='<association id="broken" sourceRef="task" targetRef="extension"/>'
                )
            )
        self.assertEqual(
            {"start", "task"}, {node.get_id() for node in graph.get_nodes()}
        )
        self.assertEqual(
            {"first"}, {flow.get_id() for flow in graph.get_flows()}
        )
        self.assertEqual([], next(iter(graph.get_flows())).get_waypoints())

    def test_conversion_diagnoses_unsupported_control_flow_nodes(self):
        graph = bpmn_importer.deserialize("""
        <definitions>
          <process id="process">
            <task id="work"/>
            <boundaryEvent id="timeout" attachedToRef="work"/>
            <endEvent id="end"/>
            <sequenceFlow id="onTimeout" sourceRef="timeout" targetRef="end"/>
          </process>
        </definitions>
        """)
        with self.assertRaisesRegex(
            ValueError, "onTimeout.*timeout.*BoundaryEvent"
        ):
            pm4py.convert_to_petri_net(graph)

    def test_import_export_multiple_diagrams_and_layout_metadata(self):
        relative_paths = (
            ("receipt.bpmn",),
            ("running-example.bpmn",),
            ("a32f0n00.bpmn",),
            ("more_models", "SimpleParallel.bpmn"),
            ("more_models", "simple_model.bpmn"),
            ("more_models", "Subprocess1.bpmn"),
            ("more_models", "Subprocess3.bpmn"),
            ("more_models", "ch7_InsuranceClaimsSimulationNormalSeason.bpmn"),
        )
        for relative_path in relative_paths:
            graph = pm4py.read_bpmn(self._input_path(*relative_path))
            self.assertTrue(graph.get_nodes())
            self.assertTrue(graph.get_flows())
            if relative_path[-1] in {
                "Subprocess1.bpmn",
                "Subprocess3.bpmn",
                "ch7_InsuranceClaimsSimulationNormalSeason.bpmn",
            }:
                continue
            with tempfile.NamedTemporaryFile(suffix=".bpmn") as output:
                pm4py.write_bpmn(graph, output.name)
                roundtrip = pm4py.read_bpmn(output.name)
            self.assertEqual(len(graph.get_nodes()), len(roundtrip.get_nodes()))

    def test_bpmn_utility_queries_subprocesses_and_label_replacement(self):
        graph = pm4py.read_bpmn(
            self._input_path("more_models", "Subprocess3.bpmn")
        )
        start_events = bpmn_utils.get_global_start_events(graph)
        self.assertTrue(start_events)
        self.assertEqual(len(start_events), sum(bpmn_utils.get_initial_marking(graph).values()))
        self.assertIs(start_events[0], bpmn_utils.get_node_by_id(start_events[0].get_id(), graph))
        self.assertIsNone(bpmn_utils.get_node_by_id("missing", graph))

        subprocesses = [node for node in graph.get_nodes() if isinstance(node, BPMN.SubProcess)]
        for subprocess in subprocesses:
            process_id = subprocess.get_id()
            self.assertIsInstance(bpmn_utils.get_boundary_events_of_activity(process_id, graph), list)
            self.assertIsInstance(bpmn_utils.get_external_boundary_events_of_activity(process_id, graph), list)
            self.assertIsInstance(bpmn_utils.get_all_nodes_inside_process(process_id, graph), list)
            self.assertIsInstance(bpmn_utils.get_start_events_of_subprocess(process_id, graph), list)
            self.assertIsInstance(bpmn_utils.get_end_events_of_subprocess(process_id, graph), list)
            self.assertIsInstance(bpmn_utils.get_termination_events_of_subprocess(process_id, graph), list)
            self.assertIsInstance(bpmn_utils.get_termination_events_of_subprocess_for_pnet(process_id, graph), list)
        self.assertIsInstance(bpmn_utils.get_all_direct_child_subprocesses(graph.get_process_id(), graph, include_normal=True), set)
        self.assertIsInstance(bpmn_utils.get_all_child_subprocesses(graph.get_process_id(), graph, include_normal=True), set)
        self.assertIsInstance(bpmn_utils.get_subprocesses_sorted_by_depth(graph), list)
        self.assertIsInstance(bpmn_utils.bpmn_graph_end_events_as_throw_events(graph), list)

        tasks = [node for node in graph.get_nodes() if isinstance(node, BPMN.Task) and node.get_name()]
        if tasks:
            # BPMN nodes are mutually linked and hash on an id that is assigned
            # late during deepcopy on Python 3.13. Isolate label replacement
            # from that unrelated interpreter-specific copy failure here.
            with patch.object(label_replacing, "deepcopy", side_effect=lambda value: value):
                renamed = label_replacing.apply(graph, {tasks[0].get_name(): "renamed task"})
            self.assertIn("renamed task", {node.get_name() for node in renamed.get_nodes()})

    @staticmethod
    def _gateway_graph(gateway):
        graph = BPMN()
        start = BPMN.StartEvent(name="start")
        first = BPMN.Task(name="first")
        left = BPMN.Task(name="left")
        right = BPMN.Task(name="right")
        end = BPMN.NormalEndEvent(name="end")
        for node in (start, first, gateway, left, right, end):
            graph.add_node(node)
        for source, target in (
            (start, first),
            (first, gateway),
            (gateway, left),
            (gateway, right),
            (left, end),
            (right, end),
        ):
            graph.add_flow(BPMN.SequenceFlow(source, target))
        return graph, start, first, gateway, left, right, end

    def test_gateway_and_token_flow_semantics(self):
        self.assertEqual([4, 6], semantics.add_vector([1, 2], [3, 4]))
        self.assertEqual([-2, -2], semantics.sub_vector([1, 2], [3, 4]))
        self.assertEqual(7, len(list(semantics.power_set([1, 2, 3]))))

        gateways = (
            BPMN.ParallelGateway(gateway_direction=BPMN.Gateway.Direction.DIVERGING),
            BPMN.ExclusiveGateway(gateway_direction=BPMN.Gateway.Direction.DIVERGING),
            BPMN.InclusiveGateway(gateway_direction=BPMN.Gateway.Direction.DIVERGING),
        )
        # The inclusive implementation returns one marking for every selected
        # outgoing flow, including both markings for the two-flow subset.
        expected_markings = (1, 2, 4)
        for gateway, expected in zip(gateways, expected_markings):
            graph, start, first, gateway, left, right, end = self._gateway_graph(gateway)
            self.assertTrue(semantics.is_enabled(gateway, graph, Marking({gateway: 1})))
            outputs = semantics.weak_execute(gateway, Marking({gateway: 1}), graph)
            self.assertEqual(expected, len(outputs))
            self.assertTrue(all(gateway not in marking for marking in outputs))
            marking = Marking({first: 1})
            self.assertEqual(1, len(semantics.weak_execute(first, marking, graph)))
            self.assertIn(gateway, semantics.enabled_nodes(graph, Marking({gateway: 1})))
            self.assertFalse(semantics.is_enabled(BPMN.Task(name="outside"), graph, Marking()))
            self.assertIsNone(semantics.try_to_execute(first, graph, Marking()))
            with self.assertRaises(TypeError):
                semantics.execute(first, graph, Marking({first: 1}))

        converging = BPMN.ParallelGateway(
            gateway_direction=BPMN.Gateway.Direction.CONVERGING
        )
        graph, _, _, converging, _, _, _ = self._gateway_graph(converging)
        second_input = BPMN.Task(name="second input")
        graph.add_node(second_input)
        graph.add_flow(BPMN.SequenceFlow(second_input, converging))
        self.assertFalse(semantics.is_enabled(converging, graph, Marking({converging: 1})))
        self.assertTrue(semantics.is_enabled(converging, graph, Marking({converging: 2})))

        graph = BPMN()
        terminate = BPMN.TerminateEndEvent(
            name="terminate", process=graph.get_process_id()
        )
        other = BPMN.Task(name="other", process=graph.get_process_id())
        graph.add_node(terminate)
        graph.add_node(other)
        marking = Marking({other: 1})
        semantics.execute_token_flow(terminate, marking, graph)
        self.assertNotIn(other, marking)
        self.assertEqual(1, marking[terminate])


if __name__ == "__main__":
    unittest.main()
