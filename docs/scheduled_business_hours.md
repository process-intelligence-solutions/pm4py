# Scheduled elapsed business time

This contribution adds an opt-in elapsed-time metric to performance
directly-follows graph (DFG) discovery. Supply `business_hours=True` and an
explicit `business_timezone` to measure elapsed seconds within a weekly
working schedule in that timezone.
The calendar accepts or rejects each business-local date.

PM4Py's existing business-hours calculation deliberately ignores timestamp
timezone offsets. Its defaults remain unchanged. The new metric preserves the
instant represented by an event, including both occurrences of a repeated hour.

## Example

Run [the Sydney example](../examples/scheduled_business_hours.py) from the
repository root:

```powershell
.\.venv\Scripts\python.exe examples\scheduled_business_hours.py
```

On Linux, run `python examples/scheduled_business_hours.py` with the source
installed in the active virtual environment.

The source timestamps include explicit offsets and are stored in UTC. The
selected schedule opens on Sunday from midnight to 4 am in Sydney.
Holiday exclusions are disabled for this synthetic example.

| Local window | Clock hours | Elapsed seconds |
| --- | ---: | ---: |
| 5 April 2026, midnight to 4 am | 4 | 18,000 |
| 4 October 2026, midnight to 4 am | 4 | 10,800 |

The example aggregates these two `A` to `B` cases. Its minimum is 10,800 seconds,
maximum is 18,000 seconds and mean is 14,400 seconds.

## Contract

- Timestamps must be valid aware datetimes with microsecond precision.
  Different source offsets are accepted. Pandas object columns containing
  aware timestamps are validated before UTC conversion.
- Slots are half-open intervals in seconds since Monday midnight. Endpoints
  must satisfy `0 <= start < end <= 604800`. Split Sunday-to-Monday intervals
  at the week boundary. Overlaps and touching intervals count once; positive
  gaps remain closed. An empty schedule gives zero working time.
- Calendar exclusions apply to each local date, including both parts of an
  overnight slot. Use an object exposing `is_working_day(date)` that gives
  consistent answers during the calculation.
- Schedule boundaries must identify one instant. An ambiguous or nonexistent
  boundary raises `ValueError`. This includes midnights introduced when slots
  are split by date, so some historical midnight changes and skipped dates
  are deliberately unsupported.
- Event conversions and candidate boundaries must fit Python's datetime
  range. Extreme queries near years 1 and 9999 can raise `OverflowError`,
  including while resolving a guard date. Results returned as floats can
  lose microsecond resolution over very long intervals.
- Equal or reversed UTC intervals return zero. EventLog preserves caller
  order; dataframe adapters retain their existing sorting behaviour.
- The new option reaches EventLog, pandas and Polars LazyFrame performance
  discovery. It also extends `soj_time_business_hours_diff`. The `BusinessHours`
  class retains its existing wall-time behaviour.

The result remains a mapping of activity pairs with the existing aggregation
shapes. Its `business_timezone` and immutable `business_hour_slots` attributes
survive `.copy()`. Existing working-day labels retain nominal schedule scaling.

The evaluator visits dates and working intervals, rather than elapsed seconds.
Long intervals therefore cost more than short intervals. It uses bounded caches
for pure schedule preparation and boundary resolution, and does not cache
calendar verdicts globally.

## Calendar data

The installed Workalendar 17.0.0 provider was checked against the NSW Christmas
Day and additional Boxing Day holidays in 2026. The integration tests cover
those dates through all three public input paths.

That check does not establish complete Australian calendar coverage.
Workalendar 17.0.0 treats 27 April 2026 as a working day in NSW, while the
[NSW Government calendar](https://www.nsw.gov.au/about-nsw/public-holidays)
lists it as an additional public holiday. This 2026 gap remains in
[Workalendar's current NSW source](https://github.com/workalendar/workalendar/blob/b131f2b64377e951654652a9a32e72a34f34e88f/workalendar/oceania/australia.py#L170).
The provider already excludes 26 April 2027 through its Sunday rule.
Correcting the 2026 exception is a separate contribution opportunity.

Timezone rules also affect results. The development environment uses
`tzdata==2026.4` on Windows. Record the effective timezone data and calendar
versions when reproducing results. Python's `zoneinfo` uses system timezone
data where available and otherwise uses the installed `tzdata` package.
See the [Python timezone documentation](https://docs.python.org/3/library/zoneinfo.html).

## Verification

From the repository root, run the focused checks with:

```powershell
.\.venv\Scripts\python.exe tests\business_hours_test.py
```

All 42 checks pass on CPython 3.11.16 and 3.13.15, with pandas, Polars and
Workalendar installed. The minimum Python environment runs these fixtures
without the optional Arrow conversion package.

The same 42 checks pass on Linux under WSL2 with CPython 3.14.4, pandas 3.0.5,
Polars 1.44.2 and Workalendar 17.0.0. That environment uses the system IANA
timezone database, version 2026c. Run `python tests/business_hours_test.py`
from the repository root after installing the source and optional extras.

On Windows, the repository's `python execute_tests.py --pipeline` command,
run from `tests`, completes 981 test methods: 941 pass, 11 are skipped and 29 fail.
One test module also fails to import. The failure identities match the clean
upstream baseline. Missing Graphviz executables, Windows file locks and a
dotted-chart assertion account for these existing failures. There are no
additional failures in this run.

On Linux, the same command completes 981 test methods: 948 pass, 11 are skipped
and 22 fail, with the same one module import failure. Clean upstream in the
same environment runs 939 methods: 906 pass, 11 are skipped and the same 22
fail. The failure identities and import failure match, with no added failures.
The missing Graphviz executable and dotted-chart assertion remain in this run.

Flake8 passes on the shared helper, focused tests and example. Existing style
findings remain elsewhere in the touched upstream modules; modified lines add
none. Aikido's local path scan of the nine changed Python files reports no
findings.

The declared build tool, run as `python -m build`, produces the source
distribution and wheel on Linux. The installed wheel also passes all 42 focused
checks. macOS and upstream CI have not been checked. The repository defines no
dedicated build or lint command; its declared developer tools were run manually.

A helper benchmark on this Windows machine uses a Sydney schedule from
9 am to 5 pm, Monday to Friday. Holiday exclusions are disabled and boundary
caches are warm. The figures are medians across seven batches on CPython
3.13.15:

| Query span | Microseconds per pair | Calls per batch |
| --- | ---: | ---: |
| 2 hours | 13.0 | 2,000 |
| 3 days | 15.8 | 500 |
| 365 days | 385.5 | 10 |

These timings measure one helper calculation. Full dataframe processing
requires separate measurement.

## Contribution status

This contribution is published on the `scheduled-business-time` branch of the
[personal PM4Py fork](https://github.com/ryanduguid/pm4py), based on upstream
commit `24a3bf610aea6ecc4938b1864b3ad71fcfb82084`. Upstream review remains
pending. PM4Py's
[contribution guide](https://processintelligence.solutions/pm4py/contributing)
requires a CLA, whose operative terms are sent during the contribution process.
No agreement has been signed.
