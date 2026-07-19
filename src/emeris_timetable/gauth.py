from pathlib import Path
from platformdirs import user_config_path, user_data_path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

APP_NAME = "emeris-timetable"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly"
]

credentials_file = user_config_path(APP_NAME) / "google_credentials.json"
token_file = user_data_path(APP_NAME) / "google_token.json"

def get_credentials(credentials_file: Path = credentials_file,
                    token_file: Path = token_file):
    """Load, refresh, or create OAuth credentials for Google API access."""
    creds = None

    # 1) Reuse prior token if present
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    # 2) Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None  # Force re-authentication if refresh fails
        else:
            token_file.write_text(creds.to_json(), encoding="utf-8")
            token_file.chmod(0o600)
            return creds

    # 3) If still invalid/missing, do full interactive OAuth once
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
        creds = flow.run_local_server(port=0)  # opens browser

        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")
        token_file.chmod(0o600)

    return creds