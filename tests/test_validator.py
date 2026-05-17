"""Unit tests cho Validator (refactored 2026-05-17, Phase 8.1).

Philosophy: chi 1 CORE field per sheet bat buoc. Soft field thieu -> warning, KHONG fail.
"""

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

    def test_only_core_field_passes(self) -> None:
        result = validate_record({"insured_name": "NGUYEN VAN A"}, "travel")
        assert result.is_valid is True
        assert result.errors == []
        assert len(result.warnings) > 0

    def test_missing_core_field_fails(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["insured_name"]
        result = validate_record(record, "travel")
        assert result.is_valid is False
        assert any("CORE" in e for e in result.errors)

    def test_missing_soft_issued_date_passes(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["issued_date"]
        result = validate_record(record, "travel")
        assert result.is_valid is True

    def test_missing_destination_passes(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["destination"]
        result = validate_record(record, "travel")
        assert result.is_valid is True

    def test_wrong_type_for_date_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "issued_date": "2026-05-14"}
        result = validate_record(record, "travel")
        assert result.is_valid is False
        assert any("issued_date" in e for e in result.errors)

    def test_wrong_type_for_name_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "insured_name": 12345}
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_optional_field_with_wrong_type_fails(self) -> None:
        record = {**_VALID_TRAVEL, "effective_from": "not-a-date"}
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_empty_string_core_field_fails(self) -> None:
        record = {**_VALID_TRAVEL, "insured_name": ""}
        result = validate_record(record, "travel")
        assert result.is_valid is False

    def test_empty_string_soft_field_passes(self) -> None:
        record = {**_VALID_TRAVEL, "destination": ""}
        result = validate_record(record, "travel")
        assert result.is_valid is True

    def test_none_soft_field_passes(self) -> None:
        record = {**_VALID_TRAVEL, "trip_start": None}
        result = validate_record(record, "travel")
        assert result.is_valid is True

    def test_unknown_sheet_alias_passes(self) -> None:
        result = validate_record(_VALID_TRAVEL, "unknown_sheet")
        assert result.is_valid is True

    def test_premium_int_passes(self) -> None:
        record = {**_VALID_TRAVEL, "premium": 1500000}
        result = validate_record(record, "travel")
        assert result.is_valid is True

    def test_premium_float_passes(self) -> None:
        record = {**_VALID_TRAVEL, "premium": 1500000.0}
        result = validate_record(record, "travel")
        assert result.is_valid is True


class TestAutoSchema:
    def test_only_insured_name_passes(self) -> None:
        result = validate_record({"insured_name": "Nguyen Van B"}, "auto")
        assert result.is_valid is True

    def test_only_plate_number_passes(self) -> None:
        result = validate_record({"plate_number": "51A-12345"}, "auto")
        assert result.is_valid is True

    def test_both_missing_fails(self) -> None:
        result = validate_record({"vehicle_brand": "Mazda"}, "auto")
        assert result.is_valid is False
        assert any("CORE" in e for e in result.errors)


class TestHealthSchema:
    def test_only_insured_name_passes(self) -> None:
        result = validate_record({"insured_name": "Pham Thi Lien"}, "health")
        assert result.is_valid is True

    def test_buyer_dob_distinct_from_insured_dob(self) -> None:
        record = {
            "insured_name": "Do Danh Minh Phuc",
            "insured_dob": date(2018, 12, 12),
            "buyer_name": "Do Thi Thuan",
            "buyer_dob": date(1988, 8, 30),
        }
        result = validate_record(record, "health")
        assert result.is_valid is True


class TestValidateAndRaise:
    def test_valid_record_does_not_raise(self) -> None:
        validate_and_raise(_VALID_TRAVEL, "travel")

    def test_minimal_record_does_not_raise(self) -> None:
        validate_and_raise({"insured_name": "X"}, "travel")

    def test_missing_core_raises(self) -> None:
        record = {**_VALID_TRAVEL}
        del record["insured_name"]
        with pytest.raises(ValidationError, match="CORE"):
            validate_and_raise(record, "travel")

    def test_wrong_type_raises(self) -> None:
        record = {**_VALID_TRAVEL, "premium": "not-a-number"}
        with pytest.raises(ValidationError):
            validate_and_raise(record, "travel")

    def test_error_message_contains_sheet_alias(self) -> None:
        with pytest.raises(ValidationError, match="travel"):
            validate_and_raise({}, "travel")
