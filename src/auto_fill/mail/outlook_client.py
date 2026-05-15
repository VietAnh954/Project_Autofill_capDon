"""Outlook COM client — kết nối Outlook Desktop qua pywin32.

Tầng Mail trong pipeline (xem ARCHITECTURE.md mục 2).
Chỉ chạy trên Windows với Outlook Desktop đã cài.
"""

from __future__ import annotations

import contextlib
import io
import logging
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

logger = logging.getLogger(__name__)

# pywin32 chỉ có trên Windows — import lazy để test mock được
try:
    import win32com.client

    _WIN32_AVAILABLE = True
except ImportError:
    _WIN32_AVAILABLE = False


@dataclass
class MailMessage:
    """Đại diện 1 mail đã fetch từ Outlook."""

    entry_id: str
    subject: str
    sender_email: str
    received_at: datetime
    body: str = ""
    attachment_names: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"[{self.received_at:%Y-%m-%d %H:%M}] "
            f"From: {self.sender_email} | Subject: {self.subject}"
        )


class OutlookClient:
    """Wrapper pywin32 cho Outlook Desktop.

    Args:
        profile: Tên profile Outlook (xem Control Panel → Mail → Show Profiles).
        inbox_folder: Tên thư mục inbox (mặc định "Inbox").
    """

    def __init__(self, profile: str = "Outlook", inbox_folder: str = "Inbox") -> None:
        if not _WIN32_AVAILABLE:
            raise RuntimeError(
                "pywin32 không có sẵn. Cài: pip install pywin32. "
                "Module này chỉ chạy trên Windows."
            )
        self._profile = profile
        self._inbox_folder_name = inbox_folder
        self._outlook: Any = None
        self._inbox: Any = None

    def connect(self) -> None:
        """Kết nối Outlook COM. Raise RuntimeError nếu Outlook chưa chạy."""
        try:
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = self._outlook.GetNamespace("MAPI")
            namespace.Logon(self._profile)
            self._inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            logger.info("outlook_connected", extra={"profile": self._profile})
        except Exception as exc:
            raise RuntimeError(f"Không kết nối được Outlook: {exc}") from exc

    def list_recent(self, count: int = 5) -> list[MailMessage]:
        """Trả về `count` mail mới nhất trong inbox, mới nhất trước.

        Raises:
            RuntimeError: nếu chưa gọi connect().
        """
        if self._inbox is None:
            raise RuntimeError("Chưa connect(). Gọi OutlookClient.connect() trước.")

        items = self._inbox.Items
        items.Sort("[ReceivedTime]", Descending=True)

        messages: list[MailMessage] = []
        for i, item in enumerate(items):
            if i >= count:
                break
            try:
                msg = _mail_item_to_message(item)
                messages.append(msg)
            except Exception:
                logger.warning("skip_mail_item", extra={"index": i}, exc_info=True)
        return messages

    def resolve_folder(self, relative_path: str | None = None) -> Any:
        """Return the Outlook folder to scan.

        Navigates relative_path as subfolder names separated by "/" or "\\"
        relative to the default inbox. Falls back to inbox with a warning when
        any segment is not found.

        Args:
            relative_path: e.g. "AutoFill/Incoming". None → default inbox.
        """
        if self._inbox is None:
            raise RuntimeError("Chưa connect().")
        if not relative_path:
            return self._inbox
        folder: Any = self._inbox
        for part in relative_path.replace("\\", "/").split("/"):
            try:
                folder = folder.Folders[part]
            except Exception:
                logger.warning(
                    "target_folder_not_found_fallback",
                    extra={"path": relative_path, "missing_part": part},
                )
                return self._inbox
        return folder

    def iter_unread(self, folder: Any | None = None) -> Iterator[MailMessage]:
        """Yield từng mail chưa đọc trong `folder` (mặc định: inbox).

        Args:
            folder: Outlook folder COM object. None → use default inbox.

        Raises:
            RuntimeError: nếu chưa gọi connect().
        """
        if self._inbox is None:
            raise RuntimeError("Chưa connect(). Gọi OutlookClient.connect() trước.")

        target = folder if folder is not None else self._inbox
        items = target.Items
        items.Sort("[ReceivedTime]", Descending=True)
        unread_items = items.Restrict("[Unread]=True")

        for item in unread_items:
            try:
                yield _mail_item_to_message(item)
            except Exception:
                logger.warning("skip_unread_item", exc_info=True)

    def mark_as_read(self, entry_id: str) -> None:
        """Mark mail theo entry_id là đã đọc."""
        if self._outlook is None:
            raise RuntimeError("Chưa connect().")
        try:
            namespace = self._outlook.GetNamespace("MAPI")
            item = namespace.GetItemFromID(entry_id)
            item.UnRead = False
            item.Save()
        except Exception as exc:
            logger.error("mark_as_read_failed", extra={"entry_id": entry_id[:8]}, exc_info=True)
            raise RuntimeError(f"Không thể mark mail: {exc}") from exc

    def move_to_folder(self, entry_id: str, folder_name: str) -> None:
        """Di chuyển mail vào folder theo tên (tạo nếu chưa có)."""
        if self._outlook is None:
            raise RuntimeError("Chưa connect().")
        try:
            namespace = self._outlook.GetNamespace("MAPI")
            item = namespace.GetItemFromID(entry_id)
            target = _get_or_create_folder(self._inbox, folder_name)
            item.Move(target)
        except Exception as exc:
            logger.error("move_failed", extra={"folder": folder_name}, exc_info=True)
            raise RuntimeError(f"Không di chuyển được mail: {exc}") from exc

    def ensure_folder_structure(self, folder_paths: list[str]) -> list[str]:
        """Create nested folders relative to inbox if they don't already exist.

        Args:
            folder_paths: List of "/" or "\\" separated paths, e.g.
                ["AutoFill/Incoming", "AutoFill/Processed", "AutoFill/Needs_Review"].

        Returns:
            List of folder paths that were successfully created or already existed.
        """
        if self._inbox is None:
            raise RuntimeError("Chưa connect().")
        created: list[str] = []
        for path in folder_paths:
            parent = self._inbox
            parts = path.replace("\\", "/").split("/")
            try:
                for part in parts:
                    parent = _get_or_create_folder(parent, part)
                created.append(path)
                logger.info("folder_ensured", extra={"path": path})
            except Exception:
                logger.error("folder_ensure_failed", extra={"path": path}, exc_info=True)
        return created

    def move_to_nested_folder(self, entry_id: str, folder_path: str) -> None:
        """Di chuyển mail vào nested folder (vd "Processed/2026-05-16").

        Tự tạo từng cấp folder nếu chưa có.
        """
        if self._outlook is None:
            raise RuntimeError("Chưa connect().")
        try:
            namespace = self._outlook.GetNamespace("MAPI")
            item = namespace.GetItemFromID(entry_id)
            parent = self._inbox
            for part in folder_path.replace("\\", "/").split("/"):
                parent = _get_or_create_folder(parent, part)
            item.Move(parent)
        except Exception as exc:
            logger.error("move_nested_failed", extra={"folder": folder_path}, exc_info=True)
            raise RuntimeError(f"Không di chuyển được mail: {exc}") from exc


