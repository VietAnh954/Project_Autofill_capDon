"""Sheet mapping — anh xa canonical field → chi so cot Excel cho tung sheet.

Moi SheetColumnMap bao gom:
  - col_map: [(canonical_field | None, col_idx_1based)]
    None = truong tinh toan noi bo (STT, trip_days, ...)
  - stt_col: chi so cot STT (de auto-increment)
  - computed: tap cac truong tinh toan dac biet

Xem MAPPING.md §6 de xem nguon goc mapping nay.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SheetColumnMap:
    alias: str
    col_map: tuple[tuple[str | None, int], ...]
    stt_col: int | None = None
    computed_fields: frozenset[str] = field(default_factory=frozenset)


# ---------------------------------------------------------------------------
# 6.1  Du lich  (MAPPING §6.1)
# ---------------------------------------------------------------------------
TRAVEL = SheetColumnMap(
    alias="travel",
    col_map=(
        ("issued_date", 1),
        (None, 2),  # STT — auto
        ("insured_name", 3),
        ("insured_dob", 4),
        ("insured_id_number", 5),
        ("effective_from", 6),
        ("trip_start", 7),
        ("trip_end", 8),
        (None, 9),  # trip_days — computed
        ("destination", 10),
        ("scope", 11),
        ("plan", 13),
        ("premium", 14),
        ("buyer_name", 15),
    ),
    stt_col=2,
    computed_fields=frozenset({"trip_days"}),
)

# ---------------------------------------------------------------------------
# 6.2  Bao hiem oto  (MAPPING §6.2)
# ---------------------------------------------------------------------------
AUTO = SheetColumnMap(
    alias="auto",
    col_map=(
        ("issued_date", 1),
        (None, 2),  # STT
        ("insured_name", 3),
        ("insured_phone", 4),
        ("insured_email", 5),
        ("insured_address", 6),
        ("plate_number", 7),
        ("frame_number", 8),
        ("engine_number", 9),
        ("vehicle_load", 10),
        ("seats", 11),
        ("vehicle_type", 12),
        ("vehicle_brand", 13),
        ("vehicle_value", 14),
        ("usage_purpose", 15),
    ),
    stt_col=2,
)

# ---------------------------------------------------------------------------
# 6.3  Xe may  (MAPPING §6.3)
# ---------------------------------------------------------------------------
MOTORBIKE = SheetColumnMap(
    alias="motorbike",
    col_map=(
        ("issued_date", 1),
        (None, 2),  # STT
        ("plate_number", 3),
        ("frame_number", 4),
        ("engine_number", 5),
        ("insured_name", 6),
        ("premium_tnds", 7),
        ("premium_accident", 8),
        ("years", 9),
        ("premium", 10),
        # col 11 trong file tong thuong la ghi chu / trong
        ("effective_from", 12),
        ("effective_to", 13),
        ("vehicle_type", 14),
        ("vehicle_brand", 15),
    ),
    stt_col=2,
)

# ---------------------------------------------------------------------------
# 6.4  Suc khoe  (MAPPING §6.4, header row 3)
# ---------------------------------------------------------------------------
HEALTH = SheetColumnMap(
    alias="health",
    col_map=(
        ("issued_date", 1),
        (None, 2),  # STT
        ("insured_name", 3),
        ("insured_dob", 4),
        ("insured_gender", 5),
        ("insured_email", 6),
        ("insured_passport", 7),
        ("insured_id_number", 8),
        ("insured_address", 9),
        ("buyer_name", 10),
    ),
    stt_col=2,
)

# ---------------------------------------------------------------------------
# 6.5  BHYTBHXH  (MAPPING §6.5)
# ---------------------------------------------------------------------------
BHYT_BHXH = SheetColumnMap(
    alias="bhyt_bhxh",
    col_map=(
        ("issued_date", 1),
        (None, 2),  # STT
        ("insured_name", 3),
        ("insured_dob", 4),
        ("insured_gender", 5),
        ("insured_id_number", 6),
        ("insured_address", 7),
        ("insured_phone", 8),
        ("insured_email", 9),
        ("buyer_name", 10),
        ("buyer_dob", 11),
        ("buyer_id_number", 12),
        ("buyer_relation", 13),
    ),
    stt_col=2,
)

# ---------------------------------------------------------------------------
# 6.6  HSSV  (MAPPING §6.6)
# ---------------------------------------------------------------------------
STUDENT = SheetColumnMap(
    alias="student",
    col_map=(
        ("issued_date", 1),
        ("insured_name", 2),
        ("insured_dob", 3),
        ("insured_gender", 4),
        ("insured_id_number", 5),
        ("insured_email", 6),
        ("insured_phone", 7),
        ("insured_address", 8),
        ("school", 9),
        ("class_name", 10),
        ("buyer_name", 11),
        ("buyer_relation", 12),
    ),
    stt_col=None,  # HSSV khong co cot STT trong mapping hien tai
)

# ---------------------------------------------------------------------------
# Registry — tra cuu nhanh bang alias
# ---------------------------------------------------------------------------
SHEET_COL_MAPS: dict[str, SheetColumnMap] = {
    m.alias: m for m in (TRAVEL, AUTO, MOTORBIKE, HEALTH, BHYT_BHXH, STUDENT)
}


def get_map(alias: str) -> SheetColumnMap:
    """Tra ve SheetColumnMap cho alias cho truoc.

    Raises:
        KeyError: Neu alias khong ton tai.
    """
    return SHEET_COL_MAPS[alias]
