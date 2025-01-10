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
from enum import Enum

from pm4py.objects.ocel import constants
from pm4py.util import exec_utils, pandas_utils
import pandas as pd
import numpy as np
from collections import Counter
from copy import copy, deepcopy


class Parameters(Enum):
    EVENT_ID = constants.PARAM_EVENT_ID
    EVENT_ACTIVITY = constants.PARAM_EVENT_ACTIVITY
    EVENT_TIMESTAMP = constants.PARAM_EVENT_TIMESTAMP
    OBJECT_ID = constants.PARAM_OBJECT_ID
    OBJECT_TYPE = constants.PARAM_OBJECT_TYPE
    QUALIFIER = constants.PARAM_QUALIFIER
    CHANGED_FIELD = constants.PARAM_CHNGD_FIELD


class OCEL(object):
    def __init__(self, events=None, objects=None, relations=None, globals=None, parameters=None, o2o=None, e2e=None,
                 object_changes=None):
        if parameters is None:
            parameters = {}

        self.event_id_column = exec_utils.get_param_value(Parameters.EVENT_ID, parameters, constants.DEFAULT_EVENT_ID)
        self.object_id_column = exec_utils.get_param_value(Parameters.OBJECT_ID, parameters,
                                                           constants.DEFAULT_OBJECT_ID)
        self.object_type_column = exec_utils.get_param_value(Parameters.OBJECT_TYPE, parameters,
                                                             constants.DEFAULT_OBJECT_TYPE)

        self.event_activity = exec_utils.get_param_value(Parameters.EVENT_ACTIVITY, parameters,
                                                         constants.DEFAULT_EVENT_ACTIVITY)
        self.event_timestamp = exec_utils.get_param_value(Parameters.EVENT_TIMESTAMP, parameters,
                                                          constants.DEFAULT_EVENT_TIMESTAMP)
        self.qualifier = exec_utils.get_param_value(Parameters.QUALIFIER, parameters, constants.DEFAULT_QUALIFIER)
        self.changed_field = exec_utils.get_param_value(Parameters.CHANGED_FIELD, parameters,
                                                        constants.DEFAULT_CHNGD_FIELD)

        if events is None:
            events = pandas_utils.instantiate_dataframe(
                {self.event_id_column: [], self.event_activity: [], self.event_timestamp: []})
        if objects is None:
            objects = pandas_utils.instantiate_dataframe({self.object_id_column: [], self.object_type_column: []})
        if relations is None:
            relations = pandas_utils.instantiate_dataframe(
                {self.event_id_column: [], self.event_activity: [], self.event_timestamp: [], self.object_id_column: [],
                 self.object_type_column: []})
        if globals is None:
            globals = {}
        if o2o is None:
            o2o = pandas_utils.instantiate_dataframe(
                {self.object_id_column: [], self.object_id_column + "_2": [], self.qualifier: []})
        if e2e is None:
            e2e = pandas_utils.instantiate_dataframe(
                {self.event_id_column: [], self.event_id_column + "_2": [], self.qualifier: []})
        if object_changes is None:
            object_changes = pandas_utils.instantiate_dataframe(
                {self.object_id_column: [], self.object_type_column: [], self.event_timestamp: [],
                 self.changed_field: []})
        if self.qualifier not in relations:
            relations[self.qualifier] = [None] * len(relations)

        self.events = events
        self.objects = objects
        self.relations = relations
        self.globals = globals
        self.o2o = o2o
        self.e2e = e2e
        self.object_changes = object_changes

        self.parameters = parameters

    def get_extended_table(self, ot_prefix=constants.DEFAULT_OBJECT_TYPE_PREFIX_EXTENDED) -> pd.DataFrame:
        """
        Transforms the current OCEL data structure into a Pandas dataframe containing the events with their
        attributes and the related objects per object type.
        """
        object_types = pandas_utils.format_unique(self.relations[self.object_type_column].unique())
        table = self.events.copy().set_index(self.event_id_column)
        for ot in object_types:
            table[ot_prefix + ot] = \
                self.relations[self.relations[self.object_type_column] == ot].groupby(self.event_id_column)[
                    self.object_id_column].agg(list)
        table = table.reset_index()
        return table

    def get_summary(self) -> str:
        """
        Gets a string summary of the object-centric event log
        """
        ret = []
        ret.append("Object-Centric Event Log (")
        ret.append("number of events: %d" % (len(self.events)))
        ret.append(", number of objects: %d" % (len(self.objects)))
        ret.append(", number of activities: %d" % (self.events[self.event_activity].nunique()))
        ret.append(", number of object types: %d" % (self.objects[self.object_type_column].nunique()))
        ret.append(", events-objects relationships: %d)" % (len(self.relations)))
        ret.append("\n")
        ret.append("Activities occurrences: " + str(Counter(self.events[self.event_activity].value_counts().to_dict())))
        ret.append("\n")
        ret.append("Object types occurrences (number of objects): " + str(
            Counter(self.objects[self.object_type_column].value_counts().to_dict())))
        ret.append("\n")
        ret.append("Unique activities per object type: " + str(
            Counter(self.relations.groupby(self.object_type_column)[self.event_activity].nunique().to_dict())))
        ret.append("\n")
        ret.append(
            "Please use <THIS>.get_extended_table() to get a dataframe representation of the events related to the objects.")
        return "".join(ret)

    def is_ocel20(self):
        unique_qualifiers = []
        if self.qualifier in self.relations.columns:
            unique_qualifiers = [x for x in pandas_utils.format_unique(self.relations[self.qualifier].unique()) if
                                 not self.__check_is_nan(x)]

        return len(self.o2o) > 0 or len(self.object_changes) > 0 or len(unique_qualifiers) > 0

    def __check_is_nan(self, x):
        try:
            if x is None:
                return True
            if np.isnan(x):
                return True
        except:
            return False

    def __str__(self):
        return str(self.get_summary())

    def __repr__(self):
        return str(self.get_summary())

    def __copy__(self):
        return OCEL(self.events, self.objects, self.relations, copy(self.globals), copy(self.parameters),
                    copy(self.o2o), copy(self.e2e), copy(self.object_changes))

    def __deepcopy__(self, memo):
        return OCEL(self.events.copy(), self.objects.copy(), self.relations.copy(), deepcopy(self.globals),
                    deepcopy(self.parameters), deepcopy(self.o2o), deepcopy(self.e2e), deepcopy(self.object_changes))
