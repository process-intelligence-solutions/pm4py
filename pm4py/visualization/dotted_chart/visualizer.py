import shutil
from enum import Enum
from typing import List, Any, Dict, Optional, Union

import pandas as pd

from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventLog
from pm4py.util import exec_utils, vis_utils
from pm4py.visualization.dotted_chart.variants import classic
from pm4py.util import constants, pandas_utils


class Variants(Enum):
    CLASSIC = classic


def apply(log_obj: Union[pd.DataFrame, EventLog], attributes: List[str], variant=Variants.CLASSIC,
          parameters: Optional[Dict[Any, Any]] = None) -> str:
    """
    Creates the dotted chart with the log objects and the provided attributes

    Parameters
    ---------------
    log_obj
        Log object
    attributes
        List of attributes that should be included in the dotted chart
    parameters
        Variant-specific parameters

    Returns
    ---------------
    file_path
        Path to the dotted chart visualization
    """
    if parameters is None:
        parameters = {}

    if pandas_utils.check_is_pandas_dataframe(log_obj):
        log_obj = log_obj[list(set(attributes))]

    parameters["deepcopy"] = False
    stream = log_converter.apply(log_obj, variant=log_converter.Variants.TO_EVENT_STREAM, parameters=parameters)
    stream = [tuple(y[a] for a in attributes) for y in stream]

    return exec_utils.get_variant(variant).apply(stream, attributes, parameters=parameters)


def view(figure: str):
    """
    Views the dotted chart on the screen

    Parameters
    ---------------
    figure
        Path to the dotted chart
    """
    if constants.DEFAULT_ENABLE_VISUALIZATIONS_VIEW:
        if constants.DEFAULT_GVIZ_VIEW == "matplotlib_view":
            import matplotlib.pyplot as plt
            import matplotlib.image as mpimg
            img = mpimg.imread(figure)
            plt.axis('off')
            plt.tight_layout(pad=0, w_pad=0, h_pad=0)
            plt.imshow(img)
            plt.show()
            return

        if vis_utils.check_visualization_inside_jupyter():
            vis_utils.view_image_in_jupyter(figure)
        else:
            vis_utils.open_opsystem_image_viewer(figure)


def save(figure: str, output_file_path: str):
    """
    Saves the dotted chart to a specified path

    Parameters
    ----------------
    figure
        Current path to the dotted chart
    output_file_path
        Destination path
    """
    shutil.copyfile(figure, output_file_path)
    return ""


def serialize(figure: str):
    """
    Performs the serialization of the dotted chart visualization

    Parameters
    -----------------
    figure
        Current path to the dotted chart
    """
    with open(figure, "rb") as f:
        return f.read()


def matplotlib_view(figure: str):
    """
    Views the dotted chart on the screen using Matplotlib

    Parameters
    ---------------
    figure
        Path to the dotted chart
    """
    if constants.DEFAULT_ENABLE_VISUALIZATIONS_VIEW:
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg

        img = mpimg.imread(figure)
        plt.imshow(img)
        plt.show()
