"""Tests for classify_mail_type() — MAIL_PATTERNS.md §6."""

from __future__ import annotations

from auto_fill.mapper.skip_filter import classify_mail_type

# ── 4 mail fixtures from tests/fixtures/example_mail/ ──────────────────────

MAIL1_SUBJECT = "Bill Ck Re: CHECK PHƯƠNG ÁN TÁI TỤC KH TRỊNH NAM HƯNG"
MAIL1_BODY = "Chào anh,\n\nAnh xem giúp em phương án này nhé.\n\nThanks."
MAIL1_ATTACHMENTS: list[str] = ["IMG_4686.jpeg", "IMG_4687.jpeg"]

MAIL2_SUBJECT = "Re: THÔNG TIN TÁI TỤC"
MAIL2_BODY = "Anh ơi em gửi thông tin tái tục ạ."
MAIL2_ATTACHMENTS = ["NĐBH Đỗ Danh Minh Phúc - Đỗ Danh Minh Hiếu.xlsx"]

MAIL3_SUBJECT = "RE: [AFFINA - TCGIs] XÁC NHẬN PHƯƠNG ÁN TÁI TỤC TỪ 15/05/2025 - 31/05/2026"
MAIL3_BODY = "Gửi anh Việt Anh,\n\nTCGI xác nhận phương án tái tục."
MAIL3_ATTACHMENTS = ["GCN NGUYỄN ANH TÚ tái tục.pdf"]

MAIL4_SUBJECT = "RE: [AFFINA - TCGIs] XÁC NHẬN PHƯƠNG ÁN TÁI TỤC TỪ 01/05/2025 - 31/05/2026"
MAIL4_BODY = "Kính gửi,\n\nĐã phát hành GCN."
MAIL4_ATTACHMENTS = ["GCN NGUYỄN ĐĂNG NHẤT tái tục.pdf"]


# ── Core acceptance criteria ────────────────────────────────────────────────


class TestFourMailSamples:
    def test_mail1_is_type_c(self) -> None:
        result = classify_mail_type(MAIL1_SUBJECT, MAIL1_BODY, MAIL1_ATTACHMENTS)
        assert result == "C"

    def test_mail2_is_type_a(self) -> None:
        result = classify_mail_type(MAIL2_SUBJECT, MAIL2_BODY, MAIL2_ATTACHMENTS)
        assert result == "A"

    def test_mail3_is_type_b(self) -> None:
        result = classify_mail_type(MAIL3_SUBJECT, MAIL3_BODY, MAIL3_ATTACHMENTS)
        assert result == "B"

    def test_mail4_is_type_b(self) -> None:
        result = classify_mail_type(MAIL4_SUBJECT, MAIL4_BODY, MAIL4_ATTACHMENTS)
        assert result == "B"


# ── TYPE D detection ────────────────────────────────────────────────────────


class TestTypeD:
    def test_status_report_body(self) -> None:
        body = "Tổng: 227 cases\nTrả phương án: 126\nCòn: 101 cases"
        result = classify_mail_type("RE: Cập nhật tiến độ", body, [])
        assert result == "D"

    def test_status_report_with_excel_still_d(self) -> None:
        """TYPE D has priority even when xlsx is attached (MAIL_PATTERNS §3 warning)."""
        body = "Tổng: 50\nTrả phương án: 30\nCòn: 20 cases"
        result = classify_mail_type("Báo cáo", body, ["danh_sach.xlsx"])
        assert result == "D"

    def test_partial_status_body_not_d(self) -> None:
        body = "Tổng: 5 khách"
        result = classify_mail_type("Cấp đơn mới", body, ["data.xlsx"])
        assert result != "D"


# ── TYPE A variations ───────────────────────────────────────────────────────


class TestTypeA:
    def test_bill_ck_subject(self) -> None:
        result = classify_mail_type("Bill Ck THÔNG TIN CẤP ĐƠN", "", ["data.xlsx"])
        assert result == "A"

    def test_phi_da_thanh_toan(self) -> None:
        result = classify_mail_type("Phí đã thanh toán", "", ["record.xlsx"])
        assert result == "A"

    def test_cap_don_moi(self) -> None:
        result = classify_mail_type("Cấp đơn mới KH Nguyễn A", "", ["form.xlsx"])
        assert result == "A"

    def test_type_a_no_excel_is_review(self) -> None:
        result = classify_mail_type("Bill Ck", "", [])
        assert result == "review"

    def test_gui_don_with_csv(self) -> None:
        result = classify_mail_type("Gửi đơn bảo hiểm", "", ["data.csv"])
        assert result == "A"


# ── TYPE B variations ───────────────────────────────────────────────────────


class TestTypeB:
    def test_gcn_in_subject_and_filename(self) -> None:
        result = classify_mail_type("GCN đã phát hành", "", ["GCN Trần Văn A.pdf"])
        assert result == "B"

    def test_gcn_filename_case_insensitive(self) -> None:
        result = classify_mail_type("xác nhận phương án", "", ["gcn nguyen van b.pdf"])
        assert result == "B"

    def test_non_gcn_pdf_is_review(self) -> None:
        result = classify_mail_type("Xác nhận phương án", "", ["invoice.pdf"])
        assert result == "review"

    def test_gcn_pdf_without_matching_subject_is_review(self) -> None:
        result = classify_mail_type("Chào anh", "", ["GCN Trần Văn A.pdf"])
        assert result == "review"


# ── TYPE C variations ───────────────────────────────────────────────────────


class TestTypeC:
    def test_check_phuong_an_no_excel(self) -> None:
        result = classify_mail_type("CHECK PHƯƠNG ÁN tái tục", "", [])
        assert result == "C"

    def test_check_phuong_an_with_excel_is_review(self) -> None:
        """If excel is attached alongside CHECK PHƯƠNG ÁN → treat as review."""
        result = classify_mail_type("CHECK PHƯƠNG ÁN tái tục", "", ["data.xlsx"])
        assert result == "review"

    def test_check_phuong_an_mixed_case(self) -> None:
        result = classify_mail_type("check phuong an", "", [])
        assert result == "C"

    def test_fwd_check_phuong_an(self) -> None:
        result = classify_mail_type("Fwd: CHECK PHƯƠNG ÁN KH XYZ", "", [])
        assert result == "C"


# ── needs_review fallback ───────────────────────────────────────────────────


class TestReview:
    def test_unknown_subject_no_attachment(self) -> None:
        result = classify_mail_type("Chào anh", "Nội dung bình thường.", [])
        assert result == "review"

    def test_pdf_without_gcn_name(self) -> None:
        result = classify_mail_type("RE: xác nhận", "", ["hop_dong.pdf"])
        assert result == "review"
