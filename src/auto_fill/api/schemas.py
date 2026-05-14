"""Pydantic schemas cho FastAPI request/response."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel


class RecordOut(BaseModel):
    """Generic record response — tra ve tat ca fields cua 1 ban ghi."""

    id: int
    sheet: str
    data: dict[str, Any]

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    """Tong so ban ghi theo tung sheet."""

    travel: int = 0
    auto: int = 0
    motorbike: int = 0
    health: int = 0
    bhyt_bhxh: int = 0
    student: int = 0
    total: int = 0


class HealthOut(BaseModel):
    status: str = "ok"
    db_url: str


class QueryParams(BaseModel):
    """Common query parameters."""

    skip: int = 0
    limit: int = 100
    date_from: date | None = None
    date_to: date | None = None
    insured_name: str | None = None
