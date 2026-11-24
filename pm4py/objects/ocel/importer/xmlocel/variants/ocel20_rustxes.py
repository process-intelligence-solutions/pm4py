from typing import Optional, Dict, Any
from pm4py.objects.ocel.importer.xmlocel.variants import ocel20
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import compression
from pm4py.util.rustxes_utils import import_rustxes_backend


def apply(file_path: str, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    """
    Imports an OCEL 2.0 XML using the r4pm/rustxes parser.

    Parameters
    ---------------
    file_path
        Path to the OCEL 2.0 XML
    parameters
        Optional parameters.

    Returns
    ---------------
    ocel
        Object-centric event log
    """
    if parameters is None:
        parameters = {}

    rustxes_backend, _ = import_rustxes_backend()

    with compression.decompressed_path(file_path) as path:
        try:
            return rustxes_backend.import_ocel_xml_pm4py(path)
        except OSError:
            return ocel20.apply(path, parameters)
