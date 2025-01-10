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

import os
import importlib.util
from enum import Enum


def get_param_from_env(name, default):
    if name in os.environ and os.environ[name]:
        return str(os.environ[name])
    return default


TEST_CUDF_DATAFRAMES_ENVIRONMENT = get_param_from_env("PM4PY_TEST_CUDF_DATAFRAMES_ENVIRONMENT", False)


def get_default_timestamp_format():
    if importlib.util.find_spec("cudf") or TEST_CUDF_DATAFRAMES_ENVIRONMENT:
        return "%Y-%m-%d %H:%M:%S"
        pass

    return None


def get_default_xes_timestamp_format():
    if importlib.util.find_spec("cudf") or TEST_CUDF_DATAFRAMES_ENVIRONMENT:
        return "%Y-%m-%dT%H:%M:%S"
        pass

    return "ISO8601"


def get_default_is_aware_enabled():
    if importlib.util.find_spec("cudf") or TEST_CUDF_DATAFRAMES_ENVIRONMENT:
        return False
        pass
    
    return True


PARAMETER_CONSTANT_ACTIVITY_KEY = 'pm4py:param:activity_key'
PARAMETER_CONSTANT_ATTRIBUTE_KEY = "pm4py:param:attribute_key"
PARAMETER_CONSTANT_TIMESTAMP_KEY = 'pm4py:param:timestamp_key'
PARAMETER_CONSTANT_START_TIMESTAMP_KEY = 'pm4py:param:start_timestamp_key'
PARAMETER_CONSTANT_CASEID_KEY = 'pm4py:param:case_id_key'
PARAMETER_CONSTANT_RESOURCE_KEY = 'pm4py:param:resource_key'
PARAMETER_CONSTANT_TRANSITION_KEY = 'pm4py:param:transition_key'
PARAMETER_CONSTANT_GROUP_KEY = 'pm4py:param:group_key'

GROUPED_DATAFRAME = 'grouped_dataframe'
RETURN_EA_COUNT_DICT_AUTOFILTER = 'return_ea_count_dict_autofilter'
PARAM_MOST_COMMON_VARIANT = "most_common_variant"
PARAM_MOST_COMMON_PATHS = "most_common_paths"

CASE_CONCEPT_NAME = "case:concept:name"
CASE_ATTRIBUTE_GLUE = 'case:concept:name'
CASE_ATTRIBUTE_PREFIX = 'case:'

# the following can be removed
PARAMETER_KEY_CASE_GLUE = 'case_id_glue'
PARAMETER_KEY_CASE_ATTRIBUTE_PRFIX = 'case:'

STOCHASTIC_DISTRIBUTION = "stochastic_distribution"
LAYOUT_INFORMATION_PETRI = "layout_information_petri"
PLACE_NAME_TAG = "place_name_tag"
TRANS_NAME_TAG = "trans_name_tag"

DEFAULT_VARIANT_SEP = ","
DEFAULT_INDEX_KEY = "@@index"
DEFAULT_CASE_INDEX_KEY = "@@case_index"
DEFAULT_INDEX_IN_TRACE_KEY = "@@index_in_trace"
DEFAULT_EVENT_INDEX_KEY = "@@event_index"
DEFAULT_FLOW_TIME = "@@flow_time"
DEFAULT_CLASSIFIER_ATTRIBUTE = "@@classifier"

DEFAULT_ENCODING = get_param_from_env("PM4PY_DEFAULT_ENCODING", "utf-8")
DEFAULT_XES_PARSER = get_param_from_env("PM4PY_DEFAULT_XES_PARSER", "iterparse" if importlib.util.find_spec("lxml") else "chunk_regex")
DEFAULT_ALIGNMENTS_VARIANT = get_param_from_env("PM4PY_DEFAULT_ALIGNMENTS_VARIANT", "Variants.VERSION_STATE_EQUATION_A_STAR")

PARAM_ARTIFICIAL_START_ACTIVITY = "pm4py:param:art_start_act"
PARAM_ARTIFICIAL_END_ACTIVITY = "pm4py:param:art_end_act"
DEFAULT_ARTIFICIAL_START_ACTIVITY = "▶"
DEFAULT_ARTIFICIAL_END_ACTIVITY = "■"

DEFAULT_BUSINESS_HOURS_WORKCALENDAR = None

SHOW_EVENT_LOG_DEPRECATION = True if get_param_from_env("PM4PY_SHOW_EVENT_LOG_DEPRECATION", "False").lower() == "true" else False
SHOW_INTERNAL_WARNINGS = True if get_param_from_env("PM4PY_SHOW_INTERNAL_WARNINGS", "True").lower() == "true" else False

TRIGGERED_DT_PARSING_WARNING = False

DEFAULT_BGCOLOR = get_param_from_env("PM4PY_DEFAULT_BGCOLOR", "white")
DEFAULT_FORMAT_GVIZ_VIEW = get_param_from_env("PM4PY_DEFAULT_FORMAT_GVIZ_VIEW", "png")
DEFAULT_RANKDIR_GVIZ = get_param_from_env("PM4PY_DEFAULT_RANKDIR_GVIZ", "LR")
DEFAULT_TIMESTAMP_PARSE_FORMAT = get_param_from_env("PM4PY_DEFAULT_TIMESTAMP_PARSE_FORMAT", get_default_timestamp_format())
DEFAULT_XES_TIMESTAMP_PARSE_FORMAT = get_param_from_env("PM4PY_DEFAULT_XES_TIMESTAMP_PARSE_FORMAT", get_default_xes_timestamp_format())

