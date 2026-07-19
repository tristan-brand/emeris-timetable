"""Google Calendar integration utilities for emeris-timetable.

This module handles OAuth credential lifecycle and event publishing to a
configured Google Calendar.
"""

from __future__ import annotations

from datetime import datetime

from googleapiclient.discovery import build

from .event import Event, RemoteEvent
from .gauth import get_credentials

CALENDAR_ID = (
    "5fd290252a17d7f200dd40bebe24ba459d69a5eb863f00f1902c80f56c14f93b" "@group.calendar.google.com"
)


def get_calendar_service():
    """Build and return an authenticated Google Calendar service client."""
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)


def publish(service, event: Event) -> RemoteEvent:
    """Insert an event and return its local and remote representation."""
    resource = (
        service.events()
        .insert(
            calendarId=CALENDAR_ID,
            body=event.to_google(),
        )
        .execute()
    )

    return RemoteEvent(
        google_id=resource["id"],
        source_id=event.source_id,
        event=event,
    )


def delete(service, remote_event: RemoteEvent) -> None:
    """Delete a previously persisted event from Google Calendar."""
    service.events().delete(
        calendarId=CALENDAR_ID,
        eventId=remote_event.google_id,
    ).execute()


def get_calendar_events(service, min_time: datetime) -> list[RemoteEvent]:
    """Fetch managed events beginning at min_time."""
    result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=min_time.isoformat(),
            singleEvents=True,
            privateExtendedProperty="sync_name=emeris-timetable",
        )
        .execute()
    )

    remote_events = []
    for item in result.get("items", []):
        private = item.get("extendedProperties", {}).get("private", {})
        source_id = private.get("source_id")

        if source_id:
            remote_events.append(
                RemoteEvent(
                    google_id=item["id"],
                    source_id=source_id,
                    event=Event.from_google(item),
                )
            )

    return remote_events


def smoke_test(service):
    """Run a minimal connectivity check against the Calendar API."""
    # Non-destructive call that works with calendar.events scope
    result = (
        service.events()
        .list(
            calendarId="primary",
            maxResults=5,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    print("Connected. Able to read events on primary calendar.")
    print("Fetched events:", len(result.get("items", [])))
