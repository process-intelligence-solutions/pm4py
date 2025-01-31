'''
    PM4Py – A Process Mining Library for Python
Copyright (C) 2024 Process Intelligence Solutions UG (haftungsbeschränkt)

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
from collections import Counter
from copy import deepcopy
from typing import Any, Collection, Dict


class Marking(Counter):

    def __hash__(self):
        return frozenset(self).__hash__() # credits egrocha

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
            if other.get(p) < self.get(p):
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
        return str([str(p.name) + ":" + str(self.get(p)) for p in sorted(list(self.keys()), key=lambda x: x.name)])

    def __str__(self):
        return self.__repr__()

    def __deepcopy__(self, memodict={}):
        marking = Marking()
        memodict[id(self)] = marking
        for place in self:
            place_occ = self[place]
            new_place = memodict[id(place)] if id(place) in memodict else PetriNet.Place(place.name,
                                                                                         properties=place.properties)
            marking[new_place] = place_occ
        return marking


class PetriNet(object):
    class Place(object):

        def __init__(self, name, in_arcs=None, out_arcs=None, properties=None):
            self.__name = name
            self.__in_arcs = set() if in_arcs is None else in_arcs
            self.__out_arcs = set() if out_arcs is None else out_arcs
            self.__properties = dict() if properties is None else properties

        def __set_name(self, name):
            self.__name = name

        def __get_name(self):
            return self.__name

        def __get_out_arcs(self):
            return self.__out_arcs

        def __get_in_arcs(self):
            return self.__in_arcs

        def __get_properties(self):
            return self.__properties

        def __repr__(self):
            return str(self.name)

        def __str__(self):
            return self.__repr__()

        def __eq__(self, other):
            # keep the ID for now in places
            return id(self) == id(other)

        def __hash__(self):
            # keep the ID for now in places
            return id(self)

        def __deepcopy__(self, memodict={}):
            if id(self) in memodict:
                return memodict[id(self)]
            new_place = PetriNet.Place(self.name, properties=self.properties)
            memodict[id(self)] = new_place
            for arc in self.in_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_place.in_arcs.add(new_arc)
            for arc in self.out_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_place.out_arcs.add(new_arc)
            return new_place

        name = property(__get_name, __set_name)
        in_arcs = property(__get_in_arcs)
        out_arcs = property(__get_out_arcs)
        properties = property(__get_properties)

    class Transition(object):

        def __init__(self, name, label=None, in_arcs=None, out_arcs=None, properties=None):
            self.__name = name
            self.__label = None if label is None else label
            self.__in_arcs = set() if in_arcs is None else in_arcs
            self.__out_arcs = set() if out_arcs is None else out_arcs
            self.__properties = dict() if properties is None else properties

        def __set_name(self, name):
            self.__name = name

        def __get_name(self):
            return self.__name

        def __set_label(self, label):
            self.__label = label

        def __get_label(self):
            return self.__label

        def __get_out_arcs(self):
            return self.__out_arcs

        def __get_in_arcs(self):
            return self.__in_arcs

        def __get_properties(self):
            return self.__properties

        def __repr__(self):
            if self.label is None:
                return "("+str(self.name)+", None)"
            else:
                return "("+str(self.name)+", '"+str(self.label)+"')"

        def __str__(self):
            return self.__repr__()

        def __eq__(self, other):
            # keep the ID for now in transitions
            return id(self) == id(other)

        def __hash__(self):
            # keep the ID for now in transitions
            return id(self)

        def __deepcopy__(self, memodict={}):
            if id(self) in memodict:
                return memodict[id(self)]
            new_trans = PetriNet.Transition(self.name, self.label, properties=self.properties)
            memodict[id(self)] = new_trans
            for arc in self.in_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_trans.in_arcs.add(new_arc)
            for arc in self.out_arcs:
                new_arc = deepcopy(arc, memo=memodict)
                new_trans.out_arcs.add(new_arc)
            return new_trans

        name = property(__get_name, __set_name)
        label = property(__get_label, __set_label)
        in_arcs = property(__get_in_arcs)
        out_arcs = property(__get_out_arcs)
        properties = property(__get_properties)

    class Arc(object):

        def __init__(self, source, target, weight=1, properties=None):
            if type(source) is type(target):
                raise Exception('Petri nets are bipartite graphs!')
            self.__source = source
            self.__target = target
            self.__weight = weight
            self.__properties = dict() if properties is None else properties

        def __get_source(self):
            return self.__source

        def __get_target(self):
            return self.__target

        def __set_weight(self, weight):
            self.__weight = weight

        def __get_weight(self):
            return self.__weight

        def __get_properties(self):
            return self.__properties

        def __repr__(self):
            source_rep = repr(self.source)
            target_rep = repr(self.target)
            return source_rep+"->"+target_rep

        def __str__(self):
            return self.__repr__()

        def __hash__(self):
            return id(self)

        def __eq__(self, other):
            return self.source == other.source and self.target == other.target

        def __deepcopy__(self, memodict={}):
            if id(self) in memodict:
                return memodict[id(self)]
            new_source = memodict[id(self.source)] if id(self.source) in memodict else deepcopy(self.source,
                                                                                                memo=memodict)
            new_target = memodict[id(self.target)] if id(self.target) in memodict else deepcopy(self.target,
                                                                                                memo=memodict)
            memodict[id(self.source)] = new_source
            memodict[id(self.target)] = new_target
            new_arc = PetriNet.Arc(new_source, new_target, weight=self.weight, properties=self.properties)
            memodict[id(self)] = new_arc
            return new_arc

        source = property(__get_source)
        target = property(__get_target)
        weight = property(__get_weight, __set_weight)
        properties = property(__get_properties)

    def __init__(self, name: str=None, places: Collection[Place]=None, transitions: Collection[Transition]=None, arcs: Collection[Arc]=None, properties:Dict[str, Any]=None):
        self.__name = "" if name is None else name
        self.__places = set() if places is None else places
        self.__transitions = set() if transitions is None else transitions
        self.__arcs = set() if arcs is None else arcs
        self.__properties = dict() if properties is None else properties

    def __get_name(self) -> str:
        return self.__name

    def __set_name(self, name):
        self.__name = name

    def __get_places(self) -> Collection[Place]:
        return self.__places

    def __get_transitions(self) -> Collection[Transition]:
        return self.__transitions

    def __get_arcs(self) -> Collection[Arc]:
        return self.__arcs

    def __get_properties(self) -> Dict[str, Any]:
        return self.__properties

    def __hash__(self):
        ret = 0
        for p in self.places:
            ret += hash(p)
            ret = ret % 479001599
        for t in self.transitions:
            ret += hash(t)
            ret = ret % 479001599
        return ret

    def __eq__(self, other):
        # for the Petri net equality keep the ID for now
        return id(self) == id(other)

    def __deepcopy__(self, memodict={}):
        from pm4py.objects.petri_net.utils.petri_utils import add_arc_from_to
        this_copy = PetriNet(self.name)
        memodict[id(self)] = this_copy
        for place in self.places:
            place_copy = PetriNet.Place(place.name, properties=place.properties)
            this_copy.places.add(place_copy)
            memodict[id(place)] = place_copy
        for trans in self.transitions:
            trans_copy = PetriNet.Transition(trans.name, trans.label, properties=trans.properties)
            this_copy.transitions.add(trans_copy)
            memodict[id(trans)] = trans_copy
        for arc in self.arcs:
            add_arc_from_to(memodict[id(arc.source)], memodict[id(arc.target)], this_copy, weight=arc.weight)
        return this_copy

    def __repr__(self):
        ret = ["places: ["]
        places_rep = []
        for place in self.places:
            places_rep.append(repr(place))
        places_rep.sort()
        ret.append(" " + ", ".join(places_rep) + " ")
        ret.append("]\ntransitions: [")
        trans_rep = []
        for trans in self.transitions:
            trans_rep.append(repr(trans))
        trans_rep.sort()
        ret.append(" " + ", ".join(trans_rep) + " ")
        ret.append("]\narcs: [")
        arcs_rep = []
        for arc in self.arcs:
            arcs_rep.append(repr(arc))
        arcs_rep.sort()
        ret.append(" " + ", ".join(arcs_rep) + " ")
        ret.append("]")
        return "".join(ret)

    def __str__(self):
        return self.__repr__()

    name = property(__get_name, __set_name)
    places = property(__get_places)
    transitions = property(__get_transitions)
    arcs = property(__get_arcs)
    properties = property(__get_properties)


class InhibitorNet(PetriNet):
    def __init__(self, name=None, places=None, transitions=None, arcs=None, properties=None):
        PetriNet.__init__(self, name=name, places=places, transitions=transitions, arcs=arcs, properties=properties)

    class InhibitorArc(PetriNet.Arc):
        def __init__(self, source, target, weight=1, properties=None):
            PetriNet.Arc.__init__(self, source, target, weight=weight, properties=properties)


class ResetNet(PetriNet):
    def __init__(self, name=None, places=None, transitions=None, arcs=None, properties=None):
        PetriNet.__init__(self, name=name, places=places, transitions=transitions, arcs=arcs, properties=properties)

    class ResetArc(PetriNet.Arc):
        def __init__(self, source, target, weight=1, properties=None):
            PetriNet.Arc.__init__(self, source, target, weight=weight, properties=properties)


class ResetInhibitorNet(InhibitorNet, ResetNet):
    def __init__(self, name=None, places=None, transitions=None, arcs=None, properties=None):
        PetriNet.__init__(self, name=name, places=places, transitions=transitions, arcs=arcs, properties=properties)
