import pandas as pd


EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


def object_change_time(value):
    """Return the assignment timestamp, or None for an initial value."""
    if value is None or str(value) == "0":
        return None
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return None if timestamp == EPOCH else timestamp
