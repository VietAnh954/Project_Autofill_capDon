"""Registry: ánh xạ giữa sheet name tiếng Việt và alias code English.

Xem ADR-005 và GLOSSARY.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SheetInfo:
    excel_name: str       # tên thật trong file Excel
    alias: str            # tên trong code
    header_row: int       # số hàng header (1-indexed)
    dedup_keys: tuple[str, ...]   # canonical field names dùng cho dedup
    enabled_in_mvp: bool = False


SHEET_REGISTRY: dict[str, SheetInfo] = {
    "travel": SheetInfo(
        excel_name="Du lịch",
        alias="travel",
        header_row=1,
        dedup_keys=("insured_id_number", "trip_start", "destination"),
        enabled_in_mvp=True,
    ),
    "health": SheetInfo(
        excel_name="Sức khỏe",
        alias="health",
        header_row=3,
        dedup_keys=("insured_id_number", "effective_from"),
    ),
    "auto": SheetInfo(
        excel_name="Bao hiem oto",
        alias="auto",
        header_row=1,
        dedup_keys=("plate_number", "issued_date"),
    ),
    "motorbike": SheetInfo(
        excel_name="Thông tin cấp Bảo hiểm xe máy",
        alias="motorbike",
        header_row=2,
        dedup_keys=("plate_number", "issued_date"),
    ),
    "bhyt_bhxh": SheetInfo(
        excel_name="BHYTBHXH",
        alias="bhyt_bhxh",
        header_row=2,
        dedup_keys=("insured_id_number", "effective_from"),
    ),
    "student": SheetInfo(
        excel_name="HSSV",
        alias="student",
        header_row=1,
        dedup_keys=("insured_id_number", "school", "issued_date"),
    ),
    # Các sheet còn lại sẽ thêm ở Phase 2.
}


def by_alias(alias: str) -> SheetInfo:
    return SHEET_REGISTRY[alias]


def by_excel_name(name: str) -> SheetInfo | None:
    for info in SHEET_REGISTRY.values():
        if info.excel_name == name:
            return info
    return None
