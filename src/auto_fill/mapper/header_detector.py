"""header_detector — detect BMBH-first vs NDBH-first column layout.

When an input file has group headers ('Ben mua bao hiem' / 'Nguoi duoc bao hiem'),
this module detects which group appears first (left side) and provides a
group-aware rename map to correctly disambiguate shared column names like
'Ngay sinh' (can be insured_dob or buyer_dob depending on group context).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd
from rapidfuzz import fuzz

GroupOrder = Literal["bmbh_first", "insured_first", "unknown"]

# Match on ASCII-normalised text to avoid Vietnamese diacritic variants.
_BMBH_RE = re.compile(r"ben\s*mua|bmbh", re.IGNORECASE)
_INSURED_RE = re.compile(r"nguoi\s*duoc|ndbh", re.IGNORECASE)


def _norm(s: str) -> str:
    """Strip diacritics and special letters → ASCII-safe string for regex matching.

    Handles Vietnamese characters that do not decompose via NFD (đ/Đ).
    """
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# When a column is in the BMBH group and the standard alias resolves to insured_X,
# remap to the equivalent buyer_X field.
_INSURED_TO_BUYER: dict[str, str] = {
    "insured_dob": "buyer_dob",
    "insured_name": "buyer_name",
    "insured_id_number": "buyer_id_number",
    "insured_phone": "buyer_phone",
    "insured_email": "buyer_email",
    "insured_address": "buyer_address",
    "insured_gender": "buyer_gender",
}

_MIN_FUZZY_RATIO = 85
_MAX_SCAN_ROWS = 5


@dataclass(frozen=True)
class GroupLayout:
    """BMBH/NDBH group position info derived from the input file's group header row."""

    order: GroupOrder
    bmbh_cols: frozenset[int] = field(default_factory=frozenset)  # 1-indexed Excel cols
    insured_cols: frozenset[int] = field(default_factory=frozenset)  # 1-indexed Excel cols


def detect_group_layout(raw_df: pd.DataFrame) -> GroupLayout:
    """Scan the first rows of *raw_df* for BMBH/NDBH group header text.

    Args:
        raw_df: Raw DataFrame from pd.read_excel(..., header=None).

    Returns:
        GroupLayout with 1-indexed column sets. When no group headers are
        found, order='unknown' and both col sets are empty.
    """
    n_cols = raw_df.shape[1]
    bmbh_col: int | None = None  # 0-indexed position in DataFrame
    insured_col: int | None = None

    for row_idx in range(min(_MAX_SCAN_ROWS, len(raw_df))):
        for col_idx in range(n_cols):
            val = raw_df.iat[row_idx, col_idx]
            if not isinstance(val, str):
                continue
            s = _norm(val.strip())
            if bmbh_col is None and _BMBH_RE.search(s):
                bmbh_col = col_idx
            if insured_col is None and _INSURED_RE.search(s):
                insured_col = col_idx
        if bmbh_col is not None and insured_col is not None:
            break

    if bmbh_col is None or insured_col is None:
        return GroupLayout(order="unknown")

    bmbh_1 = bmbh_col + 1  # convert to 1-indexed (Excel convention)
    insured_1 = insured_col + 1

    if bmbh_1 < insured_1:
        bmbh_set = frozenset(range(bmbh_1, insured_1))  # [bmbh_1, insured_1)
        insured_set = frozenset(range(insured_1, n_cols + 1))  # [insured_1, end]
        return GroupLayout(order="bmbh_first", bmbh_cols=bmbh_set, insured_cols=insured_set)
    else:
        insured_set = frozenset(range(insured_1, bmbh_1))  # [insured_1, bmbh_1)
        bmbh_set = frozenset(range(bmbh_1, n_cols + 1))
        return GroupLayout(order="insured_first", bmbh_cols=bmbh_set, insured_cols=insured_set)


def build_group_aware_col_map(
    headers: list[str],
    aliases: dict[str, list[str]],
    layout: GroupLayout,
) -> dict[int, str]:
    """Build a position-indexed canonical map using BMBH/NDBH group context.

    Returns a dict {1-indexed Excel col → canonical_name}. Using column position
    (not header string) as key correctly handles duplicate headers like 'Ngay sinh'
    that appear in both BMBH and NDBH groups.

    For columns within the BMBH group: if the standard alias lookup resolves to an
    insured_X canonical, remap to the equivalent buyer_X.

    Args:
        headers: Normalized header strings (0-indexed; position i = Excel col i+1).
        aliases: Full aliases dict {canonical_name: [alias, ...]}.
        layout: GroupLayout from detect_group_layout().

    Returns:
        {1-indexed_col: canonical_name}
    """
    exact_lookup: dict[str, str] = {}
    for canonical, alias_list in aliases.items():
        for alias in alias_list:
            exact_lookup[alias.lower().strip()] = canonical

    col_map: dict[int, str] = {}
    for i, header in enumerate(headers):
        excel_col = i + 1  # 1-indexed
        normalized = header.lower().strip()

        resolved: str | None = exact_lookup.get(normalized) or _fuzzy_match(
            normalized, exact_lookup
        )
        if not resolved:
            continue

        if excel_col in layout.bmbh_cols and resolved in _INSURED_TO_BUYER:
            resolved = _INSURED_TO_BUYER[resolved]

        col_map[excel_col] = resolved

    return col_map


def _fuzzy_match(query: str, exact_lookup: dict[str, str]) -> str | None:
    best_ratio: float = 0.0
    best_canonical: str | None = None
    for alias, canonical in exact_lookup.items():
        ratio = fuzz.ratio(query, alias)
        if ratio > best_ratio:
            best_ratio = ratio
            best_canonical = canonical
    return best_canonical if best_ratio >= _MIN_FUZZY_RATIO else None
