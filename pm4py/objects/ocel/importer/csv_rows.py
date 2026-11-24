import csv
from collections.abc import Iterable
from threading import Lock


_csv_reader_lock = Lock()
_portable_field_limit = 2**31 - 1


def read_csv_rows(source: Iterable[str]) -> list[list[str]]:
    """Read strict RFC 4180 rows without the default limit on text attributes."""
    # The csv module's limit is shared by its readers in this interpreter.
    with _csv_reader_lock:
        previous_limit = csv.field_size_limit()
        csv.field_size_limit(max(previous_limit, _portable_field_limit))
        try:
            return list(csv.reader(source, dialect="excel", strict=True))
        finally:
            csv.field_size_limit(previous_limit)
