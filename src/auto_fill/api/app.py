"""FastAPI application — query va export du lieu bao hiem.

Chay:
    uvicorn auto_fill.api.app:app --reload
    python -m auto_fill serve

Endpoints:
    GET  /health                     — kiem tra ket noi DB
    GET  /stats                      — dem ban ghi moi sheet
    GET  /records/{sheet}            — list ban ghi (skip, limit, filter)
    GET  /records/{sheet}/{id}       — lay 1 ban ghi theo id
    GET  /export/{sheet}             — tai Excel snapshot 1 sheet
    GET  /export                     — tai Excel snapshot tat ca sheet
"""

from __future__ import annotations

import io
from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from auto_fill.api.schemas import HealthOut, RecordOut, StatsOut
from auto_fill.db.engine import get_db_url_from_settings, get_engine
from auto_fill.db.models import (
    AutoInsurance,
    BhytBhxhInsurance,
    HealthInsurance,
    MotorbikeInsurance,
    StudentInsurance,
    TravelInsurance,
)

app = FastAPI(
    title="AutoFill Cap Don API",
    description="Query va export du lieu phieu cap don bao hiem.",
    version="0.4.0",
)

_ALIAS_TO_MODEL: dict[str, type[Any]] = {
    "travel": TravelInsurance,
    "auto": AutoInsurance,
    "motorbike": MotorbikeInsurance,
    "health": HealthInsurance,
    "bhyt_bhxh": BhytBhxhInsurance,
    "student": StudentInsurance,
}

_DATE_FIELD: dict[str, str] = {
    "travel": "issued_date",
    "auto": "issued_date",
    "motorbike": "issued_date",
    "health": "effective_from",
    "bhyt_bhxh": "effective_from",
    "student": "issued_date",
}


def _get_engine() -> Any:
    return get_engine(get_db_url_from_settings())


def _row_to_dict(row: Any) -> dict[str, Any]:
    mapper = type(row).__mapper__
    return {col.key: getattr(row, col.key, None) for col in mapper.columns}


# --------------------------------------------------------------------------- #
# Routes                                                                       #
# --------------------------------------------------------------------------- #


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Kiem tra ket noi DB."""
    db_url = get_db_url_from_settings()
    engine = get_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return HealthOut(status="ok", db_url=_mask_url(db_url))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/stats", response_model=StatsOut)
def stats() -> StatsOut:
    """Tong so ban ghi moi sheet."""
    engine = _get_engine()
    counts: dict[str, int] = {}
    with Session(engine) as s:
        for alias, model_cls in _ALIAS_TO_MODEL.items():
            counts[alias] = s.query(model_cls).count()
    return StatsOut(
        travel=counts.get("travel", 0),
        auto=counts.get("auto", 0),
        motorbike=counts.get("motorbike", 0),
        health=counts.get("health", 0),
        bhyt_bhxh=counts.get("bhyt_bhxh", 0),
        student=counts.get("student", 0),
        total=sum(counts.values()),
    )


@app.get("/records/{sheet}", response_model=list[RecordOut])
def list_records(
    sheet: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    date_from: date | None = None,
    date_to: date | None = None,
    insured_name: str | None = None,
) -> list[RecordOut]:
    """List ban ghi cua 1 sheet voi filter."""
    if sheet not in _ALIAS_TO_MODEL:
        raise HTTPException(status_code=404, detail=f"Sheet '{sheet}' khong ton tai.")
    model_cls = _ALIAS_TO_MODEL[sheet]
    date_col = _DATE_FIELD[sheet]
    engine = _get_engine()

    with Session(engine) as s:
        q = s.query(model_cls)
        if date_from:
            q = q.filter(getattr(model_cls, date_col) >= date_from)
        if date_to:
            q = q.filter(getattr(model_cls, date_col) <= date_to)
        if insured_name:
            name_attr = getattr(model_cls, "insured_name", None)
            if name_attr is not None:
                q = q.filter(name_attr.ilike(f"%{insured_name}%"))
        rows = q.order_by(model_cls.id).offset(skip).limit(limit).all()
    return [RecordOut(id=row.id, sheet=sheet, data=_row_to_dict(row)) for row in rows]


@app.get("/records/{sheet}/{record_id}", response_model=RecordOut)
def get_record(sheet: str, record_id: int) -> RecordOut:
    """Lay 1 ban ghi theo id."""
    if sheet not in _ALIAS_TO_MODEL:
        raise HTTPException(status_code=404, detail=f"Sheet '{sheet}' khong ton tai.")
    model_cls = _ALIAS_TO_MODEL[sheet]
    engine = _get_engine()

    with Session(engine) as s:
        row = s.get(model_cls, record_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ban ghi {record_id} khong tim thay.")
    return RecordOut(id=row.id, sheet=sheet, data=_row_to_dict(row))


@app.get("/export/{sheet}")
def export_sheet(sheet: str) -> StreamingResponse:
    """Tai Excel snapshot cua 1 sheet."""
    if sheet not in _ALIAS_TO_MODEL:
        raise HTTPException(status_code=404, detail=f"Sheet '{sheet}' khong ton tai.")
    return _export_response([sheet], f"export_{sheet}.xlsx")


@app.get("/export")
def export_all() -> StreamingResponse:
    """Tai Excel snapshot tat ca 6 sheet."""
    return _export_response(list(_ALIAS_TO_MODEL.keys()), "export_all.xlsx")


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _export_response(sheet_aliases: list[str], filename: str) -> StreamingResponse:
    """Tao Excel file trong bo nho va tra ve StreamingResponse."""
    import openpyxl

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    engine = _get_engine()
    with Session(engine) as s:
        for alias in sheet_aliases:
            model_cls = _ALIAS_TO_MODEL[alias]
            rows = s.query(model_cls).all()
            mapper = model_cls.__mapper__
            col_keys = [col.key for col in mapper.columns]

            ws = wb.create_sheet(title=alias)
            ws.append(col_keys)
            for row in rows:
                ws.append([_serialize(getattr(row, k, None)) for k in col_keys])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _serialize(value: Any) -> Any:
    """Chuyen doi gia tri sang kieu Excel-safe."""
    if isinstance(value, date):
        return value.isoformat()
    return value


def _mask_url(url: str) -> str:
    """An password trong URL de log an toan."""
    if "@" in url:
        scheme_user, rest = url.split("@", 1)
        if ":" in scheme_user:
            parts = scheme_user.rsplit(":", 1)
            return f"{parts[0]}:***@{rest}"
    return url
