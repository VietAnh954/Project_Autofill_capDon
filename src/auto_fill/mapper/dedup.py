"""Dedup — kiem tra ban ghi trung lap trong sheet Du lich.

Khoa dedup theo DATABASE §2.1: (CCCD/CMND/ID, Ngay di, Noi den).
Tra True neu da ton tai, False neu moi.
"""

from __future__ import annotations

import logging
import warnings
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

# Suppress openpyxl warning ve cell co serial date ngoai pham vi
# (vd master file co cell F479 voi serial 6693508 - data cu, vo hai).
# Mac dinh warning xuat hien moi lan dedup load master -> spam log.
warnings.filterwarnings(
    "ignore",
    message=r".*serial value .* is outside the limits.*",
    category=UserWarning,
    module=r"openpyxl\..*",
)

logger = logging.getLogger(__name__)

_DEDUP_KEY = ("insured_id_number", "trip_start", "destination")


def is_duplicate(
    record: dict[str, Any],
    master_path: Path,
    sheet_name: str = "Du lịch",
    header_row: int = 0,
    aliases: dict[str, list[str]] | None = None,
) -> bool:
    """Kiem tra record co ton tai trong sheet master chua.

    Args:
        record: Dict co canonical keys da qua normalizer.
        master_path: Duong dan toi file tong (.xlsx).
        sheet_name: Ten sheet trong file tong.
        header_row: Index row header (0-based), default 0 cho sheet Du lich.
        aliases: Mapping canonical → list alias headers trong file tong.
                 Neu None, su dung column names goc.

    Returns:
        True neu da ton tai ban ghi trung khoa dedup, False neu moi.
    """
    try:
        df = _load_sheet(master_path, sheet_name, header_row)
    except Exception:
        logger.warning(
            "dedup_load_failed",
            extra={"path": str(master_path), "sheet": sheet_name},
            exc_info=True,
        )
        return False

    if aliases:
        df = _rename_columns(df, aliases)

    missing = [k for k in _DEDUP_KEY if k not in df.columns]
    if missing:
        # DEBUG — informational only. Reader đã ghi warning 1 lần khi load file.
        # Mỗi row gọi dedup → spam log nếu là WARNING (xem Phase 8 bug fix).
        logger.debug("dedup_columns_missing", extra={"missing": missing})
        return False

    return _check_match(df, record)


def _load_sheet(path: Path, sheet_name: str, header_row: int) -> pd.DataFrame:
    return pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=header_row,
        dtype=str,
        engine="openpyxl",
    )


def _rename_columns(df: pd.DataFrame, aliases: dict[str, list[str]]) -> pd.DataFrame:
    """Doi ten cot tu raw header → canonical dua tren aliases exact match."""
    reverse: dict[str, str] = {}
    for canonical, alias_list in aliases.items():
        for alias in alias_list:
            reverse[alias.strip().lower()] = canonical
    rename_map = {
        col: reverse[col.strip().lower()] for col in df.columns if col.strip().lower() in reverse
    }
    return df.rename(columns=rename_map)


def _check_match(df: pd.DataFrame, record: dict[str, Any]) -> bool:
    """So sanh cac gia tri dedup key voi tung dong trong df."""
    id_val = str(record.get("insured_id_number", "")).strip()
    start_val = record.get("trip_start")
    dest_val = str(record.get("destination", "")).strip().lower()

    if not id_val or start_val is None or not dest_val:
        return False

    for _, row in df.iterrows():
        if _row_matches(row, id_val, start_val, dest_val):
            logger.info(
                "dedup_found",
                extra={"id": id_val, "trip_start": str(start_val), "dest": dest_val},
            )
            return True
    return False


def _row_matches(
    row: pd.Series[Any],
    id_val: str,
    start_val: date,
    dest_val: str,
) -> bool:
    row_id = str(row.get("insured_id_number", "")).strip()
    row_dest = str(row.get("destination", "")).strip().lower()
    row_start_raw = row.get("trip_start", "")

    if row_id != id_val or row_dest != dest_val:
        return False

    row_start = _parse_date(str(row_start_raw).strip())
    return row_start == start_val


def _parse_date(value: str) -> date | None:
    """Thu parse chuoi ngay theo cac dinh dang pho bien, tra None neu that bai."""
    from datetime import datetime

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    # Excel serial
    try:
        serial = int(float(value))
        from auto_fill.mapper.normalizer import _EXCEL_EPOCH

        result: date = _EXCEL_EPOCH + timedelta(days=serial)
        return result
    except (ValueError, OverflowError):
        pass
    return None
