from __future__ import annotations

"""Google Calendar integration utilities for emeris-timetable.

This module handles OAuth credential lifecycle and event publishing to a
configured Google Calendar.
"""

from emeris_timetable.event import Event
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CREDENTIALS_FILE = Path("bin/resrc/google_credentials.json")
TOKEN_FILE = Path("bin/resrc/google_token.json")

CALENDER_ID = "5fd290252a17d7f200dd40bebe24ba459d69a5eb863f00f1902c80f56c14f93b@group.calendar.google.com"



def get_google_credentials(
    credentials_file: Path = CREDENTIALS_FILE,
    token_file: Path = TOKEN_FILE,
) -> Credentials:
    """Load, refresh, or create OAuth credentials for Calendar API access."""
    creds = None

    # 1) Reuse prior token if present
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    # 2) Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json(), encoding="utf-8")
        return creds

    # 3) If still invalid/missing, do full interactive OAuth once
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
        creds = flow.run_local_server(port=0)  # opens browser

        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_calendar_service():
    """Build and return an authenticated Google Calendar service client."""
    creds = get_google_credentials()
    return build("calendar", "v3", credentials=creds)


def publish_events(events: list[Event]):
    """Insert each `Event` in the target calendar as a new Google event."""
    creds = get_google_credentials()
    service = build("calendar", "v3", credentials=creds)
    for event in events:
        # One insert call per event; no duplicate protection here.
        service.events().insert(calendarId=CALENDER_ID, body = event.to_google_event()).execute()
        print(f"Published event: {event.title} on {event.date} at {event.start_time} in {event.location}")

def sync(events: list[Event]):
    """Load upcoming events and build a source-id map for sync workflows."""
    creds = get_google_credentials()
    service = build("calendar", "v3", credentials=creds)

    # Fetch existing events from today onwards from calendar
    now = datetime.now(datetime.timezone.utc).isoformat() + "Z"  # 'Z' indicates UTC time
    existing_events_result = service.events().list(
        calendarId=CALENDER_ID,
        timeMin=now,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    existing_events = existing_events_result.get("items", [])
    existing_events_map = {e["extendedProperties"]["private"]["source_id"]: e for e in existing_events if "extendedProperties" in e and "private" in e["extendedProperties"] and "source_id" in e["extendedProperties"]["private"]}

def smoke_test():
    """Run a minimal connectivity check against the Calendar API."""
    creds = get_google_credentials()
    print("Credential scopes:", creds.scopes)
    print("Credential valid:", creds.valid)
    print("Credential expired:", creds.expired)
    print("Has refresh token:", bool(creds.refresh_token))
    service = build("calendar", "v3", credentials=creds)
    # Non-destructive call that works with calendar.events scope
    result = service.events().list(
        calendarId="primary",
        maxResults=5,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    print("Connected. Able to read events on primary calendar.")
    print("Fetched events:", len(result.get("items", [])))


if __name__ == "__main__":
    smoke_test()
