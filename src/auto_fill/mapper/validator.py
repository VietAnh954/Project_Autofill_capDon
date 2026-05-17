"""Validator — kiem tra CORE field theo philosophy linh hoat (DATABASE.md section 5.1).

Refactor 2026-05-17 (Phase 8.1):
- Truoc day: bat buoc 7+ field per sheet -> record thieu data bi reject toan bo.
- Bay gio: chi 1 CORE field per sheet (insured_name / plate_number).
  Cac field khac -> log warning, KHONG raise. Pipeline van ghi vao master,
  cell trong = None, user review tay neu can.
- Type check van con — chi check khi value khong phai None.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from auto_fill.utils.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class FieldSpec:
    """Mo ta mot truong can validate.

    - core=True: bat buoc co — thieu hoac trong -> record fail validation.
    - core=False: optional — thieu chi log warning, type check chi khi co value.
    """

    name: str
    core: bool = False
    expected_type: Any = None  # type or tuple of types; None = khong check type


@dataclass
class ValidationResult:
    """Ket qua validate 1 record."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ============================================================
# Schema per sheet — chi 1 CORE field, con lai SOFT
# Reference: docs/DATABASE.md section 5.1
# ============================================================

# CORE field rule:
# - travel/health/bhyt_bhxh/student: insured_name -> bat buoc
# - auto/motorbike: insured_name HOAC plate_number -> it nhat 1
# Logic OR duoc xu ly trong validate_record() boi co the co nhieu CORE option.

TRAVEL_SCHEMA: list[FieldSpec] = [
    FieldSpec("insured_name", core=True, expected_type=str),
    FieldSpec("issued_date", expected_type=date),
    FieldSpec("insured_dob", expected_type=date),
    FieldSpec("insured_id_number", expected_type=str),
    FieldSpec("trip_start", expected_type=date),
    FieldSpec("trip_end", expected_type=date),
    FieldSpec("destination", expected_type=str),
    FieldSpec("premium", expected_type=(int, float)),
    FieldSpec("insured_phone", expected_type=str),
    FieldSpec("effective_from", expected_type=date),
    FieldSpec("buyer_name", expected_type=str),
    FieldSpec("buyer_dob", expected_type=date),
]

HEALTH_SCHEMA: list[FieldSpec] = [
    FieldSpec("insured_name", core=True, expected_type=str),
    FieldSpec("issued_date", expected_type=date),
    FieldSpec("insured_dob", expected_type=date),
    FieldSpec("insured_id_number", expected_type=str),
    FieldSpec("insured_email", expected_type=str),
    FieldSpec("insured_address", expected_type=str),
    FieldSpec("buyer_name", expected_type=str),
    FieldSpec("buyer_relation", expected_type=str),
    FieldSpec("buyer_dob", expected_type=date),
    FieldSpec("buyer_id_number", expected_type=str),
    FieldSpec("buyer_phone", expected_type=str),
    FieldSpec("plan", expected_type=str),
    FieldSpec("premium", expected_type=(int, float)),
    FieldSpec("effective_from", expected_type=date),
    FieldSpec("effective_to", expected_type=date),
]

AUTO_SCHEMA: list[FieldSpec] = [
    FieldSpec("insured_name", core=True, expected_type=str),
    FieldSpec("plate_number", core=True, expected_type=str),
    FieldSpec("issued_date", expected_type=date),
    FieldSpec("frame_number", expected_type=str),
    FieldSpec("engine_number", expected_type=str),
    FieldSpec("seats", expected_type=(int, str)),
    FieldSpec("vehicle_type", expected_type=str),
    FieldSpec("vehicle_brand", expected_type=str),
    FieldSpec("vehicle_value", expected_type=(int, float)),
    FieldSpec("premium", expected_type=(int, float)),
    FieldSpec("effective_from", expected_type=date),
    FieldSpec("effective_to", expected_type=date),
]

MOTORBIKE_SCHEMA: list[FieldSpec] = [
    FieldSpec("insured_name", core=True, expected_type=str),
    FieldSpec("plate_number", core=True, expected_type=str),
    FieldSpec("issued_date", expected_type=date),
    FieldSpec("frame_number", expected_type=str),
    FieldSpec("engine_number", expected_type=str),
    FieldSpec("premium_tnds", expected_type=(int, float)),
    FieldSpec("premium_accident", expected_type=(int, float)),
    FieldSpec("premium_total", expected_type=(int, float)),
    FieldSpec("years", expected_type=(int, float)),
    FieldSpec("effective_from", expected_type=date),
    FieldSpec("effective_to", expected_type=date),
    FieldSpec("vehicle_brand", expected_type=str),
]

