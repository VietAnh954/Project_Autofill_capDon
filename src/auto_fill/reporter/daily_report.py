"""Daily report renderer — tao file report_YYYY-MM-DD.md tong hop ket qua.

Xem TODO #2.6.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RunStats:
    """Thong ke tong hop sau 1 lan chay pipeline."""

    run_date: date = field(default_factory=date.today)
    processed: int = 0
    written: int = 0
    duplicates: int = 0
    errors: int = 0
    per_sheet: dict[str, int] = field(default_factory=dict)
    error_details: list[str] = field(default_factory=list)

    def add_written(self, sheet_alias: str) -> None:
        """Ghi nhan 1 record da ghi thanh cong."""
        self.written += 1
        self.per_sheet[sheet_alias] = self.per_sheet.get(sheet_alias, 0) + 1

    def add_duplicate(self) -> None:
        self.duplicates += 1

    def add_error(self, detail: str) -> None:
        self.errors += 1
        self.error_details.append(detail)


def render_report(stats: RunStats, output_dir: Path) -> Path:
    """Render bao cao thanh file Markdown trong output_dir.

    Args:
        stats: Du lieu thong ke tu pipeline.
        output_dir: Thu muc luu file (tao neu chua co).

    Returns:
        Path toi file report da tao.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"report_{stats.run_date.strftime('%Y-%m-%d')}.md"
    report_path = output_dir / filename

    content = _build_markdown(stats)
    report_path.write_text(content, encoding="utf-8")

    logger.info("report_rendered", extra={"path": str(report_path)})
    return report_path


def _build_markdown(stats: RunStats) -> str:
    """Tao noi dung Markdown tu RunStats."""
    lines: list[str] = []
    date_str = stats.run_date.strftime("%d/%m/%Y")

    lines += [
        f"# Báo cáo cấp đơn ngày {date_str}",
        "",
        "## Tóm tắt",
        "",
        "| Chỉ số | Giá trị |",
        "|--------|---------|",
        f"| Hồ sơ đã xử lý | {stats.processed} |",
        f"| Đã ghi vào file tổng | {stats.written} |",
        f"| Trùng (bỏ qua) | {stats.duplicates} |",
        f"| Lỗi / Bỏ qua | {stats.errors} |",
        "",
    ]

    if stats.per_sheet:
        lines += [
            "## Chi tiết theo sheet",
            "",
            "| Sheet | Số dòng mới |",
            "|-------|------------|",
        ]
        for sheet, count in sorted(stats.per_sheet.items()):
            lines.append(f"| {sheet} | {count} |")
        lines.append("")

    if stats.error_details:
        lines += [
            "## Lỗi / Bỏ qua",
            "",
        ]
        for detail in stats.error_details:
            lines.append(f"- {detail}")
        lines.append("")

    if stats.written == 0 and stats.errors == 0:
        lines += ["_Không có hồ sơ nào được xử lý trong ngày._", ""]

    return "\n".join(lines)
