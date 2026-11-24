import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import numpy as np
import pandas as pd

import pm4py
from pm4py.algo.transformation.ocel.features.events import algorithm as event_features
from pm4py.algo.transformation.ocel.features.events_objects import algorithm as event_object_features
from pm4py.algo.transformation.ocel.features.objects import algorithm as object_features
from pm4py.objects.conversion.ocel.variants import ocel_to_nx
from pm4py.objects.log.obj import Event, EventLog, Trace
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import (
    event_prefix_suffix_per_obj,
    explode,
    log_ocel,
    ocel_to_dict_types_rel,
)


class OcelDeepCoverageTest(unittest.TestCase):
    @staticmethod
    def _input_path(*parts):
        return os.path.join(os.path.dirname(__file__), "input_data", *parts)

    @classmethod
    def _ocel(cls):
        return pm4py.read_ocel(cls._input_path("ocel", "example_log.jsonocel"))

    def test_legacy_json_preserves_isolated_events_and_objects(self):
        source = {
            "ocel:global-log": {"ocel:version": "1.0"},
            "ocel:global-event": {},
            "ocel:global-object": {},
            "ocel:events": {
                "e1": {
                    "ocel:activity": "linked",
                    "ocel:timestamp": "2024-01-01T09:30:00Z",
                    "ocel:vmap": {},
                    "ocel:omap": ["o1", "o1", "missing"],
                },
                "e2": {
                    "ocel:activity": "isolated",
                    "ocel:timestamp": "2024-01-01T10:00:00Z",
                    "ocel:vmap": {"note": "keep me"},
                    "ocel:omap": [],
                },
            },
            "ocel:objects": {
                "o1": {"ocel:type": "order", "ocel:ovmap": {}},
                "o2": {"ocel:type": "order", "ocel:ovmap": {"amount": 12}},
            },
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "isolated.jsonocel"
            path.write_text(json.dumps(source), encoding="utf-8")
            ocel = pm4py.read_ocel(str(path))

        self.assertEqual(ocel.events.set_index("ocel:eid").loc["e2", "note"], "keep me")
        self.assertEqual(ocel.objects.set_index("ocel:oid").loc["o2", "amount"], 12)
        self.assertEqual(
            list(ocel.relations[["ocel:eid", "ocel:oid"]].itertuples(index=False, name=None)),
            [("e1", "o1")],
        )

    def test_legacy_csv_with_mixed_timezone_offsets(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "mixed_offsets.csv"
            path.write_text(
                "ocel:eid,ocel:activity,ocel:timestamp,ocel:type:order\n"
                "e2,finish,2024-01-01T09:30:00-05:00,['o1']\n"
                "e1,start,2024-01-01T15:00:00+01:00,['o1']\n",
                encoding="utf-8",
            )
            ocel = pm4py.read_ocel(str(path))

        expected = [
            ("e1", pd.Timestamp("2024-01-01T14:00:00Z")),
            ("e2", pd.Timestamp("2024-01-01T14:30:00Z")),
        ]
        for table in (ocel.events, ocel.relations):
            self.assertEqual(
                list(table[["ocel:eid", "ocel:timestamp"]].itertuples(index=False, name=None)),
                expected,
            )
        self.assertEqual(ocel.objects["ocel:oid"].tolist(), ["o1"])
        self.assertNotIn("ocel:original-object-id", ocel.objects)

    def test_legacy_csv_object_ids_shared_across_types(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "typed_objects.csv"
            path.write_text(
                "ocel:eid,ocel:activity,ocel:timestamp,ocel:type:order,ocel:type:file\n"
                "e1,start,2024-01-01T09:30:00Z,['same'],['same']\n"
                'e2,finish,2024-01-01T10:00:00Z,"[\'ocel:typed-object:[""order"", ""same""]\']",[]\n',
                encoding="utf-8",
            )
            ocel = pm4py.read_ocel(str(path))

        self.assertTrue(ocel.objects["ocel:oid"].is_unique)
        self.assertIn('ocel:typed-object:["order", "same"]', set(ocel.objects["ocel:oid"]))
        objects = ocel.objects.set_index("ocel:oid")
        first_event = ocel.relations[ocel.relations["ocel:eid"] == "e1"]
        self.assertEqual(set(first_event["ocel:type"]), {"order", "file"})
        for relation_id, kind in first_event[["ocel:oid", "ocel:type"]].itertuples(index=False, name=None):
            self.assertEqual(objects.loc[relation_id, "ocel:type"], kind)
            self.assertEqual(objects.loc[relation_id, "ocel:original-object-id"], "same")

    def test_networkx_conversion_keeps_default_node_ids(self):
        ocel = pm4py.read_ocel(
            str(Path(__file__).parent / "input_data" / "ocel" / "example_log.jsonocel")
        )
        graph = pm4py.convert_ocel_to_networkx(ocel)
        self.assertEqual(
            set(graph), set(ocel.events[ocel.event_id_column]) | set(ocel.objects[ocel.object_id_column])
        )
        self.assertIn("attr", next(iter(graph.nodes(data=True)))[1])

        start = pd.Timestamp("2024-01-01T10:00:00+01:00")
        end = start + pd.Timedelta(days=1)
        ocel = OCEL(
            events=pd.DataFrame({
                "ocel:eid": ["end", "same"],
                "ocel:activity": ["Finish", "Start"],
                "ocel:timestamp": [end, start],
            }),
            objects=pd.DataFrame({
                "ocel:oid": ["same", "other"],
                "ocel:type": ["order", "item"],
            }),
            relations=pd.DataFrame({
                "ocel:eid": ["end", "same", "same", "same", "end"],
                "ocel:oid": ["same", "same", "same", "other", "other"],
                "ocel:qualifier": ["used", "created", "owned", None, pd.NA],
            }),
        )
        graph = ocel_to_nx.apply(ocel, parameters={"include_node_id_type": True})
        df_edges = [(source, target) for source, target, data in graph.edges(data=True)
                    if data["attr"]["type"] == "DF"]
        self.assertEqual(df_edges, [("EVENT:same", "EVENT:end")] * 2)

    @staticmethod
    def _dataframe(prefix, object_type):
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        return pd.DataFrame(
            [
                {
                    "case:concept:name": f"{prefix}1",
                    "concept:name": "create",
                    "time:timestamp": base,
                    "case:customer": "gold",
                    "value": 1.0,
                    object_type: f"{object_type}-1",
                },
                {
                    "case:concept:name": f"{prefix}1",
                    "concept:name": "complete",
                    "time:timestamp": base + timedelta(hours=1),
                    "case:customer": "gold",
                    "value": 2.0,
                    object_type: f"{object_type}-1 AND {object_type}-2",
                },
            ],
            index=[0, 1],
        )

    def test_all_object_event_and_event_object_features(self):
        ocel = self._ocel()
        object_parameters = {
            "enable_all": True,
            "enable_object_work_in_progress": True,
            "enable_related_events_features": True,
            "enable_related_activities_features": True,
            "enable_obj_con_in_graph_features": True,
            "enable_object_lifecycle_paths": True,
            "debug": True,
        }
        object_data, object_names = object_features.apply(ocel, parameters=object_parameters)
        self.assertEqual(len(ocel.objects), len(object_data))
        self.assertEqual(len(object_names), len(object_data[0]))
        object_dict = object_features.transform_features_to_dict_dict(
            ocel, object_data, object_names
        )
        self.assertEqual(len(ocel.objects), len(object_dict))

        object_type = ocel.objects.iloc[0][ocel.object_type_column]
        filtered, filtered_names = object_features.apply(
            ocel,
            parameters={
                **object_parameters,
                "debug": False,
                "filter_per_type": object_type,
            },
        )
        self.assertTrue(filtered)
        self.assertEqual(object_names, filtered_names)

        event_data, event_names = event_features.apply(
            ocel,
            parameters={"enable_all": True, "enable_related_objects_features": True},
        )
        self.assertEqual(len(ocel.events), len(event_data))
        self.assertEqual(len(event_names), len(event_data[0]))
        event_dict = event_features.transform_features_to_dict_dict(
            ocel, event_data, event_names
        )
        self.assertEqual(len(ocel.events), len(event_dict))

        eo_data, eo_names = event_object_features.apply(ocel)
        self.assertTrue(eo_data)
        self.assertEqual(len(eo_names), len(eo_data[0]))

    def test_traditional_log_and_dataframe_to_ocel(self):
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        log = EventLog(
            [
                Trace(
                    [
                        Event({"concept:name": "A", "time:timestamp": base, "cost": 1}),
                        Event({"concept:name": "B", "time:timestamp": base + timedelta(minutes=1), "cost": 2}),
                    ],
                    attributes={"concept:name": "case-1", "customer": "gold"},
                )
            ]
        )
        ocel = log_ocel.from_traditional_log(log, parameters={"target_object_type": "case"})
        self.assertEqual(2, len(ocel.events))
        self.assertEqual(1, len(ocel.objects))

        dataframe = self._dataframe("c", "order")
        pandas_ocel = log_ocel.from_traditional_pandas(
            dataframe, parameters={"target_object_type": "case"}
        )
        self.assertEqual(2, len(pandas_ocel.events))
        self.assertEqual(1, len(pandas_ocel.objects))

    def test_interleavings_and_multiple_object_types(self):
        left = self._dataframe("left", "order")
        right = self._dataframe("right", "item")
        interleavings = pd.DataFrame(
            [
                {"@@left_index": 0, "@@right_index": 0, "@@direction": "LR"},
                {"@@left_index": 1, "@@right_index": 1, "@@direction": "RL"},
            ]
        )
        combined = log_ocel.from_interleavings(
            left.copy(),
            right.copy(),
            interleavings,
            parameters={"target_object_type": "left", "target_object_type_2": "right"},
        )
        self.assertEqual(4, len(combined.events))
        self.assertGreater(len(combined.relations), 4)

        source = pd.DataFrame(
            [
                {
                    "concept:name": "create",
                    "time:timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "orders": "o1 AND o2",
                    "items": "i1",
                    "value": 3.0,
                    "customer": "gold",
                    "nullable": np.nan,
                },
                {
                    "concept:name": "ship",
                    "time:timestamp": datetime(2024, 1, 2, tzinfo=timezone.utc),
                    "orders": "o1",
                    "items": None,
                    "value": 4.0,
                    "customer": "gold",
                    "nullable": pd.NaT,
                },
            ]
        )
        multi = log_ocel.log_to_ocel_multiple_obj_types(
            source,
            "concept:name",
            "time:timestamp",
            ["orders", "items"],
            additional_event_attributes=["value", "nullable"],
            additional_object_attributes={"orders": ["customer"]},
        )
        self.assertEqual(2, len(multi.events))
        self.assertEqual(3, len(multi.objects))
        self.assertNotIn("nullable", multi.events.columns)

    def test_ocel_prefix_and_relation_dictionary_utilities(self):
        ocel = self._ocel()
        exploded = explode.apply(ocel)
        self.assertGreaterEqual(len(exploded.events), len(ocel.events))
        prefixes = event_prefix_suffix_per_obj.apply(exploded)
        self.assertIsInstance(prefixes, dict)
        relation_dictionary = ocel_to_dict_types_rel.apply(ocel)
        self.assertIsInstance(relation_dictionary, dict)
        self.assertTrue(relation_dictionary)


if __name__ == "__main__":
    unittest.main()
