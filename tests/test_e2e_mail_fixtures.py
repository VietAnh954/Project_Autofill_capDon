"""End-to-end integration tests using the 4 example mail fixtures.

Task 7.13 acceptance:
  mail1 → TYPE C (review)        — no fill
  mail2 → TYPE A (fill)          — 2 NĐBH rows with canonical fields
  mail3 → TYPE B (GCN/đối soát)  — GcnRecord with 7+ fields
  mail4 → TYPE B (GCN/đối soát)  — GcnRecord with 7+ fields
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from auto_fill.mapper.skip_filter import classify_mail_type
from auto_fill.reader.excel_reader import read_excel
from auto_fill.reader.gcn_pdf_reader import parse_gcn_pdf

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "example_mail"

ALIASES: dict[str, list[str]] = {}


@pytest.fixture(scope="module")
def aliases() -> dict[str, list[str]]:
    path = Path(__file__).parent.parent / "src" / "auto_fill" / "mapper" / "aliases.yaml"
    with path.open(encoding="utf-8") as f:
        data: dict[str, list[str]] = yaml.safe_load(f)
    return data


# ── Subjects / bodies / attachment names from real mail metadata ────────────

MAIL1_SUBJECT = "Bill Ck Re: CHECK PHƯƠNG ÁN TÁI TỤC KH TRỊNH NAM HƯNG"
MAIL1_BODY = "Anh xem giúp em phương án này nhé."
MAIL1_ATTACHMENTS = ["IMG_4686.jpeg", "IMG_4687.jpeg"]

MAIL2_SUBJECT = "Re: THÔNG TIN TÁI TỤC"
MAIL2_BODY = "Anh ơi em gửi thông tin tái tục ạ."
MAIL2_ATTACHMENTS = ["NĐBH Đỗ Danh Minh Phúc - Đỗ Danh Minh Hiếu.xlsx"]

MAIL3_SUBJECT = "RE: [AFFINA - TCGIs] XÁC NHẬN PHƯƠNG ÁN TÁI TỤC TỪ 15/05/2025 - 31/05/2026"
MAIL3_BODY = "TCGI xác nhận phương án tái tục."
MAIL3_ATTACHMENTS = ["GCN NGUYỄN ANH TÚ tái tục.pdf"]

MAIL4_SUBJECT = "RE: [AFFINA - TCGIs] XÁC NHẬN PHƯƠNG ÁN TÁI TỤC TỪ 01/05/2025 - 31/05/2026"
MAIL4_BODY = "Đã phát hành GCN."
MAIL4_ATTACHMENTS = ["GCN NGUYỄN ĐĂNG NHẬT tái tục.pdf"]


# ── mail1 — TYPE C (needs_review) ──────────────────────────────────────────


class TestMail1TypeC:
    def test_classify_is_c(self) -> None:
        result = classify_mail_type(MAIL1_SUBJECT, MAIL1_BODY, MAIL1_ATTACHMENTS)
        assert result == "C"

    def test_no_excel_attachment(self) -> None:
        assert not any(a.endswith((".xlsx", ".xls", ".csv")) for a in MAIL1_ATTACHMENTS)


# ── mail2 — TYPE A (fill, 2 NĐBH) ─────────────────────────────────────────


class TestMail2TypeA:
    def test_classify_is_a(self) -> None:
        result = classify_mail_type(MAIL2_SUBJECT, MAIL2_BODY, MAIL2_ATTACHMENTS)
        assert result == "A"

    def test_excel_produces_two_rows(self, aliases: dict[str, list[str]]) -> None:
        xlsx = next((_FIXTURE_DIR / "mail2").glob("*.xlsx"))
        df = read_excel(xlsx, aliases)
        assert len(df) == 2

    def test_buyer_filled_down_to_second_row(self, aliases: dict[str, list[str]]) -> None:
        xlsx = next((_FIXTURE_DIR / "mail2").glob("*.xlsx"))
        df = read_excel(xlsx, aliases)
        assert df.iloc[1]["buyer_name"] == "Đỗ Thị Thuận"

    def test_insured_names_canonical(self, aliases: dict[str, list[str]]) -> None:
        xlsx = next((_FIXTURE_DIR / "mail2").glob("*.xlsx"))
        df = read_excel(xlsx, aliases)
        insured = list(df["insured_name"])
        assert "Đỗ Danh Minh Phúc" in insured
        assert "Đỗ Danh Minh Hiếu" in insured

    def test_plan_present_for_first_row(self, aliases: dict[str, list[str]]) -> None:
        xlsx = next((_FIXTURE_DIR / "mail2").glob("*.xlsx"))
        df = read_excel(xlsx, aliases)
        assert df.iloc[0]["plan"] == "B4"


# ── mail3 — TYPE B (GCN đối soát, Nguyễn Anh Tú) ─────────────────────────


class TestMail3TypeB:
    def test_classify_is_b(self) -> None:
        result = classify_mail_type(MAIL3_SUBJECT, MAIL3_BODY, MAIL3_ATTACHMENTS)
        assert result == "B"

    def test_gcn_number_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail3").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert rec.gcn_number == "26.02.05.0107.P0002745"

    def test_insured_name_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail3").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert "NGUYỄN ANH TÚ" in rec.insured_name.upper()

    def test_buyer_name_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail3").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert "VŨ THỊ HÀ" in rec.buyer_name.upper()

    def test_plan_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail3").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert rec.plan == "B3"

    def test_premium_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail3").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert rec.premium is not None


# ── mail4 — TYPE B (GCN đối soát, Nguyễn Đăng Nhật) ──────────────────────


class TestMail4TypeB:
    def test_classify_is_b(self) -> None:
        result = classify_mail_type(MAIL4_SUBJECT, MAIL4_BODY, MAIL4_ATTACHMENTS)
        assert result == "B"

    def test_gcn_number_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail4").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert rec.gcn_number == "26.02.05.0107.P0002743"

    def test_insured_name_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail4").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert "NHẬT" in rec.insured_name.upper()

    def test_plan_extracted(self) -> None:
        pdf = next((_FIXTURE_DIR / "mail4").glob("*.pdf"))
        rec = parse_gcn_pdf(pdf)
        assert rec.plan == "B3"
