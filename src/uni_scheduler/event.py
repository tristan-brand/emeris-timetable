from datetime import datetime
import hashlib

class Event:
    def __init__(self, title: str, location: str, date: str, start_time: str, end_time: str):
        self.title = title
        self.location = location
        self.date = date
        self.start_time = start_time
        self.end_time = end_time

    def to_google_event(self, year: int, timezone: str = "Africa/Johannesburg") -> dict:
        iso_date = self._norm_date(self.date, year)
        start = self._norm_time(self.start_time)
        end = self._norm_time(self.end_time)

        return {
            "summary": self.title,
            "location": self.location,
            "start": {
                "dateTime": f"{iso_date}T{start}:00",
                "timeZone": timezone,
            },
            "end": {
                "dateTime": f"{iso_date}T{end}:00",
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
        # Normalize time formats like "9H00" to "09:00"
        t = t.strip().upper().replace("H", ":")
        if ":" not in t:
            t = f"{t}:00"
        h, m = t.split(":")
        return f"{int(h):02d}:{int(m):02d}"

    @staticmethod
    def _norm_date(d: str, year: int) -> str:
        # Normalize date formats like "1 Jan" to "YYYY-MM-DD"
        value = d.strip().replace(",", "")
        for fmt in ("%d %b %Y", "%d %B %Y"):
            try:
                dt = datetime.strptime(f"{value} {year}", fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        raise ValueError(f"Unsupported date format: '{d}'")
    
    def gen_source_id(self) -> str:
        """
        Generate a unique ID for the event based on its properties
        
        :param self: Event instance
        :return: A unique string ID for the event
        :rtype: str
        """
        source_str = f"{self.title.strip().upper()}_{self.date}_{self.start_time}"
        return hashlib.sha256(source_str.encode()).hexdigest()[:20]

def __str__(self):
        return f"{self.title} at {self.location} on {self.day} {self.date} from {self.start_time} to {self.end_time}"