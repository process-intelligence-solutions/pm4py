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
from enum import Enum
from collections import Counter
from pm4py.util import nx_utils


DEFAULT_PROCESS = str(uuid.uuid4())


class Marking(Counter):
    pass

    # required = Counter()

    def __hash__(self):
        r = 0
        for p in self.items():
            r += 31 * hash(p[0]) * p[1]
        return r

    def __eq__(self, other):
        if not self.keys() == other.keys():
            return False
        for p in self.keys():
            if other.get(p) != self.get(p):
                return False
        return True

    def __le__(self, other):
        if not self.keys() <= other.keys():
            return False
        for p in self.keys():
            if sum(other.get(p)) < sum(self.get(p)):
                return False
        return True

    def __add__(self, other):
        m = Marking()
        for p in self.items():
            m[p[0]] = p[1]
        for p in other.items():
            m[p[0]] += p[1]
        return m

    def __sub__(self, other):
        m = Marking()
        for p in self.items():
            m[p[0]] = p[1]
        for p in other.items():
            m[p[0]] -= p[1]
            if m[p[0]] == 0:
                del m[p[0]]
        return m

    def __repr__(self):
        # return str([str(p.name) + ":" + str(self.get(p)) for p in self.keys()])
        # The previous representation had a bug, it took into account the order
        # of the places with tokens
        return str(
            [
                str(p.id) + ":" + str(self.get(p))
                for p in sorted(list(self.keys()), key=lambda x: x.id)
            ]
        )

    def __deepcopy__(self, memodict={}):
        marking = Marking()
        memodict[id(self)] = marking
        for node in self:
            node_occ = self[node]
            new_node = (
                memodict[id(node)]
                if id(node) in memodict
                else BPMN.BPMNNode(node.id, node.name)
            )
            marking[new_node] = node_occ
        return marking


class BPMNNodeLayout(object):
    def __init__(self):
        self.__x = 0
        self.__y = 0
        self.__width = 100
        self.__height = 100

    def set_x(self, x):
        self.__x = x

    def set_y(self, y):
        self.__y = y

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_width(self):
        return self.__width

    def set_width(self, width):
        self.__width = width

    def get_height(self):
        return self.__height

    def set_height(self, height):
        self.__height = height


class BPMNEdgeLayout(object):
    def __init__(self):
        self.__waypoints = [(0, 0), (0, 0)]

    def add_waypoint(self, waypoint):
        self.__waypoints.append(waypoint)

    def del_waypoints(self):
        self.__waypoints = list()

    def get_waypoints(self):
        return self.__waypoints


class BPMNLayout(object):
    def __init__(self):
        self.layout_dict = {}

    def get(self, n):
        if n not in self.layout_dict:
            if isinstance(n, BPMN.BPMNNode):
                self.layout_dict[n] = BPMNNodeLayout()
            elif isinstance(n, BPMN.Flow):
                self.layout_dict[n] = BPMNEdgeLayout()
        return self.layout_dict[n]


