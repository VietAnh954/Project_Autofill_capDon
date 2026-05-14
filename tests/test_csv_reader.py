"""Unit tests cho CSV reader."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_fill.reader.csv_reader import read_csv
from auto_fill.utils.errors import ReaderError

ALIASES: dict[str, list[str]] = {
    "insured_name": ["Ho va ten", "ho va ten", "Ten khach hang"],
    "insured_id_number": ["CCCD/CMND", "cccd"],
    "premium": ["Phi bao hiem", "phi"],
    "trip_start": ["Ngay di"],
    "destination": ["Noi den"],
}


def _write_csv(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.write_bytes(content.encode(encoding))


class TestReadCsv:
    def test_reads_utf8_csv(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_csv(
            csv_path,
            "Ho va ten,CCCD/CMND,Phi bao hiem\n"
            "NGUYEN VAN A,012345678901,1500000\n"
            "TRAN THI B,098765432100,3000000\n",
        )
        df = read_csv(csv_path, ALIASES)
        assert len(df) == 2
        assert "insured_name" in df.columns
        assert "insured_id_number" in df.columns

    def test_reads_utf8_bom_csv(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test_bom.csv"
        _write_csv(
            csv_path,
            "Ho va ten,CCCD/CMND\nNGUYEN VAN A,012345678901\n",
            encoding="utf-8-sig",
        )
        df = read_csv(csv_path, ALIASES)
        assert "insured_name" in df.columns

    def test_renames_columns_to_canonical(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_csv(csv_path, "Ho va ten,CCCD/CMND\nNGUYEN VAN A,123456789012\n")
        df = read_csv(csv_path, ALIASES)
        assert "insured_name" in df.columns
        assert "insured_id_number" in df.columns

    def test_unknown_column_kept_as_is(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_csv(csv_path, "Ho va ten,ghi_chu\nNGUYEN VAN A,OK\n")
        df = read_csv(csv_path, ALIASES)
        assert "ghi_chu" in df.columns

    def test_data_values_correct(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_csv(csv_path, "Ho va ten,Phi bao hiem\nNGUYEN VAN A,1500000\n")
        df = read_csv(csv_path, ALIASES)
        assert df.iloc[0]["insured_name"] == "NGUYEN VAN A"
        assert df.iloc[0]["premium"] == "1500000"

    def test_raises_reader_error_for_bad_file(self, tmp_path: Path) -> None:
        bad_path = tmp_path / "bad.csv"
        bad_path.write_bytes(bytes(range(256)) * 10)  # binary garbage
        with pytest.raises(ReaderError):
            read_csv(bad_path, ALIASES)

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_csv(tmp_path / "missing.csv", ALIASES)

    def test_semicolon_delimiter(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "semicolon.csv"
        _write_csv(csv_path, "Ho va ten;CCCD/CMND\nNGUYEN VAN A;012345678901\n")
        df = read_csv(csv_path, ALIASES, delimiter=";")
        assert "insured_name" in df.columns
        assert len(df) == 1

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "blanks.csv"
        _write_csv(csv_path, "Ho va ten,CCCD/CMND\nNGUYEN VAN A,012345678901\n\n\n")
        df = read_csv(csv_path, ALIASES)
        assert len(df) == 1
