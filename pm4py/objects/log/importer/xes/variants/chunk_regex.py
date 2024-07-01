import gzip
import os
import sys
from enum import Enum
from io import BytesIO

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.util import constants, exec_utils
from pm4py.util.dt_parsing import parser as dt_parser
import re
from collections import deque


class Parameters(Enum):
    DECOMPRESS_SERIALIZATION = "decompress_serialization"
    ENCODING = "encoding"


def apply(filename, parameters=None):
    return import_log(filename, parameters)


def import_log_from_file_object(F, encoding, file_size=sys.maxsize, parameters=None):
    """
    Import a log object from a (XML) file object

    Parameters
    -----------
    F
        file object
    encoding
        Encoding
    file_size
        Size of the file (measured on disk)
    parameters
        Parameters of the algorithm

    Returns
    -----------
    log
        Log file
    """
    nb = 2 ** 12 # bytes per chunk
    rex = re.compile(r"(<|>)")
    parser = dt_parser.get()
    cont = F.read(nb)
    curr_els_attrs = []
    fk_dict = {}
    log = EventLog()
    trace = None
    while cont:
        lst = deque(rex.split(cont.decode(encoding)))
        while lst:
            el = lst.popleft()
            if len(el.rstrip()) > 0:
                if el == '<':
                    continue
                elif el == '>':
                    continue
                while len(lst) == 0:
                    # need to read more
                    cont = F.read(nb)
                    if cont:
                        lst2 = rex.split(cont.decode(encoding))
                        el = el + lst2[0]
                        lst = deque(lst2[1:])
                    else:
                        break
                if el[0] == '/':
                    if len(curr_els_attrs) > 1:
                        curr_els_attrs.pop()
                    else:
                        return log
                    continue
                idx = el.find(' ')
                if idx > -1:
                    tag = el[:idx]
                    el = el.split('\"')
                    el[-1] = el[-1].strip()
                    if tag == "string":
                        curr_els_attrs[-1][el[1]] = el[3]
                        if el[-1] != '/':
                            curr_els_attrs.append(fk_dict)
                        continue
                    elif tag == "date":
                        curr_els_attrs[-1][el[1]] = parser.apply(el[3])
                        if el[-1] != '/':
                            curr_els_attrs.append(fk_dict)
                        continue
                    elif tag == "int":
                        curr_els_attrs[-1][el[1]] = int(el[3])
                        if el[-1] != '/':
                            curr_els_attrs.append(fk_dict)
                        continue
                    elif tag == "float":
                        curr_els_attrs[-1][el[1]] = float(el[3])
                        if el[-1] != '/':
                            curr_els_attrs.append(fk_dict)
                        continue
                    elif tag == "boolean":
                        curr_els_attrs[-1][el[1]] = True if el[3] == "true" else False
                        if el[-1] != '/':
                            curr_els_attrs.append(fk_dict)
                        continue
                    elif tag == "extension":
                        ext = log.extensions
                        name = el[[i for i in range(len(el)) if "name=" in el[i]][0] + 1]
                        prefix = el[[i for i in range(len(el)) if "prefix=" in el[i]][0] + 1]
                        uri = el[[i for i in range(len(el)) if "uri=" in el[i]][0] + 1]
                        ext[name] = {"prefix": prefix, "uri": uri}
                        if el[-1] != '/':
                            curr_els_attrs.append(ext)
                        continue
                    elif tag == "classifier":
                        classif = log.classifiers
                        name = el[[i for i in range(len(el)) if "name=" in el[i]][0] + 1]
                        keys = el[[i for i in range(len(el)) if "keys=" in el[i]][0] + 1]
                        if "'" in keys:
                            classif[name] = [x for x in keys.split("'") if x.strip()]
                        else:
                            classif[name] = keys.split()
                        if el[-1] != '/':
                            curr_els_attrs.append(classif)
                        continue
                    elif tag == "global":
                        glob = log.omni_present
                        scope = el[1]
                        dct = {}
                        glob[scope] = dct
                        if el[-1] != '/':
                            curr_els_attrs.append(dct)
                        continue
                    elif tag == "log":
                        curr_els_attrs.append(log.attributes)
                        continue
                    elif tag == "list":
                        dct_children = {}
                        dct = {"value": None, "children": dct_children}
                        curr_els_attrs[-1][el[1]] = dct
                        curr_els_attrs.append(dct_children)
                        continue
                else:
                    if el == "event":
                        event = Event()
                        curr_els_attrs.append(event)
                        trace.append(event)
                        continue
                    elif el == "trace":
                        trace = Trace()
                        curr_els_attrs.append(trace.attributes)
                        log.append(trace)
                        continue
                    elif el == "log":
                        curr_els_attrs.append(log.attributes)
                        continue
                    elif el == "values":
                        curr_els_attrs.append(curr_els_attrs[-1])
        cont = F.read(nb)
    return log


def import_log(filename, parameters=None):
    """
    Import a log object from a XML file
    containing the traces, the events and the simple attributes of them

    Parameters
    -----------
    filename
        XES file to parse
    parameters
        Parameters of the algorithm, including
            Parameters.TIMESTAMP_SORT -> Specify if we should sort log by timestamp
            Parameters.TIMESTAMP_KEY -> If sort is enabled, then sort the log by using this key
            Parameters.REVERSE_SORT -> Specify in which direction the log should be sorted
            Parameters.MAX_TRACES -> Specify the maximum number of traces to import from the log (read in order in the XML file)
            Parameters.MAX_BYTES -> Maximum number of bytes to read
            Parameters.SKYP_BYTES -> Number of bytes to skip
            Parameters.SET_ATTRIBUTES_TO_READ -> Names of the attributes that should be parsed. If not specified,
                                                then, all the attributes are parsed.
            Parameters.ENCODING -> Regulates the encoding of the log (default: utf-8)

    Returns
    -----------
    log
        Log file
    """
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, constants.DEFAULT_ENCODING)

    is_compressed = filename.endswith(".gz")
    file_size = os.stat(filename).st_size

    if is_compressed:
        f = gzip.open(filename, mode="rb")
    else:
        f = open(filename, "rb")

    log = import_log_from_file_object(f, encoding, file_size=file_size, parameters=parameters)

    f.close()

    return log


def import_from_string(log_string, parameters=None):
    """
    Deserialize a text/binary string representing a XES log

    Parameters
    -----------
    log_string
        String that contains the XES
    parameters
        Parameters of the algorithm

    Returns
    -----------
    log
        Trace log object
    """
    if parameters is None:
        parameters = {}

    encoding = exec_utils.get_param_value(Parameters.ENCODING, parameters, constants.DEFAULT_ENCODING)

    decompress_serialization = exec_utils.get_param_value(Parameters.DECOMPRESS_SERIALIZATION, parameters, False)

    if type(log_string) is str:
        log_string = log_string.encode(constants.DEFAULT_ENCODING)

    b = BytesIO(log_string)

    if decompress_serialization:
        s = gzip.GzipFile(fileobj=b, mode="rb")
    else:
        s = b

    log = import_log_from_file_object(s, encoding, parameters=parameters)
    s.close()
    b.close()
    return log
