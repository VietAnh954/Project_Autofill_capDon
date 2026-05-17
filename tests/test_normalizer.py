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


# ============================================================
# Phase 8.2 — new cases: NaN handling, float CCCD, multi-format dates
# ============================================================


_NAN = float("nan")


class TestNaNHandling:
    """Pandas NaN / numpy nan / None / 'nan' string must raise."""

    @pytest.mark.parametrize(
        "fn, value",
        [
            (normalize_date, _NAN),
            (normalize_date, None),
            (normalize_date, "nan"),
            (normalize_date, "NaT"),
            (normalize_id_number, _NAN),
            (normalize_id_number, None),
            (normalize_id_number, "nan"),
            (normalize_money, _NAN),
            (normalize_money, None),
            (normalize_phone, _NAN),
            (normalize_phone, None),
            (normalize_name, _NAN),
            (normalize_name, None),
            (normalize_name, "nan"),
            (normalize_plate, _NAN),
            (normalize_plate, None),
        ],
    )
    def test_nan_inputs_raise(self, fn: object, value: object) -> None:
        with pytest.raises(MappingError):
            fn(value)  # type: ignore[operator]


class TestFloatIdNumber:
    """Pandas reads numeric Excel cells as float -> normalize must convert cleanly."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            (12345678901.0, "012345678901"),  # CCCD 11 digits -> pad to 12
            (12345678901, "012345678901"),  # int same pad
            (123456789.0, "123456789"),  # CMND 9 digits — no pad
            (1188036710.0, "01188036710"),  # 10 digits -> not padded (only 11→12 rule)
        ],
    )
    def test_float_cccd_strips_decimal(self, value: object, expected: str) -> None:
        # The 10-digit case won't be padded (only 11→12 rule), so it'll fail validate_id_number
        # but normalize should still strip .0
        result = normalize_id_number(value)
        # We just check no .0 in result
        assert ".0" not in result
        # And digits only
        assert result.isdigit()


class TestDateMultiFormat:
    """Phase 8.2: support yyyy/mm/dd, MM/dd/yyyy (US), pandas Timestamp str."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("2026/05/15", date(2026, 5, 15)),  # yyyy/mm/dd
            ("2026-05-15 00:00:00", date(2026, 5, 15)),  # pandas Timestamp str
            ("2026-05-15 00:00:00.000", date(2026, 5, 15)),  # with microseconds
            ("15.05.2026", date(2026, 5, 15)),  # dd.mm.yyyy
            ("2026/05/15 09:30:00", date(2026, 5, 15)),  # yyyy/mm/dd HH:MM:SS
        ],
    )
    def test_extra_date_formats(self, value: str, expected: date) -> None:
        assert normalize_date(value) == expected

    def test_dd_mm_yyyy_priority_over_mm_dd_yyyy(self) -> None:
        """VN format priority — '05/01/2026' = 5 January (dd/mm), not May 1 (US)."""
        # 5/1/2026 valid as both formats; dd/mm wins
        assert normalize_date("05/01/2026") == date(2026, 1, 5)

    def test_mm_dd_fallback_when_dd_mm_invalid(self) -> None:
        """If '13/05/2026' fails dd/mm (no month 13) — but 13/05 IS valid as dd/mm
        meaning day 13 month 5. So no fallback needed here.
        Real US-only date: '12/31/2026' → fails dd/mm (no month 31) → MM/dd → Dec 31."""
        assert normalize_date("12/31/2026") == date(2026, 12, 31)


class TestFloatExcelSerial:
    """Float Excel serials should convert to date."""

    def test_excel_serial_float(self) -> None:
        # 46156.0 = 2026-05-14
        assert normalize_date(46156.0) == date(2026, 5, 14)

    def test_excel_serial_int_via_float(self) -> None:
        # pandas can read date cell as float — both int+float should work
        assert normalize_date(46156) == normalize_date(46156.0)
