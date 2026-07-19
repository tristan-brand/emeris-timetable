"""Domain models shared by timetable parsing and Calendar synchronization."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Event:
    """A scheduled timetable or assessment event."""

    title: str
    location: str
    start: datetime
    end: datetime

    @property
    def source_id(self) -> str:
        """Return the stable identifier used to reconcile this event."""
        value = f"{self.title}|{self.start.isoformat()}"
        return hashlib.sha256(value.encode()).hexdigest()[:20]

    def to_google(self) -> dict[str, Any]:
        """Convert the event to a Google Calendar API request body."""
        return {
            "summary": self.title,
            "location": self.location,
            "start": {
                "dateTime": self.start.isoformat(),
                "timeZone": "Africa/Johannesburg",
            },
            "end": {
                "dateTime": self.end.isoformat(),
                "timeZone": "Africa/Johannesburg",
            },
            "extendedProperties": {
                "private": {
                    "sync_name": "emeris-timetable",
                    "source_id": self.source_id,
                }
            },
        }

    @classmethod
    def from_google(cls, resource: dict[str, Any]) -> "Event":
        """Build an event from a timed Google Calendar event resource."""
        return cls(
            title=resource.get("summary", ""),
            location=resource.get("location", ""),
            start=datetime.fromisoformat(resource["start"]["dateTime"]),
            end=datetime.fromisoformat(resource["end"]["dateTime"]),
        )


@dataclass(frozen=True)
class RemoteEvent:
    """An event persisted in Google Calendar with its remote identity."""

    google_id: str
    source_id: str
    event: Event
