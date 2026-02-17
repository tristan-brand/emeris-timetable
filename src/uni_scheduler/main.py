import pdf_reader
import events_parser


def main() -> None:
    timetable_df = pdf_reader.extract_tables_from_pdf(pdf_reader.pdf_path)
    print(timetable_df.head())  # Debug statement to check the extracted DataFrame
    events = events_parser.parse_events(timetable_df)
    print(f"Extracted {len(events)} events:")

    for event in events:
        print(f"{event.name} in {event.location} on {event.day} {event.date} from {event.start_time} to {event.end_time}")

if __name__ == "__main__":
    main()