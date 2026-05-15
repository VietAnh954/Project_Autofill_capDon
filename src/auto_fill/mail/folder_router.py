"""Route processed mail to the correct Outlook folder based on mail type.

Routing rules (MAIL_PATTERNS.md §3, TODO #7.5):
  TYPE A/B, processed OK  → Processed/<YYYY-MM-DD>/
  TYPE A/B, validate fail → Needs_Review/
  TYPE C or 'review'      → Needs_Review/
  TYPE D                  → Skipped/<YYYY-MM-DD>/
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

_TODAY_FOLDER = date.today().strftime("%Y-%m-%d")

# Top-level AutoFill subfolder names
FOLDER_PROCESSED = "Processed"
FOLDER_NEEDS_REVIEW = "Needs_Review"
FOLDER_SKIPPED = "Skipped"


def route_mail(
    entry_id: str,
    mail_type: str,
    success: bool,
    outlook_client: Any,
) -> str:
    """Move a mail to the appropriate Outlook folder and return the folder path.

    Args:
        entry_id: Outlook EntryID of the mail to move.
        mail_type: One of 'A', 'B', 'C', 'D', 'review'.
        success: True when pipeline processed the mail without validation errors.
            Only relevant for TYPE A/B (ignored for C/D/review).
        outlook_client: Connected OutlookClient instance.

    Returns:
        Folder path the mail was routed to (e.g. "Processed/2026-05-16").
    """
    target_path = _decide_folder(mail_type, success)
    _move(entry_id, target_path, outlook_client)
    logger.info(
        "mail_routed",
        extra={"entry_id": entry_id[:8], "mail_type": mail_type, "folder": target_path},
    )
    return target_path


def _decide_folder(mail_type: str, success: bool) -> str:
    if mail_type == "D":
        return f"{FOLDER_SKIPPED}/{_today()}"
    if mail_type in ("C", "review"):
        return FOLDER_NEEDS_REVIEW
    if mail_type in ("A", "B"):
        if success:
            return f"{FOLDER_PROCESSED}/{_today()}"
        return FOLDER_NEEDS_REVIEW
    return FOLDER_NEEDS_REVIEW


def _today() -> str:
    return date.today().strftime("%Y-%m-%d")


def _move(entry_id: str, folder_path: str, client: Any) -> None:
    """Navigate to (and create) nested folder, then move the mail there."""
    try:
        client.move_to_nested_folder(entry_id, folder_path)
    except AttributeError:
        # Fallback: OutlookClient.move_to_folder supports only one level.
        top_folder = folder_path.split("/")[0]
        client.move_to_folder(entry_id, top_folder)
        logger.debug("folder_router_single_level_fallback", extra={"folder": top_folder})
    except Exception:
        logger.error("mail_route_failed", extra={"entry_id": entry_id[:8]}, exc_info=True)
