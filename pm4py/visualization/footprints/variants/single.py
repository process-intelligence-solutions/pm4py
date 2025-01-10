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
from graphviz import Source
import tempfile
from pm4py.util import exec_utils, constants
from enum import Enum
from typing import Optional, Dict, Any, Union


class Parameters(Enum):
    FORMAT = "format"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


XOR_SYMBOL = "&#35;"
PREV_SYMBOL = "&#60;"
SEQUENCE_SYMBOL = "&#62;"
PARALLEL_SYMBOL = "||"


def apply(fp: Dict[str, Any], parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> Source:
    """
    Visualize a footprints table

    Parameters
    ---------------
    fp
        Footprints
    parameters
        Parameters of the algorithm, including:
            - Parameters.FORMAT => Format of the visualization

    Returns
    ---------------
    gviz
        Graphviz object
    """
    if parameters is None:
        parameters = {}

    if type(fp) is list:
        raise Exception("footprints visualizer does not work on list of footprints!")

    activities = sorted(list(set(x[0] for x in fp["sequence"]).union(set(x[1] for x in fp["sequence"])).union(
        set(x[0] for x in fp["parallel"])).union(set(x[1] for x in fp["parallel"]))))
    fp_table = {}

    for a1 in activities:
        fp_table[a1] = {}
        for a2 in activities:
            fp_table[a1][a2] = XOR_SYMBOL

    for x in fp["sequence"]:
        if x not in fp["parallel"]:
            fp_table[x[0]][x[1]] = SEQUENCE_SYMBOL
            fp_table[x[1]][x[0]] = PREV_SYMBOL

    for x in fp["parallel"]:
        fp_table[x[0]][x[1]] = PARALLEL_SYMBOL

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Footprints")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    footprints_table = ["digraph {\n"]

    if enable_graph_title:
        footprints_table.append('label=<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>;\nlabelloc="top";\n')

    footprints_table.append("tbl [\n")
    footprints_table.append("shape=plaintext\n")
    footprints_table.append("label=<\n")

    footprints_table.append("<table border='0' cellborder='1' color='blue' cellspacing='0'>\n")
    footprints_table.append("<tr><td></td>")
    for act in activities:
        footprints_table.append("<td><b>"+act+"</b></td>")
    footprints_table.append("</tr>\n")
    for a1 in activities:
        footprints_table.append("<tr><td><b>"+a1+"</b></td>")
        for a2 in activities:
            footprints_table.append("<td>"+fp_table[a1][a2]+"</td>")
        footprints_table.append("</tr>\n")

    footprints_table.append("</table>\n")
    footprints_table.append(">];\n")
    footprints_table.append("}\n")

    footprints_table = "".join(footprints_table)

    gviz = Source(footprints_table, filename=filename.name)
    gviz.format = image_format

    return gviz
