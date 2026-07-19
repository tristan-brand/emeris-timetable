"""CLI entrypoint for extracting timetable data and publishing to Google Calendar."""

from pathlib import Path
from tempfile import TemporaryDirectory
from . import pdf_reader as rdr
from . import events_parser as psr
from . import gcalender as gcal
from . import gmail as gm
from .event import Event
from .event import RemoteEvent


def main() -> None:
    """Run the default sync flow.

    Currently configured to sync classes only.
    """
    sync_classes()
    # sync_assessments()

def load_classes_from_import(service) -> list[Event]:
    message = gm.scan(service)
    if message is None:
        print("No unread messages found with the 'Emeris Timetable' label.")
        return None

    message_id = message["id"]

    with TemporaryDirectory(prefix="emeris_timetable_") as temp_dir:
        pdf_path = Path(temp_dir) / "timetable.pdf"

        gm.download_pdf_attachment(
            service,
            message_id,
            pdf_path
        )

        tbls = rdr.extract_tables(pdf_path)
        week_dfs = rdr.extract_classes(tbls)
        print(f"Extracted {len(week_dfs)} week DataFrames from PDF.")

        events = []
        for df in week_dfs:
            events.extend(psr.parse_classes(df))
        
        print(f"Extracted {len(events)} events:")

    return events

def init_gmail_service():
    """Initialize and return the Gmail service client."""
    try:
        service = gm.get_gmail_service()
        return service
    except Exception as e:
        print(f"Failed to initialize Gmail service: {e}")
        return None

def init_calendar_service():
    """Initialize and return the Google Calendar service client."""
    try:
        service = gcal.get_calendar_service()
        return service
    except Exception as e:
        print(f"Failed to initialize Google Calendar service: {e}")
        return None

def sync_classes():
    """Extract class timetable events from PDF and publish them to Calendar."""
    gmail_service = init_gmail_service()
    calendar_service = init_calendar_service()
    if gmail_service is None or calendar_service is None:
        print("One or more required services failed to initialize. Exiting sync_classes.")
        return

    parsed_events = load_classes_from_import(gmail_service)

    if parsed_events is None or len(parsed_events) == 0:
        print("No new events to sync. Exiting.")
        return

    first_event = min(event.start for event in parsed_events)

    start_time = first_event.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    remote_events = gcal.get_calendar_events(calendar_service, min_time=start_time)

    remote_by_source_id = {
        item.source_id: item
        for item in remote_events
    }

    desired_by_source_id = {
        item.source_id: item
        for item in parsed_events
    }

    additions = desired_by_source_id.keys() - remote_by_source_id.keys()
    removals = remote_by_source_id.keys() - desired_by_source_id.keys()

    for source_id in additions:
        event_to_add = desired_by_source_id[source_id]
        gcal.publish(calendar_service, event_to_add)
        print(
            f"Added event: {event_to_add.title} "
            f"on {event_to_add.start:%Y-%m-%d} "
            f"at {event_to_add.start:%H:%M} "
            f"in {event_to_add.location}"
        )
    
    for source_id in removals:
        google_event_to_remove = remote_by_source_id[source_id]
        gcal.delete(calendar_service, google_event_to_remove)
        print(
            f"Removed event: {google_event_to_remove.event.title} "
            f"| id: {google_event_to_remove.google_id}"
        )


def sync_assessments() -> None:
    """Extract assessment events and publish them to Calendar."""
    calendar_service = init_calendar_service()
    if calendar_service is None:
        return

    tables = rdr.extract_tables_fallback(rdr.assess_pdf_path)
    dataframe = rdr.extract_assessments(tables)
    events = psr.parse_assessments(dataframe)

    for assessment in events:
        gcal.publish(calendar_service, assessment)



if __name__ == "__main__":
    main()
