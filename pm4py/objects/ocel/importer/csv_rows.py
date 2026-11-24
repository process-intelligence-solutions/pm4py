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
Contact: contact@processintelligence.solutions
'''
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
