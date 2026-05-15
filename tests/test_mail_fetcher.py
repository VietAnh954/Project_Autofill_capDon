"""Unit tests cho MailFetcher — mock OutlookClient (không cần Outlook chạy)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import cast
from unittest.mock import MagicMock

import pytest

from auto_fill.mail.fetcher import MailFetcher
from auto_fill.mail.outlook_client import MailMessage, OutlookClient

SUBJECT_PATTERN = r"(?i)c[aâấ]p\s*[đd][oơô]n|phi[eếề]u\s*c[aâấ]p"
ALLOWED: set[str] = {"sale@pti.com.vn", "daily@agency.com"}


def _make_msg(sender: str, subject: str) -> MailMessage:
    return MailMessage(
        entry_id=f"id-{sender}",
        subject=subject,
        sender_email=sender.lower(),
        received_at=datetime(2026, 5, 14, 9, 0, 0),
    )


def _mock_client(messages: list[MailMessage]) -> OutlookClient:
    """OutlookClient mock — iter_unread yields given messages."""
    client = MagicMock(spec=OutlookClient)

    def _iter(folder: object = None) -> Iterator[MailMessage]:
        yield from messages

    client.iter_unread.side_effect = _iter
    cast(MagicMock, client.resolve_folder).return_value = MagicMock()  # dummy folder object
    return client


class TestSenderFilter:
    def test_allowed_sender_passes(self) -> None:
        msg = _make_msg("sale@pti.com.vn", "Cấp đơn du lịch")
        fetcher = MailFetcher(_mock_client([msg]), ALLOWED, SUBJECT_PATTERN)
        assert len(list(fetcher.fetch_matching())) == 1

    def test_unknown_sender_blocked(self) -> None:
        msg = _make_msg("unknown@example.com", "Cấp đơn du lịch")
        fetcher = MailFetcher(_mock_client([msg]), ALLOWED, SUBJECT_PATTERN)
        assert list(fetcher.fetch_matching()) == []

    def test_empty_allowlist_accepts_all_senders(self) -> None:
        msg = _make_msg("any@whoever.com", "Cấp đơn du lịch")
        fetcher = MailFetcher(_mock_client([msg]), set(), SUBJECT_PATTERN)
        assert len(list(fetcher.fetch_matching())) == 1

    def test_sender_match_is_case_insensitive(self) -> None:
        msg = _make_msg("SALE@PTI.COM.VN", "Cấp đơn du lịch")
        fetcher = MailFetcher(_mock_client([msg]), ALLOWED, SUBJECT_PATTERN)
        assert len(list(fetcher.fetch_matching())) == 1


@pytest.mark.parametrize(
    "subject",
    [
        "Cấp đơn du lịch",
        "cap don bao hiem",
        "Phiếu cấp đơn sức khỏe",
        "[Test] Cấp Đơn 14/05",
        "Fwd: Cấp đơn ô tô",
    ],
)
def test_subject_matches_pattern(subject: str) -> None:
    msg = _make_msg("sale@pti.com.vn", subject)
    fetcher = MailFetcher(_mock_client([msg]), ALLOWED, SUBJECT_PATTERN)
    result = list(fetcher.fetch_matching())
    assert len(result) == 1, f"Expected match for: {subject!r}"


@pytest.mark.parametrize(
    "subject",
    [
        "Báo cáo tháng 5",
        "Hello world",
        "Invoice #1234",
        "Meeting notes",
    ],
)
def test_irrelevant_subject_blocked(subject: str) -> None:
    msg = _make_msg("sale@pti.com.vn", subject)
    fetcher = MailFetcher(_mock_client([msg]), ALLOWED, SUBJECT_PATTERN)
    assert list(fetcher.fetch_matching()) == []


class TestMixedMessages:
    def test_only_matching_mails_returned(self) -> None:
        messages = [
            _make_msg("sale@pti.com.vn", "Cấp đơn du lịch"),  # ✓ match
            _make_msg("unknown@x.com", "Cấp đơn ô tô"),  # ✗ sender blocked
            _make_msg("daily@agency.com", "Báo cáo tháng 5"),  # ✗ subject blocked
            _make_msg("daily@agency.com", "Phiếu cấp du lịch"),  # ✓ match
        ]
        fetcher = MailFetcher(_mock_client(messages), ALLOWED, SUBJECT_PATTERN)
        result = list(fetcher.fetch_matching())
        assert len(result) == 2

    def test_empty_inbox_returns_empty(self) -> None:
        fetcher = MailFetcher(_mock_client([]), ALLOWED, SUBJECT_PATTERN)
        assert list(fetcher.fetch_matching()) == []

    def test_fetch_returns_correct_messages(self) -> None:
        match1 = _make_msg("sale@pti.com.vn", "Cấp đơn du lịch")
        no_match = _make_msg("sale@pti.com.vn", "Báo cáo")
        match2 = _make_msg("daily@agency.com", "cap don oto")
        fetcher = MailFetcher(_mock_client([match1, no_match, match2]), ALLOWED, SUBJECT_PATTERN)
        result = list(fetcher.fetch_matching())
        assert result[0].entry_id == match1.entry_id
        assert result[1].entry_id == match2.entry_id


class TestTargetFolder:
    def test_default_target_folder_is_autofill_incoming(self) -> None:
        client = _mock_client([])
        fetcher = MailFetcher(client, ALLOWED, SUBJECT_PATTERN)
        assert fetcher._target_folder == "AutoFill/Incoming"

    def test_resolve_folder_called_with_target(self) -> None:
        client = _mock_client([])
        fetcher = MailFetcher(client, ALLOWED, SUBJECT_PATTERN, target_folder="AutoFill/Incoming")
        list(fetcher.fetch_matching())
        cast(MagicMock, client.resolve_folder).assert_called_once_with("AutoFill/Incoming")

    def test_iter_unread_receives_resolved_folder(self) -> None:
        dummy_folder = MagicMock()
        client = _mock_client([])
        cast(MagicMock, client.resolve_folder).return_value = dummy_folder
        fetcher = MailFetcher(client, ALLOWED, SUBJECT_PATTERN)
        list(fetcher.fetch_matching())
        cast(MagicMock, client.iter_unread).assert_called_once_with(folder=dummy_folder)

    def test_none_target_folder_passes_none_to_resolve(self) -> None:
        client = _mock_client([])
        fetcher = MailFetcher(client, ALLOWED, SUBJECT_PATTERN, target_folder=None)
        list(fetcher.fetch_matching())
        cast(MagicMock, client.resolve_folder).assert_called_once_with(None)