# === Private helpers ===


def _mail_item_to_message(item: Any) -> MailMessage:
    """Convert Outlook MailItem COM object → MailMessage dataclass."""
    try:
        raw = item.ReceivedTime
        received_at: datetime = datetime(
            raw.year, raw.month, raw.day, raw.hour, raw.minute, raw.second
        )
    except Exception:
        received_at = datetime.now()

    attachment_names: list[str] = []
    with contextlib.suppress(Exception):
        for att in item.Attachments:
            attachment_names.append(att.FileName)

    sender_email = ""
    with contextlib.suppress(Exception):
        sender_email = item.SenderEmailAddress

    return MailMessage(
        entry_id=str(item.EntryID),
        subject=str(item.Subject or ""),
        sender_email=sender_email.lower(),
        received_at=received_at,
        body=str(item.Body or ""),
        attachment_names=attachment_names,
    )


def _get_or_create_folder(parent: Any, folder_name: str) -> Any:
    """Lấy hoặc tạo subfolder trong parent folder."""
    with contextlib.suppress(Exception):
        return parent.Folders[folder_name]
    return parent.Folders.Add(folder_name)


# === CLI entry point ===


def _cli_list() -> None:
    """In 5 mail mới nhất ra stdout (UTF-8 safe)."""
    from auto_fill.config.settings import settings  # local import tránh circular

    cast(io.TextIOWrapper, sys.stdout).reconfigure(encoding="utf-8")

    client = OutlookClient(
        profile=settings.outlook_profile,
        inbox_folder=settings.outlook_inbox_folder,
    )
    client.connect()
    mails = client.list_recent(5)
    if not mails:
        print("(Không có mail nào trong inbox)")
        return
    for msg in mails:
        print(msg)


if __name__ == "__main__":
    import click

    @click.group()
    def _cli() -> None:
        """Outlook CLI tools."""

    @_cli.command(name="list")
    def _cmd_list() -> None:
        """In 5 mail mới nhất."""
        _cli_list()

    _cli()
