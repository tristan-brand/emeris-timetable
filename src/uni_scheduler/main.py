from uni_scheduler import pdf_reader as rdr
from uni_scheduler import events_parser as psr
from uni_scheduler import gcalender as gcal


def main() -> None:
    # sync_classes()
    sync_assessments()

def sync_classes():
    tbls = rdr.extract_tables(rdr.class_pdf_path)

    week_dfs = rdr.extract_classes(tbls)
    print(f"Extracted {len(week_dfs)} week DataFrames from PDF.")

    events = []
    for df in week_dfs:
        events.extend(psr.parse_classes(df))
    print(f"Extracted {len(events)} events:")

    gcal.publish_events(events)

def sync_assessments():
    tbls = rdr.extract_tables_fallback(rdr.assess_pdf_path)

    df = rdr.extract_assessments(tbls)

    events = psr.parse_assessments(df)



if __name__ == "__main__":
    main()
