import matplotlib
from copy import copy

from pm4py.visualization.graphs.util import common
from pm4py.util import exec_utils
from enum import Enum


class Parameters(Enum):
    TITLE = "title"
    FORMAT = "format"
    X_AXIS = "x_axis"
    Y_AXIS = "y_axis"


ATTRIBUTE_LABEL = "Attribute value"
DENSITY_LABEL = "Density"
GRAPH_DEFAULT_TITLE = "Attribute Distribution"


def apply_plot(x, y, parameters=None):
    """
    Plot (non-logarithmic way) the graph with axis values contained in x and y

    Parameters
    ------------
    x
        Values for x-axis
    y
        Values for y-axis
    parameters
        Parameters of the algorithm, including:
            Parameters.FORMAT -> Format of the target image
            Parameters.TITLE -> Title of the image

    Returns
    ------------
    temp_file_name
        Representation temporary file name
    """
    if parameters is None:
        parameters = {}

    format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    title = exec_utils.get_param_value(Parameters.TITLE, parameters, GRAPH_DEFAULT_TITLE)
    x_axis = exec_utils.get_param_value(Parameters.X_AXIS, parameters, ATTRIBUTE_LABEL)
    y_axis = exec_utils.get_param_value(Parameters.Y_AXIS, parameters, DENSITY_LABEL)

    filename = common.get_temp_file_name(format)

    current_backend = copy(matplotlib.get_backend())
    matplotlib.use('Agg')
    from matplotlib import pyplot

    pyplot.clf()
    pyplot.plot(x, y)
    pyplot.xlabel(x_axis)
    pyplot.ylabel(y_axis)
    pyplot.savefig(filename, bbox_inches="tight", transparent=True)
    pyplot.title(title)
    pyplot.clf()

    matplotlib.use(current_backend)

    return filename


def apply_semilogx(x, y, parameters=None):
    """
    Plot (semi-logarithmic way) the graph with axis values contained in x and y

    Parameters
    ------------
    x
        Values for x-axis
    y
        Values for y-axis
    parameters
        Parameters of the algorithm, including:
            Parameters.FORMAT -> Format of the target image
            Parameters.TITLE -> Title of the image

    Returns
    ------------
    temp_file_name
        Representation temporary file name
    """
    if parameters is None:
        parameters = {}

    format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    title = exec_utils.get_param_value(Parameters.TITLE, parameters, GRAPH_DEFAULT_TITLE)

    filename = common.get_temp_file_name(format)

    current_backend = copy(matplotlib.get_backend())
    matplotlib.use('Agg')
    from matplotlib import pyplot

    pyplot.clf()
    pyplot.semilogx(x, y)
    pyplot.xlabel(ATTRIBUTE_LABEL)
    pyplot.ylabel(DENSITY_LABEL)
    pyplot.savefig(filename, bbox_inches="tight", transparent=True)
    pyplot.title(title)
    pyplot.clf()

    matplotlib.use(current_backend)

    return filename
