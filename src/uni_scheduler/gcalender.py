from uni_scheduler.event import Event
from __future__ import annotations

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CREDENTIALS_FILE = Path("bin/resrc/google_credentials.json")
TOKEN_FILE = Path("bin/resrc/google_token.json")


def get_google_credentials(
    credentials_file: Path = CREDENTIALS_FILE,
    token_file: Path = TOKEN_FILE,
) -> Credentials:
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
    creds = get_google_credentials()
    return build("calendar", "v3", credentials=creds)


def smoke_test():
    service = get_calendar_service()
    # Simple non-destructive call
    result = service.calendarList().list(maxResults=5).execute()
    print("Connected. Calendars:")
    for item in result.get("items", []):
        print("-", item.get("summary"))


if __name__ == "__main__":
    smoke_test()
