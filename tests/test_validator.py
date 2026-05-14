"""Unit tests cho Validator."""

from __future__ import annotations

from datetime import date

import pytest

from auto_fill.mapper.validator import validate_and_raise, validate_record
from auto_fill.utils.errors import ValidationError

_VALID_TRAVEL = {
    "issued_date": date(2026, 5, 14),
    "insured_name": "NGUYEN VAN A",
    "insured_dob": date(1990, 1, 1),
    "insured_id_number": "012345678901",
    "trip_start": date(2026, 5, 20),
    "trip_end": date(2026, 5, 27),
    "destination": "Thai Lan",
}


class TestValidateRecord:
    def test_valid_travel_record_passes(self) -> None:
        result = validate_record(_VALID_TRAVEL, "travel")
        assert result.is_valid is True
        assert result.errors == []

    def test_missing_required_field_fails(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["insured_name"]
        result = validate_record(record, "travel")
        assert result.is_valid is False
        assert any("insured_name" in e for e in result.errors)

    def test_multiple_missing_fields_all_reported(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["insured_name"]
        del record["insured_id_number"]
        result = validate_record(record, "travel")
        assert result.is_valid is False
        assert len(result.errors) >= 2

    def test_wrong_type_for_date_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "issued_date": "2026-05-14"}  # str, not date
        result = validate_record(record, "travel")
        assert result.is_valid is False
        assert any("issued_date" in e for e in result.errors)

    def test_wrong_type_for_name_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "insured_name": 12345}  # int, not str
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_optional_field_absent_passes(self) -> None:
        record = {**_VALID_TRAVEL}
        result = validate_record(record, "travel")
        assert result.is_valid is True

    def test_optional_field_with_wrong_type_fails(self) -> None:
        record = {**_VALID_TRAVEL, "effective_from": "not-a-date"}
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_empty_string_required_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "destination": ""}
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_none_required_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "trip_start": None}
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_unknown_sheet_alias_passes(self) -> None:
        result = validate_record(_VALID_TRAVEL, "unknown_sheet")
        assert result.is_valid is True  # no schema = no validation

    def test_optional_field_none_passes(self) -> None:
        record = {**_VALID_TRAVEL, "premium": None}
        result = validate_record(record, "travel")
        assert result.is_valid is True


class TestValidateAndRaise:
    def test_valid_record_does_not_raise(self) -> None:
        validate_and_raise(_VALID_TRAVEL, "travel")

    def test_invalid_record_raises_validation_error(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["insured_name"]
        with pytest.raises(ValidationError, match="insured_name"):
            validate_and_raise(record, "travel")

    def test_error_message_contains_sheet_alias(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["destination"]
        with pytest.raises(ValidationError, match="travel"):
            validate_and_raise(record, "travel")
