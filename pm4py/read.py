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
from typing import Tuple, Dict, Optional, Union
import os

import tempfile
from urllib.parse import urlparse

from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.log.obj import EventLog
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util import constants

from pandas import DataFrame
from pm4py.util.rustxes_utils import get_rustxes_backend_name
from pm4py.utils import __rustxes_usage_warning, __rustxes_non_usage_warning

INDEX_COLUMN = "@@index"

__doc__ = """
The `pm4py.read` module contains all functionality related to reading files and objects from disk (or via URIs).
"""


def _matches_extension(file_path: str, extensions: Tuple[str, ...]) -> bool:
    file_path = str(file_path).lower()
    return any(
        file_path.endswith(extension)
        or file_path.endswith(extension + ".gz")
        for extension in extensions
    )


def _resolve_path(file_path: str) -> str:
    """
    Resolve a file path which can be either:
    - A local file path
    - An HTTP/HTTPS URL

    If the path is a remote URL, the file is downloaded to a temporary file,
    and the local temporary file path is returned.
    """
    parsed = urlparse(file_path)
    if parsed.scheme in ("http", "https"):
        import requests
        response = requests.get(file_path)
        response.raise_for_status()
        # Infer the file extension from the URL (if available)
        _, extension = os.path.splitext(parsed.path)
        if not extension:
            extension = ".tmp"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
        temp_file.write(response.content)
        temp_file.flush()
        temp_file.close()
        return temp_file.name
    else:
        if not os.path.exists(file_path):
            raise Exception(f"File does not exist at path: {file_path}")
        return file_path


def read_xes(
    file_path: str,
    variant: Optional[str] = None,
    return_legacy_log_object: bool = constants.DEFAULT_READ_XES_LEGACY_OBJECT,
    return_pl_lazyframe: bool = False,
    encoding: str = constants.DEFAULT_ENCODING,
    **kwargs
) -> Union[DataFrame, EventLog]:
    r"""Reads an event log stored in XES format (see `xes-standard <https://xes-standard.org/>`_).
    Returns a table (`pandas.DataFrame`) view of the event log or an `EventLog` object.

    :param file_path: Path/URI to the event log (`.xes` file).
    :param variant: Variant of the importer to use. Options include:

        - "iterparse" – traditional XML parser,
        - "line_by_line" – text-based line-by-line importer,
        - "chunk_regex" – chunk-of-bytes importer (default),
        - "iterparse20" – XES 2.0 importer,
        - "r4pm" – Rust-based importer via `r4pm.df`,
        - "rustxes" – compatibility alias for the Rust-based importer.

    :param return_legacy_log_object: Boolean indicating whether to return a legacy `EventLog` object (default: `False`).
    :param return_pl_lazyframe: Returns a Polars LazyFrame (default: `False`).
    :param encoding: Encoding to be used (default: `utf-8`).
    :param \**kwargs: Additional parameters to pass to the importer.
    :rtype: `pandas.DataFrame` or `pm4py.objects.log.obj.EventLog`

    .. code-block:: python3

        import pm4py

        log = pm4py.read_xes("<path_or_uri_to_xes_file>")
    """
    local_path = _resolve_path(file_path)

    if variant is None:
        backend_name = get_rustxes_backend_name()
        if backend_name is not None:
            __rustxes_usage_warning()
            variant = backend_name
        else:
            __rustxes_non_usage_warning()
            variant = constants.DEFAULT_XES_PARSER

    from pm4py.objects.log.importer.xes import importer as xes_importer

    v = xes_importer.Variants.CHUNK_REGEX
    if variant == "iterparse_20":
        v = xes_importer.Variants.ITERPARSE_20
    elif variant == "iterparse":
        v = xes_importer.Variants.ITERPARSE
    elif variant == "lxml":
        v = xes_importer.Variants.ITERPARSE
    elif variant == "iterparse_mem_compressed":
        v = xes_importer.Variants.ITERPARSE_MEM_COMPRESSED
    elif variant == "line_by_line":
        v = xes_importer.Variants.LINE_BY_LINE
    elif variant == "chunk_regex":
        v = xes_importer.Variants.CHUNK_REGEX
    elif variant == "rustxes" or variant == "r4pm":
        v = xes_importer.Variants.RUSTXES

    from copy import copy

    parameters = copy(kwargs)
    parameters["encoding"] = encoding
    parameters["return_legacy_log_object"] = return_legacy_log_object
    parameters["return_pl_lazyframe"] = return_pl_lazyframe

    log = xes_importer.apply(local_path, variant=v, parameters=parameters)

    if return_legacy_log_object:
        pass
    else:
        if isinstance(log, EventLog):
            from pm4py.objects.conversion.log import converter as log_converter
            log = log_converter.apply(
                log, variant=log_converter.Variants.TO_DATA_FRAME, parameters=parameters
            )

        if constants.DEFAULT_XES_FORMAT_DATAFRAME:
            from pm4py.utils import format_dataframe
            log = format_dataframe(log)

    return log


