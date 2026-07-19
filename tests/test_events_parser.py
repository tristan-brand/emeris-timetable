"""Tests for conversion from extracted tables to domain events."""

import pandas as pd

from emeris_timetable.events_parser import (
    extract_date,
    parse_assessments,
    parse_class,
    parse_event_datetime,
)


def test_parse_event_datetime_accepts_timetable_and_clock_formats():
    timetable_time = parse_event_datetime("2026-07-20", "9H00")
    clock_time = parse_event_datetime("2026-07-20", "09:00")

    assert timetable_time == clock_time
    assert timetable_time.isoformat() == "2026-07-20T09:00:00+02:00"


def test_extract_date_uses_day_first_and_rejects_invalid_text():
    assert extract_date("20 July 2026") == "2026-07-20"
    assert extract_date("not a date") is None


def test_parse_class_builds_an_event():
    event = parse_class("COMP1234 Room101", "9H00 - 10H00", "2026-07-20")

    assert event is not None
    assert event.title == "COMP1234"
    assert event.location == "Room101"
    assert event.start.isoformat() == "2026-07-20T09:00:00+02:00"
    assert event.end.isoformat() == "2026-07-20T10:00:00+02:00"


def test_parse_class_ignores_non_class_cells():
    assert parse_class("Lunch", "12H00 - 13H00", "2026-07-20") is None


def test_parse_assessments_builds_one_minute_deadline_events():
    dataframe = pd.DataFrame(
        [
            {
                "MODULE": "COMP1234",
                "ASSESSMENT": "Project",
                "DUE DATE": "20 July 2026",
                "DUE TIME": "09H00",
            }
        ]
    )

    events = parse_assessments(dataframe)

    assert len(events) == 1
    assert events[0].title == "COMP1234: Project"
    assert (events[0].end - events[0].start).total_seconds() == 60
