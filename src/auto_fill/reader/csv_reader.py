"""CSV attachment reader — doc file .csv, rename column -> canonical.

Tuong tu excel_reader nhung khong can detect header row (CSV luon co header row 1).
Tham khao MAPPING.md §4 cho alias mapping.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from auto_fill.reader.excel_reader import _build_rename_map
from auto_fill.utils.errors import ReaderError

logger = logging.getLogger(__name__)

_CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1258", "latin-1")


def read_csv(
    path: Path,
    aliases: dict[str, list[str]],
    delimiter: str = ",",
) -> pd.DataFrame:
    """Doc file CSV attachment, tra ve DataFrame voi cot canonical.

    Thu lan luot cac encoding pho bien cho file CSV Viet Nam.

    Args:
        path: Duong dan toi file .csv trong data/inbox/.
        aliases: Dict mapping canonical_name -> list[alias].
        delimiter: Ky tu phan cach (mac dinh: dau phay).

    Returns:
        DataFrame voi cot theo canonical schema.
        Cot khong map duoc giu nguyen ten goc.

    Raises:
        ReaderError: Neu khong doc duoc file voi bat ky encoding nao.
        FileNotFoundError: Neu path khong ton tai.
    """
    if not path.exists():
        raise FileNotFoundError(f"File khong ton tai: {path}")

    raw_df: pd.DataFrame | None = None
    last_exc: Exception | None = None

    for encoding in _CSV_ENCODINGS:
        try:
            raw_df = pd.read_csv(
                path,
                delimiter=delimiter,
                dtype=str,
                encoding=encoding,
                skip_blank_lines=True,
            )
            logger.debug("csv_encoding_ok", extra={"file": path.name, "encoding": encoding})
            break
        except UnicodeDecodeError as exc:
            last_exc = exc
        except Exception as exc:
            raise ReaderError(f"Khong doc duoc CSV {path.name}: {exc}") from exc

    if raw_df is None:
        raise ReaderError(f"Khong doc duoc {path.name} voi bat ky encoding nao: {last_exc}")

    if raw_df.empty:
        raise ReaderError(f"File {path.name} khong co du lieu.")

    raw_df = raw_df.dropna(how="all").reset_index(drop=True)
    headers = list(raw_df.columns)
    rename_map = _build_rename_map(headers, aliases)
    result_df = raw_df.rename(columns=rename_map)

    logger.info(
        "csv_read_ok",
        extra={
            "file": path.name,
            "rows": len(result_df),
            "cols": list(result_df.columns),
        },
    )
    return result_df
