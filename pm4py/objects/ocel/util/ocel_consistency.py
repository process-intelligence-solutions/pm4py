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

from pm4py.objects.ocel.obj import OCEL
from typing import Optional, Dict, Any
import warnings
from pm4py.util import pandas_utils


def remove_dangling_relationships(ocel: OCEL) -> OCEL:
    """Keep declared events and objects, removing links to undeclared IDs."""
    event_id = ocel.event_id_column
    object_id = ocel.object_id_column
    event_ids = ocel.events[event_id]
    object_ids = ocel.objects[object_id]
    ocel.relations = ocel.relations[
        ocel.relations[event_id].isin(event_ids)
        & ocel.relations[object_id].isin(object_ids)
    ]
    ocel.o2o = ocel.o2o[
        ocel.o2o[object_id].isin(object_ids)
        & ocel.o2o[object_id + "_2"].isin(object_ids)
    ]
    return ocel


def apply(ocel: OCEL, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    """
    Forces the consistency of the OCEL, ensuring that the event/object identifier,
    event/object type are of type string and non-empty.

    Parameters
    --------------
    ocel
        OCEL
    parameters
        Possible parameters of the method

    Returns
    --------------
    ocel
        Consistent OCEL
    """
    if parameters is None:
        parameters = {}

    # Store frequently accessed column names locally to reduce attribute lookups
    event_id_col = ocel.event_id_column
    object_id_col = ocel.object_id_column
    event_activity = ocel.event_activity
    object_type_col = ocel.object_type_column
    qualifier_col = ocel.qualifier

    # Define fields to process for each dataframe
    fields = {
        "events": [event_id_col, event_activity],
        "objects": [object_id_col, object_type_col],
        "relations": [event_id_col, object_id_col, event_activity, object_type_col],
        "o2o": [object_id_col, object_id_col + "_2"],
        "e2e": [event_id_col, event_id_col + "_2"],
        "object_changes": [object_id_col],
    }

    # Process each dataframe
    for tab, columns in fields.items():
        # Skip processing if attribute doesn't exist
        if not hasattr(ocel, tab):
            continue

        # Get dataframe
        df = getattr(ocel, tab)

        # Skip empty dataframes
        if df.empty:
            continue

        # Filter to only columns that exist in this dataframe
        valid_columns = [col for col in columns if col in df.columns]
        if not valid_columns:
            continue

        # Check for NA values - only create mask if needed
        has_na = df[valid_columns].isna().any().any()
        if has_na:
            # Create mask for rows without NA values
            valid_rows = ~df[valid_columns].isna().any(axis=1)
            df = df.loc[valid_rows]

        df = df.copy()

        # Convert columns to string type
        for col in valid_columns:
            df[col] = df[col].astype(str)

        # Efficiently filter out empty strings
        # Create a single mask for all columns and apply once
        valid_rows = pandas_utils.DATAFRAME.Series(True, index=df.index)
        for col in valid_columns:
            valid_rows &= (df[col].str.len() > 0)

        # Only filter if we found empty strings
        if not valid_rows.all():
            df = df.loc[valid_rows]

        # Update OCEL attribute
        setattr(ocel, tab, df)

    # Check uniqueness efficiently
    events_df = ocel.events
    objects_df = ocel.objects

    # Only check if there are rows to check
    if len(events_df) > 0:
        num_ev_ids = events_df[event_id_col].nunique()
        if num_ev_ids < len(events_df):
            warnings.warn("The event identifiers in the OCEL are not unique!")

    if len(objects_df) > 0:
        num_obj_ids = objects_df[object_id_col].nunique()
        if num_obj_ids < len(objects_df):
            warnings.warn("The object identifiers in the OCEL are not unique!")

    ocel.relations[qualifier_col] = ocel.relations[qualifier_col].fillna("")
    ocel.o2o[qualifier_col] = ocel.o2o[qualifier_col].fillna("")

    return ocel
