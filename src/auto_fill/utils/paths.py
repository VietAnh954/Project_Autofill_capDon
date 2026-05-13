"""Helpers cho filesystem paths."""

from __future__ import annotations

from datetime import date
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Tạo folder nếu chưa có, trả về path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def today_folder(root: Path) -> Path:
    """Trả về `root/YYYY-MM-DD/`, tự tạo."""
    return ensure_dir(root / date.today().isoformat())
