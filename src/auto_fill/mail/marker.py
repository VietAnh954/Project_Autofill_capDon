"""Mail marker — danh dau mail da xu ly trong Outlook.

Hanh dong:
1. Mark as Read (UnRead = False).
2. Move to processed_folder (default: "Processed").
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def mark_processed(
    namespace: Any,
    entry_id: str,
    processed_folder_name: str = "Processed",
) -> bool:
    """Danh dau 1 mail da xu ly: mark Read + chuyen folder.

    Args:
        namespace: Outlook MAPI namespace (win32com object).
        entry_id: EntryID cua MailItem.
        processed_folder_name: Ten sub-folder trong Inbox de chuyen mail vao.
                               Folder duoc tao neu chua ton tai.

    Returns:
        True neu thanh cong, False neu co loi (mail khong tim thay / COM error).
    """
    try:
        mail = namespace.GetItemFromID(entry_id)
    except Exception:
        logger.warning("marker_get_item_failed", extra={"entry_id": entry_id}, exc_info=True)
        return False

    try:
        mail.UnRead = False
        mail.Save()
        logger.info("mail_marked_read", extra={"entry_id": entry_id})
    except Exception:
        logger.warning("marker_mark_read_failed", extra={"entry_id": entry_id}, exc_info=True)
        return False

    try:
        dest_folder = _get_or_create_folder(namespace, processed_folder_name)
        mail.Move(dest_folder)
        logger.info(
            "mail_moved",
            extra={"entry_id": entry_id, "folder": processed_folder_name},
        )
    except Exception:
        logger.warning("marker_move_failed", extra={"entry_id": entry_id}, exc_info=True)
        return False

    return True


def _get_or_create_folder(namespace: Any, folder_name: str) -> Any:
    """Tim hoac tao sub-folder ten folder_name trong Inbox."""
    inbox = namespace.GetDefaultFolder(6)  # olFolderInbox = 6
    for i in range(1, inbox.Folders.Count + 1):
        folder = inbox.Folders.Item(i)
        if folder.Name == folder_name:
            return folder
    return inbox.Folders.Add(folder_name)
