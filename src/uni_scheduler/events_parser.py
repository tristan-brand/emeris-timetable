"""Parse normalized timetable and assessment tables into `Event` objects.

This module converts dataframe rows/cells into `Event` instances consumed by
the Google Calendar sync layer.
"""

import re
import pandas as pd
from uni_scheduler.event import Event
from dateutil import parser

def extract_date(date_str: str) -> str:
    """Parse a human-readable date into ISO format (`YYYY-MM-DD`).

    Returns `None` when parsing fails.
    """
    try:
        dt = parser.parse(date_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except (parser.ParserError, ValueError):
        return None

def parse_classes(df : pd.DataFrame) -> list[Event]:
    """Parse a normalized class timetable dataframe into class events."""
    events = []
    for col in df.columns[1:]:  # First column stores time ranges.
        for idx, cell in df[col].items():
            time_range = df.iloc[idx, 0]
            date = extract_date(col)
            event = parse_event(cell, time_range, date)
            if event is not None:
                events.append(event)
    return events

def parse_assessments(df : pd.DataFrame) -> list[Event]:
    """Parse assessment rows into events using due date and due time."""
    events = []
    for idx, row in df.iterrows():
        module = str(row["MODULE"]).strip()
        assessment_name = str(row["ASSESSMENT"]).strip()
        due_date = str(row["DUE DATE"]).strip()
        due_time = str(row["DUE TIME"]).strip()

        title = f"{module}: {assessment_name}"
        date = extract_date(due_date)
        if date is None:
            print(f"Warning: Could not parse date '{due_date}' for assessment '{title}'. Skipping event creation.")
            continue
        event = Event(title=title, location="N/A", date=date, start_time=due_time, end_time=due_time)
        events.append(event)

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

def parse_event(cell_text: str, time_range: str, date: str) -> Event:
    """Build an `Event` from one timetable cell and its time/date context."""

    if (not is_event(cell_text)): return None
    if (not is_class(cell_text)): return None

    parts = cell_text.split()

    if len(parts) < 2:
        # error: not enough parts to parse event
        # TODO: log and handle this error
        return None

    name = parts[0]
    location = parts[1]
    start_time, end_time = time_range.split('-')


    return Event(title=name, location=location, date=date, start_time=start_time, end_time=end_time)

def smoke_test():
    """Simple local sanity check for date parsing and class parsing."""
    sample_cell = "COMP1234 Room101"
    sample_time_range = "9H00 - 10H00"
    sample_date = "1 Jan"
    sample_date2 = "15 February"
    sample_date3 = "31 Mar 2024"
    sample_date4 = "InvalidDate"

    try :
        print(extract_date(sample_date))  # Expected: "2024-01-01"
        print(extract_date(sample_date2)) # Expected: "2024-02-15"
        print(extract_date(sample_date3)) # Expected: "2024-03-31"
        print(extract_date(sample_date4)) # Expected: "InvalidDate" (fallback to original)
    except Exception as e:
        print(f"Date parsing error: {e}")

    event = parse_event(sample_cell, sample_time_range, sample_date)
    if event:
        print("Parsed Event:")
        print(f"Title: {event.title}")
        print(f"Location: {event.location}")
        print(f"Date: {event.date}")
        print(f"Start Time: {event.start_time}")
        print(f"End Time: {event.end_time}")
    else:
        print("Failed to parse event.")

if __name__ == "__main__":
    smoke_test()
