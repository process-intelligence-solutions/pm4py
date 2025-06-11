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
from pm4py.visualization.bpmn.variants import classic, classic_v2, dagrejs
from pm4py.util import exec_utils
from enum import Enum
from pm4py.visualization.common.gview import serialize, serialize_dot
from typing import Optional, Dict, Any
from pm4py.objects.bpmn.obj import BPMN
import graphviz


class Variants(Enum):
    CLASSIC = classic
    CLASSIC_V2 = classic_v2
    DAGREJS = dagrejs


DEFAULT_VARIANT = Variants.CLASSIC


def apply(bpmn_graph: BPMN, variant=DEFAULT_VARIANT, parameters: Optional[Dict[Any, Any]] = None) -> graphviz.Digraph:
    """
    Visualize a BPMN graph

    Parameters
    -------------
    bpmn_graph
        BPMN graph
    variant
        Variant of the visualization, possible values:
         - Variants.CLASSIC
    parameters
        Version-specific parameters

    Returns
    ------------
    gviz
        Graphviz representation
    """
    return exec_utils.get_variant(variant).apply(bpmn_graph, parameters=parameters)


def save(gviz: graphviz.Digraph, output_file_path: str, variant=DEFAULT_VARIANT, parameters=None):
    """
    Save the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    output_file_path
        Path where the GraphViz output should be saved
    """
    return exec_utils.get_variant(variant).save(gviz, output_file_path, parameters=parameters)


def view(gviz: graphviz.Digraph, variant=DEFAULT_VARIANT, parameters=None):
    """
    View the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    """
    return exec_utils.get_variant(variant).view(gviz, parameters=parameters)


def matplotlib_view(gviz: graphviz.Digraph, variant=DEFAULT_VARIANT, parameters=None):
    """
    Views the diagram using Matplotlib

    Parameters
    ---------------
    gviz
        Graphviz
    """
    return exec_utils.get_variant(variant).matplotlib_view(gviz, parameters=parameters)
