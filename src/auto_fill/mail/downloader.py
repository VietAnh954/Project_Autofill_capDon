"""Attachment downloader — tải file đính kèm từ MailMessage vào data/inbox/.

Tầng Mail trong pipeline (xem ARCHITECTURE.md mục 2).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auto_fill.mail.outlook_client import MailMessage
from auto_fill.utils.errors import MailFetchError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = frozenset({".xlsx", ".xls", ".xlsm", ".csv", ".pdf"})


def download_attachments(
    msg: MailMessage,
    inbox_dir: Path,
    outlook_namespace: Any,
    max_size_mb: int = 20,
) -> list[Path]:
    """Tải attachment từ 1 MailMessage vào inbox_dir.

    Args:
        msg: Mail đã fetch, có entry_id để lấy COM object.
        inbox_dir: Thư mục lưu file (thường `data/inbox/`).
        outlook_namespace: Outlook MAPI namespace (COM object).
        max_size_mb: Bỏ qua attachment vượt quá giới hạn này.

    Returns:
        Danh sách Path của các file đã tải thành công.

    Raises:
        MailFetchError: Nếu không lấy được mail item từ Outlook.
    """
    inbox_dir.mkdir(parents=True, exist_ok=True)

    try:
        mail_item = outlook_namespace.GetItemFromID(msg.entry_id)
    except Exception as exc:
        raise MailFetchError(f"Không lấy được mail item {msg.entry_id[:8]}: {exc}") from exc

    downloaded: list[Path] = []
    attachments = mail_item.Attachments

    for i in range(1, attachments.Count + 1):
        att = attachments.Item(i)
        filename: str = att.FileName
        ext = Path(filename).suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            logger.debug("skip_unsupported_ext", extra={"file": filename, "ext": ext})
            continue

        size_mb = att.Size / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.warning(
                "skip_oversized_attachment",
                extra={"file": filename, "size_mb": round(size_mb, 1), "limit_mb": max_size_mb},
            )
            continue

        dest = _unique_path(inbox_dir, filename)
        att.SaveAsFile(str(dest))
        downloaded.append(dest)
        logger.info(
            "attachment_saved",
            extra={
                "file": filename,
                "dest": str(dest),
                "size_mb": round(size_mb, 2),
            },
        )

    return downloaded


def _unique_path(directory: Path, filename: str) -> Path:
    """Trả về path không trùng — thêm _1, _2, ... nếu file đã tồn tại."""
    dest = directory / filename
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
