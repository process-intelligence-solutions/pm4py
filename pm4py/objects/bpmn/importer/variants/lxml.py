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
Contact: contact@processintelligence.solutions
'''
import warnings
from enum import Enum

from pm4py.objects.bpmn.obj import BPMN
from pm4py.util import constants, exec_utils


class Parameters(Enum):
    ENCODING = "encoding"


_BPMN_MODEL = "http://www.omg.org/spec/BPMN/20100524/MODEL"
_BPMN_DI = "http://www.omg.org/spec/BPMN/20100524/DI"
_DC = "http://www.omg.org/spec/DD/20100524/DC"
_DI = "http://www.omg.org/spec/DD/20100524/DI"

_NODE_TYPES = {
    "collaboration": BPMN.Collaboration,
    "participant": BPMN.Participant,
    "textannotation": BPMN.TextAnnotation,
    "dataobjectreference": BPMN.DataObjectReference,
    "datastorereference": BPMN.DataStoreReference,
    "subprocess": BPMN.SubProcess,
    "adhocsubprocess": BPMN.SubProcess,
    "task": BPMN.Task,
    "businessruletask": BPMN.Task,
    "manualtask": BPMN.Task,
    "receivetask": BPMN.Task,
    "scripttask": BPMN.Task,
    "servicetask": BPMN.Task,
    "usertask": BPMN.UserTask,
    "sendtask": BPMN.SendTask,
    "startevent": BPMN.NormalStartEvent,
    "endevent": BPMN.NormalEndEvent,
    "intermediatecatchevent": BPMN.IntermediateCatchEvent,
    "intermediatethrowevent": BPMN.NormalIntermediateThrowEvent,
    "boundaryevent": BPMN.BoundaryEvent,
    "exclusivegateway": BPMN.ExclusiveGateway,
    "parallelgateway": BPMN.ParallelGateway,
    "inclusivegateway": BPMN.InclusiveGateway,
    "eventbasedgateway": BPMN.EventBasedGateway,
}

_EVENT_TYPES = {
    "startevent": {"messageeventdefinition": BPMN.MessageStartEvent},
    "endevent": {
        "messageeventdefinition": BPMN.MessageEndEvent,
        "terminateeventdefinition": BPMN.TerminateEndEvent,
        "erroreventdefinition": BPMN.ErrorEndEvent,
        "canceleventdefinition": BPMN.CancelEndEvent,
    },
    "intermediatecatchevent": {
        "messageeventdefinition": BPMN.MessageIntermediateCatchEvent,
        "erroreventdefinition": BPMN.ErrorIntermediateCatchEvent,
        "canceleventdefinition": BPMN.CancelIntermediateCatchEvent,
    },
    "intermediatethrowevent": {
        "messageeventdefinition": BPMN.MessageIntermediateThrowEvent,
    },
    "boundaryevent": {
        "messageeventdefinition": BPMN.MessageBoundaryEvent,
        "erroreventdefinition": BPMN.ErrorBoundaryEvent,
        "canceleventdefinition": BPMN.CancelBoundaryEvent,
    },
}

_FLOW_TYPES = {
    "sequenceflow": BPMN.SequenceFlow,
    "messageflow": BPMN.MessageFlow,
    "association": BPMN.Association,
}

_FLOW_NODE_TYPES = (BPMN.Activity, BPMN.Event, BPMN.Gateway)


def _local_name(element, namespace):
    if not isinstance(element.tag, str):
        return None
    qualifier, _, local_name = element.tag.rpartition("}")
    if qualifier in ("", "{" + namespace):
        return local_name.lower()
    return None


def _reference_id(element, value, target_namespace):
    if value is None:
        return None
    value = value.strip()
    prefix, separator, local_id = value.partition(":")
    if (
        separator
        and target_namespace
        and element.nsmap.get(prefix) == target_namespace
    ):
        return local_id
    return value or None


def _name(element, line_break=""):
    return (
        element.get("name", "")
        .replace("\r", line_break)
        .replace("\n", line_break)
    )


def _make_node(element, tag, node_id, process, depth, target_namespace):
    node_type = _NODE_TYPES[tag]
    attributes = {"id": node_id, "process": process}

    if tag in _EVENT_TYPES:
        for child in element:
            definition = _local_name(child, _BPMN_MODEL)
            if definition and definition.endswith("eventdefinition"):
                node_type = _EVENT_TYPES[tag].get(definition, node_type)
                break
        attributes["name"] = _name(element, line_break=" ")
    elif tag not in ("collaboration", "textannotation"):
        attributes["name"] = _name(element)

    if tag == "collaboration":
        attributes["process"] = node_id
    elif tag == "participant":
        attributes["process"] = None
        attributes["process_ref"] = _reference_id(
            element, element.get("processRef"), target_namespace
        )
    elif tag == "textannotation":
        attributes["text"] = next(
            (
                child.text
                for child in element
                if _local_name(child, _BPMN_MODEL) == "text"
            ),
            "",
        )
    elif tag == "dataobjectreference":
        attributes["data_object_ref"] = element.get("dataObjectRef")
    elif tag == "datastorereference":
        attributes["data_store_ref"] = _reference_id(
            element, element.get("dataStoreRef"), target_namespace
        )
    elif node_type is BPMN.SubProcess:
        attributes["depth"] = depth
    elif tag == "boundaryevent":
        attributes["activity"] = _reference_id(
            element, element.get("attachedToRef"), target_namespace
        )
    elif issubclass(node_type, BPMN.Gateway):
        direction = BPMN.Gateway.Direction
        attributes["gateway_direction"] = direction.__members__.get(
            element.get("gatewayDirection", "").upper(), direction.UNSPECIFIED
        )

    return node_type(**attributes)


def _add_flow(
    graph, nodes, flow_type, flow_id, name, process, source_id, target_id
):
    source = nodes.get(source_id)
    target = nodes.get(target_id)
    for attribute, reference, node in (
        ("sourceRef", source_id, source),
        ("targetRef", target_id, target),
    ):
        if node is None:
            reason = (
                "is missing"
                if reference is None
                else f"{reference!r} does not identify a supported BPMN node"
            )
        elif flow_type is BPMN.SequenceFlow and not isinstance(
            node, _FLOW_NODE_TYPES
        ):
            reason = (
                f"{reference!r} is a {type(node).__name__}, "
                "which cannot carry sequence flow"
            )
        else:
            continue

        message = (
            f"BPMN {flow_type.__name__} {flow_id!r}: {attribute} {reason}"
        )
        if flow_type is BPMN.SequenceFlow:
            raise ValueError(message)
        warnings.warn(f"{message}. Skipping the flow.", stacklevel=3)
        return None

    flow = flow_type(
        source, target, id=flow_id or "", name=name, process=process
    )
    graph.add_flow(flow)
    flow.del_waypoints()
    return flow


def _apply_layout(root, nodes, flows, target_namespace):
    for element in root.iter():
        tag = _local_name(element, _BPMN_DI)
        if tag not in ("bpmnshape", "shape", "bpmnedge", "edge"):
            continue
        element_id = _reference_id(
            element, element.get("bpmnElement"), target_namespace
        )
        if tag in ("bpmnshape", "shape") and element_id in nodes:
            node = nodes[element_id]
            for child in element:
                if _local_name(child, _DC) == "bounds":
                    node.set_x(float(child.get("x")))
                    node.set_y(float(child.get("y")))
                    node.set_width(float(child.get("width")))
                    node.set_height(float(child.get("height")))
                    break
        elif tag in ("bpmnedge", "edge") and element_id in flows:
            flow = flows[element_id]
            flow.del_waypoints()
            for child in element:
                if _local_name(child, _DI) == "waypoint":
                    flow.add_waypoint(
                        (float(child.get("x")), float(child.get("y")))
                    )


def import_xml_tree_from_root(root):
    """Build a BPMN graph, resolving references after all nodes have been read."""
    graph = BPMN()
    target_namespace = root.get("targetNamespace")
    nodes = {}
    flow_elements = []
    declared_flow_ids = set()
    incoming = {}
    outgoing = {}
    graph_ids = set()

    def visit(element, process=None, collaboration=None, depth=0):
        tag = _local_name(element, _BPMN_MODEL)
        if tag is None or tag in ("documentation", "extensionelements"):
            return
        element_id = element.get("id")

        if element_id is not None and (
            tag in _NODE_TYPES or tag in _FLOW_TYPES
        ):
            if element_id in graph_ids:
                raise ValueError(
                    f"Duplicate BPMN graph element ID {element_id!r}"
                )
            graph_ids.add(element_id)

        if element_id is not None and tag == "process":
            process = element_id
            graph.set_process_id(process)
            graph.set_name(_name(element))
        elif tag in _FLOW_TYPES:
            flow_type = _FLOW_TYPES[tag]
            flow_process = (
                collaboration if flow_type is BPMN.MessageFlow else process
            )
            flow_elements.append((element, flow_type, flow_process))
            if element_id is not None:
                declared_flow_ids.add(element_id)
        elif element_id is not None and tag in _NODE_TYPES:
            node = _make_node(
                element, tag, element_id, process, depth, target_namespace
            )
            graph.add_node(node)
            nodes[element_id] = node
            for child in element:
                child_tag = _local_name(child, _BPMN_MODEL)
                if child_tag in ("incoming", "outgoing"):
                    flow_id = _reference_id(
                        child, child.text, target_namespace
                    )
                    if flow_id is not None:
                        hints = (
                            incoming if child_tag == "incoming" else outgoing
                        )
                        hints.setdefault(flow_id, element_id)
            if isinstance(node, BPMN.SubProcess):
                process = element_id
            elif tag == "collaboration":
                collaboration = element_id

        for child in element:
            visit(child, process, collaboration, depth + 1)

    visit(root)

    flows = {}
    for element, flow_type, process in flow_elements:
        flow_id = element.get("id")
        source_id = _reference_id(
            element, element.get("sourceRef"), target_namespace
        )
        target_id = _reference_id(
            element, element.get("targetRef"), target_namespace
        )
        if flow_type is BPMN.SequenceFlow:
            source_id = source_id or outgoing.get(flow_id)
            target_id = target_id or incoming.get(flow_id)
        flow = _add_flow(
            graph,
            nodes,
            flow_type,
            flow_id,
            _name(element),
            process,
            source_id,
            target_id,
        )
        if flow is not None:
            flows[flow.get_id()] = flow

    # Some exporters express sequence flows only through node references.
    for flow_id in (incoming.keys() | outgoing.keys()) - declared_flow_ids:
        if flow_id in graph_ids:
            raise ValueError(f"Duplicate BPMN graph element ID {flow_id!r}")
        source_id = outgoing.get(flow_id)
        target_id = incoming.get(flow_id)
        process = nodes[source_id or target_id].get_process()
        flows[flow_id] = _add_flow(
            graph,
            nodes,
            BPMN.SequenceFlow,
            flow_id,
            "",
            process,
            source_id,
            target_id,
        )

    _apply_layout(root, nodes, flows, target_namespace)
    return graph


def apply(path, parameters=None):
    """Import a BPMN diagram from a file."""
    from lxml import etree

    encoding = exec_utils.get_param_value(
        Parameters.ENCODING, parameters or {}, None
    )
    parser = etree.XMLParser(remove_comments=True, encoding=encoding)
    with open(path, "rb") as stream:
        root = etree.parse(stream, parser=parser).getroot()
    return import_xml_tree_from_root(root)


def import_from_string(bpmn_string, parameters=None):
    """Import a BPMN diagram from a string or bytes."""
    from lxml import etree

    encoding = exec_utils.get_param_value(
        Parameters.ENCODING, parameters or {}, constants.DEFAULT_ENCODING
    )
    if isinstance(bpmn_string, str):
        bpmn_string = bpmn_string.encode(encoding)
        parser = etree.XMLParser(remove_comments=True, encoding=encoding)
    else:
        parser = etree.XMLParser(remove_comments=True)
    root = etree.fromstring(bpmn_string, parser=parser)
    return import_xml_tree_from_root(root)
