import pdf_reader as rdr
import events_parser as psr


def main() -> None:
    timetables = rdr.extract_tables(rdr.pdf_path)
    week_dfs = rdr.extract_schedule(timetables)
    print(f"Extracted {len(week_dfs)} week DataFrames from PDF.")
    events = []
    for df in week_dfs:
        events.extend(psr.parse_events(df))
    print(f"Extracted {len(events)} events:")

    for event in events:
        print(f"{event.name} in {event.location} on {event.day} {event.date} from {event.start_time} to {event.end_time}")

if __name__ == "__main__":
    main()
