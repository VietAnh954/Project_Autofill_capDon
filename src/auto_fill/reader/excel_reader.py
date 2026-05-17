"""Excel attachment reader — đọc file .xlsx, detect header, rename → canonical.

Tầng Reader trong pipeline (xem ARCHITECTURE.md mục 2).
Dùng openpyxl để đọc + pandas để thao tác DataFrame.
Alias mapping: xem MAPPING.md §4. Full aliases.yaml ở task 2.3.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from auto_fill.mapper.header_detector import (
    GroupLayout,
    build_group_aware_col_map,
    detect_group_layout,
)
from auto_fill.utils.errors import ReaderError

_DATE_LIKE_RE = re.compile(
    r"^\s*("
    r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}"  # 18/5/2026, 22-11-1988
    r"|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}(\s+\d{1,2}:\d{2}(:\d{2})?)?"  # 2026-12-06 [00:00:00]
    r")\s*$"
)
_ID_LIKE_RE = re.compile(r"^[A-Z]{1,3}\d{6,}$")  # P00987499, B12345678

logger = logging.getLogger(__name__)

_MIN_FUZZY_RATIO = 85  # nguong fuzzy match (0-100)
_MAX_HEADER_SCAN_ROWS = 10  # quét tối đa 10 hàng đầu tìm header
_DATA_ROW_NUMERIC_RATIO = 0.20  # >20% cells numeric → data row (not header)

# Buyer (BMBH) canonical columns that should be forward-filled when empty
_BUYER_FILLDOWN_COLS = frozenset(
    {
        "buyer_name",
        "buyer_id_number",
        "buyer_dob",
        "buyer_phone",
        "buyer_email",
        "buyer_address",
        "buyer_relation",
    }
)


def read_excel(
    path: Path,
    aliases: dict[str, list[str]],
    sheet_name: int | str = 0,
    header_row: int | None = None,
) -> pd.DataFrame:
    """Đọc 1 file Excel attachment, trả về DataFrame với cột canonical.

    Args:
        path: Đường dẫn tới file .xlsx / .xls trong data/inbox/.
        aliases: Dict mapping canonical_name → list[alias].
        sheet_name: Tên hoặc index sheet cần đọc (mặc định sheet đầu tiên).
        header_row: 0-indexed row number to use as header. None = auto-detect.
            Useful for known formats (e.g., Affina Care 3-row header → pass 2).

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

    header_row_idx = header_row if header_row is not None else _detect_header_row(raw_df)
    logger.debug("header_detected", extra={"file": path.name, "row": header_row_idx})

    headers = [_normalize_header(str(v)) for v in raw_df.iloc[header_row_idx]]
    data_df = raw_df.iloc[header_row_idx + 1 :].copy()
    data_df.columns = pd.Index(headers)
    data_df = data_df.dropna(how="all").reset_index(drop=True)

    group_layout: GroupLayout = detect_group_layout(raw_df)
    if group_layout.order != "unknown":
        col_map = build_group_aware_col_map(headers, aliases, group_layout)
        new_cols = [col_map.get(i + 1, h) for i, h in enumerate(headers)]
        data_df.columns = pd.Index(new_cols)
        logger.debug("group_aware_rename", extra={"file": path.name, "order": group_layout.order})
    else:
        rename_map = _build_rename_map(headers, aliases)
        data_df = data_df.rename(columns=rename_map)
    data_df = _dedupe_columns(data_df, path.name)
    data_df = _filldown_buyer(data_df)

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


