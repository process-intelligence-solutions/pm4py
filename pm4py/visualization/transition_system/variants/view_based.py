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
from pm4py.visualization.transition_system.util import visualize_graphviz
from enum import Enum
from typing import Optional, Dict, Any, Union
from pm4py.objects.transition_system.obj import TransitionSystem
import graphviz


class Parameters(Enum):
    FORMAT = "format"
    SHOW_LABELS = "show_labels"
    SHOW_NAMES = "show_names"
    FORCE_NAMES = "force_names"
    FILLCOLORS = "fillcolors"
    FONT_SIZE = "font_size"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def apply(tsys: TransitionSystem, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> graphviz.Digraph:
    """
    Get visualization of a Transition System

    Parameters
    -----------
    tsys
        Transition system
    parameters
        Optional parameters of the algorithm

    Returns
    ----------
    gviz
        Graph visualization
    """

    gviz = visualize_graphviz.visualize(tsys, parameters=parameters)
    return gviz
