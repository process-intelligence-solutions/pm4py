import random
import unittest
from math import sqrt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from pm4py.util.business_hours import (
    BusinessHours,
    get_business_day_seconds,
    soj_time_business_hours_diff,
)
from pm4py.util.constants import DEFAULT_BUSINESS_HOUR_SLOTS
from pm4py.util.vis_utils import human_readable_stat


class HolidayCalendar:
    def __init__(self, holidays):
        self.holidays = set(holidays)

    def is_working_day(self, day):
        if isinstance(day, datetime):
            day = day.date()
        return day.weekday() < 5 and day not in self.holidays


def weekday_slots(start_hour=8, end_hour=17):
    return [
        (
            weekday * 24 * 60 * 60 + start_hour * 60 * 60,
            weekday * 24 * 60 * 60 + end_hour * 60 * 60,
        )
        for weekday in range(5)
    ]


class BusinessHoursTest(unittest.TestCase):
    def test_business_day_duration_is_derived_from_weekly_slots(self):
        slots = weekday_slots(8, 16)

        self.assertEqual(8 * 60 * 60, get_business_day_seconds(slots))
        self.assertEqual(
            "4D",
            human_readable_stat(
                4 * 8 * 60 * 60, business_hour_slots=slots
            ),
        )
        self.assertEqual("1D", human_readable_stat(4 * 8 * 60 * 60))

    def test_performance_dfg_uses_business_days_in_labels(self):
        from pm4py.visualization.dfg.variants import performance

        duration = 4 * 8 * 60 * 60
        slots = weekday_slots(8, 16)
        graph = performance.apply(
            {("A", "B"): duration},
            activities_count={"A": 1, "B": 1},
            serv_time={"A": -1, "B": -1},
            parameters={"business_hour_slots": slots},
        )

        self.assertIn('label="4D"', graph.source)

    def test_discovered_performance_dfg_retains_business_hour_slots(self):
        import pm4py
        from pm4py.discovery import discover_performance_dfg
        from pm4py.objects.log.obj import Event, EventLog, Trace

        slots = weekday_slots(8, 16)
        trace = Trace(
            [
                Event(
                    {
                        "concept:name": "start",
                        "time:timestamp": datetime(2025, 1, 7, 8),
                    }
                ),
                Event(
                    {
                        "concept:name": "finish",
                        "time:timestamp": datetime(2025, 1, 10, 16),
                    }
                ),
            ]
        )

        dfg, start_activities, end_activities = discover_performance_dfg(
            EventLog([trace]),
            business_hours=True,
            business_hour_slots=slots,
            perf_aggregation_key="median",
        )
        with patch("pm4py.visualization.dfg.visualizer.view") as view:
            pm4py.view_performance_dfg(
                dfg,
                start_activities,
                end_activities,
                aggregation_measure="median",
            )
        graph = view.call_args.args[0]

        self.assertIsInstance(dfg, dict)
        self.assertEqual(4 * 8 * 60 * 60, dfg[("start", "finish")])
        self.assertEqual(tuple(slots), dfg.business_hour_slots)
        self.assertIn('label="4D"', graph.source)

    def test_pandas_performance_dfg_keeps_business_day_for_visualization(self):
        import pandas as pd
        import pm4py

        slots = weekday_slots(8, 16)
        dataframe = pd.DataFrame(
            [
                {
                    "case": 1,
                    "activity": "start",
                    "timestamp": datetime(2025, 1, 7, 8),
                },
                {
                    "case": 1,
                    "activity": "finish",
                    "timestamp": datetime(2025, 1, 10, 16),
                },
            ]
        )
        dataframe = pm4py.format_dataframe(
            dataframe,
            case_id="case",
            activity_key="activity",
            timestamp_key="timestamp",
        )

        # Keep the default "all" aggregation used in the issue reproducer.
        dfg, start_activities, end_activities = (
            pm4py.discover_performance_dfg(
                dataframe,
                business_hours=True,
                business_hour_slots=slots,
            )
        )
        with patch("pm4py.visualization.dfg.visualizer.view") as view:
            pm4py.view_performance_dfg(
                dfg,
                start_activities,
                end_activities,
                aggregation_measure="median",
            )
        graph = view.call_args.args[0]

        self.assertEqual(
            4 * 8 * 60 * 60,
            dfg[("start", "finish")]["median"],
        )
        self.assertEqual(tuple(slots), dfg.business_hour_slots)
        self.assertIn('label="4D"', graph.source)
        self.assertNotIn('label="1D"', graph.source)

    def test_variant_duration_uses_configured_working_day(self):
        from pm4py.visualization.variants_duration.variants.classic import (
            _format_duration,
        )

        duration = 4 * 8 * 60 * 60

        self.assertEqual("4.0d", _format_duration(duration, 8 * 60 * 60))
        self.assertEqual("1.3d", _format_duration(duration))

    def test_default_schedule_across_multiple_weeks(self):
        start = datetime(2024, 1, 1, 8, 30)
        end = datetime(2024, 1, 16, 10, 0)

        self.assertEqual(
            111 * 60 * 60 + 30 * 60,
            soj_time_business_hours_diff(
                start, end, DEFAULT_BUSINESS_HOUR_SLOTS
            ),
        )

    def test_overlapping_slots_are_counted_once(self):
        slots = [
            (9 * 60 * 60, 12 * 60 * 60),
            (10 * 60 * 60, 14 * 60 * 60),
        ]
        start = datetime(2024, 1, 1, 8, 0)
        end = datetime(2024, 1, 1, 15, 0)

        business_hours = BusinessHours(
            start, end, business_hour_slots=slots
        )

        self.assertEqual(5 * 60 * 60, business_hours.get_seconds())
        self.assertEqual(
            [[9 * 60 * 60, 14 * 60 * 60]],
            business_hours.business_hour_slots_unified,
        )

    def test_timezone_is_ignored_consistently(self):
        start = datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)
        end = datetime(
            2024, 1, 1, 10, 0, tzinfo=timezone(timedelta(hours=2))
        )

        self.assertEqual(
            2 * 60 * 60,
            soj_time_business_hours_diff(
                start, end, DEFAULT_BUSINESS_HOUR_SLOTS
            ),
        )

    def test_schedule_mutation_is_visible_to_later_calls(self):
        slots = [(8 * 60 * 60, 9 * 60 * 60)]
        start = datetime(2024, 1, 1, 8, 0)
        end = datetime(2024, 1, 1, 10, 0)

        self.assertEqual(
            60 * 60, soj_time_business_hours_diff(start, end, slots)
        )
        slots[0] = (8 * 60 * 60, 10 * 60 * 60)
        self.assertEqual(
            2 * 60 * 60, soj_time_business_hours_diff(start, end, slots)
        )

    def test_workcalendar_excludes_holidays(self):
        slots = weekday_slots()
        calendar = HolidayCalendar(
            {date(2026, 12, 25), date(2026, 12, 26)}
        )
        start = datetime(2026, 12, 24, 8, 0)
        end = datetime(2026, 12, 28, 17, 0)

        business_hours = BusinessHours(
            start,
            end,
            business_hour_slots=slots,
            workcalendar=calendar,
        )

        self.assertIs(calendar, business_hours.work_calendar)
        self.assertIs(calendar, business_hours.workcalendar)
        self.assertEqual(18 * 60 * 60, business_hours.get_seconds())

    def test_event_log_performance_dfg_forwards_workcalendar(self):
        from pm4py.discovery import discover_performance_dfg
        from pm4py.objects.log.obj import Event, EventLog, Trace

        calendar = HolidayCalendar({date(2026, 12, 25)})
        trace = Trace(
            [
                Event(
                    {
                        "concept:name": "A",
                        "time:timestamp": datetime(2026, 12, 24, 8),
                    }
                ),
                Event(
                    {
                        "concept:name": "B",
                        "time:timestamp": datetime(2026, 12, 28, 17),
                    }
                ),
            ]
        )

        dfg, _, _ = discover_performance_dfg(
            EventLog([trace]),
            business_hours=True,
            business_hour_slots=weekday_slots(),
            workcalendar=calendar,
            perf_aggregation_key="mean",
        )

        self.assertEqual(18 * 60 * 60, dfg[("A", "B")])

    def test_work_calendar_spelling_and_helper_are_supported(self):
        calendar = HolidayCalendar({date(2024, 1, 1)})
        start = datetime(2024, 1, 1, 8, 0)
        end = datetime(2024, 1, 2, 10, 0)

        business_hours = BusinessHours(
            start,
            end,
            business_hour_slots=DEFAULT_BUSINESS_HOUR_SLOTS,
            work_calendar=calendar,
        )

        self.assertEqual(3 * 60 * 60, business_hours.get_seconds())
        self.assertEqual(
            3 * 60 * 60,
            soj_time_business_hours_diff(
                start,
                end,
                DEFAULT_BUSINESS_HOUR_SLOTS,
                work_calendar=calendar,
            ),
        )

    def test_calendar_applies_to_each_date_of_cross_midnight_slot(self):
        monday_at_22 = 22 * 60 * 60
        tuesday_at_2 = 24 * 60 * 60 + 2 * 60 * 60
        calendar = HolidayCalendar({date(2024, 1, 2)})

        self.assertEqual(
            2 * 60 * 60,
            soj_time_business_hours_diff(
                datetime(2024, 1, 1, 21, 0),
                datetime(2024, 1, 2, 3, 0),
                [(monday_at_22, tuesday_at_2)],
                work_calendar=calendar,
            ),
        )

    def test_matches_interval_based_reference(self):
        random_generator = random.Random(1988)
        epoch = datetime(2024, 1, 1)
        calendar = HolidayCalendar(
            {
                date(2024, 1, 3),
                date(2024, 1, 8),
                date(2024, 1, 19),
                date(2024, 2, 14),
            }
        )
        slots = [
            (7 * 60 * 60, 12 * 60 * 60),
            (11 * 60 * 60, 17 * 60 * 60),
            (
                2 * 24 * 60 * 60 + 9 * 60 * 60,
                2 * 24 * 60 * 60 + 18 * 60 * 60,
            ),
            (
                4 * 24 * 60 * 60 + 8 * 60 * 60,
                4 * 24 * 60 * 60 + 16 * 60 * 60,
            ),
        ]

        for _ in range(100):
            start = epoch + timedelta(
                seconds=random_generator.randrange(35 * 24 * 60 * 60)
            )
            end = start + timedelta(
                seconds=random_generator.randrange(21 * 24 * 60 * 60)
            )
            self.assertEqual(
                self._reference_seconds(start, end, slots),
                soj_time_business_hours_diff(start, end, slots),
            )
            self.assertEqual(
                self._reference_seconds(start, end, slots, calendar),
                soj_time_business_hours_diff(
                    start, end, slots, work_calendar=calendar
                ),
            )

    @staticmethod
    def _reference_seconds(start, end, slots, work_calendar=None):
        unified = []
        for begin, finish in sorted(slots):
            if unified and unified[-1][1] >= begin - 1:
                unified[-1][1] = max(unified[-1][1], finish)
            else:
                unified.append([begin, finish])

        week_start = start - timedelta(
            days=start.weekday(),
            hours=start.hour,
            minutes=start.minute,
            seconds=start.second,
            microseconds=start.microsecond,
        )
        total = 0.0
        while week_start < end:
            for begin, finish in unified:
                slot_start = week_start + timedelta(seconds=begin)
                slot_end = week_start + timedelta(seconds=finish)
                overlap_start = max(start, slot_start)
                overlap_end = min(end, slot_end)
                if work_calendar is None:
                    total += max(
                        0.0,
                        (overlap_end - overlap_start).total_seconds(),
                    )
                else:
                    while overlap_start < overlap_end:
                        next_day = datetime.combine(
                            overlap_start.date() + timedelta(days=1),
                            datetime.min.time(),
                        )
                        segment_end = min(overlap_end, next_day)
                        if work_calendar.is_working_day(
                            overlap_start.date()
                        ):
                            total += (
                                segment_end - overlap_start
                            ).total_seconds()
                        overlap_start = segment_end
            week_start += timedelta(days=7)
        return total


