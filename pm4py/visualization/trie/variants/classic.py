import tempfile
from enum import Enum
from typing import Optional, Dict, Any, Union

from graphviz import Graph

from pm4py.objects.trie.obj import Trie
from pm4py.util import exec_utils, constants


class Parameters(Enum):
    FORMAT = "format"
    BGCOLOR = "bgcolor"
    ENABLE_GRAPH_TITLE = "enable_graph_title"
    GRAPH_TITLE = "graph_title"


def draw_recursive(trie_node: Trie, parent: Union[str, None], gviz: Graph):
    """
    Draws recursively the specified trie node

    Parameters
    --------------
    trie_node
        Node of the trie
    parent
        Parent node in the graph (expressed as a string)
    gviz
        Graphviz object
    """
    node_id = str(id(trie_node))
    if trie_node.label is not None:
        gviz.node(node_id, label=trie_node.label, shape="box")
    if parent is not None:
        gviz.edge(parent, node_id)
    for child in trie_node.children:
        draw_recursive(child, node_id if trie_node.label is not None else None, gviz)


def apply(trie: Trie, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> Graph:
    """
    Represents the trie

    Parameters
    -----------------
    trie
        Trie
    parameters
        Parameters, including:
        - Parameters.FORMAT: the format of the visualization

    Returns
    -----------------
    graph
        Representation of the trie
    """
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)

    enable_graph_title = exec_utils.get_param_value(Parameters.ENABLE_GRAPH_TITLE, parameters, constants.DEFAULT_ENABLE_GRAPH_TITLES)
    graph_title = exec_utils.get_param_value(Parameters.GRAPH_TITLE, parameters, "Prefix Tree")

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()
    
    viz = Graph("pt", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor})
    viz.attr('node', shape='ellipse', fixedsize='false')

    if enable_graph_title:
        viz.attr(label='<<FONT POINT-SIZE="20">'+graph_title+'</FONT>>', labelloc="top")

    draw_recursive(trie, None, viz)

    viz.attr(overlap='false')
    viz.attr(splines='false')
    viz.attr(rankdir='LR')
    viz.format = image_format.replace("html", "plain-ext")

    return viz
