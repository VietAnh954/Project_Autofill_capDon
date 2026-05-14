"""DB exporter — doc du lieu tu SQLite, ghi ra file Excel hang ngay.

Moi sheet bao hiem = 1 luot query DB + ghi vao 1 file Excel snapshot.
Duoc goi sau khi pipeline da ghi xong DB.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd
from sqlalchemy.orm import Session

from auto_fill.db.engine import get_engine
from auto_fill.db.models import (
    AutoInsurance,
    BhytBhxhInsurance,
    HealthInsurance,
    MotorbikeInsurance,
    StudentInsurance,
    TravelInsurance,
)

logger = logging.getLogger(__name__)

_EXPORT_CONFIG: list[tuple[str, type[Any], list[str]]] = [
    (
        "Du lich",
        TravelInsurance,
        [
            "id",
            "issued_date",
            "insured_name",
            "insured_dob",
            "insured_id_number",
            "trip_start",
            "trip_end",
            "destination",
            "scope",
            "plan",
            "premium",
            "buyer_name",
            "created_at",
        ],
    ),
    (
        "Bao hiem oto",
        AutoInsurance,
        [
            "id",
            "issued_date",
            "insured_name",
            "phone",
            "plate_number",
            "frame_number",
            "engine_number",
            "vehicle_type",
            "brand",
            "premium",
            "created_at",
        ],
    ),
    (
        "Xe may",
        MotorbikeInsurance,
        [
            "id",
            "issued_date",
            "plate_number",
            "frame_number",
            "engine_number",
            "customer_name",
            "premium_tnds",
            "premium_accident",
            "total_premium",
            "start_date",
            "end_date",
            "created_at",
        ],
    ),
    (
        "Suc khoe",
        HealthInsurance,
        [
            "id",
            "issued_date",
            "insured_name",
            "insured_id_number",
            "effective_from",
            "premium",
            "buyer_name",
            "created_at",
        ],
    ),
    (
        "BHYTBHXH",
        BhytBhxhInsurance,
        [
            "id",
            "issued_date",
            "insured_name",
            "insured_id_number",
            "effective_from",
            "premium",
            "buyer_name",
            "created_at",
        ],
    ),
    (
        "HSSV",
        StudentInsurance,
        [
            "id",
            "issued_date",
            "insured_name",
            "insured_id_number",
            "school",
            "class_name",
            "effective_from",
            "premium",
            "created_at",
        ],
    ),
]


def export_daily_snapshot(
    db_path: str,
    output_dir: Path,
    export_date: date | None = None,
) -> Path:
    """Xuat toan bo 6 sheet tu DB ra 1 file Excel snapshot.

    Args:
        db_path: Duong dan toi SQLite DB.
        output_dir: Thu muc dau ra.
        export_date: Ngay snapshot (mac dinh: hom nay).

    Returns:
        Path toi file Excel vua tao.
    """
    snap_date = export_date or date.today()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"export_{snap_date.isoformat()}.xlsx"

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    engine = get_engine(db_path)

    for sheet_label, model_cls, columns in _EXPORT_CONFIG:
        with Session(engine) as s:
            rows: Sequence[Any] = s.query(model_cls).all()

        data = []
        for row in rows:
            data.append({col: getattr(row, col, None) for col in columns})

        df = pd.DataFrame(data, columns=columns)
        ws = wb.create_sheet(title=sheet_label)

        ws.append(columns)
        for _, record in df.iterrows():
            ws.append([record[col] for col in columns])

        logger.info(
            "sheet_exported",
            extra={"sheet": sheet_label, "rows": len(df)},
        )

    wb.save(out_path)
    logger.info("daily_export_saved", extra={"path": str(out_path)})
    return out_path
