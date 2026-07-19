"""Gmail discovery and PDF attachment download utilities."""

import base64
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .gauth import get_credentials


def get_gmail_service():
    """Build and return an authenticated Gmail service client."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def get_label_id(service, label_name: str) -> str | None:
    """Retrieve the ID of a Gmail label by its name."""
    try:
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        for label in labels:
            if label["name"] == label_name:
                return label["id"]
    except HttpError as error:
        print(f"An error occurred while fetching labels: {error}")
    return None

def mark_message_as_read(service, message_id: str) -> None:
    """Mark a Gmail message as read by removing the 'UNREAD' label."""
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except HttpError as error:
        print(f"An error occurred while marking the message as read: {error}")

def mark_message_as_unread(service, message_id: str) -> None:
    """Mark a Gmail message as unread by adding the 'UNREAD' label."""
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": ["UNREAD"]},
        ).execute()
    except HttpError as error:
        print(f"An error occurred while marking the message as unread: {error}")


def iter_message_parts(part: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield every MIME part, including nested parts."""
    yield part

    for child in part.get("parts", []):
        yield from iter_message_parts(child)


def download_pdf_attachment(
    service,
    message_id: str,
    destination: Path,
) -> Path:
    """Download the first PDF attachment from a Gmail message."""
    message = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    for part in iter_message_parts(message["payload"]):
        filename = part.get("filename", "")
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})

        if mime_type != "application/pdf" and not filename.lower().endswith(".pdf"):
            continue

        if attachment_id := body.get("attachmentId"):
            body = (
                service.users()
                .messages()
                .attachments()
                .get(
                    userId="me",
                    messageId=message_id,
                    id=attachment_id,
                )
                .execute()
            )

        encoded_data = body.get("data")
        if not encoded_data:
            raise ValueError(f"PDF attachment has no data: {filename}")

        destination.write_bytes(base64.urlsafe_b64decode(encoded_data))
        return destination

    raise ValueError("No PDF attachment found in the message.")


def scan(service) -> dict[str, Any] | None:
    """Return the newest unread message carrying the timetable label."""
    label_id = get_label_id(service, "Emeris Timetable")

    if not label_id:
        print("Label 'Emeris Timetable' not found.")
        return None

    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            labelIds=[label_id],
            q="is:unread",
            maxResults=1,
        )
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        print('No unread messages found with the "Emeris Timetable" label.')
        return None

    return messages[0]
