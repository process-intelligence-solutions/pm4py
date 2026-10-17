import datetime
import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

import pandas as pd

import pm4py
from examples import dfg_playout
from pm4py.objects.log.obj import Event, EventLog, Trace
from pm4py.visualization.dfg import visualizer


class DfgTests(unittest.TestCase):
    def test_filter_act_percentage(self):
        from pm4py.algo.filtering.dfg import dfg_filtering
        log = pm4py.read_xes("input_data/running-example.xes")
        dfg, sa, ea = pm4py.discover_dfg(log)
        act_count = pm4py.get_event_attribute_values(log, "concept:name")
        dfg_filtering.filter_dfg_on_activities_percentage(dfg, sa, ea, act_count, 0.1)

    def test_filter_paths_percentage(self):
        from pm4py.algo.filtering.dfg import dfg_filtering
        log = pm4py.read_xes("input_data/running-example.xes")
        dfg, sa, ea = pm4py.discover_dfg(log)
        act_count = pm4py.get_event_attribute_values(log, "concept:name")
        dfg_filtering.filter_dfg_on_paths_percentage(dfg, sa, ea, act_count, 0.3)


    @staticmethod
    def _log_data():
        base = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        rows, log = [], EventLog()
        for case_id in ("1", "2"):
            trace = Trace(attributes={"concept:name": case_id})
            for index, activity in enumerate(("A", "B")):
                event = Event({
                    "concept:name": activity,
                    "time:timestamp": base + datetime.timedelta(
                        days=int(case_id), hours=index
                    ),
                })
                trace.append(event)
                rows.append({"case:concept:name": case_id, **event})
            log.append(trace)
        return log, pd.DataFrame(rows)

    def _execute_example(self, graphviz_available):
        find_spec = dfg_playout.importlib.util.find_spec
        for log in self._log_data():
            with self.subTest(log_type=type(log).__name__):
                output = io.StringIO()
                with (
                    mock.patch.object(pm4py, "read_xes", return_value=log),
                    mock.patch.object(
                        dfg_playout.importlib.util,
                        "find_spec",
                        side_effect=lambda name: (
                            graphviz_available if name == "graphviz" else find_spec(name)
                        ),
                    ),
                    mock.patch.object(pm4py, "view_dfg", wraps=pm4py.view_dfg) as view_dfg,
                    mock.patch.object(visualizer, "view") as view,
                    redirect_stdout(output),
                ):
                    dfg_playout.execute_script()

                self.assertEqual(2 if graphviz_available else 0, view_dfg.call_count)
                self.assertEqual(2 if graphviz_available else 0, view.call_count)
                self.assertIn(
                    "percentage of behavior allowed from DFG that is in the log "
                    "(from 0.0 to 1.0):  1.0",
                    output.getvalue(),
                )

    def test_visualizes_original_and_simulated_dfgs(self):
        self._execute_example(graphviz_available=True)

    def test_runs_without_graphviz(self):
        self._execute_example(graphviz_available=False)


if __name__ == "__main__":
    unittest.main()
