"""Classifier — quyet dinh sheet dich cho moi MailMessage / DataFrame.

Priority: sender hint > subject keyword > column signature > fallback.
Xem MAPPING.md §5.

MVP: chi support "travel" (Du lich). Cac sheet khac → ClassifierError.
"""

from __future__ import annotations

import logging
import re

from auto_fill.config.sheet_registry import SheetInfo, by_alias
from auto_fill.utils.errors import ClassifierError

logger = logging.getLogger(__name__)

# --- Subject keyword rules (MAPPING §5) ---
_SUBJECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"du\s*l[iị]ch|travel", re.IGNORECASE), "travel"),
    (re.compile(r"s[uứ]c\s*kh[oỏôõò]e|health|sk\b", re.IGNORECASE), "health"),
    (re.compile(r"[oôõ]\s*t[oô]|oto|auto|car\b", re.IGNORECASE), "auto"),
    (re.compile(r"xe\s*m[aáà]y|tnds\s*xm", re.IGNORECASE), "motorbike"),
    (re.compile(r"bhyt|bhxh", re.IGNORECASE), "bhyt_bhxh"),
    (re.compile(r"hssv|h[oọ]c\s*sinh|sinh\s*vi[eê]n", re.IGNORECASE), "student"),
]

# --- Column signature hints ---
_VEHICLE_COLS = frozenset({"plate_number", "frame_number", "engine_number"})
_TRAVEL_COLS = frozenset({"trip_start", "trip_end", "destination"})
_HEALTH_COLS = frozenset({"outpatient", "dental", "maternity"})


def classify(
    subject: str,
    sender_email: str,
    sender_hints: dict[str, str] | None = None,
    df_columns: list[str] | None = None,
) -> SheetInfo:
    """Quyet dinh SheetInfo cho mot mail/record.

    Args:
        subject: Subject cua mail.
        sender_email: Email nguoi gui (lowercase).
        sender_hints: Dict mapping email → sheet alias tu .env
                      (vi du {"daily@pti.com.vn": "travel"}).
        df_columns: Danh sach cot cua DataFrame input (canonical names).

    Returns:
        SheetInfo cua sheet dich.

    Raises:
        ClassifierError: Neu khong xac dinh duoc sheet.
    """
    # Priority 1: Sender hint
    if sender_hints:
        alias = sender_hints.get(sender_email.lower())
        if alias:
            try:
                sheet = by_alias(alias)
                logger.info("classified_by_sender", extra={"sender": sender_email, "sheet": alias})
                return sheet
            except KeyError:
                logger.warning("unknown_sender_alias", extra={"alias": alias})

    # Priority 2: Subject keyword
    for pattern, alias in _SUBJECT_RULES:
        if pattern.search(subject):
            try:
                sheet = by_alias(alias)
                logger.info(
                    "classified_by_subject",
                    extra={"subject": subject[:50], "sheet": alias},
                )
                return sheet
            except KeyError:
                pass

    # Priority 3: Column signature
    if df_columns:
        col_set = set(df_columns)
        alias = _classify_by_columns(col_set)
        if alias:
            try:
                sheet = by_alias(alias)
                logger.info("classified_by_columns", extra={"sheet": alias})
                return sheet
            except KeyError:
                pass

    raise ClassifierError(
        f"Khong xac dinh duoc sheet dich. " f"Subject: {subject!r} | Sender: {sender_email!r}"
    )


def _classify_by_columns(col_set: set[str]) -> str | None:
    """Tra ve alias sheet dua tren column signature, hoac None neu khong ro."""
    if col_set & _TRAVEL_COLS:
        return "travel"
    if col_set & _HEALTH_COLS:
        return "health"
    if col_set & _VEHICLE_COLS:
        # Phan biet oto/xemay
        return "motorbike" if "seats" not in col_set else "auto"
    return None
