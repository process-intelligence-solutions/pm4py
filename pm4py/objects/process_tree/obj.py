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
from enum import Enum
from pm4py.util import hie_utils
import sys


class Operator(Enum):
    # sequence operator
    SEQUENCE = "->"
    # exclusive choice operator
    XOR = "X"
    # parallel operator
    PARALLEL = "+"
    # loop operator
    LOOP = "*"
    # or operator
    OR = "O"
    # interleaving operator
    INTERLEAVING = "<>"
    # partially-ordered operator
    PARTIALORDER = "PO"

    def __str__(self):
        """
        Provides a string representation of the current operator

        Returns
        -----------
        stri
            String representation of the process tree
        """
        return self.value

    def __repr__(self):
        """
        Provides a string representation of the current operator

        Returns
        -----------
        stri
            String representation of the process tree
        """
        return self.value


class ProcessTree(object):

    class OperatorState(Enum):
        ENABLED = "enabled"
        OPEN = "open"
        CLOSED = "closed"
        FUTURE = "future"

    def __init__(self, operator=None, parent=None, children=None, label=None):
        """
        Constructor

        Parameters
        ------------
        operator
            Operator (of the current node) of the process tree
        parent
            Parent node (of the current node)
        children
            List of children of the current node
        label
            Label (of the current node)
        """
        self._operator = operator
        self._parent = parent
        self._children = list() if children is None else children
        self._label = label
        self._properties = {}

    def __hash__(self):
        if self.label is not None:
            return hash(self.label)
        elif len(self.children) == 0:
            return 37
        else:
            h = 1337
            for i in range(len(self.children)):
                h += 41 * i * hash(self.children[i])
            if self.operator == Operator.SEQUENCE:
                h = h * 13
            elif self.operator == Operator.XOR:
                h = h * 17
            elif self.operator == Operator.OR:
                h = h * 23
            elif self.operator == Operator.PARALLEL:
                h = h * 29
            elif self.operator == Operator.LOOP:
                h = h * 37
            elif self.operator == Operator.INTERLEAVING:
                h = h * 41
            elif self.operator == Operator.PARTIALORDER:
                h = h * 43
            return h % 268435456

    def _set_operator(self, operator):
        self._operator = operator

    def _set_parent(self, parent):
        self._parent = parent

    def _set_label(self, label):
        self._label = label

    def _set_children(self, children):
        self._children = children

    def _get_children(self):
        return self._children

    def _get_parent(self):
        return self._parent

    def _get_operator(self):
        return self._operator

    def _get_label(self):
        return self._label

    def __eq__(self, other):
        if isinstance(other, ProcessTree):
            if self.label is not None:
                return True if other.label == self.label else False
            elif len(self.children) == 0:
                return other.label is None and len(other.children) == 0
            else:
                if self.operator == other.operator:
                    if len(self.children) != len(other.children):
                        return False
                    else:
                        for i in range(len(self.children)):
                            if self.children[i] != other.children[i]:
                                return False
                        return True
                else:
                    return False
        return False

    def to_string(self, level=0, indent=False, max_indent=sys.maxsize):
        """
        Represents a process tree model as a string.

        Parameters
        -----------------
        indent
            Enable the indentation of the resulting string
        max_indent
            Maximum level of indentation
        """
        if self.operator is not None:
            rep = str(self._operator) + "( "
            for i in range(0, len(self._children)):
                child = self._children[i]
                if len(child.children) == 0:
                    if child.label is not None:
                        rep += (
                            "'" + child.to_string(level=level + 1) + "'" + ", "
                            if i < len(self._children) - 1
                            else "'" + child.to_string(level=level + 1) + "'"
                        )
                    else:
                        rep += (
                            child.to_string(level=level + 1) + ", "
                            if i < len(self._children) - 1
                            else child.to_string(level=level + 1)
                        )
                else:
                    rep += (
                        child.to_string(level=level + 1) + ", "
                        if i < len(self._children) - 1
                        else child.to_string(level=level + 1)
                    )
            stru = rep + " )"
            if level == 0 and indent:
                stru = "\n".join(
                    hie_utils.indent_representation(
                        stru, max_indent=max_indent
                    )
                )
            return stru
        elif self.label is not None:
            return self.label
        else:
            return "tau"

    def __repr__(self):
        """
        Returns a string representation of the process tree

        Returns
        ------------
        stri
            String representation of the process tree
        """
        return self.to_string()

    def __str__(self):
        """
        Returns a string representation of the process tree

        Returns
        ------------
        stri
            String representation of the process tree
        """
        return self.to_string()

    @staticmethod
    def model_description() -> str:
        descr = """A process tree is a hierarchical process model.
The following operators are defined for process trees:
-> ( A, B ) tells that the process tree A should be executed before the process tree B
X ( A, B ) tells that there is an exclusive choice between executing the process tree A or the process tree B
+ ( A, B ) tells that A and B are executed in true concurrency.
* ( A, B ) is a loop. So the process tree A is executed, then either you exit the loop, or you execute B and then A again (this can happen several times until the loop is exited).
the leafs of a process tree are either activities (denoted by 'X' where X is the name of the activity) or silent steps (indicated by tau).
An example process tree follows:
+ ( 'A', -> ( 'B', 'C' ) )
tells that you should execute B before executing C. In true concurrency, you can execute A. So the possible traces are A->B->C, B->A->C, B->C->A.
"""
        return descr

    def _get_root(self):
        root = self
        while root._get_parent() is not None:
            root = root._get_parent()
        return root

    def _get_leaves(self):
        root = self._get_root()
        leaves = [root]
        if root._get_children() != list():
            leaves = root._get_children()
            change_of_leaves = True
            while change_of_leaves:
                leaves_to_replace = list()
                new_leaves = list()
                for leaf in leaves:
                    if leaf._get_children() != list():
                        leaves_to_replace.append(leaf)
                    else:
                        new_leaves.append(leaf)
                if leaves_to_replace != list():
                    for leaf in leaves_to_replace:
                        for el in leaf.children:
                            new_leaves.append(el)
                    leaves = new_leaves
                else:
                    change_of_leaves = False
        return leaves

    def _print_tree(self):
        root = self._get_root()
        print(root)

    parent = property(_get_parent, _set_parent)
    children = property(_get_children, _set_children)
    operator = property(_get_operator, _set_operator)
    label = property(_get_label, _set_label)


