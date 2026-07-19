from dataclasses import dataclass
from datetime import datetime
import hashlib
from typing import Any

@dataclass(frozen=True)
class Event:

    title: str
    location: str
    start: datetime
    end: datetime

    @property
    def source_id(self) -> str:
        value = f"{self.title}|{self.start.isoformat()}"
        return hashlib.sha256(value.encode()).hexdigest()[:20]

    def to_google(self) -> dict[str, Any]:
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
        return cls(
            title=resource.get("summary", ""),
            location=resource.get("location", ""),
            start=datetime.fromisoformat(resource["start"]["dateTime"]),
            end=datetime.fromisoformat(resource["end"]["dateTime"]),
        )

@dataclass(frozen=True)
class RemoteEvent:
    google_id: str
    source_id: str
    event: Event