class BPMN(object):
    class BPMNNode(object):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            self.__id = ("id" + str(uuid.uuid4())) if id == "" else id
            self.__name = name
            self.__in_arcs = list() if in_arcs is None else in_arcs
            self.__out_arcs = list() if out_arcs is None else out_arcs
            self.__process = DEFAULT_PROCESS if process is None else process
            self.__layout = BPMNLayout()

        def get_id(self):
            return self.__id

        def get_name(self):
            return self.__name

        def set_name(self, name):
            self.__name = name

        def get_in_arcs(self):
            return self.__in_arcs

        def get_out_arcs(self):
            return self.__out_arcs

        def add_in_arc(self, in_arc):
            if in_arc not in self.__in_arcs:
                self.__in_arcs.append(in_arc)

        def add_out_arc(self, out_arc):
            if out_arc not in self.__out_arcs:
                self.__out_arcs.append(out_arc)

        def remove_in_arc(self, in_arc):
            self.__in_arcs.remove(in_arc)

        def remove_out_arc(self, out_arc):
            self.__out_arcs.remove(out_arc)

        def get_process(self):
            return self.__process

        def set_process(self, process):
            self.__process = process

        def set_x(self, x):
            return self.__layout.get(self).set_x(x)

        def set_y(self, y):
            return self.__layout.get(self).set_y(y)

        def get_x(self):
            return self.__layout.get(self).get_x()

        def get_y(self):
            return self.__layout.get(self).get_y()

        def get_width(self):
            return self.__layout.get(self).get_width()

        def set_width(self, width):
            return self.__layout.get(self).set_width(width)

        def get_height(self):
            return self.__layout.get(self).get_height()

        def set_height(self, height):
            return self.__layout.get(self).set_height(height)

        def get_layout(self):
            return self.__layout

        def set_layout(self, layout):
            self.__layout = layout

        def __hash__(self):
            return hash(self.id)

        def __eq__(self, other):
            # keep the ID for now in places
            return hash(self) == hash(other)

        def __repr__(self):
            return str(self.__id + "@" + self.__name)

        def __str__(self):
            return self.__repr__()

        name = property(get_name)
        id = property(get_id)
        in_arcs = property(get_in_arcs)
        out_arcs = property(get_out_arcs)
        process = property(get_process, set_process)

    class Collaboration(BPMNNode):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.BPMNNode.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class Participant(BPMNNode):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            process_ref=None,
        ):
            self.process_ref = process_ref
            BPMN.BPMNNode.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class TextAnnotation(BPMNNode):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            text=None,
        ):
            self.text = text
            BPMN.BPMNNode.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class DataObjectReference(BPMNNode):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            data_object_ref=None,
        ):
            super().__init__(id, name, in_arcs, out_arcs, process)
            self.data_object_ref = data_object_ref

    class DataStoreReference(BPMNNode):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            data_store_ref=None,
        ):
            super().__init__(id, name, in_arcs, out_arcs, process)
            self.data_store_ref = data_store_ref

    class Event(BPMNNode):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.BPMNNode.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class StartEvent(Event):
        def __init__(
            self,
            id="",
            isInterrupting=False,
            name="",
            parallelMultiple=False,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            BPMN.Event.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )
            self.__isInterrupting = isInterrupting
            self.__parallelMultiple = parallelMultiple

        def get_isInterrupting(self):
            return self.__isInterrupting

        def get_parallelMultiple(self):
            return self.__parallelMultiple

    class NormalStartEvent(StartEvent):
        def __init__(
            self,
            id="",
            isInterrupting=False,
            name="",
            parallelMultiple=False,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            BPMN.StartEvent.__init__(
                self,
                id,
                isInterrupting,
                name,
                parallelMultiple,
                in_arcs,
                out_arcs,
                process=process,
            )

    class MessageStartEvent(StartEvent):
        def __init__(
            self,
            id="",
            isInterrupting=False,
            name="",
            parallelMultiple=False,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            BPMN.StartEvent.__init__(
                self,
                id,
                isInterrupting,
                name,
                parallelMultiple,
                in_arcs,
                out_arcs,
                process=process,
            )

    class IntermediateCatchEvent(Event):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.Event.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class MessageIntermediateCatchEvent(IntermediateCatchEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.IntermediateCatchEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class ErrorIntermediateCatchEvent(IntermediateCatchEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.IntermediateCatchEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class CancelIntermediateCatchEvent(IntermediateCatchEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.IntermediateCatchEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class BoundaryEvent(Event):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            activity=None,
        ):
            self.__activity = activity
            BPMN.Event.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

        def get_activity(self):
            return self.__activity

    class MessageBoundaryEvent(BoundaryEvent):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            activity=None,
        ):
            BPMN.BoundaryEvent.__init__(
                self,
                id,
                name,
                in_arcs,
                out_arcs,
                process=process,
                activity=activity,
            )

    class ErrorBoundaryEvent(BoundaryEvent):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            activity=None,
        ):
            BPMN.BoundaryEvent.__init__(
                self,
                id,
                name,
                in_arcs,
                out_arcs,
                process=process,
                activity=activity,
            )

    class CancelBoundaryEvent(BoundaryEvent):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            activity=None,
        ):
            BPMN.BoundaryEvent.__init__(
                self,
                id,
                name,
                in_arcs,
                out_arcs,
                process=process,
                activity=activity,
            )

    class IntermediateThrowEvent(Event):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.Event.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class MessageIntermediateThrowEvent(IntermediateThrowEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.IntermediateThrowEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class NormalIntermediateThrowEvent(IntermediateThrowEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.IntermediateThrowEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class EndEvent(Event):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.Event.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class NormalEndEvent(EndEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.EndEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class MessageEndEvent(EndEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.EndEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class TerminateEndEvent(EndEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.EndEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class ErrorEndEvent(EndEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.EndEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class CancelEndEvent(EndEvent):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.EndEvent.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class Activity(BPMNNode):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.BPMNNode.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class Task(Activity):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.Activity.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class UserTask(Task):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.Task.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class SendTask(Task):
        def __init__(
            self, id="", name="", in_arcs=None, out_arcs=None, process=None
        ):
            BPMN.Task.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

    class SubProcess(Activity):
        def __init__(
            self,
            id="",
            name="",
            in_arcs=None,
            out_arcs=None,
            process=None,
            depth=None,
        ):
            self.__depth = depth
            BPMN.Activity.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )

        def get_depth(self):
            return self.__depth

    class Gateway(BPMNNode):
        class Direction(Enum):
            UNSPECIFIED = "Unspecified"
            DIVERGING = "Diverging"
            CONVERGING = "Converging"

        def __init__(
            self,
            id="",
            name="",
            gateway_direction=Direction.UNSPECIFIED,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            BPMN.BPMNNode.__init__(
                self, id, name, in_arcs, out_arcs, process=process
            )
            self.__gateway_direction = gateway_direction

        def get_gateway_direction(self):
            return self.__gateway_direction

        def set_gateway_direction(self, direction):
            self.__gateway_direction = direction

    class ParallelGateway(Gateway):
        def __init__(
            self,
            id="",
            name="",
            gateway_direction=None,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            gateway_direction = (
                gateway_direction
                if gateway_direction is not None
                else BPMN.Gateway.Direction.UNSPECIFIED
            )
            BPMN.Gateway.__init__(
                self,
                id,
                name,
                gateway_direction,
                in_arcs,
                out_arcs,
                process=process,
            )

    class ExclusiveGateway(Gateway):
        def __init__(
            self,
            id="",
            name="",
            gateway_direction=None,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            gateway_direction = (
                gateway_direction
                if gateway_direction is not None
                else BPMN.Gateway.Direction.UNSPECIFIED
            )
            BPMN.Gateway.__init__(
                self,
                id,
                name,
                gateway_direction,
                in_arcs,
                out_arcs,
                process=process,
            )

    class InclusiveGateway(Gateway):
        def __init__(
            self,
            id="",
            name="",
            gateway_direction=None,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            gateway_direction = (
                gateway_direction
                if gateway_direction is not None
                else BPMN.Gateway.Direction.UNSPECIFIED
            )
            BPMN.Gateway.__init__(
                self,
                id,
                name,
                gateway_direction,
                in_arcs,
                out_arcs,
                process=process,
            )

    class EventBasedGateway(Gateway):
        def __init__(
            self,
            id="",
            name="",
            gateway_direction=None,
            in_arcs=None,
            out_arcs=None,
            process=None,
        ):
            gateway_direction = (
                gateway_direction
                if gateway_direction is not None
                else BPMN.Gateway.Direction.UNSPECIFIED
            )
            BPMN.Gateway.__init__(
                self,
                id,
                name,
                gateway_direction,
                in_arcs,
                out_arcs,
                process=process,
            )

    class Flow(object):
        def __init__(self, source, target, id="", name="", process=None):
            self.__id = uuid.uuid4() if id == "" else id
            self.__name = name
            self.__source = source
            source.add_out_arc(self)
            self.__target = target
            target.add_in_arc(self)
            self.__process = DEFAULT_PROCESS if process is None else process
            self.__layout = BPMNLayout()

        def get_id(self):
            return self.__id

        def get_name(self):
            return self.__name

        def get_source(self):
            return self.__source

        def get_target(self):
            return self.__target

        def get_process(self):
            return self.__process

        def set_process(self, process):
            self.__process = process

        def add_waypoint(self, waypoint):
            return self.__layout.get(self).add_waypoint(waypoint)

        def del_waypoints(self):
            return self.__layout.get(self).del_waypoints()

        def get_waypoints(self):
            return self.__layout.get(self).get_waypoints()

        def get_layout(self):
            return self.__layout

        def set_layout(self, layout):
            self.__layout = layout

        def __repr__(self):
            u_id = (
                str(self.__source.get_id())
                + "@"
                + str(self.__source.get_name())
            )
            v_id = (
                str(self.__target.get_id())
                + "@"
                + str(self.__target.get_name())
            )
            return u_id + " -> " + v_id

        def __str__(self):
            return self.__repr__()

        source = property(get_source)
        target = property(get_target)

    class SequenceFlow(Flow):
        def __init__(self, source, target, id="", name="", process=None):
            BPMN.Flow.__init__(
                self, source, target, id=id, name=name, process=process
            )

    class MessageFlow(Flow):
        def __init__(self, source, target, id="", name="", process=None):
            BPMN.Flow.__init__(
                self, source, target, id=id, name=name, process=process
            )

    class Association(Flow):
        def __init__(self, source, target, id="", name="", process=None):
            BPMN.Flow.__init__(
                self, source, target, id=id, name=name, process=process
            )

    def __init__(self, process_id=None, name="", nodes=None, flows=None):
        self.__process_id = (
            str(uuid.uuid4()) if process_id is None else process_id
        )

        self.__name = name
        self.__graph = nx_utils.MultiDiGraph()
        self.__nodes = set() if nodes is None else nodes
        self.__flows = set() if flows is None else flows
        self.__layout = BPMNLayout()

        if nodes is not None:
            for node in nodes:
                node.set_layout(self.get_layout())
                self.__graph.add_node(node)
        if flows is not None:
            for flow in flows:
                flow.set_layout(self.get_layout())
                self.__graph.add_edge(flow.get_source(), flow.get_target())

    def get_process_id(self):
        return self.__process_id

    def set_process_id(self, process_id):
        self.__process_id = process_id

    def get_nodes(self):
        return self.__nodes

    def get_flows(self):
        return self.__flows

    def get_graph(self):
        return self.__graph

    def get_name(self):
        return self.__name

    def set_name(self, name: str):
        self.__name = name

    def add_node(self, node):
        node.set_layout(self.get_layout())
        self.__nodes.add(node)
        self.__graph.add_node(node)

    def remove_node(self, node):
        if node in self.__nodes:
            self.__nodes.remove(node)
            self.__graph.remove_node(node)

    def remove_flow(self, flow):
        source = flow.get_source()
        target = flow.get_target()
        if source in self.__nodes:
            source.remove_out_arc(flow)
        if target in self.__nodes:
            target.remove_in_arc(flow)
        self.__flows.remove(flow)
        self.__graph.remove_edge(source, target)

    def add_flow(self, flow):
        if not isinstance(flow, BPMN.Flow):
            raise Exception()
        flow.set_layout(self.get_layout())
        source = flow.get_source()
        target = flow.get_target()
        if source not in self.__nodes:
            self.add_node(source)
        if target not in self.__nodes:
            self.add_node(target)
        self.__flows.add(flow)
        self.__graph.add_edge(
            source, target, id=flow.get_id(), name=flow.get_name()
        )
        source.add_out_arc(flow)
        target.add_in_arc(flow)

    def get_layout(self):
        return self.__layout

    def set_layout(self, layout):
        self.__layout = layout
        for n in self.__nodes:
            n.set_layout(layout)
        for e in self.__flows:
            e.set_layout(layout)