class EnhancedProcessTree(ProcessTree):
    def __init__(self, operator=None, parent=None, children=None, label=None, start=False, stop=False, skip=False):
        super().__init__(operator=operator, parent=parent, children=children, label=label)
        self._start = start
        self._stop = stop
        self._skip = skip

    def _get_start(self):
        return self._start

    def _set_start(self, value):
        self._start = value

    def _get_stop(self):
        return self._stop

    def _set_stop(self, value):
        self._stop = value

    def _get_skip(self):
        return self._skip

    def _set_skip(self, value):
        self._skip = value

    start = property(_get_start, _set_start)
    stop = property(_get_stop, _set_stop)
    skip = property(_get_skip, _set_skip)

    def __eq__(self, other):
        is_equal = super().__eq__(other)

        if is_equal and isinstance(other, EnhancedProcessTree):
            return self.start == other.start and self._stop == other.stop and self._skip == other.skip

        return is_equal

    def __hash__(self):
        return hash((super().__hash__(), self._start, self._stop, self._skip))

    def to_string(self, level=0, indent=False, max_indent=sys.maxsize):
        start_indicator = " (start)" if self.start else ""
        stop_indicator = " (stop)" if self.stop else ""
        skip_indicator = " (skip)" if self.skip else ""

        if self.label is not None:
            return f"{start_indicator}'{self.label}'{stop_indicator}{skip_indicator}"

        if self.operator is None and self.label is None:
            return "tau"

        children_strs = [
            child.to_string(level=level + 1, indent=indent, max_indent=max_indent)
            for child in self.children
        ]

        if indent and level < max_indent:
            indent_str = "\n" + "\t" * (level + 1)
            children_joined = indent_str + indent_str.join(children_strs)
            return f"{start_indicator}{self.operator}{stop_indicator}{skip_indicator}( {children_joined} \n{'\t' * level})"
        else:
            children_joined = ", ".join(children_strs)
            return f"{start_indicator}{self.operator}{stop_indicator}{skip_indicator}( {children_joined} )"