"""Normalizer — chuan hoa gia tri field theo MAPPING.md section 3.

Rules:
  3.1 Date     — parse nhieu format (dd/mm/yyyy mac dinh + yyyy/mm/dd + MM/dd/yyyy + Excel serial),
                 tra datetime.date
  3.2 ID       — strip/uppercase, validate length (ho tro float CCCD '12345.0' -> '12345')
  3.3 Phone    — chuan hoa 10 chu so bat dau 0
  3.4 Money    — parse VN float (dau phay/cham)
  3.5 Name     — strip + collapse whitespace
  3.6 Plate    — uppercase, strip ky tu thua

Refactor 2026-05-17 (Phase 8.2):
- Ho tro pandas NaN, numpy.nan, pd.NaT
- Float -> str/int conversion cho CCCD (vd 12345678901.0 -> '12345678901')
- Them date format: yyyy/mm/dd, MM/dd/yyyy (US, fallback sau dd/mm/yyyy VN)
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta
from typing import Any

from auto_fill.utils.errors import MappingError

# Date formats theo thu tu priority: VN format dd/mm/yyyy uu tien tuoc.
# Format US MM/dd/yyyy o cuoi (chi parse khi dd/mm/yyyy fail).
_DATE_FORMATS = [
    "%d/%m/%Y",  # dd/mm/yyyy — VN MAC DINH
    "%d-%m-%Y",  # dd-mm-yyyy
    "%d.%m.%Y",  # dd.mm.yyyy
    "%Y-%m-%d",  # yyyy-mm-dd ISO
    "%Y/%m/%d",  # yyyy/mm/dd
    "%d/%m/%y",  # dd/mm/yy
    "%d-%m-%y",  # dd-mm-yy
    "%Y-%m-%d %H:%M:%S",  # yyyy-mm-dd HH:MM:SS (pandas Timestamp str)
    "%Y-%m-%d %H:%M:%S.%f",  # with microseconds
    "%d/%m/%Y %H:%M:%S",  # dd/mm/yyyy HH:MM:SS
    "%Y-%m-%dT%H:%M:%S",  # ISO 8601
    "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y",  # MM/dd/yyyy US (last resort)
    "%m-%d-%Y",
]

_EXCEL_EPOCH = date(1899, 12, 30)

_PHONE_RE = re.compile(r"[\s\-\.\(\)]+")
_PLATE_CLEAN_RE = re.compile(r"[\s]+")
_NAN_STRINGS = {"nan", "none", "null", "nat", "na", "n/a"}


def _is_nan_like(value: Any) -> bool:
    """True neu value la NaN, NaT, None, hoac string nan-like."""
    if value is None:
        return True
    if isinstance(value, float):
        try:
            return math.isnan(value) or math.isinf(value)
        except (TypeError, ValueError):
            return False
    # pandas NaT
    type_name = type(value).__name__
    if type_name == "NaTType":
        return True
    if isinstance(value, str):
        return value.strip().lower() in _NAN_STRINGS
    return False


# ===========================================================================
# 3.1 Date
# ===========================================================================


def normalize_date(value: Any) -> date:  # noqa: C901
    """Parse nhieu dinh dang ngay -> datetime.date.

    Args:
        value: Chuoi ngay, datetime, date, hoac so (Excel serial), hoac float NaN.

    Returns:
        datetime.date da parse.

    Raises:
        MappingError: Neu khong parse duoc hoac value la NaN.
    """
    if _is_nan_like(value):
        raise MappingError(f"Gia tri ngay rong/NaN: {value!r}")

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    # pandas Timestamp / numpy datetime64 — co attribute .date()
    if hasattr(value, "date") and callable(value.date):
        try:
            result = value.date()
            if isinstance(result, date):
                return result
        except (ValueError, TypeError):
            pass

    if isinstance(value, int | float):
        # Excel serial (60..2958465). Loai bo float qua nho/qua lon.
        try:
            serial_int = int(value)
            if 1 <= serial_int <= 2958465:
                return _EXCEL_EPOCH + timedelta(days=serial_int)
        except (ValueError, OverflowError) as exc:
            raise MappingError(f"So serial Excel khong hop le: {value!r}") from exc
        raise MappingError(f"So serial Excel ngoai phai vi: {value!r}")

    s = str(value).strip()
    if not s or s.lower() in _NAN_STRINGS:
        raise MappingError(f"Chuoi ngay rong: {s!r}")

    # Strip optional time component "00:00:00" trailing
    current_year = datetime.now().year
    for fmt in _DATE_FORMATS:
        try:
            d = datetime.strptime(s, fmt).date()
            if d.year < 100:
                d = d.replace(year=d.year + (2000 if d.year <= current_year % 100 + 1 else 1900))
            return d
        except ValueError:
            continue

    raise MappingError(f"Khong parse duoc ngay: {s!r}")


# ===========================================================================
# 3.2 CCCD / CMND / Passport
# ===========================================================================


def normalize_id_number(value: Any) -> str:
    """Strip whitespace, uppercase, validate CCCD/CMND length.

    Ho tro:
    - String: '012345678901', '012 345 678 901', 'P12345678'
    - Float (pandas numeric cell): 12345678901.0 -> '12345678901'
    - Int: 12345678901 -> '12345678901'

    CCCD = 12 chu so, CMND cu = 9 chu so, Passport = 6-9 ky tu alphanumeric.

    Returns:
        Chuoi ID da chuan hoa.

    Raises:
        MappingError: Neu value rong/NaN.
    """
    if _is_nan_like(value):
        raise MappingError(f"ID rong/NaN: {value!r}")

    # Float (pandas reads numeric cells as float): convert via int to strip .0
    if isinstance(value, float):
        s = str(value) if not value.is_integer() else str(int(value))
    elif isinstance(value, int):
        s = str(value)
    else:
        s = str(value).strip().upper().replace(" ", "").replace("-", "")

    # Final clean
    s = s.strip().upper().replace(" ", "").replace("-", "")
    if not s or s.lower() in _NAN_STRINGS:
        raise MappingError(f"ID number rong sau clean: {value!r}")

    # CCCD 12 so co the bi mat so 0 dau khi qua float: '12345678901' (11) -> pad
    if s.isdigit() and len(s) == 11:
        s = "0" + s

    return s


def validate_id_number(id_str: str) -> bool:
    """Kiem tra id_str co hop le khong (khong raise, chi tra bool)."""
    if id_str.isdigit():
        return len(id_str) in (9, 12)
    return 6 <= len(id_str) <= 9 and id_str.isalnum()


# ===========================================================================
# 3.3 Phone
# ===========================================================================


def normalize_phone(value: Any) -> str:
    """Chuan hoa SDT Viet Nam -> 10 chu so bat dau 0.

    Doi +84xxx -> 0xxx, 84xxx -> 0xxx.

    Returns:
        Chuoi SDT da chuan hoa.

    Raises:
        MappingError: Neu khong chuan hoa duoc.
    """
    if _is_nan_like(value):
        raise MappingError(f"Phone rong/NaN: {value!r}")

    # Float: convert via int (vd 901234567.0 -> '901234567')
    if isinstance(value, float) and value.is_integer():
        s = str(int(value))
    elif isinstance(value, int):
        s = str(value)
    else:
        s = str(value).strip()

    s = _PHONE_RE.sub("", s)

    if s.startswith("+84"):
        s = "0" + s[3:]
    elif s.startswith("84") and len(s) == 11:
        s = "0" + s[2:]
    elif s.isdigit() and len(s) == 9:
        # Mat so 0 dau khi qua float (vd '901234567' -> '0901234567')
        s = "0" + s

    if not (s.isdigit() and len(s) == 10 and s.startswith("0")):
        raise MappingError(f"SDT khong hop le sau chuan hoa: {s!r} (goc: {value!r})")
    return s


# ===========================================================================
# 3.4 Money
# ===========================================================================


def normalize_money(value: Any) -> float:
    """Parse so tien VND tu nhieu dinh dang.

    Ho tro: '1,500,000', '1.500.000', '1.500.000 VND', '1.5M', 1500000, 1500000.0.
    """
    if _is_nan_like(value):
        raise MappingError(f"Money rong/NaN: {value!r}")

    if isinstance(value, int | float):
        return float(value)

    s = str(value).strip()
    if not s or s.lower() in _NAN_STRINGS:
        raise MappingError(f"Money rong: {value!r}")

    s_lower = s.lower()
    multiplier = 1.0
    if s_lower.endswith("m"):
        multiplier = 1_000_000
        s = s[:-1]
    elif s_lower.endswith("k"):
        multiplier = 1_000
        s = s[:-1]
    elif s_lower.endswith("b"):
        multiplier = 1_000_000_000
        s = s[:-1]

    s = re.sub(r"[^\d,\.]", "", s).strip()
    s = _normalize_separators(s)

    try:
        return float(s) * multiplier
    except ValueError as exc:
        raise MappingError(f"Khong parse duoc so tien: {value!r}") from exc


def _normalize_separators(s: str) -> str:
    """Chuan hoa dau phay/cham trong chuoi so thanh dang Python float."""
    if "," in s and "." in s:
        after_last_dot = s.split(".")[-1]
        return (
            s.replace(",", "") if len(after_last_dot) <= 2 else s.replace(".", "").replace(",", ".")
        )
    if "." in s:
        parts = s.split(".")
        return s.replace(".", "") if len(parts[-1]) == 3 and len(parts) > 1 else s
    if "," in s:
        parts = s.split(",")
        return s.replace(",", "") if len(parts[-1]) == 3 and len(parts) > 1 else s.replace(",", ".")
    return s


# ===========================================================================
# 3.5 Name
# ===========================================================================


def normalize_name(value: Any) -> str:
    """Strip + collapse whitespace. Giu nguyen case (UPPER trong nganh BH)."""
    if _is_nan_like(value):
        raise MappingError(f"Name rong/NaN: {value!r}")
    s = " ".join(str(value).split())
    if not s or s.lower() in _NAN_STRINGS:
        raise MappingError(f"Name rong: {value!r}")
    return s


# ===========================================================================
# 3.6 Plate number
# ===========================================================================


def normalize_plate(value: Any) -> str:
    """Uppercase, strip khoang trang thua. Giu dau '-' va '.'."""
    if _is_nan_like(value):
        raise MappingError(f"Bien so rong/NaN: {value!r}")
    s = _PLATE_CLEAN_RE.sub("", str(value).strip()).upper()
    if not s or s.lower() in _NAN_STRINGS:
        raise MappingError(f"Bien so rong: {value!r}")
    return s
