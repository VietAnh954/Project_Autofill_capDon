"""Unit tests cho pdf_reader — mock pdfplumber de tranh phu thuoc file thuc."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from auto_fill.reader.pdf_reader import _try_extract_keyvalue, _try_extract_tables, read_pdf
from auto_fill.utils.errors import ReaderError

ALIASES: dict[str, list[str]] = {
    "insured_name": ["họ và tên", "ho va ten", "tên khách hàng"],
    "insured_id_number": ["cccd", "cmnd", "số cccd"],
    "insured_dob": ["ngày sinh", "dob"],
    "premium": ["phí bảo hiểm", "tổng phí"],
    "destination": ["nơi đến", "destination"],
}


def _mock_pdf(pages: list[Any]) -> MagicMock:
    """Tao mock pdfplumber.open context manager."""
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = pages
    return mock_pdf


def _mock_page_with_table(table_data: list[list[Any]]) -> MagicMock:
    page = MagicMock()
    page.extract_tables.return_value = [table_data]
    page.extract_text.return_value = ""
    return page


def _mock_page_with_text(text: str) -> MagicMock:
    page = MagicMock()
    page.extract_tables.return_value = []
    page.extract_text.return_value = text
    return page


def _mock_page_empty() -> MagicMock:
    page = MagicMock()
    page.extract_tables.return_value = []
    page.extract_text.return_value = ""
    return page


class TestReadPdfFileNotFound:
    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_pdf(tmp_path / "nonexistent.pdf", aliases=ALIASES)


class TestReadPdfTableStrategy:
    def test_table_extracted_and_renamed(self, tmp_path: Path) -> None:
        table = [
            ["Họ và tên", "CCCD", "Nơi đến", "Phí bảo hiểm"],
            ["Nguyen Van A", "012345678901", "Singapore", "1500000"],
            ["Tran Thi B", "098765432100", "Thai Lan", "2000000"],
        ]
        page = _mock_page_with_table(table)
        fake_pdf = _mock_pdf([page])

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with patch("auto_fill.reader.pdf_reader.pdfplumber.open", return_value=fake_pdf):
            df = read_pdf(pdf_path, aliases=ALIASES)

        assert len(df) == 2
        assert "insured_name" in df.columns
        assert "destination" in df.columns
        assert df["insured_name"].iloc[0] == "Nguyen Van A"

    def test_skips_all_empty_rows(self, tmp_path: Path) -> None:
        table = [
            ["Họ và tên", "CCCD"],
            ["", ""],
            ["Nguyen Van A", "012345678901"],
        ]
        page = _mock_page_with_table(table)
        fake_pdf = _mock_pdf([page])

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with patch("auto_fill.reader.pdf_reader.pdfplumber.open", return_value=fake_pdf):
            df = read_pdf(pdf_path, aliases=ALIASES)

        assert len(df) == 1

    def test_table_with_only_header_tries_next_strategy(self, tmp_path: Path) -> None:
        table = [["Họ và tên", "CCCD"]]  # header only, no data rows
        page_with_table = MagicMock()
        page_with_table.extract_tables.return_value = [table]
        page_with_table.extract_text.return_value = "Họ và tên: Nguyen Van A\nCCCD: 012345678901"
        fake_pdf = _mock_pdf([page_with_table])

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with patch("auto_fill.reader.pdf_reader.pdfplumber.open", return_value=fake_pdf):
            df = read_pdf(pdf_path, aliases=ALIASES)

        # Should fallback to key-value
        assert len(df) == 1


class TestReadPdfKeyValueStrategy:
    def test_kv_colon_separator(self, tmp_path: Path) -> None:
        text = "Họ và tên: Nguyen Van A\nCCCD: 012345678901\nPhí bảo hiểm: 1500000"
        page = _mock_page_with_text(text)
        fake_pdf = _mock_pdf([page])

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with patch("auto_fill.reader.pdf_reader.pdfplumber.open", return_value=fake_pdf):
            df = read_pdf(pdf_path, aliases=ALIASES)

        assert "insured_name" in df.columns
        assert df["insured_name"].iloc[0] == "Nguyen Van A"

    def test_kv_dash_separator(self, tmp_path: Path) -> None:
        text = "Họ và tên - Nguyen Van A\nPhí bảo hiểm - 1500000"
        page = _mock_page_with_text(text)
        fake_pdf = _mock_pdf([page])

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with patch("auto_fill.reader.pdf_reader.pdfplumber.open", return_value=fake_pdf):
            df = read_pdf(pdf_path, aliases=ALIASES)

        assert "insured_name" in df.columns


class TestReadPdfNoData:
    def test_raises_reader_error_when_nothing_extracted(self, tmp_path: Path) -> None:
        page = _mock_page_empty()
        fake_pdf = _mock_pdf([page])

        pdf_path = tmp_path / "empty.pdf"
        pdf_path.touch()

        with (
            patch("auto_fill.reader.pdf_reader.pdfplumber.open", return_value=fake_pdf),
            pytest.raises(ReaderError),
        ):
            read_pdf(pdf_path, aliases=ALIASES)

    def test_pdfplumber_exception_wrapped_as_reader_error(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "bad.pdf"
        pdf_path.touch()

        with (
            patch(
                "auto_fill.reader.pdf_reader.pdfplumber.open",
                side_effect=Exception("corrupt pdf"),
            ),
            pytest.raises(ReaderError, match="corrupt pdf"),
        ):
            read_pdf(pdf_path, aliases=ALIASES)


class TestTryExtractTablesUnit:
    def test_returns_none_when_no_tables(self) -> None:
        page = _mock_page_empty()
        result = _try_extract_tables([page], ALIASES, "test.pdf")
        assert result is None

    def test_returns_none_when_table_has_only_one_row(self) -> None:
        page = MagicMock()
        page.extract_tables.return_value = [[["Họ và tên"]]]
        result = _try_extract_tables([page], ALIASES, "test.pdf")
        assert result is None


class TestTryExtractKeyvalueUnit:
    def test_returns_none_when_no_kv_lines(self) -> None:
        page = _mock_page_with_text("lorem ipsum dolor sit amet")
        result = _try_extract_keyvalue([page], ALIASES, "test.pdf")
        assert result is None

    def test_multi_page_aggregates_fields(self) -> None:
        page1 = _mock_page_with_text("Họ và tên: Nguyen Van A")
        page2 = _mock_page_with_text("Phí bảo hiểm: 1500000")
        result = _try_extract_keyvalue([page1, page2], ALIASES, "test.pdf")
        assert result is not None
        assert "insured_name" in result.columns
        assert "premium" in result.columns
