"""Unit tests cho daily_report module."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from auto_fill.reporter.daily_report import RunStats, _build_markdown, render_report


class TestRunStats:
    def test_initial_state(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14))
        assert stats.processed == 0
        assert stats.written == 0
        assert stats.duplicates == 0
        assert stats.errors == 0
        assert stats.per_sheet == {}
        assert stats.error_details == []

    def test_add_written_increments(self) -> None:
        stats = RunStats()
        stats.add_written("travel")
        stats.add_written("travel")
        stats.add_written("auto")
        assert stats.written == 3
        assert stats.per_sheet == {"travel": 2, "auto": 1}

    def test_add_duplicate_increments(self) -> None:
        stats = RunStats()
        stats.add_duplicate()
        stats.add_duplicate()
        assert stats.duplicates == 2

    def test_add_error_increments_and_stores_detail(self) -> None:
        stats = RunStats()
        stats.add_error("file.xlsx: bad format")
        assert stats.errors == 1
        assert "file.xlsx: bad format" in stats.error_details


class TestBuildMarkdown:
    def test_contains_date(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14))
        md = _build_markdown(stats)
        assert "14/05/2026" in md

    def test_summary_table_present(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14), processed=5, written=4, duplicates=1)
        md = _build_markdown(stats)
        assert "Hồ sơ đã xử lý" in md
        assert "| 5 |" in md
        assert "| 4 |" in md
        assert "| 1 |" in md

    def test_per_sheet_section_present_when_data(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14))
        stats.add_written("travel")
        stats.add_written("auto")
        md = _build_markdown(stats)
        assert "Chi tiết theo sheet" in md
        assert "travel" in md
        assert "auto" in md

    def test_per_sheet_absent_when_no_data(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14))
        md = _build_markdown(stats)
        assert "Chi tiết theo sheet" not in md

    def test_error_section_present_when_errors(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14))
        stats.add_error("file.xlsx: unknown schema")
        md = _build_markdown(stats)
        assert "Lỗi / Bỏ qua" in md
        assert "file.xlsx" in md

    def test_no_activity_message_when_all_zero(self) -> None:
        stats = RunStats(run_date=date(2026, 5, 14))
        md = _build_markdown(stats)
        assert "Không có hồ sơ" in md


class TestRenderReport:
    def test_creates_file_in_output_dir(self, tmp_path: Path) -> None:
        stats = RunStats(run_date=date(2026, 5, 14), processed=3, written=2)
        path = render_report(stats, tmp_path / "reports")
        assert path.exists()
        assert path.name == "report_2026-05-14.md"

    def test_file_content_is_valid_markdown(self, tmp_path: Path) -> None:
        stats = RunStats(run_date=date(2026, 5, 14), processed=1, written=1)
        stats.add_written("travel")
        path = render_report(stats, tmp_path)
        content = path.read_text(encoding="utf-8")
        assert content.startswith("# Báo cáo cấp đơn ngày")
        assert "travel" in content

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "reports"
        stats = RunStats(run_date=date(2026, 5, 14))
        render_report(stats, nested)
        assert nested.exists()
