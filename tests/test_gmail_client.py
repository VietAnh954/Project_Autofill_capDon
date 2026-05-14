"""Tests cho Gmail modules (GmailClient, GmailFetcher, downloader, marker)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from auto_fill.mail.gmail_client import _GOOGLE_AVAILABLE, GmailClient, GmailClientError

# ── GmailClient ─────────────────────────────────────────────────────────── #


def test_gmail_client_raises_if_google_not_available(tmp_path: Path) -> None:
    """Kiem tra loi ro rang khi thu vien google chua cai."""
    creds = tmp_path / "creds.json"
    token = tmp_path / "token.json"
    creds.write_text("{}")
    with (
        patch("auto_fill.mail.gmail_client._GOOGLE_AVAILABLE", False),
        pytest.raises(GmailClientError, match="google-api-python-client"),
    ):
        client = GmailClient(creds, token)
        client.connect()


@pytest.mark.skipif(not _GOOGLE_AVAILABLE, reason="google libs not installed")
def test_gmail_client_connect_uses_existing_token(tmp_path: Path) -> None:
    """Neu token.json ton tai va hop le, ket noi ma khong mo browser."""
    creds_file = tmp_path / "creds.json"
    token_file = tmp_path / "token.json"
    creds_file.write_text("{}")

    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False

    with (
        patch(
            "auto_fill.mail.gmail_client.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ),
        patch("auto_fill.mail.gmail_client.google_build") as mock_build,
    ):
        token_file.write_text("{}")
        client = GmailClient(creds_file, token_file)
        client.connect()
        mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)


@pytest.mark.skipif(not _GOOGLE_AVAILABLE, reason="google libs not installed")
def test_gmail_client_list_messages(tmp_path: Path) -> None:
    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "abc123", "threadId": "t1"}]
    }

    client = GmailClient(tmp_path / "c.json", tmp_path / "t.json")
    client._service = mock_service

    result = client.list_messages(query="from:test@example.com")
    assert len(result) == 1
    assert result[0]["id"] == "abc123"


@pytest.mark.skipif(not _GOOGLE_AVAILABLE, reason="google libs not installed")
def test_gmail_client_get_or_create_label_existing(tmp_path: Path) -> None:
    mock_service = MagicMock()
    mock_service.users().labels().list().execute.return_value = {
        "labels": [{"id": "Label_1", "name": "AutoFill/Processed"}]
    }

    client = GmailClient(tmp_path / "c.json", tmp_path / "t.json")
    client._service = mock_service

    label_id = client.get_or_create_label("AutoFill/Processed")
    assert label_id == "Label_1"
    mock_service.users().labels().create.assert_not_called()


@pytest.mark.skipif(not _GOOGLE_AVAILABLE, reason="google libs not installed")
def test_gmail_client_get_or_create_label_new(tmp_path: Path) -> None:
    mock_service = MagicMock()
    mock_service.users().labels().list().execute.return_value = {"labels": []}
    mock_service.users().labels().create().execute.return_value = {
        "id": "Label_new",
        "name": "AutoFill/Processed",
    }

    client = GmailClient(tmp_path / "c.json", tmp_path / "t.json")
    client._service = mock_service

    label_id = client.get_or_create_label("AutoFill/Processed")
    assert label_id == "Label_new"


# ── GmailFetcher ────────────────────────────────────────────────────────── #


def test_gmail_fetcher_filters_by_allowlist(tmp_path: Path) -> None:
    from auto_fill.mail.gmail_fetcher import GmailFetcher

    mock_client = MagicMock()
    mock_client.list_messages.return_value = [{"id": "m1"}, {"id": "m2"}]

    def fake_get_message(msg_id: str, fmt: str = "full") -> dict[str, Any]:
        return {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Cap don du lich"},
                    {"name": "From", "value": "allowed@example.com"},
                    {"name": "Date", "value": "Thu, 14 May 2026 10:00:00 +0700"},
                ],
                "parts": [{"filename": "test.xlsx", "body": {"attachmentId": "att1"}, "parts": []}],
                "mimeType": "multipart/mixed",
            }
        }

    mock_client.get_message.side_effect = fake_get_message

    fetcher = GmailFetcher(
        client=mock_client,
        sender_allowlist={"allowed@example.com"},
        subject_pattern=r"cap\s*don",
    )
    results = list(fetcher.fetch())
    assert len(results) == 2
    assert all(r.sender_email == "allowed@example.com" for r in results)


def test_gmail_fetcher_rejects_unknown_sender(tmp_path: Path) -> None:
    from auto_fill.mail.gmail_fetcher import GmailFetcher

    mock_client = MagicMock()
    mock_client.list_messages.return_value = [{"id": "m1"}]

    def fake_get_message(msg_id: str, fmt: str = "full") -> dict[str, Any]:
        return {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Cap don du lich"},
                    {"name": "From", "value": "spammer@evil.com"},
                    {"name": "Date", "value": "Thu, 14 May 2026 10:00:00 +0700"},
                ],
                "parts": [],
                "mimeType": "text/plain",
            }
        }

    mock_client.get_message.side_effect = fake_get_message

    fetcher = GmailFetcher(
        client=mock_client,
        sender_allowlist={"allowed@example.com"},
    )
    results = list(fetcher.fetch())
    assert len(results) == 0


def test_gmail_fetcher_no_allowlist_accepts_all(tmp_path: Path) -> None:
    from auto_fill.mail.gmail_fetcher import GmailFetcher

    mock_client = MagicMock()
    mock_client.list_messages.return_value = [{"id": "m1"}]

    def fake_get_message(msg_id: str, fmt: str = "full") -> dict[str, Any]:
        return {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Phieu cap don"},
                    {"name": "From", "value": "anyone@example.com"},
                    {"name": "Date", "value": "Thu, 14 May 2026 10:00:00 +0700"},
                ],
                "parts": [{"filename": "data.xlsx", "body": {"attachmentId": "a1"}, "parts": []}],
                "mimeType": "multipart/mixed",
            }
        }

    mock_client.get_message.side_effect = fake_get_message

    fetcher = GmailFetcher(client=mock_client, sender_allowlist=set())
    results = list(fetcher.fetch())
    assert len(results) == 1


# ── GmailDownloader ─────────────────────────────────────────────────────── #


def test_gmail_downloader_saves_xlsx(tmp_path: Path) -> None:
    from datetime import datetime

    from auto_fill.mail.gmail_downloader import download_gmail_attachments
    from auto_fill.mail.outlook_client import MailMessage

    mock_client = MagicMock()
    mock_client.get_message.return_value = {
        "payload": {
            "filename": "data.xlsx",
            "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "body": {"attachmentId": "att_id_1"},
            "parts": [],
        }
    }
    mock_client.get_attachment.return_value = b"PK\x03\x04fake_xlsx_content"

    msg = MailMessage(
        entry_id="msg1",
        subject="Cap don",
        sender_email="a@b.com",
        received_at=datetime(2026, 5, 14, 10, 0),
        attachment_names=["data.xlsx"],
    )

    paths = download_gmail_attachments(mock_client, msg, tmp_path)
    assert len(paths) == 1
    assert paths[0].suffix == ".xlsx"
    assert paths[0].read_bytes() == b"PK\x03\x04fake_xlsx_content"


def test_gmail_downloader_skips_non_allowed_extension(tmp_path: Path) -> None:
    from datetime import datetime

    from auto_fill.mail.gmail_downloader import download_gmail_attachments
    from auto_fill.mail.outlook_client import MailMessage

    mock_client = MagicMock()
    mock_client.get_message.return_value = {
        "payload": {
            "filename": "photo.jpg",
            "mimeType": "image/jpeg",
            "body": {"attachmentId": "att_img"},
            "parts": [],
        }
    }

    msg = MailMessage(
        entry_id="msg2",
        subject="Cap don",
        sender_email="a@b.com",
        received_at=datetime(2026, 5, 14, 10, 0),
    )

    paths = download_gmail_attachments(mock_client, msg, tmp_path)
    assert paths == []


# ── GmailMarker ─────────────────────────────────────────────────────────── #


def test_gmail_marker_marks_processed(tmp_path: Path) -> None:
    from datetime import datetime

    from auto_fill.mail.gmail_marker import mark_gmail_processed
    from auto_fill.mail.outlook_client import MailMessage

    mock_client = MagicMock()
    mock_client.get_or_create_label.return_value = "Label_processed"

    msg = MailMessage(
        entry_id="msg3",
        subject="Cap don",
        sender_email="a@b.com",
        received_at=datetime(2026, 5, 14, 10, 0),
    )

    result = mark_gmail_processed(mock_client, msg)
    assert result is True
    mock_client.modify_labels.assert_called_once_with(
        "msg3",
        add_labels=["Label_processed"],
        remove_labels=["UNREAD", "INBOX"],
    )


def test_gmail_marker_returns_false_on_error(tmp_path: Path) -> None:
    from datetime import datetime

    from auto_fill.mail.gmail_marker import mark_gmail_processed
    from auto_fill.mail.outlook_client import MailMessage

    mock_client = MagicMock()
    mock_client.get_or_create_label.side_effect = RuntimeError("API error")

    msg = MailMessage(
        entry_id="msg4",
        subject="Cap don",
        sender_email="a@b.com",
        received_at=datetime(2026, 5, 14, 10, 0),
    )

    result = mark_gmail_processed(mock_client, msg)
    assert result is False
