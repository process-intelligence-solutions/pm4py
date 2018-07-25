from collections import Counter


class Marking(Counter):
    pass

    def __hash__(self):
        r = 0
        for p in self.items():
            r += 31 * hash(p[0]) * p[1]
        return r

    def __eq__(self, other):
        if not isinstance(other, Marking):
            return False
        for p in self.items():
            if p[1] != 0:
                if p[0] not in other:
                    return False
                if other[p[0]] != p[1]:
                    return False
            elif p[0] in other and other[p[0]] != 0:
                return False
        for p in other.items():
            if p[1] != 0:
                if p[0] not in self.keys():
                    return False
                if self.get(p[0]) != p[1]:
                    return False
            elif p[0] in self.keys() and self.get(p[0]) != 0:
                return False
        return True

class PetriNet(object):
    class Place(object):

        def __init__(self, name, in_arcs=None, out_arcs=None):
            self.__name = name
            self.__in_arcs = set() if in_arcs is None else in_arcs
            self.__out_arcs = set() if out_arcs is None else out_arcs

        def __set_name(self, name):
            self.__name = name

        def __get_name(self):
            return self.__name

        def __get_out_arcs(self):
            return self.__out_arcs

        def __get_in_arcs(self):
            return self.__in_arcs

        name = property(__get_name, __set_name)
        in_arcs = property(__get_in_arcs)
        out_arcs = property(__get_out_arcs)

    class Transition(object):

        def __init__(self, name, label=None, in_arcs=None, out_arcs=None):
            self.__name = name
            self.__label = None if label is None else label
            self.__in_arcs = set() if in_arcs is None else in_arcs
            self.__out_arcs = set() if out_arcs is None else out_arcs

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

        name = property(__get_name, __set_name)
        label = property(__get_label, __set_label)
        in_arcs = property(__get_in_arcs)
        out_arcs = property(__get_out_arcs)

    class Arc(object):

        def __init__(self, source, target, weight=1):
            if type(source) is type(target):
                raise Exception('Petri nets are bipartite graphs!')
            self.__source = source
            self.__target = target
            self.__weight = weight

        def __get_source(self):
            return self.__source

        def __get_target(self):
            return self.__target

        def __set_weight(self, weight):
            self.__wight = weight

        def __get_weight(self):
            return self.__weight

        source = property(__get_source)
        target = property(__get_target)
        weight = property(__get_weight, __set_weight)

    def __init__(self, name=None, places=None, transitions=None, arcs=None):
        self.__name = "" if name is None else name
        self.__places = set() if places is None else places
        self.__transitions = set() if transitions is None else transitions
        self.__arcs = set() if arcs is None else arcs

    def __get_name(self):
        return self.__name

    def __set_name(self, name):
        self.__name = name

    def __get_places(self):
        return self.__places

    def __get_transitions(self):
        return self.__transitions

    def __get_arcs(self):
        return self.__arcs

    name = property(__get_name, __set_name)
    places = property(__get_places)
    transitions = property(__get_transitions)
    arcs = property(__get_arcs)