def _dedupe_columns(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Suffix cot canonical bi trung de tranh pandas gop thanh Series.

    Khi nhieu header raw map ve cung 1 canonical (vd 2 cot 'Ngay sinh'),
    pandas tao MultiIndex/Series → validator fail. Giai phap: giu cot dau,
    cot sau them suffix '_dup2', '_dup3'… va log warning.
    """
    seen: dict[str, int] = {}
    new_cols: list[str] = []
    duplicates: list[str] = []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_name = f"{c}_dup{seen[c]}"
            duplicates.append(c)
        else:
            seen[c] = 1
            new_name = c
        new_cols.append(new_name)
    if duplicates:
        logger.warning(
            "duplicate_canonical_columns",
            extra={"file": source_name, "duplicates": duplicates},
        )
        import click

        click.echo(
            f"[warn] {source_name}: cot canonical bi trung header → "
            f"{duplicates}. Pipeline giu cot dau, cot sau suffix '_dup'. "
            f"Hay sua header trong Excel cho khac nhau."
        )
    df.columns = pd.Index(new_cols)
    return df


def _filldown_buyer(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill BMBH columns and tag buyer groups with source_buyer_group_id.

    Pattern 3: 1 BMBH buys for N NDBH — Excel has buyer info only on the first
    row per group; subsequent rows are empty. After fill-down, all N rows share
    the same canonical buyer fields AND the same source_buyer_group_id UUID.

    Pattern 1/2 (single buyer per row): each row gets its own UUID.
    """
    cols = [c for c in _BUYER_FILLDOWN_COLS if c in df.columns]
    if not cols:
        return df
    df = df.copy()
    df[cols] = df[cols].replace("", pd.NA).replace("nan", pd.NA)

    # Assign a new UUID to every row that has original buyer data; continuation
    # rows (all BMBH cols empty) get None and will inherit via ffill.
    is_group_start = df[cols].notna().any(axis=1)
    df["source_buyer_group_id"] = [str(uuid.uuid4()) if start else None for start in is_group_start]

    df[cols] = df[cols].ffill()
    df["source_buyer_group_id"] = df["source_buyer_group_id"].ffill()
    return df


def _detect_header_row(df: pd.DataFrame) -> int:
    """Trả về index hàng header trong DataFrame.

    Heuristic:
    1. Đánh dấu mỗi hàng là "data" hay "header-like" dựa vào tỉ lệ cell numeric.
       Nếu >30% cell có thể parse thành float → data row.
    2. Tìm khối hàng liên tiếp không phải data bắt đầu từ row 0 → header block.
    3. Nếu block có 2+ hàng (Affina Care 3-row header), trả về hàng CUỐI block.
    4. Nếu block chỉ có 1 hàng → trả về hàng đó.
    5. Fallback: trả về hàng có score text cao nhất.

    Raises:
        ReaderError: Nếu không tìm được hàng hợp lệ.
    """
    scan_limit = min(_MAX_HEADER_SCAN_ROWS, len(df))

    scores: list[int] = []
    is_data_row: list[bool] = []

    for i in range(scan_limit):
        row = df.iloc[i]
        non_null = int(row.notna().sum())
        text_count = sum(1 for v in row if isinstance(v, str) and v.strip())
        scores.append(text_count * 2 + non_null)

        # A row is "data" if >20% of its filled cells look like data values:
        # numeric, date-like (dd/mm/yyyy, yyyy-mm-dd HH:MM:SS), or ID-like (P12345678).
        data_like_count = 0
        filled_count = max(1, non_null)
        for v in row:
            if isinstance(v, str) and v.strip():
                s = v.strip()
                try:
                    float(s.replace(",", "."))
                    data_like_count += 1
                    continue
                except ValueError:
                    pass
                if _DATE_LIKE_RE.match(s) or _ID_LIKE_RE.match(s):
                    data_like_count += 1
        is_data_row.append(data_like_count / filled_count > _DATA_ROW_NUMERIC_RATIO)

    if not scores or max(scores) <= 0:
        raise ReaderError("Không tìm được hàng header hợp lệ trong file.")

    # Build header block: contiguous non-data rows starting at row 0
    header_block_end = -1
    for i in range(scan_limit):
        if not is_data_row[i]:
            header_block_end = i
        else:
            break  # first data row found — stop block

    if header_block_end >= 0 and not is_data_row[header_block_end]:
        return header_block_end

    # Fallback: best-scoring row
    return scores.index(max(scores))


def _normalize_header(raw: str) -> str:
    """Normalize a cell value for use as column header.

    - Strips outer whitespace
    - Replaces newlines / tabs with a single space
    - Collapses multiple spaces
    - Removes zero-width characters
    """
    import re as _re

    cleaned = raw.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    cleaned = _re.sub(r"\s{2,}", " ", cleaned)
    cleaned = cleaned.strip()
    return cleaned


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
