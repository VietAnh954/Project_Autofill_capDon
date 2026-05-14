"""OCR fallback reader — dung pytesseract de doc file PDF da scan.

Duoc goi boi pdf_reader khi ca table extraction va key-value parse deu that bai.
Yeu cau: Tesseract binary phai duoc cai tren he thong.
  Windows: https://github.com/UB-Mannheim/tesseract/wiki
  Linux:   sudo apt install tesseract-ocr tesseract-ocr-vie

Xem TODO #2.5, MAPPING.md §4.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber
import pytesseract

from auto_fill.reader.excel_reader import _build_rename_map
from auto_fill.utils.errors import ReaderError

logger = logging.getLogger(__name__)

_TESSERACT_LANGS = "vie+eng"  # Vietnamese + English
_MAX_PAGES = 20


def is_tesseract_available() -> bool:
    """Kiem tra Tesseract binary co san hay khong."""
    return shutil.which("tesseract") is not None


def read_pdf_ocr(
    path: Path,
    aliases: dict[str, list[str]],
    page_limit: int = _MAX_PAGES,
    lang: str = _TESSERACT_LANGS,
) -> pd.DataFrame:
    """Trich xuat du lieu tu PDF da scan bang OCR (pytesseract).

    Moi trang PDF duoc chuyen sang anh (PIL Image) roi dua qua Tesseract.
    Text thu duoc parse theo pattern "Key: Value" nhu pdf_reader._try_extract_keyvalue.

    Args:
        path: Duong dan toi file .pdf trong data/inbox/.
        aliases: Dict mapping canonical_name → list[alias].
        page_limit: Gioi han so trang xu ly.
        lang: Ngon ngu Tesseract (mac dinh: vie+eng).

    Returns:
        DataFrame voi cot theo canonical schema.

    Raises:
        ReaderError: Neu Tesseract chua cai, hoac khong trich xuat duoc gi.
        FileNotFoundError: Neu path khong ton tai.
    """
    if not path.exists():
        raise FileNotFoundError(f"File khong ton tai: {path}")

    if not is_tesseract_available():
        raise ReaderError(
            "Tesseract chua duoc cai tren he thong. "
            "Xem huong dan tai: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    record: dict[str, str] = {}

    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages[:page_limit]
            for page in pages:
                pil_image: Any = page.to_image(resolution=200).original
                text: str = pytesseract.image_to_string(pil_image, lang=lang)
                _parse_kv_text(text, record)
    except ReaderError:
        raise
    except Exception as exc:
        raise ReaderError(f"OCR that bai cho {path.name}: {exc}") from exc

    if not record:
        raise ReaderError(
            f"OCR khong trich xuat duoc truong nao tu {path.name}. "
            "File co the la anh chat luong thap hoac khong co text."
        )

    raw_headers = list(record.keys())
    rename_map = _build_rename_map(raw_headers, aliases)
    renamed = {rename_map.get(k, k): v for k, v in record.items()}

    logger.info(
        "pdf_ocr_extracted",
        extra={"file": path.name, "fields": list(renamed.keys())},
    )
    return pd.DataFrame([renamed])


def _parse_kv_text(text: str, record: dict[str, str]) -> None:
    """Parse "Key: Value" lines tu OCR text, update record in-place."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for sep in (":", " - ", "\t"):
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    if key and value and key not in record:
                        record[key] = value
                    break
