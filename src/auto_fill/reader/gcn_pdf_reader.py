"""Parse GCN (Giấy Chứng Nhận) PDF from TCGI/BSH/BIC insurers.

Extracts 7 canonical fields from TYPE B attachment PDFs (MAIL_PATTERNS.md §2).
Tested against TCGI Affina Care GCN format (pdfplumber text extraction).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

# ── Regex patterns ─────────────────────────────────────────────────────────

_RE_GCN_NUMBER = re.compile(r"^Số:\s*(\S+)", re.MULTILINE)

_RE_BUYER_NAME = re.compile(
    r"Họ tên:\s*(.+?)\s+Ngày tháng năm sinh",
    re.IGNORECASE,
)

_RE_INSURED_NAME = re.compile(
    r"Họ Tên:\s*(.+?)\s+Ngày sinh",
    re.IGNORECASE,
)

_RE_PREMIUM = re.compile(
    r"Phí bảo hiểm:\s*([\d.,]+)\s*VN[ĐD]",
    re.IGNORECASE,
)

_RE_DURATION = re.compile(
    r"từ\s+\d{1,2}:\d{2}\s+(\d{2}/\d{2}/\d{4})\s+đến\s+\d{1,2}:\d{2}\s+(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)

_RE_PRODUCT = re.compile(
    r"GIẤY CHỨNG NHẬN\s*\n+(.+)",
    re.IGNORECASE,
)

_RE_PLAN = re.compile(r"GÓI\s+(B\d+|[A-Z]\d+)", re.IGNORECASE)


# ── Data model ──────────────────────────────────────────────────────────────


@dataclass
class GcnRecord:
    """Parsed fields from a single GCN PDF."""

    gcn_number: str = ""
    buyer_name: str = ""
    insured_name: str = ""
    premium: str = ""
    valid_from: str = ""
    valid_to: str = ""
    product: str = ""
    plan: str = ""

    def is_complete(self) -> bool:
        """Return True when all 7 mandatory fields are non-empty."""
        mandatory = (
            self.gcn_number,
            self.buyer_name,
            self.insured_name,
            self.premium,
            self.valid_from,
            self.valid_to,
            self.product,
        )
        return all(mandatory)


# ── Parser ──────────────────────────────────────────────────────────────────


def parse_gcn_pdf(pdf_path: str | Path) -> GcnRecord:
    """Extract GCN fields from a TCGI/BSH-style PDF.

    Args:
        pdf_path: Path to the GCN PDF file.

    Returns:
        GcnRecord with populated fields. Fields that cannot be found remain "".

    Raises:
        FileNotFoundError: if pdf_path does not exist.
        ValueError: if the file is not a readable PDF.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    record = GcnRecord()

    with pdfplumber.open(path) as pdf:
        pages_text = [p.extract_text() or "" for p in pdf.pages]

    full_text = "\n".join(pages_text)

    _extract_page1_fields(pages_text[0] if pages_text else "", record)

    for page_text in pages_text[1:]:
        if "Họ Tên:" in page_text and not record.insured_name:
            _extract_insured(page_text, record)
        if "GÓI" in page_text.upper() and not record.plan:
            _extract_plan(page_text, record)

    if not record.plan:
        _extract_plan(full_text, record)

    return record


def _extract_page1_fields(text: str, record: GcnRecord) -> None:
    m = _RE_GCN_NUMBER.search(text)
    if m:
        record.gcn_number = m.group(1).strip()

    m = _RE_BUYER_NAME.search(text)
    if m:
        record.buyer_name = m.group(1).strip()

    m = _RE_PREMIUM.search(text)
    if m:
        record.premium = m.group(1).strip()

    m = _RE_DURATION.search(text)
    if m:
        record.valid_from = m.group(1).strip()
        record.valid_to = m.group(2).strip()

    m = _RE_PRODUCT.search(text)
    if m:
        record.product = m.group(1).strip()


def _extract_insured(text: str, record: GcnRecord) -> None:
    m = _RE_INSURED_NAME.search(text)
    if m:
        record.insured_name = m.group(1).strip()


def _extract_plan(text: str, record: GcnRecord) -> None:
    m = _RE_PLAN.search(text)
    if m:
        record.plan = m.group(1).upper()
