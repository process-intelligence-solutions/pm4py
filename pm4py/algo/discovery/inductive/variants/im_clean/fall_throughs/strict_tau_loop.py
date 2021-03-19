from typing import Optional

from pm4py.objects.log.log import EventLog, Trace


def detect(log: EventLog, start_activities, end_activities, act_key: str) -> Optional[EventLog]:
    proj = EventLog()
    for t in log:
        x = 0
        for i in range(1, len(t)):
            if t[i][act_key] in start_activities and t[i - 1][act_key] in end_activities:
                proj.append(Trace(t[x:i]))
                x = i
        proj.append(Trace(t[x:len(t)]))
    return proj if len(proj) > len(log) else None