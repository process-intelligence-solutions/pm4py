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
import base64
import os
import re
import shutil
import tempfile
import webbrowser

from pm4py.visualization.powl.variants import basic
from pm4py.visualization.powl.variants import net
from enum import Enum
from pm4py.util import exec_utils, constants
from typing import Optional, Dict, Any
from pm4py.objects.powl.obj import POWL


class POWLVisualizationVariants(Enum):
    BASIC = basic
    NET = net


class Parameters(Enum):
    FORMAT = "format"
    ENCODING = "encoding"


DEFAULT_VARIANT = POWLVisualizationVariants.BASIC


def apply(powl: POWL, variant=DEFAULT_VARIANT, frequency_tags=True, parameters: Optional[Dict[Any, Any]] = None)\
        -> str:
    """
    Method for POWL model representation

    Parameters
    -----------
    powl
        POWL model
    parameters
        Possible parameters of the algorithm:
            Parameters.FORMAT -> Format of the image (PDF, PNG, SVG; default PNG)
    variant
        Variant of the algorithm to use:
            - POWLVisualizationVariants.BASIC (default)
            - POWLVisualizationVariants.NET: BPMN-like visualization with decision gates
    frequency_tags
        Simplify the visualization using frequency tags

    Returns
    -----------
    str
        SVG Content
    """
    if parameters is None:
        parameters = {}

    if frequency_tags:
        powl = powl.simplify_using_frequent_transitions()

    viz = exec_utils.get_variant(variant).apply(powl, parameters=parameters)
    svg_content = viz.pipe().decode('utf-8')

    def inline_images_and_svgs(svg_content):
        img_pattern = re.compile(r'<image[^>]+xlink:href=["\'](.*?)["\'][^>]*>')

        def encode_file_to_base64(file_path):
            with open(file_path, 'rb') as file:
                return base64.b64encode(file.read()).decode('utf-8')

        def read_file_content_and_viewbox(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                content = re.sub(r'<\?xml.*?\?>', '', content, flags=re.DOTALL)
                content = re.sub(r'<!DOCTYPE.*?>', '', content, flags=re.DOTALL)
                viewBox_match = re.search(r'viewBox="([^"]*)"', content)
                viewBox = viewBox_match.group(1) if viewBox_match else "0 0 1 1"
                svg_content_match = re.search(r'<svg[^>]*>(.*?)</svg>', content, re.DOTALL)
                svg_content = svg_content_match.group(1) if svg_content_match else content
                return svg_content, viewBox

        def replace_with_inline_content(match):
            file_path = match.group(1)
            if file_path.lower().endswith('.svg'):
                svg_data, viewBox = read_file_content_and_viewbox(file_path)
                viewBox_values = [float(v) for v in viewBox.split()]
                actual_width, actual_height = viewBox_values[2], viewBox_values[3]

                intended_width = float(match.group(0).split('width="')[1].split('"')[0].replace('px', ''))
                intended_height = float(match.group(0).split('height="')[1].split('"')[0].replace('px', ''))
                x = float(match.group(0).split('x="')[1].split('"')[0])
                y = float(match.group(0).split('y="')[1].split('"')[0])

                scale_x = intended_width / actual_width
                scale_y = intended_height / actual_height

                return f'<g transform="translate({x},{y}) scale({scale_x},{scale_y})">{svg_data}</g>'
            else:
                base64_data = encode_file_to_base64(file_path)
                return match.group(0).replace(file_path, f"data:image/png;base64,{base64_data}")

        return img_pattern.sub(replace_with_inline_content, svg_content)

    svg_content_with_inline_images = inline_images_and_svgs(svg_content)

    return svg_content_with_inline_images


def save(svg_content: str, output_file_path: str, parameters: Optional[Dict[Any, Any]] = None):
    """
    Save the diagram in a specified format.

    Parameters
    -----------
    svg_content : str
        SVG content
    output_file_path : str
        Path where the output file should be saved
    """
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, "utf-8")

    with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.svg') as tmpfile:
        tmpfile.write(svg_content)
        tmpfile_path = tmpfile.name

    if output_file_path.endswith("svg"):
        shutil.move(tmpfile_path, output_file_path)
    elif output_file_path.endswith("png"):
        import cairosvg as cairosvg
        cairosvg.svg2png(bytestring=svg_content.encode(encoding), write_to=output_file_path)
    elif output_file_path.endswith("pdf"):
        import cairosvg as cairosvg
        cairosvg.svg2pdf(bytestring=svg_content.encode(encoding), write_to=output_file_path)
    else:
        raise Exception(f"Unsupported format! Please use 'svg', 'png', or 'pdf'.")

    if os.path.exists(tmpfile_path):
        os.remove(tmpfile_path)


def view(svg_content: str, parameters: Optional[Dict[Any, Any]] = None):
    """
    View the diagram

    Parameters
    -----------
    svg_content
        SVG content
    image_format
        image format
    """
    if parameters is None:
        parameters = {}

    if constants.DEFAULT_ENABLE_VISUALIZATIONS_VIEW:
        image_format = str(exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")).lower()
        encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, "utf-8")

        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.svg') as tmpfile:
            tmpfile.write(svg_content)
            tmpfile_path = tmpfile.name

            if image_format == "svg":
                absolute_path = os.path.abspath(tmpfile_path)
                return webbrowser.open('file://' + absolute_path)
            elif image_format == "png":
                import cairosvg as cairosvg
                cairosvg.svg2png(bytestring=svg_content.encode(encoding), write_to=tmpfile_path + '.png')
                webbrowser.open('file://' + os.path.abspath(tmpfile_path + '.png'))
            elif image_format == "pdf":
                import cairosvg as cairosvg
                cairosvg.svg2pdf(bytestring=svg_content.encode(encoding), write_to=tmpfile_path + '.pdf')
                webbrowser.open('file://' + os.path.abspath(tmpfile_path + '.pdf'))
            else:
                raise Exception(f"Unsupported format: {image_format}. Please use 'svg', 'png', or 'pdf'.")
