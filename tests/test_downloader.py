"""Unit tests cho attachment downloader — không cần Outlook chạy."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from auto_fill.mail.downloader import SUPPORTED_EXTENSIONS, _unique_path, download_attachments
from auto_fill.mail.outlook_client import MailMessage
from auto_fill.utils.errors import MailFetchError


def _make_msg(entry_id: str = "test-entry-id") -> MailMessage:
    return MailMessage(
        entry_id=entry_id,
        subject="Cấp đơn du lịch",
        sender_email="sale@pti.com.vn",
        received_at=datetime(2026, 5, 14, 9, 0, 0),
        attachment_names=["report.xlsx"],
    )


def _make_attachment(filename: str, size_bytes: int = 1024) -> MagicMock:
    att = MagicMock()
    att.FileName = filename
    att.Size = size_bytes
    return att


def _make_namespace(attachments: list[MagicMock]) -> MagicMock:
    """COM namespace mock với GetItemFromID trả về mail item có attachments."""
    mail_item = MagicMock()
    att_collection = MagicMock()
    att_collection.Count = len(attachments)
    att_collection.Item.side_effect = lambda i: attachments[i - 1]
    mail_item.Attachments = att_collection

    namespace = MagicMock()
    namespace.GetItemFromID.return_value = mail_item
    return namespace


class TestDownloadAttachments:
    def test_saves_xlsx_to_inbox(self, tmp_path: Path) -> None:
        att = _make_attachment("phieu.xlsx")
        ns = _make_namespace([att])
        result = download_attachments(_make_msg(), tmp_path, ns)
        assert len(result) == 1
        assert result[0] == tmp_path / "phieu.xlsx"
        att.SaveAsFile.assert_called_once_with(str(tmp_path / "phieu.xlsx"))

    def test_saves_csv_to_inbox(self, tmp_path: Path) -> None:
        att = _make_attachment("data.csv")
        ns = _make_namespace([att])
        result = download_attachments(_make_msg(), tmp_path, ns)
        assert len(result) == 1

    def test_skips_unsupported_extension(self, tmp_path: Path) -> None:
        att = _make_attachment("image.png")
        ns = _make_namespace([att])
        result = download_attachments(_make_msg(), tmp_path, ns)
        assert result == []
        att.SaveAsFile.assert_not_called()

    def test_skips_oversized_attachment(self, tmp_path: Path) -> None:
        big_size = 25 * 1024 * 1024  # 25 MB
        att = _make_attachment("big.xlsx", size_bytes=big_size)
        ns = _make_namespace([att])
        result = download_attachments(_make_msg(), tmp_path, ns, max_size_mb=20)
        assert result == []

    def test_multiple_attachments_mixed(self, tmp_path: Path) -> None:
        atts = [
            _make_attachment("a.xlsx"),
            _make_attachment("b.png"),  # skipped
            _make_attachment("c.csv"),
        ]
        ns = _make_namespace(atts)
        result = download_attachments(_make_msg(), tmp_path, ns)
        assert len(result) == 2
        assert result[0].name == "a.xlsx"
        assert result[1].name == "c.csv"

    def test_raises_mail_fetch_error_on_bad_entry_id(self, tmp_path: Path) -> None:
        ns = MagicMock()
        ns.GetItemFromID.side_effect = Exception("Item not found")
        with pytest.raises(MailFetchError, match="Không lấy được mail item"):
            download_attachments(_make_msg("bad-id"), tmp_path, ns)

    def test_creates_inbox_dir_if_missing(self, tmp_path: Path) -> None:
        inbox = tmp_path / "inbox" / "sub"
        att = _make_attachment("file.xlsx")
        ns = _make_namespace([att])
        download_attachments(_make_msg(), inbox, ns)
        assert inbox.is_dir()


class TestUniquePath:
    def test_returns_original_if_not_exists(self, tmp_path: Path) -> None:
        result = _unique_path(tmp_path, "file.xlsx")
        assert result == tmp_path / "file.xlsx"

    def test_appends_counter_when_file_exists(self, tmp_path: Path) -> None:
        (tmp_path / "file.xlsx").touch()
        result = _unique_path(tmp_path, "file.xlsx")
        assert result == tmp_path / "file_1.xlsx"

    def test_increments_counter_until_free(self, tmp_path: Path) -> None:
        (tmp_path / "file.xlsx").touch()
        (tmp_path / "file_1.xlsx").touch()
        result = _unique_path(tmp_path, "file.xlsx")
        assert result == tmp_path / "file_2.xlsx"


def test_supported_extensions_cover_common_formats() -> None:
    for ext in [".xlsx", ".xls", ".csv", ".pdf"]:
        assert ext in SUPPORTED_EXTENSIONS
