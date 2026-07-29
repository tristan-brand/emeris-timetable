"""CLI entrypoint for extracting timetable data and publishing to Google Calendar."""

from pathlib import Path
from tempfile import TemporaryDirectory
from argparse import ArgumentParser

from pandas import DataFrame

from . import events_parser as psr
from . import gcalender as gcal
from . import gmail as gm
from . import pdf_reader as rdr
from .event import Event

TIMETABLE_SRC = "Timetable"
ASSESSMENTS_SRC = "Assessments"


def main() -> None:
    """Run the default class-timetable synchronization flow."""

    parser = ArgumentParser(description="Extract timetable data from Gmail and publish to Google Calendar.")

    parser.add_argument("-c", "--classes", action="store_true", help="Sync class events")
    parser.add_argument("-a", "--assessments", action="store_true", help="Sync assessment events")

    args = parser.parse_args()

    gmail_service = init_gmail_service()
    if gmail_service is None:
        print("Failed to initialize Gmail service. Exiting.")
        return
    calendar_service = init_calendar_service()
    if calendar_service is None:
        print("Failed to initialize Google Calendar service. Exiting.")
        return

    # TODO handle the case where both classes and assessments are requested
    source = TIMETABLE_SRC if args.classes else ASSESSMENTS_SRC if args.assessments else None
    if source is None:
        print("No source specified. Use --classes or --assessments.")
        return

    sync_events(source, gmail_service, calendar_service)

def sync_events(source: str, gmail_service, calendar_service) -> None:
    """Sync events based on the provided arguments."""

    parsed_events = load_events(gmail_service, source)
    if parsed_events is None or len(parsed_events) == 0:
        print(f"No new {source.lower()} events to sync. Exiting.")
        return

    first_event = min(event.start for event in parsed_events)
    start_time = first_event.replace(hour=0, minute=0, second=0, microsecond=0)

    remote_events = gcal.get_calendar_events(calendar_service, source, min_time=start_time)

    remote_by_source_id = {item.source_id: item for item in remote_events}
    desired_by_source_id = {item.source_id: item for item in parsed_events}

    additions = desired_by_source_id.keys() - remote_by_source_id.keys()
    removals = remote_by_source_id.keys() - desired_by_source_id.keys()

    if source == TIMETABLE_SRC:
        sync_classes(additions, removals, desired_by_source_id, remote_by_source_id, calendar_service)
    if source == ASSESSMENTS_SRC:
        sync_assessments(additions, desired_by_source_id, calendar_service)

def load_events(service, source: str) -> list[Event] | None:
    """Download and parse the newest unread attachment."""

    if source not in [TIMETABLE_SRC, ASSESSMENTS_SRC]:
        raise ValueError(f"Unknown source: {source}")

    message = load_message(service, source)
    if message is None:
        return None

    payload = extract_payload(service, message["id"], source)
    events = process_events(payload, source)

    if events:
        gm.mark_message_as_read(service, message["id"])

    return events

def load_message(service, source: str) -> dict[str, any] | None:
    """Return the newest unread message carrying the timetable label."""

    message = gm.scan(service, source)
    if message is None:
        print(f"No unread messages found with the 'Emeris {source}' label for source '{source}'.")
        return None

    return message

def extract_payload(service, message_id: str, source: str) -> list[DataFrame] | None:
    """Download and parse the newest unread attachment."""

    with TemporaryDirectory(prefix="emeris_timetable_") as temp_dir:
        pdf_path = Path(temp_dir) / "attachment.pdf"

        gm.download_pdf_attachment(
            service,
            message_id,
            pdf_path,
        )

        tbls = rdr.extract_tables(pdf_path) if source == TIMETABLE_SRC else rdr.extract_tables_fallback(pdf_path)
        return tbls

def process_events(tbls: list[DataFrame], source: str) -> list[Event]:
    """Process the extracted tables into a list of events."""

    if source == TIMETABLE_SRC:
        week_dfs = rdr.extract_classes(tbls)
        print(f"Extracted {len(week_dfs)} week DataFrames from PDF.")

        events: list[Event] = []
        for df in week_dfs:
            events.extend(psr.parse_classes(df))

        print(f"Extracted {len(events)} events:")
        return events

    elif source == ASSESSMENTS_SRC:
        df = rdr.extract_assessments(tbls)
        print(f"Extracted {len(df)} assessment rows from PDF.")

        events: list[Event] = psr.parse_assessments(df)

        print(f"Extracted {len(events)} events:")
        return events

    else:
        raise ValueError(f"Unknown source: {source}")


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


# TODO solve class sync removing assessments
def sync_classes(additions, removals, desired, remote, calendar_service) -> None:
    """Reconcile the latest emailed class timetable with Google Calendar."""
    for source_id in additions:
        event_to_add = desired[source_id]
        gcal.publish(calendar_service, source=TIMETABLE_SRC, event=event_to_add)
        print(
            f"Added event: {event_to_add.title} "
            f"on {event_to_add.start:%Y-%m-%d} "
            f"at {event_to_add.start:%H:%M} "
            f"in {event_to_add.location}"
        )

    for source_id in removals:
        google_event_to_remove = remote[source_id]
        gcal.delete(calendar_service, source=TIMETABLE_SRC, remote_event=google_event_to_remove)
        print(
            f"Removed event: {google_event_to_remove.event.title} "
            f"| id: {google_event_to_remove.google_id}"
        )


def sync_assessments(additions, desired, calendar_service) -> None:
    """Reconcile the latest emailed class timetable with Google Calendar."""
    for source_id in additions:
        event_to_add = desired[source_id]
        gcal.publish(calendar_service, source=ASSESSMENTS_SRC, event=event_to_add)
        print(
            f"Added event: {event_to_add.title} "
            f"on {event_to_add.start:%Y-%m-%d} "
            f"at {event_to_add.start:%H:%M} "
            f"in {event_to_add.location}"
        )

if __name__ == "__main__":
    main()
