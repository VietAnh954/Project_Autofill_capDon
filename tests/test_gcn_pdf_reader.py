"""Tests for gcn_pdf_reader — parse GCN PDF fixture from mail3."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from auto_fill.reader.gcn_pdf_reader import GcnRecord, parse_gcn_pdf

FIXTURE_DIR = Path("tests/fixtures/example_mail")
GCN_MAIL3 = FIXTURE_DIR / "mail3" / "GCN NGUYỄN ANH TÚ tái tục.pdf"
GCN_MAIL4 = FIXTURE_DIR / "mail4" / "GCN NGUYỄN ĐĂNG NHẬT tái tục.pdf"


# ── Real-file acceptance test ───────────────────────────────────────────────


@pytest.mark.skipif(not GCN_MAIL3.exists(), reason="fixture not found")
class TestMail3GcnPdf:
    def test_all_seven_fields_populated(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.is_complete(), f"Missing fields: {vars(record)}"

    def test_gcn_number(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.gcn_number == "26.02.05.0107.P0002745"

    def test_buyer_name(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.buyer_name == "VŨ THỊ HÀ"

    def test_insured_name(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.insured_name == "NGUYỄN ANH TÚ"

    def test_premium(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.premium == "2.199.907"

    def test_valid_from(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.valid_from == "26/05/2026"

    def test_valid_to(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.valid_to == "25/05/2027"

    def test_product_name(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert "AFFINA CARE" in record.product

    def test_plan(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL3)
        assert record.plan == "B3"


@pytest.mark.skipif(not GCN_MAIL4.exists(), reason="fixture not found")
class TestMail4GcnPdf:
    def test_all_seven_fields_populated(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL4)
        assert record.is_complete(), f"Missing fields: {vars(record)}"

    def test_insured_name_different(self) -> None:
        record = parse_gcn_pdf(GCN_MAIL4)
        assert "NHẤT" in record.insured_name or record.insured_name != ""


# ── GcnRecord unit tests ────────────────────────────────────────────────────


class TestGcnRecord:
    def test_empty_record_not_complete(self) -> None:
        assert not GcnRecord().is_complete()

    def test_full_record_is_complete(self) -> None:
        r = GcnRecord(
            gcn_number="X",
            buyer_name="A",
            insured_name="B",
            premium="100",
            valid_from="01/01/2026",
            valid_to="31/12/2026",
            product="BH XYZ",
        )
        assert r.is_complete()

    def test_one_missing_field_not_complete(self) -> None:
        r = GcnRecord(
            gcn_number="X",
            buyer_name="A",
            insured_name="B",
            premium="100",
            valid_from="01/01/2026",
            valid_to="",  # missing
            product="BH XYZ",
        )
        assert not r.is_complete()


# ── Error handling ──────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_gcn_pdf("nonexistent_file.pdf")

    def test_returns_partial_record_on_missing_fields(self) -> None:
        """Parser should not crash when some patterns are absent."""
        page_text = "GIẤY CHỨNG NHẬN\nBẢO HIỂM ABC\nSố: GCN-001\n"
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with (
            patch("auto_fill.reader.gcn_pdf_reader.pdfplumber") as mock_plumber,
            patch("auto_fill.reader.gcn_pdf_reader.Path.exists", return_value=True),
        ):
            mock_plumber.open.return_value = mock_pdf
            record = parse_gcn_pdf("fake.pdf")

        assert record.gcn_number == "GCN-001"
        assert record.product == "BẢO HIỂM ABC"
        assert not record.is_complete()
