"""Gmail attachment downloader — luu file dinh kem vao data/inbox/.

Tuong duong voi downloader.py nhung dung GmailClient.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auto_fill.mail.gmail_client import GmailClient
from auto_fill.mail.outlook_client import MailMessage

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf"}


def download_gmail_attachments(
    client: GmailClient,
    message: MailMessage,
    dest_dir: Path,
) -> list[Path]:
    """Tai tat ca attachment hop le cua message xuong dest_dir.

    Returns
    -------
    list[Path]
        Danh sach cac file da luu (co the rong neu khong co attachment hop le).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    full_msg = client.get_message(message.entry_id, fmt="full")
    payload = full_msg.get("payload", {})
    _process_parts(client, message.entry_id, payload, dest_dir, saved)
    return saved


def _process_parts(
    client: GmailClient,
    message_id: str,
    payload: dict[str, Any],
    dest_dir: Path,
    saved: list[Path],
) -> None:
    filename = payload.get("filename", "")
    body = payload.get("body", {})
    attachment_id = body.get("attachmentId")

    if filename and attachment_id:
        ext = Path(filename).suffix.lower()
        if ext in _ALLOWED_EXTENSIONS:
            try:
                data = client.get_attachment(message_id, attachment_id)
                out_path = _unique_path(dest_dir, filename)
                out_path.write_bytes(data)
                saved.append(out_path)
                logger.info("Da luu attachment: %s", out_path)
            except Exception:
                logger.exception("Loi khi tai attachment %s", filename)
        else:
            logger.debug("Bo qua attachment %s (extension khong hop le)", filename)

    for part in payload.get("parts", []):
        _process_parts(client, message_id, part, dest_dir, saved)


def _unique_path(dest_dir: Path, filename: str) -> Path:
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = dest_dir / filename
    counter = 1
    while candidate.exists():
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate
