"""PDF attachment reader — trich xuat du lieu tu file .pdf dung pdfplumber.

Chien luoc:
  1. Tim table dau tien trong PDF (pdfplumber extract_tables).
  2. Neu co table → dung row dau lam header, map canonical nhu Excel reader.
  3. Neu khong co table → trich text thuan, thu parse key: value.
  4. Neu ca hai deu that bai → raise ReaderError → file vao data/failed/.

Xem MAPPING.md §4 cho alias mapping.
Xem TODO #2.5 cho OCR fallback (pytesseract) — chua implement.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from auto_fill.reader.excel_reader import _build_rename_map
from auto_fill.utils.errors import ReaderError

logger = logging.getLogger(__name__)

_MAX_PAGES = 20


def read_pdf(
    path: Path,
    aliases: dict[str, list[str]],
    page_limit: int = _MAX_PAGES,
) -> pd.DataFrame:
    """Trich xuat du lieu tu file PDF, tra ve DataFrame voi cot canonical.

    Thu table extraction truoc (structured PDF).
    Fallback sang key-value text parsing neu khong co table.

    Args:
        path: Duong dan toi file .pdf trong data/inbox/.
        aliases: Dict mapping canonical_name → list[alias].
        page_limit: Gioi han so trang xu ly (tranh file qua lon).

    Returns:
        DataFrame voi cot theo canonical schema.

    Raises:
        ReaderError: Neu khong trich xuat duoc du lieu hop le.
        FileNotFoundError: Neu path khong ton tai.
    """
    if not path.exists():
        raise FileNotFoundError(f"File khong ton tai: {path}")

    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages[:page_limit]

            # Strategy 1: structured table
            df = _try_extract_tables(pages, aliases, path.name)
            if df is not None and not df.empty:
                logger.info(
                    "pdf_table_extracted",
                    extra={"file": path.name, "rows": len(df), "strategy": "table"},
                )
                return df

            # Strategy 2: key-value text parse
            df = _try_extract_keyvalue(pages, aliases, path.name)
            if df is not None and not df.empty:
                logger.info(
                    "pdf_kv_extracted",
                    extra={"file": path.name, "rows": len(df), "strategy": "key_value"},
                )
                return df

    except ReaderError:
        raise
    except Exception as exc:
        raise ReaderError(f"Khong doc duoc PDF {path.name}: {exc}") from exc

    # Strategy 3: OCR fallback (yeu cau Tesseract binary)
    logger.warning("pdf_fallback_ocr", extra={"file": path.name})
    from auto_fill.reader.ocr_reader import read_pdf_ocr

    return read_pdf_ocr(path, aliases=aliases, page_limit=page_limit)


def _try_extract_tables(
    pages: list[Any],
    aliases: dict[str, list[str]],
    filename: str,
) -> pd.DataFrame | None:
    """Trich xuat bang dau tien tim thay trong cac trang.

    Returns None neu khong co bang nao.
    """
    for page in pages:
        tables = page.extract_tables()
        if not tables:
            continue

        table = tables[0]
        if len(table) < 2:
            continue

        # Row 0 la header
        raw_headers = [str(cell).strip() if cell else "" for cell in table[0]]
        rows = []
        for row in table[1:]:
            cells = [str(c).strip() if c is not None else "" for c in row]
            # Bo qua dong toan trong
            if all(c == "" for c in cells):
                continue
            rows.append(dict(zip(raw_headers, cells, strict=False)))

        if not rows:
            continue

        df = pd.DataFrame(rows)
        rename_map = _build_rename_map(raw_headers, aliases)
        df = df.rename(columns=rename_map)
        logger.debug("pdf_table_found", extra={"file": filename, "cols": raw_headers})
        return df

    return None


def _try_extract_keyvalue(
    pages: list[Any],
    aliases: dict[str, list[str]],
    filename: str,
) -> pd.DataFrame | None:
    """Parse text thuan theo pattern "Key: Value" hoac "Key - Value".

    Phuong phap nay danh cho phieu co dinh dang form (moi dong 1 truong).
    Returns None neu khong parse duoc truong nao.
    """
    record: dict[str, str] = {}

    for page in pages:
        text = page.extract_text() or ""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Thu phan tach "Key: Value" hoac "Key - Value"
            for sep in (":", " - ", "-", "\t"):
                if sep in line:
                    parts = line.split(sep, 1)
                    if len(parts) == 2:
                        key, value = parts[0].strip(), parts[1].strip()
                        if key and value:
                            record[key] = value
                            break

    if not record:
        logger.debug("pdf_no_kv_found", extra={"file": filename})
        return None

    raw_headers = list(record.keys())
    rename_map = _build_rename_map(raw_headers, aliases)

    renamed = {rename_map.get(k, k): v for k, v in record.items()}
    df = pd.DataFrame([renamed])
    logger.debug("pdf_kv_parsed", extra={"file": filename, "fields": list(renamed.keys())})
    return df
