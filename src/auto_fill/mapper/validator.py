"""Validator — kiem tra required fields + type theo DATABASE §2.1.

Tra ValidationError neu record thieu truong bat buoc hoac sai kieu.
Khong tu sua gia tri — chi bao loi.
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
    """Mo ta mot truong can validate."""

    name: str
    required: bool = True
    expected_type: type | None = None  # None = khong check type


@dataclass
class ValidationResult:
    """Ket qua validate 1 record."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False


# --- Schema cho tung sheet (canonical field names) ---

TRAVEL_SCHEMA: list[FieldSpec] = [
    FieldSpec("issued_date", required=True, expected_type=date),
    FieldSpec("insured_name", required=True, expected_type=str),
    FieldSpec("insured_dob", required=True, expected_type=date),
    FieldSpec("insured_id_number", required=True, expected_type=str),
    FieldSpec("trip_start", required=True, expected_type=date),
    FieldSpec("trip_end", required=True, expected_type=date),
    FieldSpec("destination", required=True, expected_type=str),
    # optional
    FieldSpec("premium", required=False),
    FieldSpec("insured_phone", required=False),
    FieldSpec("effective_from", required=False, expected_type=date),
]

SCHEMA_BY_ALIAS: dict[str, list[FieldSpec]] = {
    "travel": TRAVEL_SCHEMA,
}


def validate_record(
    record: dict[str, Any],
    sheet_alias: str,
) -> ValidationResult:
    """Kiem tra 1 record dict theo schema cua sheet_alias.

    Args:
        record: Dict {canonical_field: value}. Value da qua normalizer.
        sheet_alias: Vi du "travel".

    Returns:
        ValidationResult voi is_valid va danh sach loi.
    """
    schema = SCHEMA_BY_ALIAS.get(sheet_alias)
    if schema is None:
        logger.warning("no_schema_for_alias", extra={"alias": sheet_alias})
        return ValidationResult(is_valid=True)

    result = ValidationResult(is_valid=True)

    for spec in schema:
        value = record.get(spec.name)

        if spec.required and (value is None or (isinstance(value, str) and not value.strip())):
            result.add_error(f"Thieu truong bat buoc: {spec.name!r}")
            continue

        if value is None:
            continue

        if spec.expected_type is not None and not isinstance(value, spec.expected_type):
            result.add_error(
                f"Sai kieu truong {spec.name!r}: "
                f"can {spec.expected_type.__name__}, nhan {type(value).__name__}"
            )

    return result


def validate_and_raise(record: dict[str, Any], sheet_alias: str) -> None:
    """Goi validate_record, raise ValidationError neu khong hop le.

    Raises:
        ValidationError: Neu record co bat ky loi nao.
    """
    result = validate_record(record, sheet_alias)
    if not result.is_valid:
        msg = "; ".join(result.errors)
        raise ValidationError(f"Record khong hop le ({sheet_alias}): {msg}")
