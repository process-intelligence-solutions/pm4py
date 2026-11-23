'''
PM4Py – A Process Mining Library for Python
Copyright (C) 2026 Process Intelligence Solutions GmbH

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see this software project's root or
visit <https://www.gnu.org/licenses/>.

Website: https://processintelligence.solutions
Contact: info@processintelligence.solutions
'''
import uuid

from pm4py.objects.bpmn.obj import BPMN
from pm4py.util import constants, exec_utils
from enum import Enum


class Parameters(Enum):
    ENCODING = "encoding"
    ENABLE_BPMN_PLANE_EXPORTING = "enble_bpmn_plane_exporting"
    ENABLE_INCOMING_OUTGOING_EXPORTING = "enable_incoming_outgoing_exporting"


def apply(bpmn_graph, target_path, parameters=None):
    """
    Exports the BPMN diagram to a file

    Parameters
    -------------
    bpmn_graph
        BPMN diagram
    target_path
        Target path
    parameters
        Possible parameters of the algorithm
    """
    xml_string = get_xml_string(bpmn_graph, parameters=parameters)
    F = open(target_path, "wb")
    F.write(xml_string)
    F.close()


def get_xml_string(bpmn_graph, parameters=None):
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(
        Parameters.ENCODING, parameters, constants.DEFAULT_ENCODING
    )
    enble_bpmn_plane_exporting = exec_utils.get_param_value(
        Parameters.ENABLE_BPMN_PLANE_EXPORTING, parameters, True
    )
    enable_incoming_outgoing_exporting = exec_utils.get_param_value(
        Parameters.ENABLE_INCOMING_OUTGOING_EXPORTING, parameters, True
    )

    layout = bpmn_graph.get_layout()

    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    definitions = ET.Element("bpmn:definitions")
    definitions.set(
        "xmlns:bpmn", "http://www.omg.org/spec/BPMN/20100524/MODEL"
    )
    definitions.set("xmlns:bpmndi", "http://www.omg.org/spec/BPMN/20100524/DI")
    definitions.set("xmlns:omgdc", "http://www.omg.org/spec/DD/20100524/DC")
    definitions.set("xmlns:omgdi", "http://www.omg.org/spec/DD/20100524/DI")
    definitions.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    definitions.set("targetNamespace", "http://www.signavio.com/bpmn20")
    definitions.set("typeLanguage", "http://www.w3.org/2001/XMLSchema")
    definitions.set("expressionLanguage", "http://www.w3.org/1999/XPath")
    definitions.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")

    all_processes = set()
    process_planes = {}
    process_process = {}
    process_collaboration = None

    for node in bpmn_graph.get_nodes():
        all_processes.add(node.get_process())
    for flow in bpmn_graph.get_flows():
        all_processes.add(flow.get_process())

    if len(all_processes) > 1:
        # when several swimlanes exist, their elements should be annexed to the
        # same BPMN plane
        collaboration_nodes = [
            x
            for x in bpmn_graph.get_nodes()
            if isinstance(x, BPMN.Collaboration)
        ]
        if collaboration_nodes:
            bpmn_plane_id = collaboration_nodes[0].get_id()

        process_collaboration = ET.SubElement(
            definitions, "bpmn:collaboration", {"id": bpmn_plane_id}
        )

        participant_nodes = [
            x
            for x in bpmn_graph.get_nodes()
            if isinstance(x, BPMN.Participant)
        ]
        if participant_nodes:
            for process in participant_nodes:
                ET.SubElement(
                    process_collaboration,
                    "bpmn:participant",
                    {
                        "id": process.get_id(),
                        "name": process.get_name(),
                        "processRef": "id" + process.process_ref,
                    },
                )
                all_processes.add(process.process_ref)
    else:
        bpmn_plane_id = "id" + list(all_processes)[0]

    for process in all_processes:
        if process != bpmn_plane_id:
            p = ET.SubElement(
                definitions,
                "bpmn:process",
                {
                    "id": "id" + process,
                    "isClosed": "false",
                    "isExecutable": "false",
                    "processType": "None",
                },
            )
            process_process[process] = p
        elif process_collaboration is not None:
            process_process[process] = process_collaboration

    diagram = ET.SubElement(
        definitions,
        "bpmndi:BPMNDiagram",
        {"id": "id" + str(uuid.uuid4()), "name": "diagram"},
    )

    if enble_bpmn_plane_exporting:
        plane = ET.SubElement(
            diagram,
            "bpmndi:BPMNPlane",
            {"bpmnElement": bpmn_plane_id, "id": "id" + str(uuid.uuid4())},
        )
        for process in all_processes:
            process_planes[process] = plane

        for node in bpmn_graph.get_nodes():
            process = node.get_process()

            if process != bpmn_plane_id:
                node_shape = ET.SubElement(
                    process_planes[process],
                    "bpmndi:BPMNShape",
                    {
                        "bpmnElement": node.get_id(),
                        "id": node.get_id() + "_gui",
                    },
                )
                node_shape_layout = ET.SubElement(
                    node_shape,
                    "omgdc:Bounds",
                    {
                        "height": str(layout.get(node).get_height()),
                        "width": str(layout.get(node).get_width()),
                        "x": str(layout.get(node).get_x()),
                        "y": str(layout.get(node).get_y()),
                    },
                )

        for flow in bpmn_graph.get_flows():
            process = flow.get_process()

            flow_shape = ET.SubElement(
                process_planes[process],
                "bpmndi:BPMNEdge",
                {
                    "bpmnElement": "id" + str(flow.get_id()),
                    "id": "id" + str(flow.get_id()) + "_gui",
                },
            )
            for x, y in layout.get(flow).get_waypoints():
                waypoint = ET.SubElement(
                    flow_shape, "omgdi:waypoint", {"x": str(x), "y": str(y)}
                )

    for node in bpmn_graph.get_nodes():
        process = process_process[node.get_process()]
        task = None

        if isinstance(node, BPMN.TextAnnotation):
            task = ET.SubElement(
                process, "bpmn:textAnnotation", {"id": node.get_id()}
            )
            text = ET.SubElement(task, "bpmn:text")
            text.text = node.text
        elif isinstance(node, BPMN.DataObjectReference):
            attributes = {"id": node.get_id(), "name": node.get_name()}
            if node.data_object_ref is not None:
                attributes["dataObjectRef"] = node.data_object_ref
            task = ET.SubElement(process, "bpmn:dataObjectReference", attributes)
        elif isinstance(node, BPMN.DataStoreReference):
            attributes = {"id": node.get_id(), "name": node.get_name()}
            if node.data_store_ref is not None:
                attributes["dataStoreRef"] = node.data_store_ref
            task = ET.SubElement(process, "bpmn:dataStoreReference", attributes)
        elif isinstance(node, BPMN.StartEvent):
            isInterrupting = "true" if node.get_isInterrupting() else "false"
            parallelMultiple = (
                "true" if node.get_parallelMultiple() else "false"
            )
            task = ET.SubElement(
                process,
                "bpmn:startEvent",
                {
                    "id": node.get_id(),
                    "isInterrupting": isInterrupting,
                    "name": node.get_name(),
                    "parallelMultiple": parallelMultiple,
                },
            )
        elif isinstance(node, BPMN.EndEvent):
            task = ET.SubElement(
                process,
                "bpmn:endEvent",
                {"id": node.get_id(), "name": node.get_name()},
            )
        elif isinstance(node, BPMN.IntermediateCatchEvent):
            task = ET.SubElement(
                process,
                "bpmn:intermediateCatchEvent",
                {"id": node.get_id(), "name": node.get_name()},
            )
            messageEventDefinition = ET.SubElement(
                task, "bpmn:messageEventDefinition"
            )
        elif isinstance(node, BPMN.IntermediateThrowEvent):
            task = ET.SubElement(
                process,
                "bpmn:intermediateThrowEvent",
                {"id": node.get_id(), "name": node.get_name()},
            )
        elif isinstance(node, BPMN.BoundaryEvent):
            task = ET.SubElement(
                process,
                "bpmn:boundaryEvent",
                {"id": node.get_id(), "name": node.get_name()},
            )
        elif isinstance(node, BPMN.Task):
            if isinstance(node, BPMN.UserTask):
                task = ET.SubElement(
                    process,
                    "bpmn:userTask",
                    {"id": node.get_id(), "name": node.get_name()},
                )
            elif isinstance(node, BPMN.SendTask):
                task = ET.SubElement(
                    process,
                    "bpmn:sendTask",
                    {"id": node.get_id(), "name": node.get_name()},
                )
            else:
                task = ET.SubElement(
                    process,
                    "bpmn:task",
                    {"id": node.get_id(), "name": node.get_name()},
                )
        elif isinstance(node, BPMN.SubProcess):
            task = ET.SubElement(
                process,
                "bpmn:subProcess",
                {"id": node.get_id(), "name": node.get_name()},
            )
        elif isinstance(node, BPMN.ExclusiveGateway):
            task = ET.SubElement(
                process,
                "bpmn:exclusiveGateway",
                {
                    "id": node.get_id(),
                    "gatewayDirection": node.get_gateway_direction().value,
                    "name": node.get_name(),
                },
            )
        elif isinstance(node, BPMN.ParallelGateway):
            task = ET.SubElement(
                process,
                "bpmn:parallelGateway",
                {
                    "id": node.get_id(),
                    "gatewayDirection": node.get_gateway_direction().value,
                    "name": node.get_name(),
                },
            )
        elif isinstance(node, BPMN.InclusiveGateway):
            task = ET.SubElement(
                process,
                "bpmn:inclusiveGateway",
                {
                    "id": node.get_id(),
                    "gatewayDirection": node.get_gateway_direction().value,
                    "name": node.get_name(),
                },
            )
        elif isinstance(node, BPMN.EventBasedGateway):
            task = ET.SubElement(
                process,
                "bpmn:eventBasedGateway",
                {
                    "id": node.get_id(),
                    "gatewayDirection": node.get_gateway_direction().value,
                    "name": node.get_name(),
                },
            )

        if enable_incoming_outgoing_exporting and task is not None:
            for in_arc in node.get_in_arcs():
                if isinstance(in_arc, BPMN.SequenceFlow):
                    arc_xml = ET.SubElement(task, "bpmn:incoming")
                    arc_xml.text = "id" + str(in_arc.get_id())

            for out_arc in node.get_out_arcs():
                if isinstance(out_arc, BPMN.SequenceFlow):
                    arc_xml = ET.SubElement(task, "bpmn:outgoing")
                    arc_xml.text = "id" + str(out_arc.get_id())

    for flow in bpmn_graph.get_flows():
        process = process_process[flow.get_process()]

        source = flow.get_source()
        target = flow.get_target()

        if isinstance(flow, BPMN.SequenceFlow):
            flow_xml = ET.SubElement(
                process,
                "bpmn:sequenceFlow",
                {
                    "id": "id" + str(flow.get_id()),
                    "name": flow.get_name(),
                    "sourceRef": str(source.get_id()),
                    "targetRef": str(target.get_id()),
                },
            )
        elif isinstance(flow, BPMN.MessageFlow):
            flow_xml = ET.SubElement(
                process,
                "bpmn:messageFlow",
                {
                    "id": "id" + str(flow.get_id()),
                    "name": flow.get_name(),
                    "sourceRef": str(source.get_id()),
                    "targetRef": str(target.get_id()),
                },
            )

        elif isinstance(flow, BPMN.Association):
            flow_xml = ET.SubElement(
                process,
                "bpmn:association",
                {
                    "id": "id" + str(flow.get_id()),
                    "sourceRef": str(source.get_id()),
                    "targetRef": str(target.get_id()),
                },
            )

    return minidom.parseString(ET.tostring(definitions)).toprettyxml(
        encoding=encoding
    )
