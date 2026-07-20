# Emeris Timetable

Emeris Timetable extracts class and assessment schedules from PDF tables and
synchronizes them with Google Calendar. The class workflow discovers the newest
unread timetable email under a dedicated Gmail label, downloads its PDF
attachment to a temporary directory, parses its events, and reconciles those
events with entries previously managed by this application.

## Requirements

- Python 3.10 through 3.13
- [Poetry](https://python-poetry.org/)
- A Java runtime for the primary `tabula-py` PDF extractor
- A Google Cloud OAuth desktop client with Gmail API and Calendar API enabled
- Native dependencies required by Camelot if using the fallback PDF extractor

## Installation

```bash
git clone <repo-url>
cd emeris-timetable
poetry install
```

Poetry creates or reuses the project virtual environment and installs the
`emeris-timetable` command.

## Google Setup

Create an OAuth client for a desktop application in Google Cloud and enable the
Gmail and Google Calendar APIs. Store the downloaded client file outside the
repository at:

```text
~/.config/emeris-timetable/google_credentials.json
```

The first run opens a browser for consent. The resulting refresh token is stored
with owner-only permissions at:

```text
~/.local/share/emeris-timetable/google_token.json
```

The application currently requests these scopes:

- `calendar.events` to read and modify calendar events
- `gmail.readonly` to find timetable messages and download attachments

Create a Gmail label named `Emeris Timetable` and apply it to incoming timetable
messages. The class sync reads the newest unread message with that label. It does
not currently mark the message as read after processing.

Set the target Google Calendar ID in `src/emeris_timetable/gcalender.py`. Events
created by the application carry private `sync_name` and `source_id` properties,
which are used to identify additions and removals during later runs.

## Usage

Run the default class synchronization:

```bash
poetry run emeris-timetable
```

Run a package module directly while developing:

```bash
poetry run python -m emeris_timetable.main
```

Downloaded PDF attachments exist only for the duration of parsing and are
removed with their temporary directory afterward. PDF extraction diagnostics
may be written under `bin/extracted_tables/`.

## Development

Run the isolated unit tests:

```bash
poetry run pytest
```

Check style and import ordering:

```bash
poetry run ruff check src tests
```

Build the distribution:

```bash
poetry build
```

## Known Issues
Class parsing incorrectly parses workshop class locations (with `WKSP` tag) as `WKSP` instead of location tag

The tests mock Google API services and do not require credentials, network
access, or changes to a real mailbox or calendar.

## Project Structure

```text
src/emeris_timetable/
  event.py          Domain and remote event models
  events_parser.py  Table-row to Event conversion
  gauth.py          Shared Google OAuth lifecycle
  gmail.py          Message discovery and PDF download
  gcalender.py      Google Calendar persistence adapter
  pdf_reader.py     Tabula and Camelot table extraction
  main.py           Synchronization orchestration
tests/              Isolated unit tests
```

## Security

Do not commit OAuth client credentials or refresh tokens. Keep both files at
mode `600` and their parent directories at mode `700`. If either secret was ever
committed, revoke or rotate it; adding it to `.gitignore` does not remove it from
Git history.
