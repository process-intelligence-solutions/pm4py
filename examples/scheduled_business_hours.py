# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare Sydney working windows across both daylight-saving transitions."""

import pandas as pd

import pm4py


def execute_script():
    dataframe = pd.DataFrame(
        {
            "case:concept:name": ["autumn", "autumn", "spring", "spring"],
            "concept:name": ["A", "B", "A", "B"],
            "time:timestamp": pd.to_datetime(
                [
                    "2026-04-05T00:00:00+11:00",
                    "2026-04-05T04:00:00+10:00",
                    "2026-10-04T00:00:00+10:00",
                    "2026-10-04T04:00:00+11:00",
                ],
                utc=True,
            ),
        }
    )
    dfg, starts, ends = pm4py.discover_performance_dfg(
        dataframe,
        business_hours=True,
        business_hour_slots=[(6 * 86400, 6 * 86400 + 4 * 3600)],
        business_timezone="Australia/Sydney",
        workcalendar=None,
    )
    print("Business timezone:", dfg.business_timezone)
    print("Elapsed seconds for A to B:", dfg[("A", "B")])
    print("Start activities:", starts)
    print("End activities:", ends)


if __name__ == "__main__":
    execute_script()
