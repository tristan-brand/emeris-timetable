"""Domain model for timetable/assessment events.

`Event` instances are the internal representation used before transforming
data into Google Calendar API payloads.
"""

from datetime import datetime
import hashlib

class Event:
    """Represents a single scheduled item with date and time boundaries."""

    def __init__(self, title: str, location: str, date: str, start_time: str, end_time: str):
        """Create an event from already-parsed text values."""
        self.title = title
        self.location = location
        self.date = date
        self.start_time = start_time
        self.end_time = end_time

    def to_google_event(self, timezone: str = "Africa/Johannesburg") -> dict:
        """Convert this event into a Google Calendar `events.insert` payload."""
        start = self._norm_time(self.start_time)
        end = self._norm_time(self.end_time)

        return {
            "summary": self.title,
            "location": self.location,
            "start": {
                "dateTime": f"{self.date}T{start}:00",
                "timeZone": timezone,
            },
            "end": {
                "dateTime": f"{self.date}T{end}:00",
                "timeZone": timezone,
            },
            "extendedProperties": {
                "private": {
                    "sync_name" : "uni_scheduler",
                    "source_id": self.gen_source_id()
                }
            }
        }

    @staticmethod
    def _norm_time(t: str) -> str:
        """Normalize timetable-style time strings to 24-hour `HH:MM`."""
        t = t.strip().upper().replace("H", ":")
        if ":" not in t:
            t = f"{t}:00"
        h, m = t.split(":")
        return f"{int(h):02d}:{int(m):02d}"
    
    def gen_source_id(self) -> str:
        """Generate a stable event fingerprint used for sync deduplication."""
        source_str = f"{self.title.strip().upper()}_{self.date}_{self.start_time}"
        return hashlib.sha256(source_str.encode()).hexdigest()[:20]

    def __str__(self) -> str:
        """Return a readable one-line representation of the event."""
        return f"{self.title} at {self.location} on {self.date} from {self.start_time} to {self.end_time}"
