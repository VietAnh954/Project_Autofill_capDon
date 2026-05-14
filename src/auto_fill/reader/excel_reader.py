"""Excel attachment reader — đọc file .xlsx, detect header, rename → canonical.

Tầng Reader trong pipeline (xem ARCHITECTURE.md mục 2).
Dùng openpyxl để đọc + pandas để thao tác DataFrame.
Alias mapping: xem MAPPING.md §4. Full aliases.yaml ở task 2.3.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from auto_fill.utils.errors import ReaderError

logger = logging.getLogger(__name__)

_MIN_FUZZY_RATIO = 85  # nguong fuzzy match (0-100)
_MAX_HEADER_SCAN_ROWS = 10  # quét tối đa 10 hàng đầu tìm header


def read_excel(
    path: Path,
    aliases: dict[str, list[str]],
    sheet_name: int | str = 0,
) -> pd.DataFrame:
    """Đọc 1 file Excel attachment, trả về DataFrame với cột canonical.

    Args:
        path: Đường dẫn tới file .xlsx / .xls trong data/inbox/.
        aliases: Dict mapping canonical_name → list[alias]. Ví dụ:
                 {"insured_name": ["họ tên", "ho va ten", ...]}.
        sheet_name: Tên hoặc index sheet cần đọc (mặc định sheet đầu tiên).

    Returns:
        DataFrame với cột theo canonical schema (MAPPING.md §2).
        Cột không map được giữ nguyên tên gốc.

    Raises:
        ReaderError: Nếu không đọc được file hoặc không tìm thấy header.
        FileNotFoundError: Nếu path không tồn tại.
    """
    if not path.exists():
        raise FileNotFoundError(f"File không tồn tại: {path}")

    try:
        raw_df = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str)
    except Exception as exc:
        raise ReaderError(f"Không đọc được file {path.name}: {exc}") from exc

    if raw_df.empty:
        raise ReaderError(f"File {path.name} không có dữ liệu.")

    header_row_idx = _detect_header_row(raw_df)
    logger.debug("header_detected", extra={"file": path.name, "row": header_row_idx})

    headers = [str(v).strip() for v in raw_df.iloc[header_row_idx]]
    data_df = raw_df.iloc[header_row_idx + 1 :].copy()
    data_df.columns = pd.Index(headers)
    data_df = data_df.dropna(how="all").reset_index(drop=True)

    rename_map = _build_rename_map(headers, aliases)
    data_df = data_df.rename(columns=rename_map)

    logger.info(
        "excel_read_ok",
        extra={
            "file": path.name,
            "rows": len(data_df),
            "cols": list(data_df.columns),
            "header_row": header_row_idx,
        },
    )
    return data_df


def _detect_header_row(df: pd.DataFrame) -> int:
    """Trả về index hàng header trong DataFrame (raw, không có cột tên).

    Heuristic: hàng đầu có nhiều cell text nhất (và ít NaN nhất)
    trong _MAX_HEADER_SCAN_ROWS hàng đầu.

    Raises:
        ReaderError: Nếu không tìm được hàng hợp lệ.
    """
    scan_limit = min(_MAX_HEADER_SCAN_ROWS, len(df))
    best_row = 0
    best_score = -1

    for i in range(scan_limit):
        row_values = df.iloc[i]
        non_null = row_values.notna().sum()
        text_count = sum(1 for v in row_values if isinstance(v, str) and v.strip())
        score = text_count * 2 + non_null  # ưu tiên text cells
        if score > best_score:
            best_score = score
            best_row = i

    if best_score <= 0:
        raise ReaderError("Không tìm được hàng header hợp lệ trong file.")
    return best_row


def _build_rename_map(
    headers: list[str],
    aliases: dict[str, list[str]],
) -> dict[str, str]:
    """Tạo dict {original_header: canonical_name} dùng exact + fuzzy match.

    Priority: exact match > fuzzy match > giữ nguyên.
    """
    # Pre-build lookup: alias_lower → canonical
    exact_lookup: dict[str, str] = {}
    for canonical, alias_list in aliases.items():
        for alias in alias_list:
            exact_lookup[alias.lower().strip()] = canonical

    rename_map: dict[str, str] = {}
    for header in headers:
        normalized = header.lower().strip()

        # 1. Exact match
        if normalized in exact_lookup:
            rename_map[header] = exact_lookup[normalized]
            continue

        # 2. Fuzzy match
        best_canonical = _fuzzy_match(normalized, exact_lookup)
        if best_canonical:
            rename_map[header] = best_canonical

        # 3. No match → column stays with original name (no entry in map)

    return rename_map


def _fuzzy_match(query: str, exact_lookup: dict[str, str]) -> str | None:
    """Fuzzy match query lên tất cả alias, trả về canonical nếu ratio >= ngưỡng."""
    best_ratio: float = 0.0
    best_canonical: str | None = None

    for alias, canonical in exact_lookup.items():
        ratio = fuzz.ratio(query, alias)
        if ratio > best_ratio:
            best_ratio = ratio
            best_canonical = canonical

    return best_canonical if best_ratio >= _MIN_FUZZY_RATIO else None
