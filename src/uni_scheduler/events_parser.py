import re
import pandas as pd
from uni_scheduler.event import Event


def extract_day_date(day_str: str) -> tuple[str, str]:
    # Example input: "Mon 1 Jan:
    match = re.match(r"(\w+)\s+(\d{1,2}\s+\w+)", day_str)
    if match:
        return match.group(1), match.group(2)
    return day_str, ""  # Fallback if format is unexpected

def parse_events(df : pd.DataFrame) -> list[Event]:
    events = []
    for col in df.columns[1:]:  # Skip the first column which is likely time
        for idx, cell in df[col].items():
            time_range = df.iloc[idx, 0]  # Assuming first column has time ranges
            day, date = extract_day_date(col)
            event = parse_event(cell, time_range, day, date)
            if event is not None:
                events.append(event)
    return events


# is_event method: check if cell contains event
def is_event(cell_text: str) -> bool:
    if (not isinstance(cell_text, str)) or cell_text.strip() == "":
        return False
    return True

# is_class method: check if event is a class
def is_class(cell_text: str) -> bool:
    class_pattern = r"\b[A-Z]{4}\d{4}\b"
    return bool(re.search(class_pattern, cell_text))

# parse_event method: extract event details from cell text and create Event object
def parse_event(cell_text: str, time_range: str, day: str, date: str) -> Event:

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


    return Event(name=name, location=location, day=day, date=date, start_time=start_time, end_time=end_time)