class ScheduledBusinessHoursTest(unittest.TestCase):
    zone_name = "Australia/Sydney"
    sunday_slots = [(6 * 86400, 6 * 86400 + 4 * 3600)]

    @classmethod
    def seconds(cls, start, end, slots=None, calendar=None, zone=None):
        return soj_time_business_hours_diff(
            start,
            end,
            cls.sunday_slots if slots is None else slots,
            work_calendar=calendar,
            business_timezone=cls.zone_name if zone is None else zone,
        )

    @classmethod
    def transition_pair(cls, month, day):
        zone = ZoneInfo(cls.zone_name)
        return (
            datetime(2026, month, day, 0, tzinfo=zone),
            datetime(2026, month, day, 4, tzinfo=zone),
        )

    @staticmethod
    def polars_input(dataframe):
        """Construct fixtures without requiring the optional Arrow package."""
        import pandas as pd
        import polars as pl

        columns = []
        for name in dataframe:
            values = dataframe[name]
            if pd.api.types.is_datetime64_any_dtype(values.dtype):
                zone = values.dt.tz
                integers = [
                    None if pd.isna(value) else value.value for value in values
                ]
                dtype = pl.Datetime(
                    "ns", str(zone) if zone is not None else None
                )
                columns.append(pl.Series(name, integers, pl.Int64).cast(dtype))
            else:
                dtype = (
                    pl.String
                    if pd.api.types.is_string_dtype(values.dtype) else None
                )
                columns.append(pl.Series(name, values.tolist(), dtype=dtype))
        return pl.DataFrame({column.name: column for column in columns}).lazy()

    @staticmethod
    def inputs(pairs):
        import pandas as pd
        from pm4py.objects.log.obj import Event, EventLog, Trace

        rows = []
        traces = []
        for case, pair in enumerate(pairs):
            trace = []
            for activity, timestamp in zip(("A", "B"), pair):
                event = {
                    "case:concept:name": str(case),
                    "concept:name": activity,
                    "time:timestamp": timestamp,
                }
                rows.append(event)
                trace.append(Event(event.copy()))
            traces.append(Trace(trace))
        yield "event_log", EventLog(traces)
        dataframe = pd.DataFrame(rows)
        yield "pandas", dataframe
        try:
            frame = ScheduledBusinessHoursTest.polars_input(dataframe)
        except ImportError:
            return
        yield "polars", frame

    def test_dst_windows_measure_elapsed_seconds(self):
        for month, day, expected in ((4, 5, 18000), (10, 4, 10800)):
            with self.subTest(month=month):
                start, end = self.transition_pair(month, day)
                self.assertEqual(expected, self.seconds(start, end))
                self.assertEqual(
                    14400,
                    soj_time_business_hours_diff(
                        start, end, self.sunday_slots
                    ),
                )
                next_day = datetime(
                    2026, month, day + 1, tzinfo=ZoneInfo(self.zone_name)
                )
                self.assertEqual(
                    expected + 20 * 3600,
                    self.seconds(start, next_day, [(0, 7 * 86400)]),
                )

    def test_fold_endpoints_and_representation_invariance(self):
        zone = ZoneInfo(self.zone_name)
        start = datetime(2026, 4, 5, 2, 30, tzinfo=zone, fold=0)
        end = start.replace(fold=1)
        for first in (start, start.astimezone(timezone.utc)):
            for last in (end, end.astimezone(timezone.utc)):
                self.assertEqual(3600, self.seconds(first, last))
                self.assertEqual(0, self.seconds(last, first))
        self.assertEqual(
            0, self.seconds(start, start.astimezone(timezone.utc))
        )
        self.assertEqual(
            3600,
            self.seconds(
                start.replace(tzinfo=timezone(timedelta(hours=11))),
                end.replace(tzinfo=timezone(timedelta(hours=10))),
            ),
        )

    def test_elapsed_time_is_additive_across_transitions(self):
        zone = ZoneInfo(self.zone_name)
        for month, day, cuts, expected in (
            (4, 5, [(2, 30, 0), (2, 30, 1)], [9000, 3600, 5400]),
            (10, 4, [(1, 30, 0), (3, 30, 0)], [5400, 3600, 1800]),
        ):
            start, end = self.transition_pair(month, day)
            points = [start] + [
                datetime(
                    2026, month, day, hour, minute, tzinfo=zone, fold=fold
                )
                for hour, minute, fold in cuts
            ] + [end]
            pieces = [
                self.seconds(first, last)
                for first, last in zip(points, points[1:])
            ]
            self.assertEqual(expected, pieces)
            self.assertEqual(self.seconds(start, end), sum(pieces))

    def test_utc_events_use_the_business_local_calendar_date(self):
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = start + timedelta(hours=1)
        slots = weekday_slots(9, 17)
        self.assertEqual(3600, self.seconds(start, end, slots))
        calendar = HolidayCalendar({date(2026, 6, 1)})
        self.assertEqual(0, self.seconds(start, end, slots, calendar))

    def test_cross_midnight_exclusions_use_each_local_date(self):
        start = datetime(2026, 1, 5, 10, tzinfo=timezone.utc)
        end = start + timedelta(hours=6)
        slots = [(22 * 3600, 26 * 3600)]
        for excluded, expected in (
            (set(), 14400),
            ({date(2026, 1, 5)}, 7200),
            ({date(2026, 1, 6)}, 7200),
            ({date(2026, 1, 5), date(2026, 1, 6)}, 0),
        ):
            with self.subTest(excluded=excluded):
                self.assertEqual(
                    expected,
                    self.seconds(start, end, slots, HolidayCalendar(excluded)),
                )

    def test_exact_union_preserves_positive_gaps(self):
        start = datetime(2026, 6, 1, 9, tzinfo=timezone.utc)
        for gap in (1, 0.5, 0.000001):
            slots = [(9 * 3600, 9 * 3600 + 1),
                     (9 * 3600 + 1 + gap, 9 * 3600 + 3)]
            self.assertEqual(
                3 - gap,
                self.seconds(start, start + timedelta(seconds=3), slots,
                             zone="UTC"),
            )
            self.assertEqual(
                0,
                self.seconds(start + timedelta(seconds=1),
                             start + timedelta(seconds=1 + gap), slots,
                             zone="UTC"),
            )

    def test_union_removes_redundant_ambiguous_boundaries(self):
        start, end = self.transition_pair(4, 5)
        sunday = 6 * 86400
        slots = [(sunday, sunday + 2.5 * 3600),
                 (sunday + 2.5 * 3600, sunday + 4 * 3600),
                 (sunday + 3600, sunday + 3 * 3600)]
        self.assertEqual(18000, self.seconds(start, end, slots))

    def test_effective_ambiguous_and_nonexistent_boundaries_raise(self):
        sunday = 6 * 86400
        for month, day, kind in ((4, 5, "Ambiguous"), (10, 4, "Nonexistent")):
            start, end = self.transition_pair(month, day)
            for slots in (
                [(sunday, sunday + 2.5 * 3600)],
                [(sunday + 2.5 * 3600, sunday + 4 * 3600)],
            ):
                with self.subTest(month=month, slots=slots):
                    with self.assertRaisesRegex(ValueError, kind):
                        self.seconds(start, end, slots)

    def test_irrelevant_boundary_occurrences_do_not_raise(self):
        start = datetime(2026, 10, 5, 0, tzinfo=timezone.utc)
        self.assertEqual(
            0,
            self.seconds(start, start + timedelta(hours=1),
                         [(6 * 86400 + 2.5 * 3600, 6 * 86400 + 4 * 3600)]),
        )

    def test_strict_midnight_and_skipped_date_policy(self):
        for zone, start, end in (
            ("America/Havana", datetime(2020, 3, 8, 4, tzinfo=timezone.utc),
             datetime(2020, 3, 8, 8, tzinfo=timezone.utc)),
            ("America/Havana", datetime(2020, 11, 1, 4, tzinfo=timezone.utc),
             datetime(2020, 11, 1, 8, tzinfo=timezone.utc)),
            ("Pacific/Apia", datetime(2011, 12, 29, 22, tzinfo=timezone.utc),
             datetime(2011, 12, 30, 22, tzinfo=timezone.utc)),
        ):
            with self.subTest(zone=zone, start=start):
                with self.assertRaisesRegex(
                    ValueError, "business-hour boundary"
                ):
                    self.seconds(start, end, [(0, 7 * 86400)], zone=zone)

    def test_invalid_source_values_are_rejected(self):
        start, end = self.transition_pair(10, 4)
        for value in (None, "2026-10-04", start.replace(tzinfo=None),
                      datetime(2026, 10, 4, 2, 30, tzinfo=start.tzinfo)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.seconds(value, end)
        # A fixed offset declares an instant, rather than a Sydney wall time.
        fixed = datetime(2026, 10, 4, 2, 30,
                         tzinfo=timezone(timedelta(hours=10)))
        self.assertEqual(1800, self.seconds(fixed, end))

    def test_empty_and_invalid_schedules_and_zone_names(self):
        start, end = self.transition_pair(4, 5)
        self.assertEqual(0, self.seconds(start, end, []))
        for slots in ([(1, 1)], [(-1, 1)], [(1, 7 * 86400 + 1)],
                      [(True, 2)], [(0, float("nan"))],
                      [(0, float("inf"))], [(0, 1e308)], [(0, 0.0000001)]):
            with self.subTest(slots=slots):
                with self.assertRaises(ValueError):
                    self.seconds(start, end, slots)
        with self.assertRaises(ZoneInfoNotFoundError):
            self.seconds(start, end, zone="No/Such_Zone")

    def test_cached_schedules_do_not_accept_boolean_slots(self):
        start, end = self.transition_pair(4, 5)
        self.seconds(start, end, [(0, 2)])
        self.seconds(start, end, [(1, 2)])
        for slots in ([(False, 2)], [(True, 2)]):
            with self.subTest(slots=slots):
                with self.assertRaises(ValueError):
                    self.seconds(start, end, slots)

    def test_numeric_scalar_types_share_exact_cached_results(self):
        import numpy as np
        from pm4py.util import business_hours
        import pm4py

        start = datetime(2026, 6, 1, 9, tzinfo=timezone.utc)
        end = start + timedelta(seconds=10)
        native = [(32402, 32403)]
        split_cache = business_hours._split_business_hour_slots_by_weekday
        boundary_cache = business_hours._business_boundary_candidates
        representations = [
            [(np.float32(32402), np.float32(32403))],
            [(np.int32(32402), np.int32(32403))],
        ]
        for representation in representations:
            for order in ((representation, native), (native, representation)):
                split_cache.cache_clear()
                boundary_cache.cache_clear()
                for slots in order:
                    with self.subTest(slots=slots):
                        self.assertEqual(
                            1, self.seconds(start, end, slots, zone="UTC")
                        )
            split_cache.cache_clear()
            boundary_cache.cache_clear()
            soj_time_business_hours_diff(
                start, end, representation, HolidayCalendar(set())
            )
            self.assertEqual(1, self.seconds(start, end, native, zone="UTC"))
            for name, log in self.inputs([(start, end)]):
                with self.subTest(backend=name):
                    dfg, _, _ = pm4py.discover_performance_dfg(
                        log, business_hours=True,
                        business_hour_slots=representation,
                        business_timezone="UTC", perf_aggregation_key="mean",
                    )
                    self.assertEqual(1, dfg[("A", "B")])

    def test_rational_slot_precision_and_large_integer_validation(self):
        from fractions import Fraction

        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = start + timedelta(seconds=2)
        for slots, expected in (
            ([(Fraction(1, 10), Fraction(11, 10))], 1),
            ([(Fraction(1, 1000000), Fraction(2, 1000000))], 0.000001),
        ):
            self.assertEqual(
                expected, self.seconds(start, end, slots, zone="UTC")
            )
        for slots in (
            [(Fraction(1, 10000000), Fraction(1, 10))],
            [(0, 10 ** 400)],
        ):
            with self.assertRaises(ValueError):
                self.seconds(start, end, slots, zone="UTC")

    def test_interval_bounds_and_additivity_against_utc_reference(self):
        generator = random.Random(1988)
        epoch = datetime(2026, 4, 4, tzinfo=timezone.utc)
        for _ in range(40):
            start = epoch + timedelta(seconds=generator.randrange(48 * 3600))
            end = start + timedelta(seconds=generator.randrange(36 * 3600))
            midpoint = start + (end - start) / 2
            duration = self.seconds(start, end, [(0, 7 * 86400)])
            self.assertEqual((end - start).total_seconds(), duration)
            self.assertEqual(
                duration,
                self.seconds(start, midpoint, [(0, 7 * 86400)])
                + self.seconds(midpoint, end, [(0, 7 * 86400)]),
            )

    def test_public_routes_and_aggregation_shapes(self):
        import pm4py

        pairs = [self.transition_pair(4, 5), self.transition_pair(10, 4)]
        expected = {"min": 10800, "max": 18000, "sum": 28800,
                    "mean": 14400, "median": 14400,
                    "stdev": 3600 * sqrt(2)}
        for name, log in self.inputs(pairs):
            for aggregation in ("mean", "all"):
                with self.subTest(backend=name, aggregation=aggregation):
                    result = pm4py.discover_performance_dfg(
                        log, business_hours=True,
                        business_hour_slots=self.sunday_slots,
                        business_timezone=self.zone_name,
                        perf_aggregation_key=aggregation,
                    )
                    self.assertEqual(3, len(result))
                    dfg, starts, ends = result
                    self.assertEqual({"A": 2}, starts)
                    self.assertEqual({"B": 2}, ends)
                    if aggregation == "all":
                        self.assertEqual(set(expected), set(dfg[("A", "B")]))
                        for key, value in expected.items():
                            self.assertAlmostEqual(value, dfg[("A", "B")][key])
                    else:
                        self.assertEqual(14400, dfg[("A", "B")])
                    self.assertEqual(self.zone_name, dfg.business_timezone)
                    self.assertEqual(
                        self.zone_name, dfg.copy().business_timezone
                    )

    def test_pandas_mixed_offsets_and_nonmutation_on_success_or_error(self):
        import pandas as pd
        import pm4py

        zone = ZoneInfo(self.zone_name)
        start = datetime(2026, 4, 5, 2, 30, tzinfo=zone, fold=0)
        end = start.replace(fold=1).astimezone(timezone.utc)
        for final in (end, end.replace(tzinfo=None)):
            dataframe = pd.DataFrame({"case:concept:name": ["1", "1"],
                                      "concept:name": ["A", "B"],
                                      "time:timestamp": [start, final]})
            original = dataframe.copy(deep=True)
            arguments = dict(business_hours=True,
                             business_hour_slots=self.sunday_slots,
                             business_timezone=self.zone_name,
                             perf_aggregation_key="mean")
            if final.tzinfo is None:
                with self.assertRaises(ValueError):
                    pm4py.discover_performance_dfg(dataframe, **arguments)
            else:
                dfg, _, _ = pm4py.discover_performance_dfg(
                    dataframe, **arguments
                )
                self.assertEqual(3600, dfg[("A", "B")])
            pd.testing.assert_frame_equal(original, dataframe)

    def test_empty_singleton_and_configuration_preflight(self):
        import pandas as pd
        import pm4py
        from pm4py.objects.log.obj import EventLog

        empty = pd.DataFrame({"case:concept:name": pd.Series(dtype=str),
                              "concept:name": pd.Series(dtype=str),
                              "time:timestamp": pd.Series(
                                  dtype="datetime64[ns, UTC]")})
        inputs = [("event_log", EventLog()), ("pandas", empty)]
        try:
            inputs.append(("polars", self.polars_input(empty)))
        except ImportError:
            pass
        for name, log in inputs:
            with self.subTest(backend=name):
                result = pm4py.discover_performance_dfg(
                    log, business_hours=True,
                    business_timezone=self.zone_name,
                )
                self.assertEqual(({}, {}, {}), result)
                with self.assertRaises(ZoneInfoNotFoundError):
                    pm4py.discover_performance_dfg(
                        log, business_hours=True,
                        business_timezone="No/Such_Zone"
                    )
                with self.assertRaises(ValueError):
                    pm4py.discover_performance_dfg(
                        log, business_timezone=self.zone_name
                    )
        for aware in (False, True):
            timestamp = datetime(2026, 6, 1, 10,
                                 tzinfo=timezone.utc if aware else None)
            for name, log in self.inputs([(timestamp,)]):
                with self.subTest(aware=aware, backend=name):
                    arguments = dict(business_hours=True,
                                     business_timezone=self.zone_name)
                    if aware:
                        dfg, starts, ends = pm4py.discover_performance_dfg(
                            log, **arguments
                        )
                        self.assertEqual({}, dfg)
                        self.assertEqual({"A": 1}, starts)
                        self.assertEqual({"A": 1}, ends)
                    else:
                        with self.assertRaises(ValueError):
                            pm4py.discover_performance_dfg(log, **arguments)

    def test_dataframe_nanoseconds_are_rejected_before_scalar_conversion(self):
        import pandas as pd
        import pm4py

        dataframe = pd.DataFrame({
            "case:concept:name": ["1"], "concept:name": ["A"],
            "time:timestamp": [pd.Timestamp("2026-06-01T00:00:00.000000001Z")],
        })
        inputs = [("pandas", dataframe)]
        try:
            inputs.append(("polars", self.polars_input(dataframe)))
        except ImportError:
            pass
        for name, log in inputs:
            with self.subTest(backend=name):
                with self.assertRaisesRegex(ValueError, "microsecond"):
                    pm4py.discover_performance_dfg(
                        log, business_hours=True,
                        business_timezone=self.zone_name,
                    )

    def test_schedule_mutations_are_visible_only_to_later_calls(self):
        start = datetime(2026, 6, 1, 9, tzinfo=timezone.utc)
        end = start + timedelta(hours=2)
        slots = [(9 * 3600, 10 * 3600)]
        self.assertEqual(3600, self.seconds(start, end, slots, zone="UTC"))
        slots[0] = (9 * 3600, 11 * 3600)
        self.assertEqual(7200, self.seconds(start, end, slots, zone="UTC"))

    def test_optional_calendar_provider_through_each_public_route(self):
        import pm4py
        try:
            from workalendar.oceania import NewSouthWales
        except ImportError:
            self.skipTest("workalendar is not installed")
        calendar = NewSouthWales()
        start = datetime(2026, 12, 24, tzinfo=timezone.utc)
        end = datetime(2026, 12, 28, 6, tzinfo=timezone.utc)
        # NSW Christmas Day and the additional Boxing Day holiday are closed.
        self.assertFalse(calendar.is_working_day(date(2026, 12, 25)))
        self.assertFalse(calendar.is_working_day(date(2026, 12, 28)))
        for name, log in self.inputs([(start, end)]):
            with self.subTest(backend=name):
                dfg, _, _ = pm4py.discover_performance_dfg(
                    log, business_hours=True,
                    business_hour_slots=weekday_slots(9, 17),
                    business_timezone=self.zone_name,
                    workcalendar=calendar, perf_aggregation_key="mean",
                )
                self.assertEqual(21600, dfg[("A", "B")])

    def test_selected_start_column_is_validated_before_pair_filtering(self):
        import pandas as pd
        import pm4py

        for value in (datetime(2026, 6, 1, 9), pd.NaT,
                      pd.Timestamp("2026-06-01T00:00:00.000000001Z")):
            dataframe = pd.DataFrame({
                "case:concept:name": ["1"], "concept:name": ["A"],
                "time:timestamp": [pd.Timestamp("2026-06-01T01:00:00Z")],
                "start_timestamp": [value],
            })
            inputs = [("pandas", dataframe)]
            try:
                inputs.append(("polars", self.polars_input(dataframe)))
            except ImportError:
                pass
            for name, log in inputs:
                with self.subTest(backend=name, value=value):
                    with self.assertRaises(ValueError):
                        pm4py.discover_performance_dfg(
                            log, business_hours=True,
                            business_timezone=self.zone_name,
                        )

    def test_empty_naive_dataframe_schema_is_rejected(self):
        import pandas as pd
        import pm4py

        dataframe = pd.DataFrame({
            "case:concept:name": pd.Series(dtype=str),
            "concept:name": pd.Series(dtype=str),
            "time:timestamp": pd.Series(dtype="datetime64[ns]"),
        })
        inputs = [("pandas", dataframe)]
        try:
            inputs.append(("polars", self.polars_input(dataframe)))
        except ImportError:
            pass
        for name, log in inputs:
            with self.subTest(backend=name):
                with self.assertRaises(ValueError):
                    pm4py.discover_performance_dfg(
                        log, business_hours=True,
                        business_timezone=self.zone_name,
                    )

    def test_direct_adapters_keep_the_same_timezone_contract(self):
        from pm4py.algo.discovery.dfg.adapters.pandas import df_statistics
        from pm4py.algo.discovery.dfg.variants import performance

        pairs = [self.transition_pair(4, 5)]
        for name, log in self.inputs(pairs):
            with self.subTest(backend=name):
                if name == "event_log":
                    result = performance.apply(log, parameters={
                        "business_hours": True,
                        "business_hour_slots": self.sunday_slots,
                        "business_timezone": self.zone_name,
                    })
                else:
                    if name == "polars":
                        from pm4py.algo.discovery.dfg.adapters.polars import (
                            df_statistics as adapter,
                        )
                    else:
                        adapter = df_statistics
                    result = adapter.get_dfg_graph(
                        log, measure="performance", business_hours=True,
                        business_hours_slot=self.sunday_slots,
                        business_timezone=self.zone_name,
                    )
                self.assertEqual(18000, result[("A", "B")])

    def test_explicit_empty_start_key_gets_full_dataframe_preflight(self):
        import pandas as pd
        from pm4py.algo.discovery.dfg.adapters.pandas import df_statistics

        timestamp = pd.Timestamp("2026-06-01T00:00:00Z")
        one_hour = timestamp + pd.Timedelta(hours=1)
        two_hours = timestamp + pd.Timedelta(hours=2)
        invalid = (
            timestamp - pd.Timedelta(hours=1) + pd.Timedelta(1, unit="ns")
        )
        frames = [
            (pd.DataFrame({
                "case:concept:name": ["1", "1"],
                "concept:name": ["A", "B"],
                "time:timestamp": [timestamp, two_hours],
                "": [invalid, one_hour],
            }), True),
            (pd.DataFrame({
                "case:concept:name": ["1"], "concept:name": ["A"],
                "time:timestamp": [timestamp], "": [invalid],
            }), True),
            (pd.DataFrame({
                "case:concept:name": pd.Series(dtype=str),
                "concept:name": pd.Series(dtype=str),
                "time:timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
                "": pd.Series(dtype="datetime64[ns]"),
            }), True),
            (pd.DataFrame({
                "case:concept:name": ["1", "1"],
                "concept:name": ["A", "B"],
                "time:timestamp": [timestamp, two_hours],
                "": [timestamp, one_hour],
            }), False),
        ]
        for dataframe, invalid_frame in frames:
            adapters = [("pandas", df_statistics, dataframe)]
            try:
                from pm4py.algo.discovery.dfg.adapters.polars import (
                    df_statistics as polars_adapter,
                )
                frame = self.polars_input(dataframe)
            except ImportError:
                pass
            else:
                adapters.append(("polars", polars_adapter, frame))
            for name, adapter, frame in adapters:
                with self.subTest(backend=name, invalid=invalid_frame):
                    arguments = dict(
                        measure="performance", start_timestamp_key="",
                        business_hours=True, business_hours_slot=[(0, 604800)],
                        business_timezone="UTC",
                    )
                    if invalid_frame:
                        with self.assertRaises(ValueError):
                            adapter.get_dfg_graph(frame, **arguments)
                    else:
                        result = adapter.get_dfg_graph(frame, **arguments)
                        self.assertEqual(3600, result[("A", "B")])

    def test_calendar_verdicts_are_fresh_and_ignore_disjoint_dates(self):
        class RecordingCalendar:
            working = True

            def __init__(self):
                self.calls = []

            def is_working_day(self, day):
                self.calls.append(day)
                return self.working

        calendar = RecordingCalendar()
        start = datetime(2026, 6, 1, 9, tzinfo=timezone.utc)
        end = start + timedelta(hours=1)
        self.assertEqual(
            3600, self.seconds(start, end, [(0, 604800)], calendar, "UTC")
        )
        self.assertEqual([date(2026, 6, 1)], calendar.calls)
        calendar.working = False
        self.assertEqual(
            0, self.seconds(start, end, [(0, 604800)], calendar, "UTC")
        )
        self.assertEqual([date(2026, 6, 1)] * 2, calendar.calls)

    def test_calendar_mutation_keeps_current_schedule_and_metadata(self):
        import pm4py

        start = datetime(2026, 6, 1, 9, tzinfo=timezone.utc)
        end = start + timedelta(hours=2)
        for name, log in self.inputs([(start, end)]):
            with self.subTest(backend=name):
                slots = [[9 * 3600, 10 * 3600]]

                class MutatingCalendar:
                    def is_working_day(self, day):
                        slots[0][1] = 11 * 3600
                        return True

                arguments = dict(
                    business_hours=True, business_hour_slots=slots,
                    business_timezone="UTC", workcalendar=MutatingCalendar(),
                    perf_aggregation_key="mean",
                )
                first, _, _ = pm4py.discover_performance_dfg(log, **arguments)
                second, _, _ = pm4py.discover_performance_dfg(log, **arguments)
                self.assertEqual(3600, first[("A", "B")])
                self.assertEqual(((32400, 36000),), first.business_hour_slots)
                self.assertEqual(7200, second[("A", "B")])
                self.assertEqual(((32400, 39600),), second.business_hour_slots)


if __name__ == "__main__":
    unittest.main()
