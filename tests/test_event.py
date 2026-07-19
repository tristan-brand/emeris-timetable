"""Tests for local and remote event representations."""

from datetime import datetime
from zoneinfo import ZoneInfo

from emeris_timetable.event import Event, RemoteEvent

TIMEZONE = ZoneInfo("Africa/Johannesburg")


def make_event(
    *,
    title: str = "MATH1010",
    location: str = "Room A",
    start: datetime | None = None,
    end: datetime | None = None,
) -> Event:
    """Return a representative timezone-aware event for a test."""
    return Event(
        title=title,
        location=location,
        start=start or datetime(2026, 7, 20, 9, 0, tzinfo=TIMEZONE),
        end=end or datetime(2026, 7, 20, 10, 0, tzinfo=TIMEZONE),
    )


def test_source_id_is_stable_for_identical_events():
    assert make_event().source_id == make_event().source_id


def test_source_id_changes_with_title_or_start():
    original = make_event()
    renamed = make_event(title="PHYS1010")
    moved = make_event(start=datetime(2026, 7, 20, 11, 0, tzinfo=TIMEZONE))

    assert original.source_id != renamed.source_id
    assert original.source_id != moved.source_id


def test_to_google_preserves_event_data_and_sync_metadata():
    event = make_event()

    payload = event.to_google()

    assert payload["summary"] == event.title
    assert payload["location"] == event.location
    assert payload["start"]["dateTime"] == "2026-07-20T09:00:00+02:00"
    assert payload["end"]["dateTime"] == "2026-07-20T10:00:00+02:00"
    assert payload["extendedProperties"]["private"] == {
        "sync_name": "emeris-timetable",
        "source_id": event.source_id,
    }


def test_from_google_builds_domain_event():
    resource = {
        "id": "google-event-id",
        "summary": "MATH1010",
        "location": "Room A",
        "start": {"dateTime": "2026-07-20T09:00:00+02:00"},
        "end": {"dateTime": "2026-07-20T10:00:00+02:00"},
    }

    event = Event.from_google(resource)

    assert event == make_event()


def test_remote_event_keeps_google_identity_separate():
    event = make_event()

    remote = RemoteEvent("google-event-id", event.source_id, event)

    assert remote.google_id == "google-event-id"
    assert remote.event is event
