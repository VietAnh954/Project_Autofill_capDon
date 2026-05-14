"""DB repository — insert canonical record dicts vao SQLite tables.

Duoc goi tu pipeline sau khi record da pass validator + dedup.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy.exc import IntegrityError
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

_ALIAS_TO_MODEL: dict[str, type[Any]] = {
    "travel": TravelInsurance,
    "auto": AutoInsurance,
    "motorbike": MotorbikeInsurance,
    "health": HealthInsurance,
    "bhyt_bhxh": BhytBhxhInsurance,
    "student": StudentInsurance,
}

_TRAVEL_FIELDS = frozenset(
    {
        "issued_date",
        "insured_name",
        "insured_dob",
        "insured_id_number",
        "payment_date",
        "trip_start",
        "trip_end",
        "destination",
        "scope",
        "plan",
        "premium",
        "buyer_name",
    }
)
_AUTO_FIELDS = frozenset(
    {
        "issued_date",
        "insured_name",
        "phone",
        "email",
        "address",
        "plate_number",
        "frame_number",
        "engine_number",
        "payload",
        "seats",
        "vehicle_type",
        "brand",
        "vehicle_value",
        "purpose",
        "premium",
    }
)
_MOTORBIKE_FIELDS = frozenset(
    {
        "issued_date",
        "plate_number",
        "frame_number",
        "engine_number",
        "customer_name",
        "premium_tnds",
        "premium_accident",
        "years",
        "total_premium",
        "start_date",
        "end_date",
        "vehicle_type",
        "brand",
    }
)
_MOTORBIKE_REMAP = {"trip_start": "start_date", "trip_end": "end_date"}

_HEALTH_FIELDS = frozenset(
    {
        "issued_date",
        "insured_name",
        "insured_dob",
        "insured_id_number",
        "effective_from",
        "outpatient",
        "dental",
        "maternity",
        "premium",
        "buyer_name",
        "buyer_dob",
        "buyer_id_number",
        "buyer_relation",
    }
)
_BHYT_BHXH_FIELDS = frozenset(
    {
        "issued_date",
        "insured_name",
        "insured_id_number",
        "effective_from",
        "buyer_name",
        "buyer_dob",
        "buyer_relation",
        "premium",
    }
)
_STUDENT_FIELDS = frozenset(
    {
        "issued_date",
        "insured_name",
        "insured_dob",
        "insured_id_number",
        "school",
        "class_name",
        "effective_from",
        "premium",
        "buyer_name",
    }
)

_ALIAS_TO_FIELDS: dict[str, frozenset[str]] = {
    "travel": _TRAVEL_FIELDS,
    "auto": _AUTO_FIELDS,
    "motorbike": _MOTORBIKE_FIELDS,
    "health": _HEALTH_FIELDS,
    "bhyt_bhxh": _BHYT_BHXH_FIELDS,
    "student": _STUDENT_FIELDS,
}


def insert_record(
    record: Mapping[str, Any],
    sheet_alias: str,
    db_path: str,
    source_email_id: str | None = None,
    source_attachment: str | None = None,
) -> bool:
    """Insert 1 canonical record vao table tuong ung.

    Returns:
        True neu insert thanh cong, False neu duplicate (IntegrityError).

    Raises:
        KeyError: Neu sheet_alias khong hop le.
    """
    model_cls = _ALIAS_TO_MODEL[sheet_alias]
    allowed_fields = _ALIAS_TO_FIELDS[sheet_alias]

    kwargs: dict[str, Any] = {}
    for field in allowed_fields:
        remap = _MOTORBIKE_REMAP if sheet_alias == "motorbike" else {}
        src_field = {v: k for k, v in remap.items()}.get(field, field)
        val = record.get(src_field) if src_field != field else record.get(field)
        if val is not None:
            kwargs[field] = val

    if source_email_id:
        kwargs["source_email_id"] = source_email_id
    if source_attachment:
        kwargs["source_attachment"] = source_attachment

    engine = get_engine(db_path)
    try:
        with Session(engine) as s:
            s.add(model_cls(**kwargs))
            s.commit()
        logger.info(
            "db_insert_ok",
            extra={"sheet": sheet_alias, "id": record.get("insured_id_number")},
        )
        return True
    except IntegrityError:
        logger.debug("db_duplicate_skip", extra={"sheet": sheet_alias})
        return False
