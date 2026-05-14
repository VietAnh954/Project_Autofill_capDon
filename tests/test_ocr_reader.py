"""Unit tests cho ocr_reader — mock tesseract va pdfplumber."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from auto_fill.reader.ocr_reader import _parse_kv_text, is_tesseract_available, read_pdf_ocr
from auto_fill.utils.errors import ReaderError

ALIASES: dict[str, list[str]] = {
    "insured_name": ["họ và tên", "ho va ten"],
    "insured_id_number": ["cccd", "cmnd"],
    "premium": ["phí bảo hiểm", "tổng phí"],
}


class TestIsTesseractAvailable:
    def test_returns_false_when_not_found(self) -> None:
        with patch("auto_fill.reader.ocr_reader.shutil.which", return_value=None):
            assert is_tesseract_available() is False

    def test_returns_true_when_found(self) -> None:
        with patch(
            "auto_fill.reader.ocr_reader.shutil.which",
            return_value="C:/tesseract/tesseract.exe",
        ):
            assert is_tesseract_available() is True


class TestReadPdfOcr:
    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_pdf_ocr(tmp_path / "missing.pdf", aliases=ALIASES)

    def test_raises_reader_error_when_tesseract_not_installed(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "scan.pdf"
        pdf_path.touch()
        with (
            patch("auto_fill.reader.ocr_reader.is_tesseract_available", return_value=False),
            pytest.raises(ReaderError, match="Tesseract"),
        ):
            read_pdf_ocr(pdf_path, aliases=ALIASES)

    def test_ocr_extracts_kv_text(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "scan.pdf"
        pdf_path.touch()

        mock_image = MagicMock()
        mock_page = MagicMock()
        mock_page.to_image.return_value.original = mock_image
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        ocr_text = "Họ và tên: Nguyen Van A\nPhí bảo hiểm: 1500000"

        with (
            patch("auto_fill.reader.ocr_reader.is_tesseract_available", return_value=True),
            patch("auto_fill.reader.ocr_reader.pdfplumber.open", return_value=mock_pdf),
            patch(
                "auto_fill.reader.ocr_reader.pytesseract.image_to_string",
                return_value=ocr_text,
            ),
        ):
            df = read_pdf_ocr(pdf_path, aliases=ALIASES)

        assert "insured_name" in df.columns
        assert df["insured_name"].iloc[0] == "Nguyen Van A"
        assert "premium" in df.columns

    def test_raises_reader_error_when_no_fields_extracted(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "blank.pdf"
        pdf_path.touch()

        mock_image = MagicMock()
        mock_page = MagicMock()
        mock_page.to_image.return_value.original = mock_image
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with (
            patch("auto_fill.reader.ocr_reader.is_tesseract_available", return_value=True),
            patch("auto_fill.reader.ocr_reader.pdfplumber.open", return_value=mock_pdf),
            patch(
                "auto_fill.reader.ocr_reader.pytesseract.image_to_string",
                return_value="lorem ipsum no colon here",
            ),
            pytest.raises(ReaderError),
        ):
            read_pdf_ocr(pdf_path, aliases=ALIASES)

    def test_pdfplumber_exception_wrapped(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "bad.pdf"
        pdf_path.touch()

        with (
            patch("auto_fill.reader.ocr_reader.is_tesseract_available", return_value=True),
            patch(
                "auto_fill.reader.ocr_reader.pdfplumber.open",
                side_effect=Exception("corrupt"),
            ),
            pytest.raises(ReaderError, match="corrupt"),
        ):
            read_pdf_ocr(pdf_path, aliases=ALIASES)


class TestParseKvText:
    def test_colon_separator(self) -> None:
        record: dict[str, str] = {}
        _parse_kv_text("Họ và tên: Nguyen Van A\nCCCD: 012345678901", record)
        assert record["Họ và tên"] == "Nguyen Van A"
        assert record["CCCD"] == "012345678901"

    def test_dash_separator(self) -> None:
        record: dict[str, str] = {}
        _parse_kv_text("Họ và tên - Nguyen Van A", record)
        assert record["Họ và tên"] == "Nguyen Van A"

    def test_empty_lines_skipped(self) -> None:
        record: dict[str, str] = {}
        _parse_kv_text("\n\n\nHọ và tên: A\n\n", record)
        assert len(record) == 1

    def test_first_occurrence_wins(self) -> None:
        record: dict[str, str] = {}
        _parse_kv_text("Họ và tên: A\nHọ và tên: B", record)
        assert record["Họ và tên"] == "A"

    def test_line_without_separator_ignored(self) -> None:
        record: dict[str, str] = {}
        _parse_kv_text("Khong co sep\nHọ và tên: A", record)
        assert len(record) == 1
