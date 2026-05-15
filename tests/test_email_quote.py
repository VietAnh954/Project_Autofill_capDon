"""Tests for strip_reply_quotes() — MAIL_PATTERNS.md §5.1."""

from __future__ import annotations

from auto_fill.mapper.email_quote import strip_reply_quotes

# ── Fixture: mail3-style body with 5 nested replies ────────────────────────
# Lien (TCGI) is the top-level sender; below are forwarded/replied sections.

MAIL3_BODY = """\
Gửi anh Việt Anh,

TCGI xác nhận phương án tái tục cho khách hàng Nguyễn Anh Tú.
GCN đính kèm theo mail này ạ.

Trân trọng,
Lien (TCGI)

-----Original Message-----
From: Nguyen Kieu Linh <linh@affina.com.vn>
Sent: Thursday, May 14, 2025 9:00 AM
To: Lien TCGI
Subject: RE: [AFFINA - TCGIs] XÁC NHẬN PHƯƠNG ÁN TÁI TỤC

Chị ơi, em gửi lại thông tin phương án.

From: Lien TCGI <lien@tcgi.com.vn>
Sent: Wednesday, May 13, 2025 3:00 PM
Subject: Re: XÁC NHẬN PHƯƠNG ÁN

Tổng: 227 / Trả phương án: 126 / Còn: 101

From: Nguyen Kieu Linh
Sent: Tuesday, May 12, 2025
Subject: Fwd: Phương án tái tục

...original content deeper...

From: Sale Affina
Sent: Monday, May 11, 2025
Subject: Phương án đề xuất

Khách hàng Nguyễn Hữu Minh Đức mong muốn mua B3 nội trú.
"""

MAIL3_EXPECTED_LINES = [
    "Gửi anh Việt Anh,",
    "",
    "TCGI xác nhận phương án tái tục cho khách hàng Nguyễn Anh Tú.",
    "GCN đính kèm theo mail này ạ.",
    "",
    "Trân trọng,",
    "Lien (TCGI)",
]


class TestMail3Fixture:
    def test_top_level_only(self) -> None:
        result = strip_reply_quotes(MAIL3_BODY)
        assert result == "\n".join(MAIL3_EXPECTED_LINES)

    def test_result_has_no_from_header(self) -> None:
        result = strip_reply_quotes(MAIL3_BODY)
        assert "From:" not in result

    def test_result_has_no_status_report(self) -> None:
        result = strip_reply_quotes(MAIL3_BODY)
        assert "Tổng:" not in result

    def test_result_is_roughly_10_lines(self) -> None:
        result = strip_reply_quotes(MAIL3_BODY)
        assert len(result.splitlines()) <= 10


# ── Outlook "On DATE, NAME wrote:" style ───────────────────────────────────


class TestOnDateWrote:
    def test_removes_on_wrote_quote(self) -> None:
        body = "Hello anh,\n\nThông tin đính kèm.\n\nOn Thu, May 14, 2025, Linh wrote:\n> Chị ơi em gửi lại.\n"
        result = strip_reply_quotes(body)
        assert "wrote:" not in result
        assert "Hello anh" in result

    def test_strips_angle_quote_lines(self) -> None:
        body = "Top line\n\n> quoted line 1\n> quoted line 2\n"
        result = strip_reply_quotes(body)
        assert ">" not in result
        assert "Top line" in result


# ── Vietnamese Outlook quote headers ───────────────────────────────────────


class TestVietnameseHeaders:
    def test_tu_colon(self) -> None:
        body = "Nội dung mới.\n\nTừ: Nguyen Van A\nGửi: 14/05/2025\nĐến: Việt Anh\n"
        result = strip_reply_quotes(body)
        assert "Từ:" not in result
        assert "Nội dung mới." in result


# ── Separator line style ────────────────────────────────────────────────────


class TestSeparatorLine:
    def test_dashes_separator(self) -> None:
        body = "Top content\n\n---- Original Message ----\nOld content\n"
        result = strip_reply_quotes(body)
        assert "Old content" not in result
        assert "Top content" in result

    def test_underscores_separator(self) -> None:
        body = "Top content\n\n___________\nOld content\n"
        result = strip_reply_quotes(body)
        assert "Old content" not in result

    def test_no_quote_returns_full_body(self) -> None:
        body = "Just a plain email body\nwith no quoted sections."
        result = strip_reply_quotes(body)
        assert result == body.strip()


# ── Edge cases ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_body(self) -> None:
        assert strip_reply_quotes("") == ""

    def test_whitespace_only(self) -> None:
        assert strip_reply_quotes("   \n\n  ") == ""

    def test_body_with_only_quotes(self) -> None:
        body = "From: someone\nSent: today\nSubject: test"
        result = strip_reply_quotes(body)
        assert result == ""

    def test_from_in_middle_of_line_not_cut(self) -> None:
        body = "Thông tin từ khách hàng ABC.\nĐịa chỉ: 123 đường XYZ."
        result = strip_reply_quotes(body)
        assert "Thông tin" in result
