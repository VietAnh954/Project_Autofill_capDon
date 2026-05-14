"""Backup — snapshot file tong truoc moi lan ghi.

Sao chep file tong vao data/backup/YYYY-MM-DD/ truoc khi sua.
Giu toi da max_days ngay, xoa backup cu hon.
"""

from __future__ import annotations

import logging
import shutil
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

_DATE_FMT = "%Y-%m-%d"


def snapshot(
    source: Path,
    backup_root: Path,
    today: date | None = None,
    max_days: int = 30,
) -> Path:
    """Sao chep source vao backup_root/YYYY-MM-DD/<filename>.

    Args:
        source: File can backup (file tong).
        backup_root: Thu muc goc chua backup (vi du data/backup/).
        today: Ngay de dat ten thu muc (mac dinh = date.today()).
        max_days: Giu toi da bao nhieu ngay backup. Backup cu hon bi xoa.

    Returns:
        Path den file backup vua tao.

    Raises:
        FileNotFoundError: Neu source khong ton tai.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file khong ton tai: {source}")

    if today is None:
        today = date.today()

    dest_dir = backup_root / today.strftime(_DATE_FMT)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / source.name
    shutil.copy2(source, dest)
    logger.info("backup_created", extra={"dest": str(dest)})

    _purge_old(backup_root, max_days, today)
    return dest


def _purge_old(backup_root: Path, max_days: int, today: date) -> None:
    """Xoa cac thu muc backup co hon max_days ngay."""
    if not backup_root.exists():
        return
    for entry in sorted(backup_root.iterdir()):
        if not entry.is_dir():
            continue
        try:
            folder_date = date.fromisoformat(entry.name)
        except ValueError:
            continue
        age = (today - folder_date).days
        if age > max_days:
            shutil.rmtree(entry)
            logger.info("backup_purged", extra={"folder": entry.name, "age_days": age})
