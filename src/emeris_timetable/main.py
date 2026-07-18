"""CLI entrypoint for extracting timetable data and publishing to Google Calendar."""

from emeris_timetable import pdf_reader as rdr
from emeris_timetable import events_parser as psr
from emeris_timetable import gcalender as gcal
from emeris_timetable import event


def main() -> None:
    """Run the default sync flow.

    Currently configured to sync assessments only.
    """
    # sync_classes()
    sync_assessments()

def sync_classes():
    """Extract class timetable events from PDF and publish them to Calendar."""
    tbls = rdr.extract_tables(rdr.class_pdf_path)

    week_dfs = rdr.extract_classes(tbls)
    print(f"Extracted {len(week_dfs)} week DataFrames from PDF.")

    events = []
    for df in week_dfs:
        events.extend(psr.parse_classes(df))
    print(f"Extracted {len(events)} events:")

    gcal.publish_events(events)

def sync_assessments():
    """Extract assessment events from PDF and publish them to Calendar."""
    tbls = rdr.extract_tables_fallback(rdr.assess_pdf_path)

    df = rdr.extract_assessments(tbls)

    events  = psr.parse_assessments(df)

    gcal.publish_events(events)



if __name__ == "__main__":
    main()
