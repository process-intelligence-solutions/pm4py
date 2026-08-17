import gzip
import os
import tempfile
import unittest

from pm4py.objects.log.importer.xes import importer
from pm4py.objects.log.importer.xes.variants import (
    iterparse,
    iterparse_20,
    iterparse_mem_compressed,
)


XES = b"""<?xml version='1.0' encoding='UTF-8'?>
<log xmlns='http://www.xes-standard.org/' xes.version='2.0'>
  <extension name='Concept' prefix='concept' uri='http://www.xes-standard.org/concept.xesext'/>
  <global scope='event'><string key='concept:name' value='unknown'/></global>
  <classifier name='Activity' keys="'concept:name' 'lifecycle:transition'"/>
  <string key='creator' value='coverage-test'/>
  <trace>
    <string key='concept:name' value='case-1'/>
    <event>
      <string key='concept:name' value='A'/>
      <date key='time:timestamp' value='2024-01-02T00:00:00Z'/>
      <int key='count' value='2'/>
      <float key='cost' value='1.5'/>
      <boolean key='approved' value='true'/>
      <id key='identifier' value='id-1'/>
      <list key='children'><values><string key='child' value='value'/></values></list>
      <container key='container'><string key='nested' value='inside'/></container>
    </event>
    <event>
      <string key='concept:name' value='B'/>
      <date key='time:timestamp' value='2024-01-01T00:00:00Z'/>
      <boolean key='approved' value='false'/>
    </event>
  </trace>
  <trace>
    <string key='concept:name' value='case-2'/>
    <event><string key='concept:name' value='C'/><date key='time:timestamp' value='2024-01-03T00:00:00Z'/></event>
  </trace>
</log>"""


XES_NESTED_LIST_LOG_ATTRIBUTE = b"""<?xml version='1.0' encoding='UTF-8'?>
<log xmlns='http://www.xes-standard.org/' xes.version='2.0'>
  <string key='extraction-date' value='2026-08-12'/>
  <list key='entities'>
    <values>
      <list key='SalesOrg'>
        <values>
          <string key='level' value='trace'/>
          <string key='key-attribute' value='SalesOrg'/>
        </values>
      </list>
    </values>
  </list>
  <list key='kpi'>
    <values>
      <list key='OTC-ON'>
        <values>
          <string key='kpi-code' value='OTC-ON'/>
          <float key='value' value='8687.0'/>
        </values>
      </list>
      <list key='OTC-CN'>
        <values>
          <string key='kpi-code' value='OTC-CN'/>
          <float key='value' value='377.0'/>
        </values>
      </list>
    </values>
  </list>
  <trace>
    <string key='concept:name' value='case-1'/>
    <event><string key='concept:name' value='A'/><date key='time:timestamp' value='2024-01-02T00:00:00Z'/></event>
  </trace>
</log>"""


class XesDeepCoverageTest(unittest.TestCase):
    def _assert_log(self, log):
        self.assertEqual(2, len(log))
        self.assertEqual("coverage-test", log.attributes["creator"])
        self.assertIn("Concept", log.extensions)
        self.assertIn("Activity", log.classifiers)
        event_a = next(
            event
            for trace in log
            for event in trace
            if event["concept:name"] == "A"
        )
        self.assertEqual(2, event_a["count"])

    def test_iterparse_20_string_compressed_and_file_paths(self):
        log = iterparse_20.import_from_string(
            XES,
            parameters={"show_progress_bar": True, "timestamp_sort": True, "reverse_sort": True},
        )
        self._assert_log(log)
        compressed = iterparse_20.import_from_string(
            gzip.compress(XES),
            parameters={"decompress_serialization": True, "show_progress_bar": False, "max_traces": 1},
        )
        self.assertEqual(1, len(compressed))
        with tempfile.NamedTemporaryFile(suffix=".xes.gz") as target:
            target.write(gzip.compress(XES))
            target.flush()
            file_log = iterparse_20.apply(target.name, parameters={"show_progress_bar": True})
        self._assert_log(file_log)

    def test_memory_compressed_string_compressed_and_file_paths(self):
        log = iterparse_mem_compressed.import_from_string(
            XES,
            parameters={"show_progress_bar": True, "timestamp_sort": True},
        )
        self._assert_log(log)
        compressed = iterparse_mem_compressed.import_from_string(
            gzip.compress(XES),
            parameters={"decompress_serialization": True, "show_progress_bar": False, "max_traces": 1},
        )
        self.assertEqual(1, len(compressed))
        with tempfile.NamedTemporaryFile(suffix=".xes.gz") as target:
            target.write(gzip.compress(XES))
            target.flush()
            file_log = iterparse_mem_compressed.apply(
                target.name, parameters={"show_progress_bar": True}
            )
        self._assert_log(file_log)

    def test_importer_string_variant_routing(self):
        for variant in ("iterparse_20", "iterparse_mem_compressed"):
            log = importer.deserialize(XES, parameters={"show_progress_bar": False}, variant=variant)
            self.assertEqual(2, len(log))
        self.assertIs(importer.Variants.ITERPARSE_20, importer.__dict__["__get_variant"]("iterparse_20"))
        self.assertIs(importer.Variants.ITERPARSE_MEM_COMPRESSED, importer.__dict__["__get_variant"]("iterparse_mem_compressed"))

    def test_iterparse_nested_list_inside_a_list_of_values(self):
        # A <list> whose <values> children are themselves further <list>
        # elements (e.g. a log-level "kpi" list containing several named
        # sub-lists) used to raise "TypeError: list indices must be
        # integers or slices, not str", since the nested list's own
        # attribute store was a list (a list-of-values container), not a
        # dict, and __parse_attribute() only knew how to assign into it by
        # key when it was a dict.
        log = iterparse.import_from_string(XES_NESTED_LIST_LOG_ATTRIBUTE)
        self.assertEqual(1, len(log))

        entities_children = dict(log.attributes["entities"]["children"])
        sales_org_value, sales_org_children = entities_children["SalesOrg"]["value"], dict(
            entities_children["SalesOrg"]["children"]
        )
        self.assertIsNone(sales_org_value)
        self.assertEqual("trace", sales_org_children["level"])
        self.assertEqual("SalesOrg", sales_org_children["key-attribute"])

        kpi_children = dict(log.attributes["kpi"]["children"])
        otc_on_children = dict(kpi_children["OTC-ON"]["children"])
        self.assertEqual("OTC-ON", otc_on_children["kpi-code"])
        self.assertEqual(8687.0, otc_on_children["value"])
        otc_cn_children = dict(kpi_children["OTC-CN"]["children"])
        self.assertEqual("OTC-CN", otc_cn_children["kpi-code"])
        self.assertEqual(377.0, otc_cn_children["value"])


if __name__ == "__main__":
    unittest.main()
