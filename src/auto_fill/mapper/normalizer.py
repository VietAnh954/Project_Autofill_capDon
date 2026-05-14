"""Normalizer — chuan hoa gia tri field theo MAPPING.md §3.

Rules:
  §3.1 Date     — parse nhieu format, tra datetime.date
  §3.2 ID       — strip/uppercase, validate length
  §3.3 Phone    — chuan hoa 10 chu so bat dau 0
  §3.4 Money    — parse VN float (dau phay/cham)
  §3.5 Name     — strip + collapse whitespace
  §3.6 Plate    — uppercase, strip ky tu thua
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from auto_fill.utils.errors import MappingError

_DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%y",
    "%d-%m-%y",
]

_EXCEL_EPOCH = date(1899, 12, 30)

_PHONE_RE = re.compile(r"[\s\-\.\(\)]+")
_PLATE_CLEAN_RE = re.compile(r"[\s]+")
_MONEY_NON_NUMERIC_RE = re.compile(r"[^\d,\.kmb]", re.IGNORECASE)


# ===========================================================================
# §3.1 Date
# ===========================================================================


def normalize_date(value: Any) -> date:
    """Parse nhieu dinh dang ngay → datetime.date.

    Args:
        value: Chuoi ngay hoac so (Excel serial).

    Returns:
        datetime.date da parse.

    Raises:
        MappingError: Neu khong parse duoc.
    """
    if value is None or (isinstance(value, float) and str(value) in ("nan", "inf")):
        raise MappingError(f"Gia tri ngay rong: {value!r}")

    if isinstance(value, datetime | date):
        return value.date() if isinstance(value, datetime) else value

    if isinstance(value, int | float):
        return _from_excel_serial(int(value))

    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        raise MappingError(f"Chuoi ngay rong: {s!r}")

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


def _from_excel_serial(serial: int) -> date:
    from datetime import timedelta

    if serial < 1:
        raise MappingError(f"Excel serial khong hop le: {serial}")
    return _EXCEL_EPOCH + timedelta(days=serial)


# ===========================================================================
# §3.2 CCCD / CMND / Passport
# ===========================================================================


def normalize_id_number(value: Any) -> str:
    """Strip whitespace, uppercase, validate CCCD/CMND length.

    CCCD = 12 chu so, CMND cu = 9 chu so, Passport = 6-9 ky tu alphanumeric.

    Returns:
        Chuoi ID da chuan hoa.

    Raises:
        MappingError: Neu value rong.
    """
    if value is None:
        raise MappingError("ID number la None.")
    s = str(value).strip().upper().replace(" ", "").replace("-", "")
    if not s or s.lower() in ("nan", "none"):
        raise MappingError(f"ID number rong: {value!r}")
    return s


def validate_id_number(id_str: str) -> bool:
    """Kiem tra id_str co hop le khong (khong raise, chi tra bool)."""
    if id_str.isdigit():
        return len(id_str) in (9, 12)
    return 6 <= len(id_str) <= 9 and id_str.isalnum()


# ===========================================================================
# §3.3 Phone
# ===========================================================================


def normalize_phone(value: Any) -> str:
    """Chuan hoa SĐT Viet Nam → 10 chu so bat dau 0.

    Doi +84xxx → 0xxx, 84xxx → 0xxx.

    Returns:
        Chuoi SĐT da chuan hoa.

    Raises:
        MappingError: Neu khong chuan hoa duoc.
    """
    if value is None:
        raise MappingError("Phone la None.")
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        raise MappingError(f"Phone rong: {value!r}")

    s = _PHONE_RE.sub("", s)

    if s.startswith("+84"):
        s = "0" + s[3:]
    elif s.startswith("84") and len(s) == 11:
        s = "0" + s[2:]

    if not (s.isdigit() and len(s) == 10 and s.startswith("0")):
        raise MappingError(f"SĐT khong hop le sau chuan hoa: {s!r} (goc: {value!r})")
    return s


# ===========================================================================
# §3.4 Money
# ===========================================================================


def normalize_money(value: Any) -> float:
    """Parse so tien VND tu nhieu dinh dang.

    Ho tro: "1,500,000", "1.500.000", "1.500.000 VND", "1.5M", "1500000".

    Returns:
        float (VND).

    Raises:
        MappingError: Neu khong parse duoc.
    """
    if value is None:
        raise MappingError("Money la None.")

    if isinstance(value, int | float):
        if str(value).lower() in ("nan", "inf"):
            raise MappingError(f"Money la NaN/Inf: {value!r}")
        return float(value)

    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
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
# §3.5 Name
# ===========================================================================


def normalize_name(value: Any) -> str:
    """Strip + collapse whitespace. Giu nguyen case (UPPER trong nganh BH).

    Raises:
        MappingError: Neu value rong.
    """
    if value is None:
        raise MappingError("Name la None.")
    s = " ".join(str(value).split())
    if not s or s.lower() in ("nan", "none"):
        raise MappingError(f"Name rong: {value!r}")
    return s


# ===========================================================================
# §3.6 Plate number
# ===========================================================================


def normalize_plate(value: Any) -> str:
    """Uppercase, strip khoang trang thua. Giu dau '-' va '.'.

    Raises:
        MappingError: Neu value rong.
    """
    if value is None:
        raise MappingError("Bien so la None.")
    s = _PLATE_CLEAN_RE.sub("", str(value).strip()).upper()
    if not s or s.lower() in ("NAN", "NONE"):
        raise MappingError(f"Bien so rong: {value!r}")
    return s
