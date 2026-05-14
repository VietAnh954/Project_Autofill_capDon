"""Unit tests cho Normalizer — 10+ case moi rule (MAPPING.md §3)."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from auto_fill.mapper.normalizer import (
    normalize_date,
    normalize_id_number,
    normalize_money,
    normalize_name,
    normalize_phone,
    normalize_plate,
    validate_id_number,
)
from auto_fill.utils.errors import MappingError


class TestNormalizeDate:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("14/05/2026", date(2026, 5, 14)),
            ("01/01/1990", date(1990, 1, 1)),
            ("31/12/2000", date(2000, 12, 31)),
            ("14-05-2026", date(2026, 5, 14)),
            ("2026-05-14", date(2026, 5, 14)),
            ("14/05/26", date(2026, 5, 14)),
            ("01/01/90", date(1990, 1, 1)),
            (datetime(2026, 5, 14, 9, 0, 0), date(2026, 5, 14)),
            (date(2026, 5, 14), date(2026, 5, 14)),
            (46156, date(2026, 5, 14)),  # Excel serial
        ],
    )
    def test_valid_dates(self, value: object, expected: date) -> None:
        assert normalize_date(value) == expected

    @pytest.mark.parametrize(
        "value",
        ["not a date", "", "nan", None, 0, "32/01/2026"],
    )
    def test_invalid_dates_raise(self, value: object) -> None:
        with pytest.raises(MappingError):
            normalize_date(value)


class TestNormalizeIdNumber:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("012345678901", "012345678901"),
            ("  012345678901  ", "012345678901"),
            ("012-345-678-901", "012345678901"),
            ("abcdef123", "ABCDEF123"),
            ("123456789", "123456789"),  # CMND 9 chu so
            ("B1234567", "B1234567"),  # Passport
        ],
    )
    def test_valid_ids(self, value: str, expected: str) -> None:
        assert normalize_id_number(value) == expected

    @pytest.mark.parametrize("value", [None, "", "nan", "none"])
    def test_empty_raises(self, value: object) -> None:
        with pytest.raises(MappingError):
            normalize_id_number(value)


class TestValidateIdNumber:
    @pytest.mark.parametrize(
        "id_str, expected",
        [
            ("012345678901", True),  # CCCD 12 chu so
            ("123456789", True),  # CMND 9 chu so
            ("B1234567", True),  # Passport
            ("12345", False),  # qua ngan
            ("ABCDEFGHIJ", False),  # qua dai
            ("1234567890", False),  # 10 chu so - khong phu hop
        ],
    )
    def test_validate(self, id_str: str, expected: bool) -> None:
        assert validate_id_number(id_str) == expected


class TestNormalizePhone:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("0901234567", "0901234567"),
            ("090 123 4567", "0901234567"),
            ("090-123-4567", "0901234567"),
            ("+84901234567", "0901234567"),
            ("84901234567", "0901234567"),
            ("0912345678", "0912345678"),
            ("0933333333", "0933333333"),
            ("(090)1234567", "0901234567"),
            ("090.123.4567", "0901234567"),
            ("0388123456", "0388123456"),
        ],
    )
    def test_valid_phones(self, value: str, expected: str) -> None:
        assert normalize_phone(value) == expected

    @pytest.mark.parametrize(
        "value",
        [None, "", "nan", "12345", "123456789012", "1234567890"],  # 10 chu so nhung khong bat dau 0
    )
    def test_invalid_phones_raise(self, value: object) -> None:
        with pytest.raises(MappingError):
            normalize_phone(value)


class TestNormalizeMoney:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("1500000", 1_500_000.0),
            ("1,500,000", 1_500_000.0),
            ("1.500.000", 1_500_000.0),
            ("1.500.000 VND", 1_500_000.0),
            ("1.5M", 1_500_000.0),
            ("1.5K", 1_500.0),
            (1500000, 1_500_000.0),
            (1500000.5, 1_500_000.5),
            ("500,000", 500_000.0),
            ("2.000.000", 2_000_000.0),
            ("3,500,250.50", 3_500_250.50),
        ],
    )
    def test_valid_money(self, value: object, expected: float) -> None:
        assert normalize_money(value) == pytest.approx(expected, rel=1e-6)

    @pytest.mark.parametrize("value", [None, "", "nan", "abc"])
    def test_invalid_money_raise(self, value: object) -> None:
        with pytest.raises(MappingError):
            normalize_money(value)


class TestNormalizeName:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("NGUYEN VAN A", "NGUYEN VAN A"),
            ("  TRAN   THI   B  ", "TRAN THI B"),
            ("Le Van C", "Le Van C"),
            ("NGUYEN\tVAN\tA", "NGUYEN VAN A"),
            ("A", "A"),
            (" PHAM THI D ", "PHAM THI D"),
        ],
    )
    def test_valid_names(self, value: str, expected: str) -> None:
        assert normalize_name(value) == expected

    @pytest.mark.parametrize("value", [None, "", "nan", "none"])
    def test_empty_raises(self, value: object) -> None:
        with pytest.raises(MappingError):
            normalize_name(value)


class TestNormalizePlate:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("51A-123.45", "51A-123.45"),
            ("51a-123.45", "51A-123.45"),
            (" 30F-999.99 ", "30F-999.99"),
            ("29B-12345", "29B-12345"),
            ("HN-12345", "HN-12345"),
            ("51 A 123 45", "51A12345"),
        ],
    )
    def test_valid_plates(self, value: str, expected: str) -> None:
        assert normalize_plate(value) == expected

    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_raises(self, value: object) -> None:
        with pytest.raises(MappingError):
            normalize_plate(value)
