"""Unit tests cho Mail marker."""

from __future__ import annotations

from unittest.mock import MagicMock

from auto_fill.mail.marker import _get_or_create_folder, mark_processed


def _make_namespace(entry_id: str = "AAA", folder_count: int = 0) -> MagicMock:
    ns = MagicMock()
    mail = MagicMock()
    mail.UnRead = True
    ns.GetItemFromID.return_value = mail

    inbox = MagicMock()
    inbox.Folders.Count = folder_count
    ns.GetDefaultFolder.return_value = inbox

    return ns


class TestMarkProcessed:
    def test_returns_true_on_success(self) -> None:
        ns = _make_namespace()
        assert mark_processed(ns, "AAA") is True

    def test_marks_mail_unread_false(self) -> None:
        ns = _make_namespace()
        mail = ns.GetItemFromID.return_value
        mark_processed(ns, "AAA")
        assert mail.UnRead is False

    def test_calls_save_after_mark_read(self) -> None:
        ns = _make_namespace()
        mail = ns.GetItemFromID.return_value
        mark_processed(ns, "AAA")
        mail.Save.assert_called_once()

    def test_calls_move(self) -> None:
        ns = _make_namespace()
        mail = ns.GetItemFromID.return_value
        mark_processed(ns, "AAA")
        mail.Move.assert_called_once()

    def test_returns_false_when_get_item_fails(self) -> None:
        ns = MagicMock()
        ns.GetItemFromID.side_effect = Exception("COM error")
        assert mark_processed(ns, "AAA") is False

    def test_returns_false_when_mark_read_fails(self) -> None:
        ns = _make_namespace()
        mail = ns.GetItemFromID.return_value
        mail.Save.side_effect = Exception("Save error")
        assert mark_processed(ns, "AAA") is False

    def test_returns_false_when_move_fails(self) -> None:
        ns = _make_namespace()
        mail = ns.GetItemFromID.return_value
        mail.Move.side_effect = Exception("Move error")
        assert mark_processed(ns, "AAA") is False

    def test_custom_folder_name_used(self) -> None:
        ns = _make_namespace()
        inbox = ns.GetDefaultFolder.return_value
        mark_processed(ns, "AAA", processed_folder_name="Done")
        inbox.Folders.Add.assert_called_with("Done")

    def test_existing_folder_reused(self) -> None:
        ns = _make_namespace(folder_count=1)
        inbox = ns.GetDefaultFolder.return_value
        existing = MagicMock()
        existing.Name = "Processed"
        inbox.Folders.Item.return_value = existing
        mark_processed(ns, "AAA")
        inbox.Folders.Add.assert_not_called()

    def test_uses_inbox_folder_constant(self) -> None:
        ns = _make_namespace()
        mark_processed(ns, "AAA")
        ns.GetDefaultFolder.assert_called_with(6)


class TestGetOrCreateFolder:
    def test_creates_folder_when_not_found(self) -> None:
        ns = MagicMock()
        inbox = MagicMock()
        inbox.Folders.Count = 0
        ns.GetDefaultFolder.return_value = inbox
        _get_or_create_folder(ns, "NewFolder")
        inbox.Folders.Add.assert_called_once_with("NewFolder")

    def test_returns_existing_folder(self) -> None:
        ns = MagicMock()
        inbox = MagicMock()
        ns.GetDefaultFolder.return_value = inbox
        inbox.Folders.Count = 2
        existing = MagicMock()
        existing.Name = "Processed"
        other = MagicMock()
        other.Name = "Other"
        inbox.Folders.Item.side_effect = lambda i: existing if i == 1 else other
        result = _get_or_create_folder(ns, "Processed")
        assert result is existing
