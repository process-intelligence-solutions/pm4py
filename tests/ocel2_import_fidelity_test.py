import csv
import gzip
import importlib.util
import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pandas as pd

import pm4py
from pm4py.objects.ocel import constants
from pm4py.objects.ocel.importer.attribute_time import object_change_time
from pm4py.objects.ocel.importer.bundled.variants import ocel20 as bundled_ocel20
from pm4py.objects.ocel.importer.jsonocel.variants import ocel20_rustxes
from pm4py.objects.ocel.importer.sqlite.variants import ocel20 as sqlite_ocel20


INTEGER = 9007199254740993
FIRST_CHANGE = "2024-01-01T04:00:00Z"


class Ocel2ImportFidelityTest(unittest.TestCase):
    def test_csv_readers_preserve_long_quoted_attributes_and_restore_field_limit(self):
        body = 'Opening line, with "quotes".\r\n' + "a" * 140_000
        limit = 131_072
        previous = csv.field_size_limit(limit)
        try:
            with TemporaryDirectory() as directory:
                path = Path(directory) / "log.ocel.csv"
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(["id", "activity", "timestamp", "ot:order", "body"])
                    writer.writerow(["e1", "Start", FIRST_CHANGE, "o1", body])

                log = pm4py.read_ocel2(str(path))
                self.assertEqual(log.events.iloc[0]["body"], body)
                self.assertEqual(csv.field_size_limit(), limit)

                bundle = str(Path(directory) / "bundle")
                pm4py.write_ocel2_bundle(log, bundle, storage_format="csv")
                bundled_log = pm4py.read_ocel2_bundle(bundle)
                self.assertEqual(bundled_log.events.iloc[0]["body"], body)
                self.assertEqual(csv.field_size_limit(), limit)

                path.write_bytes(b'id,activity,timestamp,body\r\ne2,Start,2024-01-01T00:00:00Z,"' + b"a" * len(body))
                with self.assertRaisesRegex(ValueError, "Invalid RFC 4180 CSV syntax"):
                    pm4py.read_ocel2(str(path))
                self.assertEqual(csv.field_size_limit(), limit)
        finally:
            csv.field_size_limit(previous)

    def test_compact_csv_preserves_sparse_integers_and_index_named_attributes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "log.ocel.csv"
            path.write_text(
                "id,activity,timestamp,ot:order,@@index,amount\n"
                f"e1,Start,{FIRST_CHANGE},o1,keep,{INTEGER}\n"
                f"e2,Start,{FIRST_CHANGE},o2,,\n"
                f',,,"o1{{""serial"":{INTEGER},""mixed"":{INTEGER}}}",,\n'
                f',,{FIRST_CHANGE},"o2{{""cost"":{INTEGER},""@@index"":""change""}}",,\n'
                ',,2024-01-02T00:00:00Z,"o2{""mixed"":1.5}",,\n',
                encoding="utf-8",
            )
            log = pm4py.read_ocel2(str(path))

        self.assertEqual(list(log.events[log.event_id_column]), ["e1", "e2"])
        self.assertEqual(log.events.iloc[0]["@@index"], "keep")
        changes = log.object_changes.set_index(log.changed_field)
        self.assertEqual(changes.loc["@@index", "@@index"], "change")
        for value in (log.events.iloc[0]["amount"], log.objects.iloc[0]["serial"], changes.loc["cost", "cost"]):
            self.assertIs(type(value), int)
            self.assertEqual(value, INTEGER)
        self.assertEqual(log.objects.iloc[0]["mixed"], str(INTEGER))
        self.assertEqual(changes.loc["mixed", "mixed"], "1.5")

    def test_object_change_time_compares_instants_without_nanoseconds_conversion(self):
        self.assertIsNone(object_change_time("1970-01-01T01:00:00+01:00"))
        for instant in ("1970-01-01T00:00:00.000000001Z", "2500-01-01T00:00:00Z"):
            self.assertEqual(object_change_time(instant), pd.Timestamp(instant))

    def assert_log_contents(self, ocel):
        self.assertEqual(set(ocel.objects[ocel.object_id_column]), {"o1", "o2"})
        self.assertEqual(set(ocel.relations[ocel.qualifier]), {"input", "output", ""})
        self.assertEqual(list(ocel.o2o[ocel.qualifier]), ["next"])
        event = ocel.events.set_index(ocel.event_id_column).loc["e1"]
        self.assertEqual(event["amount"], INTEGER)
        self.assertEqual(event["comment"], "null")
        self.assertEqual(event["empty"], "")
        self.assertIs(event["flag"], False)
        self.assertEqual(ocel.globals[constants.OCEL_EVTYPES_KEY]["Unused"], {"unset": "time"})
        self.assertEqual(ocel.globals[constants.OCEL_OBJTYPES_KEY]["Bin"], {"quantity": "integer"})
        self.assertEqual(len(ocel.object_changes), 1)
        change = ocel.object_changes.iloc[0]
        self.assertEqual(change[ocel.object_id_column], "o1")
        self.assertEqual(change[ocel.changed_field], "quantity")
        self.assertEqual(change["quantity"], 7)
        self.assertEqual(change[ocel.event_timestamp], pd.Timestamp(FIRST_CHANGE))

    def test_json_preserves_qualified_and_temporal_data(self):
        log = {
            "eventTypes": [
                {"name": "Adjust", "attributes": [
                    {"name": "amount", "type": "integer"},
                    {"name": "comment", "type": "string"},
                    {"name": "empty", "type": "string"},
                    {"name": "flag", "type": "boolean"},
                ]},
                {"name": "Unused", "attributes": [{"name": "unset", "type": "time"}]},
            ],
            "objectTypes": [{"name": "Bin", "attributes": [{"name": "quantity", "type": "integer"}]}],
            "events": [
                {
                    "id": "e1", "type": "Adjust", "time": "2024-01-01T00:00:00Z",
                    "attributes": [
                        {"name": "amount", "value": INTEGER},
                        {"name": "comment", "value": "null"},
                        {"name": "empty", "value": ""},
                        {"name": "flag", "value": False},
                    ],
                    "relationships": [
                        {"objectId": "o1", "qualifier": "input"},
                        {"objectId": "o1", "qualifier": "output"},
                    ],
                },
                {
                    "id": "e2", "type": "Adjust", "time": "2024-01-02T00:00:00Z",
                    "relationships": [{"objectId": "o1", "qualifier": None}],
                },
            ],
            "objects": [
                {
                    "id": "o1", "type": "Bin",
                    "attributes": [{"name": "quantity", "time": FIRST_CHANGE, "value": 7}],
                    "relationships": [{"objectId": "o2", "qualifier": "next"}],
                },
                {"id": "o2", "type": "Bin"},
            ],
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "log.json"
            path.write_text(json.dumps(log), encoding="utf-8")
            for reader in (pm4py.read_ocel2, pm4py.read_ocel2_json):
                self.assert_log_contents(reader(str(path), variant_str="standard"))
            backend = Mock()
            backend.import_ocel_json_pm4py.side_effect = OSError("null qualifier")
            with patch.object(ocel20_rustxes, "import_rustxes_backend", return_value=(backend, "r4pm")):
                self.assert_log_contents(ocel20_rustxes.apply(str(path)))
            backend.import_ocel_json_pm4py.assert_called_once()

    def test_xml_preserves_qualified_and_temporal_data(self):
        log = f"""<log>
            <object-types><object-type name="Bin"><attributes>
                <attribute name="quantity" type="integer" />
            </attributes></object-type></object-types>
            <event-types>
                <event-type name="Adjust"><attributes>
                    <attribute name="amount" type="integer" />
                    <attribute name="comment" type="string" />
                    <attribute name="empty" type="string" />
                    <attribute name="flag" type="boolean" />
                </attributes></event-type>
                <event-type name="Unused"><attributes>
                    <attribute name="unset" type="time" />
                </attributes></event-type>
            </event-types>
            <objects>
                <object id="o1" type="Bin">
                    <attributes><attribute name="quantity" time="{FIRST_CHANGE}">7</attribute></attributes>
                    <objects><object object-id="o2" qualifier="next" /></objects>
                </object>
                <object id="o2" type="Bin" />
            </objects>
            <events>
                <event id="e1" type="Adjust" time="2024-01-01T00:00:00Z">
                    <attributes>
                        <attribute name="amount">{INTEGER}</attribute>
                        <attribute name="comment">null</attribute>
                        <attribute name="empty" />
                        <attribute name="flag">false</attribute>
                    </attributes>
                    <objects>
                        <relationship object-id="o1" qualifier="input" />
                        <relationship object-id="o1" qualifier="output" />
                    </objects>
                </event>
                <event id="e2" type="Adjust" time="2024-01-02T00:00:00Z">
                    <objects><relationship object-id="o1" qualifier="" /></objects>
                </event>
            </events>
        </log>"""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "log.xml"
            path.write_text(log, encoding="utf-8")
            for reader in (pm4py.read_ocel2, pm4py.read_ocel2_xml):
                self.assert_log_contents(reader(str(path), variant_str="standard"))
            compressed = Path(directory) / "namespaced.xml.gz"
            with gzip.open(compressed, "wt", encoding="utf-8") as stream:
                stream.write(log.replace("<log>", '<log xmlns="urn:ocel:example">', 1))
            self.assert_log_contents(pm4py.read_ocel2(str(compressed), variant_str="standard"))

    def test_sqlite_preserves_objects_and_attributes_used_as_scratch_columns(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "log.sqlite"
            with sqlite3.connect(path) as conn:
                conn.executescript(f"""
                    CREATE TABLE event (ocel_id TEXT, ocel_type TEXT);
                    CREATE TABLE object (ocel_id TEXT, ocel_type TEXT);
                    CREATE TABLE event_map_type (ocel_type TEXT, ocel_type_map TEXT);
                    CREATE TABLE object_map_type (ocel_type TEXT, ocel_type_map TEXT);
                    CREATE TABLE event_Adjust (ocel_id TEXT, ocel_time TEXT, "@@index" INTEGER);
                    CREATE TABLE object_Bin (
                        ocel_id TEXT, ocel_time TEXT, ocel_changed_field TEXT, "@@cumcount" INTEGER
                    );
                    CREATE TABLE event_object (ocel_event_id TEXT, ocel_object_id TEXT, ocel_qualifier TEXT);
                    CREATE TABLE object_object (ocel_source_id TEXT, ocel_target_id TEXT, ocel_qualifier TEXT);
                    INSERT INTO event VALUES ('e1', 'Adjust'), ('e2', 'Adjust');
                    INSERT INTO object VALUES ('o1', 'Bin'), ('o2', 'Bin'), ('o3', 'Bin');
                    INSERT INTO event_map_type VALUES ('Adjust', 'Adjust');
                    INSERT INTO object_map_type VALUES ('Bin', 'Bin');
                    INSERT INTO event_Adjust VALUES ('e1', '{FIRST_CHANGE}', {INTEGER}), ('e2', '{FIRST_CHANGE}', NULL);
                    INSERT INTO object_Bin VALUES
                        ('o1', '1970-01-01T00:00:00Z', NULL, {INTEGER}),
                        ('o2', '{FIRST_CHANGE}', '@@cumcount', 7);
                    INSERT INTO event_object VALUES ('e1', 'o1', 'link'), ('e1', 'missing', 'invalid');
                    INSERT INTO object_object VALUES ('o1', 'o2', 'next'), ('o2', 'missing', 'invalid');
                """)
            ocel = sqlite_ocel20.apply(str(path))
        self.assertEqual(set(ocel.events[ocel.event_id_column]), {"e1", "e2"})
        self.assertEqual(set(ocel.objects[ocel.object_id_column]), {"o1", "o2", "o3"})
        self.assertEqual(list(ocel.relations[ocel.qualifier]), ["link"])
        self.assertEqual(list(ocel.o2o[ocel.qualifier]), ["next"])
        self.assertEqual(ocel.events.iloc[0]["@@index"], INTEGER)
        self.assertEqual(ocel.objects.iloc[0]["@@cumcount"], INTEGER)
        self.assertEqual(ocel.object_changes.iloc[0]["@@cumcount"], 7)
        self.assertEqual(ocel.object_changes.iloc[0][ocel.event_timestamp], pd.Timestamp(FIRST_CHANGE))
        self.assertEqual(ocel.globals[constants.OCEL_OBJTYPES_KEY], {"Bin": {"@@cumcount": "INTEGER"}})

    @unittest.skipUnless(importlib.util.find_spec("pyarrow"), "pyarrow is required")
    def test_parquet_accepts_timestamp_nanoseconds_and_untyped_missing_column(self):
        import pyarrow as pa
        import pyarrow.parquet as pq

        nanoseconds = pa.timestamp("ns", tz="UTC")
        timestamp = "2024-01-01T04:00:00.000000123Z"
        schema = pa.schema([
            pa.field("ocel_id", pa.string(), nullable=False),
            pa.field("ocel_time", nanoseconds, nullable=False),
            pa.field("missing", pa.string()),
            pa.field("amount", pa.int64()),
        ])
        data = pa.Table.from_arrays([
            pa.array(["e1", "e2"]),
            pa.array([pd.Timestamp(timestamp).value] * 2, type=nanoseconds),
            pa.array([None, None], type=pa.string()),
            pa.array([INTEGER, None], type=pa.int64()),
        ], schema=schema)
        with TemporaryDirectory() as directory:
            pq.write_table(data, Path(directory) / "events.parquet")
            loaded = bundled_ocel20._read_table(
                directory, "events.parquet", "parquet", "utf-8",
                [("ocel_id", "string"), ("ocel_time", "time")],
                [("missing", "integer"), ("amount", "integer")],
                {"ocel_id", "ocel_time"},
            )
        self.assertEqual(loaded.iloc[0]["ocel_time"], pd.Timestamp(timestamp))
        self.assertEqual(loaded.iloc[0]["amount"], INTEGER)
        self.assertTrue(loaded["missing"].isna().all())
