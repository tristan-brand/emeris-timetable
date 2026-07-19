"""Parse normalized timetable and assessment tables into `Event` objects.

This module converts dataframe rows/cells into `Event` instances consumed by
the Google Calendar sync layer.
"""

import re

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from dateutil import parser

from .event import Event

APP_TIMEZONE = ZoneInfo("Africa/Johannesburg")


def extract_date(date_str: str) -> str | None:
    """Parse a human-readable date into ISO format (`YYYY-MM-DD`).

    Returns `None` when parsing fails.
    """
    try:
        dt = parser.parse(date_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except (parser.ParserError, ValueError):
        return None


def parse_classes(df: pd.DataFrame) -> list[Event]:
    """Parse a normalized class timetable dataframe into class events."""
    events = []
    for col in df.columns[1:]:  # First column stores time ranges.
        for idx, cell in df[col].items():
            time_range = df.iloc[idx, 0]
            date = extract_date(col)
            if date is None:
                continue
            event = parse_class(cell, time_range, date)
            if event is not None:
                events.append(event)
    return events


def parse_assessments(df: pd.DataFrame) -> list[Event]:
    """Convert normalized assessment rows into one-minute deadline events."""
    events = []
    for _, row in df.iterrows():
        module = str(row["MODULE"]).strip()
        assessment_name = str(row["ASSESSMENT"]).strip()
        due_date = extract_date(str(row["DUE DATE"]).strip())
        due_time = str(row["DUE TIME"]).strip()

        if due_date is None:
            print(
                f"Warning: Could not parse date '{row['DUE DATE']}' for assessment "
                f"'{module}: {assessment_name}'. Skipping event creation."
            )
            continue

        start = parse_event_datetime(due_date, due_time)

        events.append(
            Event(
                title=f"{module}: {assessment_name}",
                location="",
                start=start,
                end=start + timedelta(minutes=1),
            )
        )

    return events


def is_event(cell_text: str) -> bool:
    """Return True when a timetable cell contains non-empty text."""
    if (not isinstance(cell_text, str)) or cell_text.strip() == "":
        return False
    return True


def is_class(cell_text: str) -> bool:
    """Return True when cell text contains a module code pattern."""
    class_pattern = r"\b[A-Z]{4}\d{4}\b"
    return bool(re.search(class_pattern, cell_text))


def parse_event_datetime(date: str, time: str) -> datetime:
    """Combine an ISO date with timetable-style time into an aware datetime."""
    normalized_time = time.strip().upper().replace("H", ":")

    parsed = datetime.strptime(
        f"{date} {normalized_time}",
        "%Y-%m-%d %H:%M",
    )

    return parsed.replace(tzinfo=APP_TIMEZONE)


def parse_class(cell_text: str, time_range: str, date: str) -> Event | None:
    """Build an `Event` from one timetable cell and its time/date context."""

    if not is_event(cell_text) or not is_class(cell_text):
        return None

    parts = cell_text.split()
    if len(parts) < 2 or date is None:
        return None

    title = parts[0]
    location = parts[1]
    start_time, end_time = time_range.split("-", maxsplit=1)

    return Event(
        title=title,
        location=location,
        start=parse_event_datetime(date, start_time),
        end=parse_event_datetime(date, end_time),
    )