BHYT_BHXH_SCHEMA: list[FieldSpec] = [
    FieldSpec("insured_name", core=True, expected_type=str),
    FieldSpec("issued_date", expected_type=date),
    FieldSpec("insured_dob", expected_type=date),
    FieldSpec("insured_id_number", expected_type=str),
    FieldSpec("buyer_name", expected_type=str),
    FieldSpec("buyer_dob", expected_type=date),
    FieldSpec("premium", expected_type=(int, float)),
]

STUDENT_SCHEMA: list[FieldSpec] = [
    FieldSpec("insured_name", core=True, expected_type=str),
    FieldSpec("issued_date", expected_type=date),
    FieldSpec("insured_dob", expected_type=date),
    FieldSpec("school", expected_type=str),
    FieldSpec("class_name", expected_type=str),
    FieldSpec("buyer_name", expected_type=str),
    FieldSpec("buyer_relation", expected_type=str),
    FieldSpec("buyer_dob", expected_type=date),
    FieldSpec("premium", expected_type=(int, float)),
]


SCHEMA_BY_ALIAS: dict[str, list[FieldSpec]] = {
    "travel": TRAVEL_SCHEMA,
    "health": HEALTH_SCHEMA,
    "auto": AUTO_SCHEMA,
    "motorbike": MOTORBIKE_SCHEMA,
    "bhyt_bhxh": BHYT_BHXH_SCHEMA,
    "student": STUDENT_SCHEMA,
}


def _is_empty(value: Any) -> bool:
    """True neu value None, empty string, hoac whitespace-only."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _check_type(value: Any, expected: Any) -> bool:
    """Type check chap nhan tuple of types (vd (int, float))."""
    return isinstance(value, expected)


def validate_record(
    record: dict[str, Any],
    sheet_alias: str,
) -> ValidationResult:
    """Kiem tra 1 record dict theo schema cua sheet_alias.

    Rules:
    - CORE fields: it nhat 1 trong cac field core phai co value non-empty -> fail neu khong.
    - SOFT fields thieu -> log warning, KHONG fail.
    - Type check: chi check khi value khong None/empty. Sai type -> fail.

    Args:
        record: Dict {canonical_field: value}. Value da qua normalizer.
        sheet_alias: Vi du "travel", "health", "auto".

    Returns:
        ValidationResult voi is_valid + errors (block write) + warnings (info only).
    """
    schema = SCHEMA_BY_ALIAS.get(sheet_alias)
    if schema is None:
        logger.warning("no_schema_for_alias", extra={"alias": sheet_alias})
        return ValidationResult(is_valid=True)

    result = ValidationResult(is_valid=True)

    core_fields = [s for s in schema if s.core]
    if core_fields:
        has_any_core = any(not _is_empty(record.get(s.name)) for s in core_fields)
        if not has_any_core:
            names = " HOAC ".join(repr(s.name) for s in core_fields)
            result.add_error(f"Thieu CORE field ({sheet_alias}): can co {names}")

    for spec in schema:
        value = record.get(spec.name)
        if _is_empty(value):
            if not spec.core:
                result.add_warning(f"Soft field trong: {spec.name!r}")
            continue
        if spec.expected_type is not None and not _check_type(value, spec.expected_type):
            if isinstance(spec.expected_type, tuple):
                expected_name = "|".join(t.__name__ for t in spec.expected_type)
            else:
                expected_name = spec.expected_type.__name__
            result.add_error(
                f"Sai kieu truong {spec.name!r}: "
                f"can {expected_name}, nhan {type(value).__name__}"
            )

    return result


def validate_and_raise(record: dict[str, Any], sheet_alias: str) -> None:
    """Goi validate_record, raise ValidationError neu khong hop le.

    Raises:
        ValidationError: Neu record thieu CORE field hoac sai type.
    """
    result = validate_record(record, sheet_alias)

    if result.warnings:
        logger.info(
            "soft_fields_missing",
            extra={"alias": sheet_alias, "warnings": result.warnings},
        )

    if not result.is_valid:
        msg = "; ".join(result.errors)
        raise ValidationError(f"Record khong hop le ({sheet_alias}): {msg}")
