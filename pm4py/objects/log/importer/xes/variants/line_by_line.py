import gzip
import os
import sys
from enum import Enum
from io import BytesIO

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.log.util import sorting
from pm4py.util import constants, xes_constants, exec_utils
from pm4py.util.dt_parsing import parser as dt_parser


class Parameters(Enum):
    TIMESTAMP_SORT = "timestamp_sort"
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    REVERSE_SORT = "reverse_sort"
    MAX_TRACES = "max_traces"
    MAX_BYTES = "max_bytes"
    SKIP_BYTES = "skip_bytes"
    SET_ATTRIBUTES_TO_READ = "set_attributes_to_read"
    DECOMPRESS_SERIALIZATION = "decompress_serialization"
    ENCODING = "encoding"


def apply(filename, parameters=None):
    return import_log(filename, parameters)


def __fetch_param_value(param, params):
    return params[param] if param in params else param.value


def read_attribute_key_value(tag, content, date_parser, values_dict, set_attributes_to_read):
    """
    Reads an attribute from the line of the log

    Parameters
    --------------
    tag
        Tag
    content
        Full content of the line
    date_parser
        Date parser
    values_dict
        Dictionary of keys/values already met during the parsing
    set_attributes_to_read
        Names of the attributes that should be parsed. If None, then, all the attributes are parsed.

    Returns
    --------------
    key
        Key of the attribute
    value
        Value of the attribute
    """
    key = content[1]
    value = None

    if set_attributes_to_read is None or key in set_attributes_to_read:
        if tag.startswith("string"):
            value = content[3]
        elif tag.startswith("date"):
            value = date_parser.apply(content[3])
        elif tag.startswith("int"):
            value = int(content[3])
        elif tag.startswith("float"):
            value = float(content[3])
        elif tag.startswith("boolean"):
            value = True if content[3] == "true" else False
        else:
            value = content[3]

        # limits the number of different instantiations of the same key
        if key in values_dict:
            key = values_dict[key]
        else:
            values_dict[key] = key

        # limits the number of different instantations of the same value
        if value in values_dict:
            value = values_dict[value]
        else:
            values_dict[value] = value

    return key, value


def import_log_from_file_object(f, encoding, file_size=sys.maxsize, parameters=None):
    """
    Import a log object from a (XML) file object

    Parameters
    -----------
    f
        file object
    encoding
        Encoding
    file_size
        Size of the file (measured on disk)
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

    Returns
    -----------
    log
        Log file
    """
    values_dict = {}
    date_parser = dt_parser.get()

    set_attributes_to_read = exec_utils.get_param_value(Parameters.SET_ATTRIBUTES_TO_READ, parameters, None)
    max_no_traces_to_import = exec_utils.get_param_value(Parameters.MAX_TRACES, parameters, sys.maxsize)
    timestamp_sort = exec_utils.get_param_value(Parameters.TIMESTAMP_SORT, parameters, False)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)
    reverse_sort = exec_utils.get_param_value(Parameters.REVERSE_SORT, parameters, False)

    skip_bytes = exec_utils.get_param_value(Parameters.SKIP_BYTES, parameters, False)
    max_bytes_to_read = exec_utils.get_param_value(Parameters.MAX_BYTES, parameters, sys.maxsize)

    if file_size > max_bytes_to_read:
        skip_bytes = file_size - max_bytes_to_read

    log = EventLog()
    tracecount = 0
    trace = None
    event = None

    f.seek(skip_bytes)

    for line in f:
        content = line.decode(encoding).split("\"")
        if len(content) > 0:
            tag = content[0].split("<")[-1]
            if trace is not None:
                if event is not None:
                    if len(content) == 5:
                        key, value = read_attribute_key_value(tag, content, date_parser, values_dict,
                                                              set_attributes_to_read)
                        if value is not None:
                            event[key] = value
                    elif tag.startswith("/event"):
                        trace.append(event)
                        event = None
                elif tag.startswith("event"):
                    event = Event()
                elif len(content) == 5:
                    key, value = read_attribute_key_value(tag, content, date_parser, values_dict,
                                                          set_attributes_to_read)
                    if value is not None:
                        trace.attributes[key] = value
                elif tag.startswith("/trace"):
                    log.append(trace)
                    tracecount += 1
                    if tracecount > max_no_traces_to_import:
                        break
                    trace = None
            elif tag.startswith("trace"):
                trace = Trace()

    if timestamp_sort:
        log = sorting.sort_timestamp(log, timestamp_key=timestamp_key, reverse_sort=reverse_sort)

    # sets the activity key as default classifier in the log's properties
    log.properties[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = xes_constants.DEFAULT_NAME_KEY
    log.properties[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = xes_constants.DEFAULT_NAME_KEY
    # sets the default timestamp key
    log.properties[constants.PARAMETER_CONSTANT_TIMESTAMP_KEY] = xes_constants.DEFAULT_TIMESTAMP_KEY
    # sets the default resource key
    log.properties[constants.PARAMETER_CONSTANT_RESOURCE_KEY] = xes_constants.DEFAULT_RESOURCE_KEY
    # sets the default transition key
    log.properties[constants.PARAMETER_CONSTANT_TRANSITION_KEY] = xes_constants.DEFAULT_TRANSITION_KEY
    # sets the default group key
    log.properties[constants.PARAMETER_CONSTANT_GROUP_KEY] = xes_constants.DEFAULT_GROUP_KEY
    
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
        Parameters of the algorithm, including
            Parameters.TIMESTAMP_SORT -> Specify if we should sort log by timestamp
            Parameters.TIMESTAMP_KEY -> If sort is enabled, then sort the log by using this key
            Parameters.REVERSE_SORT -> Specify in which direction the log should be sorted
            Parameters.INSERT_TRACE_INDICES -> Specify if trace indexes should be added as event attribute for each event
            Parameters.MAX_TRACES -> Specify the maximum number of traces to import from the log (read in order in the XML file)
            Parameters.DECOMPRESS_SERIALIZATION -> Specify if the string needs to be decompressed during the parsing
            Parameters.SET_ATTRIBUTES_TO_READ -> Names of the attributes that should be parsed. If not specified,
                                                then, all the attributes are parsed.
            Parameters.ENCODING -> Regulates the encoding of the log (default: utf-8)

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
