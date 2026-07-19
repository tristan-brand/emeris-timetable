"""Tests for Gmail MIME traversal and attachment decoding."""

import base64
from unittest.mock import Mock

from emeris_timetable.gmail import download_pdf_attachment, iter_message_parts


def test_iter_message_parts_recurses_through_multipart_messages():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {"mimeType": "text/plain"},
            {
                "mimeType": "multipart/alternative",
                "parts": [{"mimeType": "text/html"}],
            },
        ],
    }

    assert [part["mimeType"] for part in iter_message_parts(payload)] == [
        "multipart/mixed",
        "text/plain",
        "multipart/alternative",
        "text/html",
    ]


def test_download_pdf_attachment_decodes_attachment_data(tmp_path):
    service = Mock()
    messages = service.users.return_value.messages.return_value
    messages.get.return_value.execute.return_value = {
        "payload": {
            "parts": [
                {
                    "filename": "timetable.pdf",
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "attachment-1"},
                }
            ]
        }
    }
    messages.attachments.return_value.get.return_value.execute.return_value = {
        "data": base64.urlsafe_b64encode(b"%PDF-test").decode()
    }
    destination = tmp_path / "timetable.pdf"

    result = download_pdf_attachment(service, "message-1", destination)

    assert result == destination
    assert destination.read_bytes() == b"%PDF-test"