ENABLE_MULTIPROCESSING_DEFAULT = True if get_param_from_env("PM4PY_ENABLE_MULTIPROCESSING_DEFAULT", "False").lower() == "true" else False
SHOW_PROGRESS_BAR = True if get_param_from_env("PM4PY_SHOW_PROGRESS_BAR", "True").lower() == "true" else False
DEFAULT_READ_XES_LEGACY_OBJECT = True if get_param_from_env("PM4PY_DEFAULT_READ_XES_LEGACY_OBJECT", "False").lower() == "true" else False
DEFAULT_RETURN_DIAGNOSTICS_DATAFRAME = True if get_param_from_env("PM4PY_DEFAULT_RETURN_DIAGNOSTICS_DATAFRAME", "False").lower() == "true" else False
DEFAULT_PANDAS_PARSING_DTYPE_BACKEND = get_param_from_env("PM4PY_DEFAULT_PANDAS_PARSING_DTYPE_BACKEND", "numpy_nullable")
ENABLE_DATETIME_COLUMNS_AWARE = get_param_from_env("PM4PY_ENABLE_DATETIME_COLUMNS_AWARE", get_default_is_aware_enabled())

# Default business hour slots: Mondays to Fridays, 7:00 - 17:00 (in seconds)
DEFAULT_BUSINESS_HOUR_SLOTS = [
    ((0 * 24 + 7) * 60 * 60, (0 * 24 + 17) * 60 * 60),
    ((1 * 24 + 7) * 60 * 60, (1 * 24 + 17) * 60 * 60),
    ((2 * 24 + 7) * 60 * 60, (2 * 24 + 17) * 60 * 60),
    ((3 * 24 + 7) * 60 * 60, (3 * 24 + 17) * 60 * 60),
    ((4 * 24 + 7) * 60 * 60, (4 * 24 + 17) * 60 * 60),
]

OPENAI_MAX_LEN = int(get_param_from_env("PM4PY_OPENAI_MAX_LEN", "10000"))
OPENAI_API_KEY = get_param_from_env("PM4PY_OPENAI_API_KEY", None)
ANTHROPIC_API_KEY = get_param_from_env("PM4PY_ANTHROPIC_API_KEY", None)
GOOGLE_API_KEY = get_param_from_env("PM4PY_GOOGLE_API_KEY", None)
OPENAI_API_URL = get_param_from_env("PM4PY_OPENAI_API_URL", "https://api.openai.com/v1/")
OPENAI_DEFAULT_MODEL = get_param_from_env("PM4PY_OPENAI_DEFAULT_MODEL", "gpt-4o")
OPENAI_DEFAULT_VISION_MODEL = get_param_from_env("PM4PY_OPENAI_DEFAULT_VISION_MODEL", "gpt-4o")
ANTHROPIC_DEFAULT_MODEL = get_param_from_env("PM4PY_ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
GOOGLE_DEFAULT_MODEL = get_param_from_env("PM4PY_GOOGLE_DEFAULT_MODEL", "gemini-1.5-flash-002")
OPENAI_DEFAULT_STT_MODEL = get_param_from_env("PM4PY_OPENAI_DEFAULT_STT_MODEL", "whisper-1")
OPENAI_DEFAULT_TTS_MODEL = get_param_from_env("PM4PY_OPENAI_DEFAULT_TTS_MODEL", "tts-1")
OPENAI_DEFAULT_TTS_VOICE = get_param_from_env("PM4PY_OPENAI_DEFAULT_TTS_VOICE", "alloy")

ENABLE_INTERNAL_IMPORTS = False if get_param_from_env("PM4PY_ENABLE_INTERNAL_IMPORTS", "True").lower() == "false" else True

OPENAI_EXEC_RESULT = True if get_param_from_env("PM4PY_OPENAI_EXEC_RESULT", "False").lower() == "true" else False
DEFAULT_GVIZ_VIEW = get_param_from_env("PM4PY_DEFAULT_GVIZ_VIEW", None)
DEFAULT_ENABLE_VISUALIZATIONS_VIEW = get_param_from_env("PM4PY_DEFAULT_ENABLE_VISUALIZATIONS_VIEW", True)
DEFAULT_ENABLE_GRAPH_TITLES = get_param_from_env("PM4PY_DEFAULT_ENABLE_GRAPH_TITLES", False)

JQUERY_LINK = "https://code.jquery.com/jquery-3.6.3.min.js"
GRAPHVIZJS_LINK = "https://github.com/mdaines/viz-js/releases/download/v1.8.2/viz.js"

if importlib.util.find_spec("psutil"):
    import psutil

    parent_pid = os.getppid()
    parent_name = str(psutil.Process(parent_pid).name())

    if "PBIDesktop" in parent_name:
        DEFAULT_GVIZ_VIEW = "matplotlib_view"


if DEFAULT_GVIZ_VIEW is None:
    DEFAULT_GVIZ_VIEW = "view"


class AvailableSerializations(Enum):
    EVENT_LOG = "event_log"
    DATAFRAME = "dataframe"
    PETRI_NET = "petri_net"
    PROCESS_TREE = "process_tree"
    BPMN = "bpmn"
    DFG = "dfg"
