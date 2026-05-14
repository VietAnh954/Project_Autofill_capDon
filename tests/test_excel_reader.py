"""Unit tests cho Excel reader — dùng fixture tạo bằng openpyxl."""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from auto_fill.reader.excel_reader import _build_rename_map, _detect_header_row, read_excel
from auto_fill.utils.errors import ReaderError

ALIASES: dict[str, list[str]] = {
    "insured_name": ["Họ và tên", "ho va ten", "tên khách hàng", "tên ndbh"],
    "insured_id_number": ["CCCD/CMND", "cccd", "số cccd", "cmnd"],
    "insured_dob": ["Ngày sinh", "ngay sinh", "dob"],
    "insured_phone": ["Số điện thoại", "sdt", "phone"],
    "premium": ["Phí bảo hiểm", "phi bao hiem", "tổng phí"],
    "trip_start": ["Ngày đi", "ngay di", "from date"],
    "trip_end": ["Ngày về", "ngay ve", "to date"],
    "destination": ["Nơi đến", "noi den", "destination"],
}


@pytest.fixture
def sample_dulich_xlsx(tmp_path: Path) -> Path:
    """Tạo file Excel mẫu có header tiếng Việt (dạng đại lý gửi)."""
    wb = openpyxl.Workbook()
    ws = wb.active

    # Row 1: header
    headers = [
        "Họ và tên",
        "CCCD/CMND",
        "Ngày sinh",
        "Số điện thoại",
        "Ngày đi",
        "Ngày về",
        "Nơi đến",
        "Phí bảo hiểm",
    ]
    ws.append(headers)

    # Row 2-4: data
    ws.append(
        [
            "NGUYỄN VĂN A",
            "012345678901",
            "01/01/1990",
            "0901234567",
            "20/05/2026",
            "27/05/2026",
            "Thái Lan",
            "1500000",
        ]
    )
    ws.append(
        [
            "TRẦN THỊ B",
            "098765432100",
            "15/06/1985",
            "0912345678",
            "01/06/2026",
            "10/06/2026",
            "Nhật Bản",
            "3000000",
        ]
    )
    ws.append(
        [
            "LÊ VĂN C",
            "001122334455",
            "30/12/2000",
            "0933333333",
            "10/07/2026",
            "20/07/2026",
            "Hàn Quốc",
            "2000000",
        ]
    )

    dest = tmp_path / "sample_dulich.xlsx"
    wb.save(dest)
    return dest


@pytest.fixture
def sample_with_empty_rows_xlsx(tmp_path: Path) -> Path:
    """File Excel có 2 hàng trống trước header (thực tế gặp nhiều)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([None, None, None])  # empty row
    ws.append([None, None, None])  # empty row
    ws.append(["Họ và tên", "CCCD/CMND", "Phí bảo hiểm"])
    ws.append(["NGUYỄN VĂN A", "012345678901", "1500000"])

    dest = tmp_path / "with_empty_rows.xlsx"
    wb.save(dest)
    return dest


class TestReadExcel:
    def test_returns_dataframe_with_correct_rows(self, sample_dulich_xlsx: Path) -> None:
        df = read_excel(sample_dulich_xlsx, ALIASES)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_columns_renamed_to_canonical(self, sample_dulich_xlsx: Path) -> None:
        df = read_excel(sample_dulich_xlsx, ALIASES)
        assert "insured_name" in df.columns
        assert "insured_id_number" in df.columns
        assert "insured_dob" in df.columns
        assert "premium" in df.columns

    def test_data_values_preserved(self, sample_dulich_xlsx: Path) -> None:
        df = read_excel(sample_dulich_xlsx, ALIASES)
        assert df.iloc[0]["insured_name"] == "NGUYỄN VĂN A"
        assert df.iloc[1]["insured_id_number"] == "098765432100"

    def test_handles_empty_rows_before_header(self, sample_with_empty_rows_xlsx: Path) -> None:
        df = read_excel(sample_with_empty_rows_xlsx, ALIASES)
        assert len(df) == 1
        assert "insured_name" in df.columns

    def test_raises_reader_error_on_corrupt_file(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "corrupt.xlsx"
        bad_file.write_bytes(b"not an excel file")
        with pytest.raises(ReaderError):
            read_excel(bad_file, ALIASES)

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_excel(tmp_path / "missing.xlsx", ALIASES)

    def test_empty_aliases_keeps_original_columns(self, sample_dulich_xlsx: Path) -> None:
        df = read_excel(sample_dulich_xlsx, {})
        assert "Họ và tên" in df.columns
        assert "CCCD/CMND" in df.columns


class TestDetectHeaderRow:
    def test_finds_row_with_most_text(self) -> None:
        import pandas as pd

        df = pd.DataFrame(
            [
                [None, None, None],
                ["Họ và tên", "CCCD", "Phí"],
                ["NGUYỄN A", "123456789012", "1500000"],
            ]
        )
        assert _detect_header_row(df) == 1

    def test_first_row_is_header_by_default(self) -> None:
        import pandas as pd

        df = pd.DataFrame(
            [
                ["Họ và tên", "CCCD", "Phí"],
                ["NGUYỄN A", "123456789012", "1500000"],
            ]
        )
        assert _detect_header_row(df) == 0


class TestBuildRenameMap:
    def test_exact_match_case_insensitive(self) -> None:
        rename_map = _build_rename_map(["Họ và tên", "CCCD/CMND"], ALIASES)
        assert rename_map.get("Họ và tên") == "insured_name"
        assert rename_map.get("CCCD/CMND") == "insured_id_number"

    def test_fuzzy_match_for_typo(self) -> None:
        rename_map = _build_rename_map(["ho va ten"], ALIASES)
        assert rename_map.get("ho va ten") == "insured_name"

    def test_unmatched_column_not_in_rename_map(self) -> None:
        rename_map = _build_rename_map(["Cột không biết"], ALIASES)
        assert "Cột không biết" not in rename_map
