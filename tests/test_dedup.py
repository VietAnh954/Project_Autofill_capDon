"""Unit tests cho Dedup."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from auto_fill.mapper.dedup import _check_match, _parse_date, is_duplicate

_RECORD = {
    "insured_id_number": "012345678901",
    "trip_start": date(2026, 5, 20),
    "destination": "Thai Lan",
}


def _make_df(rows: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


class TestIsDuplicate:
    def test_duplicate_found_returns_true(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "20/05/2026",
                    "destination": "Thai Lan",
                }
            ]
        )
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is True

    def test_no_duplicate_returns_false(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "999999999999",
                    "trip_start": "20/05/2026",
                    "destination": "Thai Lan",
                }
            ]
        )
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is False

    def test_empty_sheet_returns_false(self, tmp_path: Path) -> None:
        df = _make_df([])
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is False

    def test_missing_columns_returns_false(self, tmp_path: Path) -> None:
        df = _make_df([{"insured_id_number": "012345678901"}])
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is False

    def test_load_exception_returns_false(self, tmp_path: Path) -> None:
        with patch("auto_fill.mapper.dedup._load_sheet", side_effect=FileNotFoundError):
            assert is_duplicate(_RECORD, tmp_path) is False

    def test_different_destination_no_match(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "20/05/2026",
                    "destination": "Nhat Ban",
                }
            ]
        )
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is False

    def test_different_trip_start_no_match(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "01/06/2026",
                    "destination": "Thai Lan",
                }
            ]
        )
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is False

    def test_destination_case_insensitive(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "20/05/2026",
                    "destination": "THAI LAN",
                }
            ]
        )
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is True

    def test_iso_date_format_in_sheet(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "2026-05-20",
                    "destination": "Thai Lan",
                }
            ]
        )
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path) is True

    def test_with_aliases_renames_columns(self, tmp_path: Path) -> None:
        df = _make_df(
            [
                {
                    "CCCD/CMND/Paspost ID": "012345678901",
                    "Ngày đi": "20/05/2026",
                    "Nơi đến": "Thai Lan",
                }
            ]
        )
        aliases = {
            "insured_id_number": ["CCCD/CMND/Paspost ID", "cccd/cmnd/paspost id"],
            "trip_start": ["Ngày đi", "ngày đi"],
            "destination": ["Nơi đến", "nơi đến"],
        }
        with patch("auto_fill.mapper.dedup._load_sheet", return_value=df):
            assert is_duplicate(_RECORD, tmp_path, aliases=aliases) is True


class TestParseDate:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("20/05/2026", date(2026, 5, 20)),
            ("2026-05-20", date(2026, 5, 20)),
            ("05/20/2026", date(2026, 5, 20)),
            ("20-05-2026", date(2026, 5, 20)),
            ("46156", date(2026, 5, 14)),
            ("not-a-date", None),
            ("", None),
        ],
    )
    def test_parse_date(self, value: str, expected: date | None) -> None:
        assert _parse_date(value) == expected


class TestCheckMatch:
    def test_all_keys_match(self) -> None:
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "20/05/2026",
                    "destination": "Thai Lan",
                }
            ]
        )
        assert _check_match(df, _RECORD) is True

    def test_empty_id_returns_false(self) -> None:
        record = {**_RECORD, "insured_id_number": ""}
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "20/05/2026",
                    "destination": "Thai Lan",
                }
            ]
        )
        assert _check_match(df, record) is False

    def test_none_trip_start_returns_false(self) -> None:
        record = {**_RECORD, "trip_start": None}
        df = _make_df(
            [
                {
                    "insured_id_number": "012345678901",
                    "trip_start": "20/05/2026",
                    "destination": "Thai Lan",
                }
            ]
        )
        assert _check_match(df, record) is False
