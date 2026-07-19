"""Shared OAuth credential loading for Google API clients."""

from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from platformdirs import user_config_path, user_data_path

APP_NAME = "emeris-timetable"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.modify",
]

CREDENTIALS_FILE = user_config_path(APP_NAME) / "google_credentials.json"
TOKEN_FILE = user_data_path(APP_NAME) / "google_token.json"


def get_credentials(
    credentials_file: Path = CREDENTIALS_FILE,
    token_file: Path = TOKEN_FILE,
) -> Credentials:
    """Load, refresh, or create OAuth credentials for Google API access."""
    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None
        else:
            token_file.write_text(creds.to_json(), encoding="utf-8")
            token_file.chmod(0o600)
            return creds

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
        creds = flow.run_local_server(port=0)

        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")
        token_file.chmod(0o600)

    return creds
