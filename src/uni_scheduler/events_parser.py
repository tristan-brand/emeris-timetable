import re
import pandas as pd
from uni_scheduler.event import Event
from dateutil import parser

def extract_date(date_str: str) -> str:
    try:
        dt = parser.parse(date_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except (parser.ParserError, ValueError):
        return date_str  # Return original if parsing fails

def parse_classes(df : pd.DataFrame) -> list[Event]:
    events = []
    for col in df.columns[1:]:  # Skip the first column which is likely time
        for idx, cell in df[col].items():
            time_range = df.iloc[idx, 0]  # Assuming first column has time ranges
            date = extract_date(col)
            event = parse_event(cell, time_range, date)
            if event is not None:
                events.append(event)
    return events

def parse_assessments(df : pd.DataFrame) -> list[Event]:
    events = []
    for idx, row in df.iterrows():
        module = str(row["MODULE"]).strip()
        assessment_name = str(row["ASSESSMENT"]).strip()
        due_date = str(row["DUE DATE"]).strip()
        due_time = str(row["DUE TIME"]).strip()

        title = f"{module}: {assessment_name}"
        date = extract_date(due_date)
        event = Event(title=title, location="N/A", date=date, start_time=due_time, end_time=due_time)
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
def parse_event(cell_text: str, time_range: str, date: str) -> Event:

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
    sample_cell = "COMP1234 Room101"
    sample_time_range = "9H00 - 10H00"
    sample_day = "Monday"
    sample_date = "1 Jan"

    event = parse_event(sample_cell, sample_time_range, sample_day, sample_date)
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