def read_pnml(
    file_path: str,
    auto_guess_final_marking: bool = False,
    encoding: str = constants.DEFAULT_ENCODING,
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Reads a Petri net object from a `.pnml` file.
    The returned Petri net object is a tuple containing:

    1. PetriNet object (`PetriNet`)
    2. Initial Marking (`Marking`)
    3. Final Marking (`Marking`)

    :param file_path: Path/URI to the Petri net model (`.pnml` file).
    :param auto_guess_final_marking: Boolean indicating whether to automatically guess the final marking (default: `False`).
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `Tuple[PetriNet, Marking, Marking]`

    .. code-block:: python3

        import pm4py

        pn = pm4py.read_pnml("<path_or_uri_to_pnml_file>")
    """
    local_path = _resolve_path(file_path)
    from pm4py.objects.petri_net.importer import importer as pnml_importer

    net, im, fm = pnml_importer.apply(
        local_path,
        parameters={
            "auto_guess_final_marking": auto_guess_final_marking,
            "encoding": encoding,
        },
    )
    return net, im, fm


def read_ptml(
    file_path: str, encoding: str = constants.DEFAULT_ENCODING
) -> ProcessTree:
    """
    Reads a process tree object from a `.ptml` file.

    :param file_path: Path/URI to the process tree file on disk.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `ProcessTree`

    .. code-block:: python3

        import pm4py

        process_tree = pm4py.read_ptml("<path_or_uri_to_ptml_file>")
    """
    local_path = _resolve_path(file_path)
    from pm4py.objects.process_tree.importer import importer as tree_importer

    tree = tree_importer.apply(local_path, parameters={"encoding": encoding})
    return tree


def read_dfg(
    file_path: str, encoding: str = constants.DEFAULT_ENCODING
) -> Tuple[Dict[Tuple[str, str], int], Dict[str, int], Dict[str, int]]:
    """
    Reads a Directly-Follows Graph (DFG) from a `.dfg` file.
    The returned DFG object is a tuple containing:

    1. DFG (`Dict[Tuple[str, str], int]`): Maps pairs of activities to their occurrence count.
       For example, `DFG[('a', 'b')] = k` indicates that activity `'a'` is directly followed by activity `'b'` a total of `k` times in the log.
    2. Start Activity Dictionary (`Dict[str, int]`): Maps activities to the number of traces they start.
       For example, `S['a'] = k` implies that activity `'a'` starts `k` traces in the event log.
    3. End Activity Dictionary (`Dict[str, int]`): Maps activities to the number of traces they end.
       For example, `E['z'] = k` implies that activity `'z'` ends `k` traces in the event log.

    :param file_path: Path/URI to the DFG model file.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `Tuple[Dict[Tuple[str, str], int], Dict[str, int], Dict[str, int]]`

    .. code-block:: python3

        import pm4py

        dfg = pm4py.read_dfg("<path_or_uri_to_dfg_file>")
    """
    local_path = _resolve_path(file_path)
    from pm4py.objects.dfg.importer import importer as dfg_importer

    dfg, start_activities, end_activities = dfg_importer.apply(
        local_path, parameters={"encoding": encoding}
    )
    return dfg, start_activities, end_activities


def read_bpmn(
    file_path: str, encoding: str = constants.DEFAULT_ENCODING
) -> BPMN:
    """
    Reads a BPMN model from a `.bpmn` file.

    Data object and data store references are represented as graph nodes.
    Associations and message flows with unresolved endpoints are skipped with a warning.

    :param file_path: Path/URI to the BPMN model file.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `BPMN`
    :raises ValueError: If graph element IDs are duplicated or a sequence flow
        has an unresolved or invalid endpoint.

    .. code-block:: python3

        import pm4py

        bpmn = pm4py.read_bpmn('<path_or_uri_to_bpmn_file>')
    """
    local_path = _resolve_path(file_path)
    from pm4py.objects.bpmn.importer import importer as bpmn_importer

    bpmn_graph = bpmn_importer.apply(
        local_path, parameters={"encoding": encoding}
    )
    return bpmn_graph


def read_ocel(
    file_path: str,
    objects_path: Optional[str] = None,
    encoding: str = constants.DEFAULT_ENCODING,
) -> OCEL:
    """
    Reads an object-centric event log from a file (see: http://www.ocel-standard.org/).
    Returns an `OCEL` object.

    :param file_path: Path/URI to the object-centric event log file.
    :param objects_path: [Optional] Path/URI to the objects dataframe file.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel("<path_or_uri_to_ocel_file>")
    """
    local_path = _resolve_path(file_path)
    local_objects_path = _resolve_path(objects_path) if objects_path else None

    if local_path.lower().endswith("csv"):
        return read_ocel_csv(local_path, local_objects_path, encoding=encoding)
    elif local_path.lower().endswith("jsonocel"):
        return read_ocel_json(local_path, encoding=encoding)
    elif local_path.lower().endswith("xmlocel"):
        return read_ocel_xml(local_path, encoding=encoding)
    elif local_path.lower().endswith(".sqlite"):
        return read_ocel_sqlite(local_path, encoding=encoding)
    raise Exception("Unsupported file format")


def read_ocel_csv(
    file_path: str,
    objects_path: Optional[str] = None,
    encoding: str = constants.DEFAULT_ENCODING,
) -> OCEL:
    """
    Reads an object-centric event log from a CSV file (see: http://www.ocel-standard.org/).
    Returns an `OCEL` object.

    :param file_path: Path/URI to the object-centric event log file (`.csv`).
    :param objects_path: [Optional] Path/URI to the objects dataframe file.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel_csv("<path_or_uri_to_ocel_file.csv>")
    """
    from pm4py.objects.ocel.importer.csv import importer as csv_importer

    return csv_importer.apply(
        file_path, objects_path=objects_path, parameters={"encoding": encoding}
    )


def read_ocel_json(
    file_path: str, encoding: str = constants.DEFAULT_ENCODING
) -> OCEL:
    """
    Reads an object-centric event log from a JSON-OCEL file (see: http://www.ocel-standard.org/).
    Returns an `OCEL` object.

    :param file_path: Path/URI to the object-centric event log file (`.jsonocel`).
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel_json("<path_or_uri_to_ocel_file.jsonocel>")
    """
    from pm4py.objects.ocel.importer.jsonocel import importer as jsonocel_importer

    return jsonocel_importer.apply(
        file_path,
        variant=jsonocel_importer.Variants.CLASSIC,
        parameters={"encoding": encoding},
    )


def read_ocel_xml(
    file_path: str, encoding: str = constants.DEFAULT_ENCODING
) -> OCEL:
    """
    Reads an object-centric event log from an XML-OCEL file (see: http://www.ocel-standard.org/).
    Returns an `OCEL` object.

    :param file_path: Path/URI to the object-centric event log file (`.xmlocel`).
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel_xml("<path_or_uri_to_ocel_file.xmlocel>")
    """
    from pm4py.objects.ocel.importer.xmlocel import importer as xmlocel_importer

    return xmlocel_importer.apply(
        file_path,
        variant=xmlocel_importer.Variants.CLASSIC,
        parameters={"encoding": encoding},
    )


def read_ocel_sqlite(
    file_path: str, encoding: str = constants.DEFAULT_ENCODING
) -> OCEL:
    """
    Reads an object-centric event log from a SQLite database (see: http://www.ocel-standard.org/).
    Returns an `OCEL` object.

    :param file_path: Path/URI to the SQLite database file (`.sqlite`).
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel_sqlite("<path_or_uri_to_ocel_file.sqlite>")
    """
    from pm4py.objects.ocel.importer.sqlite import importer as sqlite_importer

    return sqlite_importer.apply(
        file_path,
        variant=sqlite_importer.Variants.PANDAS_IMPORTER,
        parameters={"encoding": encoding},
    )


def read_ocel2(
    file_path: str,
    variant_str: Optional[str] = None,
    encoding: str = constants.DEFAULT_ENCODING,
) -> OCEL:
    """
    Reads an OCEL 2.0 event log.

    :param file_path: Path/URI to the OCEL 2.0 event log file.
    :param variant_str: Use ``standard`` to select the Python reader for JSON or XML.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    Supported file formats based on extension:
        - `.ocel.zip` – bundled CSV/Parquet archive,
        - `.sqlite` – SQLite database,
        - `.ocel.csv` – compact OCEL 2.0 CSV file,
        - `.xml`, `.xmlocel`, `.xml.gz`, or `.xmlocel.gz` – XML file,
        - `.json`, `.jsonocel`, `.json.gz`, or `.jsonocel.gz` – JSON file.

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2("<path_or_uri_to_ocel_file>")
    """
    local_path = _resolve_path(file_path)
    extension_path = str(file_path)

    if (
        extension_path.lower().endswith(".ocel.zip")
        or local_path.lower().endswith(".ocel.zip")
        or (
            os.path.isdir(local_path)
            and os.path.exists(os.path.join(local_path, "ocel-meta.json"))
        )
    ):
        return read_ocel2_bundle(local_path, encoding=encoding)
    if extension_path.lower().endswith("sqlite") or local_path.lower().endswith(
        "sqlite"
    ):
        return read_ocel2_sqlite(
            local_path, variant_str=variant_str, encoding=encoding
        )
    elif extension_path.lower().endswith(".ocel.csv") or local_path.lower().endswith(".ocel.csv"):
        return read_ocel2_csv(local_path, encoding=encoding)
    elif _matches_extension(extension_path, ("xml", "xmlocel")) or _matches_extension(
        local_path, ("xml", "xmlocel")
    ):
        return read_ocel2_xml(
            local_path, encoding=encoding, variant_str=variant_str
        )
    elif _matches_extension(extension_path, ("json", "jsonocel")) or _matches_extension(
        local_path, ("json", "jsonocel")
    ):
        return read_ocel2_json(
            local_path, encoding=encoding, variant_str=variant_str
        )
    raise Exception("Unsupported file format for OCEL 2.0")


def read_ocel2_bundle(
    file_path: str,
    encoding: str = constants.DEFAULT_ENCODING,
) -> OCEL:
    """
    Reads an OCEL 2.0 event log from the bundled CSV/Parquet format.

    The input can be a ``.ocel.zip`` archive or an uncompressed bundle directory
    containing ``ocel-meta.json``.

    :param file_path: Path/URI to the bundled OCEL 2.0 archive or directory.
    :param encoding: Encoding for metadata and CSV files; the format requires `utf-8`.
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2_bundle("<path_to_bundle.ocel.zip>")
    """
    from pm4py.objects.ocel.importer.bundled import importer as bundled_importer

    return bundled_importer.apply(file_path, parameters={"encoding": encoding})


def read_ocel2_csv(
    file_path: str,
    encoding: str = constants.DEFAULT_ENCODING,
) -> OCEL:
    """
    Reads an OCEL 2.0 event log from a compact CSV file.

    :param file_path: Path/URI to the OCEL 2.0 CSV file (`.ocel.csv`).
    :param encoding: Encoding to be used; the format requires `utf-8`.
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2_csv("<path_or_uri_to_ocel_file.ocel.csv>")
    """
    from pm4py.objects.ocel.importer.csv import importer as csv_importer

    return csv_importer.apply(
        file_path,
        variant=csv_importer.Variants.OCEL20,
        parameters={"encoding": encoding},
    )


def read_ocel2_json(
    file_path: str,
    encoding: str = constants.DEFAULT_ENCODING,
    variant_str: Optional[str] = None,
) -> OCEL:
    """
    Reads an OCEL 2.0 event log from a JSON-OCEL2 file.

    :param file_path: Path/URI to the JSON file (`.json`, `.jsonocel`, or their `.gz` variants).
    :param encoding: Encoding to be used (default: `utf-8`).
    :param variant_str: Use ``standard`` for the Python reader, which retains declared
        attribute types and timestamps on first object attribute assignments.
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2_json("<path_or_uri_to_ocel_file.jsonocel>")
    """
    from pm4py.objects.ocel.importer.jsonocel import importer as jsonocel_importer

    variant = jsonocel_importer.Variants.OCEL20_STANDARD
    if variant_str != "standard" and get_rustxes_backend_name() is not None:
        variant = jsonocel_importer.Variants.OCEL20_RUSTXES

    return jsonocel_importer.apply(
        file_path, variant=variant, parameters={"encoding": encoding}
    )


def read_ocel2_sqlite(
    file_path: str,
    variant_str: Optional[str] = None,
    encoding: str = constants.DEFAULT_ENCODING,
) -> OCEL:
    """
    Reads an OCEL 2.0 event log from a SQLite database.

    :param file_path: Path/URI to the OCEL 2.0 SQLite database file (`.sqlite`).
    :param variant_str: [Optional] Specification of the importer variant to be used.
    :param encoding: Encoding to be used (default: `utf-8`).
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2_sqlite("<path_or_uri_to_ocel_file.sqlite>")
    """
    from pm4py.objects.ocel.importer.sqlite import importer as sqlite_importer

    return sqlite_importer.apply(
        file_path,
        variant=sqlite_importer.Variants.OCEL20,
        parameters={"encoding": encoding},
    )


def read_ocel2_xml(
    file_path: str,
    encoding: str = constants.DEFAULT_ENCODING,
    variant_str: Optional[str] = None,
) -> OCEL:
    """
    Reads an OCEL 2.0 event log from an XML file.

    :param file_path: Path/URI to the OCEL 2.0 XML file (`.xml`, `.xmlocel`, or their `.gz` variants).
    :param encoding: Encoding to be used (default: `utf-8`).
    :param variant_str: Use ``standard`` for the Python reader, which retains declared
        attribute types and timestamps on first object attribute assignments.
    :rtype: `OCEL`

    .. code-block:: python3

        import pm4py

        ocel = pm4py.read_ocel2_xml("<path_or_uri_to_ocel_file.xmlocel>")
    """
    from pm4py.objects.ocel.importer.xmlocel import importer as xml_importer

    variant = xml_importer.Variants.OCEL20
    if variant_str != "standard" and get_rustxes_backend_name() is not None:
        variant = xml_importer.Variants.OCEL20_RUSTXES

    return xml_importer.apply(
        file_path, variant=variant, parameters={"encoding": encoding}
    )
