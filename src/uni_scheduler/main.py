from uni_scheduler import pdf_reader as rdr
from uni_scheduler import events_parser as psr
from uni_scheduler import gcalender as gcal


def main() -> None:
    timetables = rdr.extract_tables(rdr.pdf_path)
    week_dfs = rdr.extract_schedule(timetables)
    print(f"Extracted {len(week_dfs)} week DataFrames from PDF.")
    events = []
    for df in week_dfs:
        events.extend(psr.parse_events(df))
    print(f"Extracted {len(events)} events:")

    gcal.publish_events(events)


if __name__ == "__main__":
    main()
