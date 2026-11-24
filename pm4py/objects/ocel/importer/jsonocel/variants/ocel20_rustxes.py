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
from typing import Optional, Dict, Any
from pm4py.objects.ocel.importer.jsonocel.variants import ocel20_standard
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import compression
from pm4py.util.rustxes_utils import import_rustxes_backend


def apply(file_path: str, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    """
    Imports an OCEL 2.0 JSON using the r4pm/rustxes parser.

    Parameters
    ---------------
    file_path
        Path to the OCEL 2.0 JSON
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
            return rustxes_backend.import_ocel_json_pm4py(path)
        except OSError:
            # Some published logs use null qualifiers or values. The Python
            # importer also accepts these legacy OCEL 2 serializations.
            return ocel20_standard.apply(path, parameters)
