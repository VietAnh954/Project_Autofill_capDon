"""Unit tests cho Excel filler."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import openpyxl
import pytest

from auto_fill.filler.excel_filler import _next_stt, append_travel_rows

_SHEET = "Du lịch"
_HEADERS = [
    "Ngày",
    "STT",
    "Họ Và Tên",
    "Ngày sinh",
    "CCCD/CMND/Paspost ID",
    "Ngày thanh toán",
    "Ngày đi",
    "Ngày về",
    "Số ngày",
    "Nơi đến",
    "Phạm vi",
    "Gói tham gia",
    "Plan tham gia",
    "Phí bảo hiểm",
    "Họ tên người mua",
]

_RECORD = {
    "issued_date": date(2026, 5, 14),
    "insured_name": "NGUYEN VAN A",
    "insured_dob": date(1990, 1, 1),
    "insured_id_number": "012345678901",
    "trip_start": date(2026, 5, 20),
    "trip_end": date(2026, 5, 27),
    "destination": "Thai Lan",
    "scope": "Chau A",
    "plan": "Plan A",
    "premium": 1500000.0,
    "buyer_name": "NGUYEN VAN B",
}


def _make_workbook(tmp_path: Path, existing_rows: int = 0) -> Path:
    path = tmp_path / "master.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = _SHEET
    ws.append(_HEADERS)
    for i in range(1, existing_rows + 1):
        ws.append(
            [
                date(2026, 5, 1),
                i,
                f"Person {i}",
                date(1990, 1, 1),
                f"00000000000{i}",
                None,
                date(2026, 5, 10),
                date(2026, 5, 17),
                7,
                "Singapore",
                "Chau A",
                None,
                "Plan B",
                2000000.0,
                f"Buyer {i}",
            ]
        )
    wb.save(path)
    return path


class TestAppendTravelRows:
    def test_appends_one_row(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        written = append_travel_rows([_RECORD], path)
        assert written == 1

    def test_row_count_increases(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        wb_before = openpyxl.load_workbook(path)
        rows_before = wb_before[_SHEET].max_row
        append_travel_rows([_RECORD], path)
        wb_after = openpyxl.load_workbook(path)
        assert wb_after[_SHEET].max_row == rows_before + 1

    def test_appends_multiple_rows(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        written = append_travel_rows([_RECORD, _RECORD], path)
        assert written == 2

    def test_insured_name_written(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        append_travel_rows([_RECORD], path)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        row = ws.max_row
        assert ws.cell(row=row, column=3).value == "NGUYEN VAN A"

    def test_stt_auto_increments(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path, existing_rows=5)
        append_travel_rows([_RECORD], path)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        row = ws.max_row
        assert ws.cell(row=row, column=2).value == 6

    def test_stt_starts_at_1_for_empty_sheet(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path, existing_rows=0)
        append_travel_rows([_RECORD], path)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        assert ws.cell(row=2, column=2).value == 1

    def test_trip_days_computed(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        append_travel_rows([_RECORD], path)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        row = ws.max_row
        assert ws.cell(row=row, column=9).value == 7  # 27-20 = 7

    def test_issued_date_written(self, tmp_path: Path) -> None:
        from datetime import datetime

        path = _make_workbook(tmp_path)
        append_travel_rows([_RECORD], path)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        row = ws.max_row
        val = ws.cell(row=row, column=1).value
        # openpyxl reads date cells back as datetime
        if isinstance(val, datetime):
            val = val.date()
        assert val == date(2026, 5, 14)

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            append_travel_rows([_RECORD], tmp_path / "missing.xlsx")

    def test_wrong_sheet_name_raises(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        with pytest.raises(KeyError):
            append_travel_rows([_RECORD], path, sheet_name="Wrong Sheet")

    def test_optional_field_none_skipped(self, tmp_path: Path) -> None:
        record = {**_RECORD}
        del record["buyer_name"]
        path = _make_workbook(tmp_path)
        written = append_travel_rows([record], path)
        assert written == 1

    def test_premium_written_as_float(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path)
        append_travel_rows([_RECORD], path)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        row = ws.max_row
        assert ws.cell(row=row, column=14).value == 1500000.0


class TestNextStt:
    def test_empty_sheet_returns_1(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path, existing_rows=0)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        assert _next_stt(ws, col_idx=2, header_row=1) == 1

    def test_returns_max_plus_1(self, tmp_path: Path) -> None:
        path = _make_workbook(tmp_path, existing_rows=3)
        wb = openpyxl.load_workbook(path)
        ws = wb[_SHEET]
        assert _next_stt(ws, col_idx=2, header_row=1) == 4
