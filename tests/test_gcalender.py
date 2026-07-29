"""Tests for the Google Calendar adapter without external API calls."""

from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from emeris_timetable.event import Event, RemoteEvent
from emeris_timetable.gcalender import TIMETABLE_CALENDAR_ID, delete, get_calendar_events, publish

TIMEZONE = ZoneInfo("Africa/Johannesburg")


def make_event() -> Event:
    """Return an event used by Calendar adapter tests."""
    return Event(
        title="COMP1234",
        location="Room101",
        start=datetime(2026, 7, 20, 9, 0, tzinfo=TIMEZONE),
        end=datetime(2026, 7, 20, 10, 0, tzinfo=TIMEZONE),
    )

# TODO fix the tests below to use the new source parameter in publish() and delete() functions
def test_publish_returns_remote_event():
    service = Mock()
    service.events.return_value.insert.return_value.execute.return_value = {"id": "remote-1"}
    event = make_event()

    remote = publish(service, event)

    assert remote == RemoteEvent("remote-1", event.source_id, event)
    service.events.return_value.insert.assert_called_once_with(
        calendarId=TIMETABLE_CALENDAR_ID,
        body=event.to_google(),
    )


# TODO fix the tests below to use the new source parameter in publish() and delete() functions
def test_delete_uses_google_event_id():
    service = Mock()
    event = make_event()
    remote = RemoteEvent("remote-1", event.source_id, event)

    delete(service, remote)

    service.events.return_value.delete.assert_called_once_with(
        calendarId=TIMETABLE_CALENDAR_ID,
        eventId="remote-1",
    )


def test_get_calendar_events_converts_google_resources():
    service = Mock()
    event = make_event()
    service.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "remote-1",
                "summary": event.title,
                "location": event.location,
                "start": {"dateTime": event.start.isoformat()},
                "end": {"dateTime": event.end.isoformat()},
                "extendedProperties": {
                    "private": {
                        "sync_name": "emeris-timetable",
                        "source_id": event.source_id,
                    }
                },
            }
        ]
    }

    remote_events = get_calendar_events(service, event.start)

    assert remote_events == [RemoteEvent("remote-1", event.source_id, event)]
    service.events.return_value.list.assert_called_once_with(
        calendarId=TIMETABLE_CALENDAR_ID,
        timeMin="2026-07-20T09:00:00+02:00",
        singleEvents=True,
        privateExtendedProperty="sync_name=emeris-timetable",
    )
