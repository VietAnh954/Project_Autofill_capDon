"""Tests for mapper.header_detector — group layout detection + group-aware rename."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from auto_fill.mapper.header_detector import (
    GroupLayout,
    build_group_aware_col_map,
    detect_group_layout,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_df(rows: list[list[str | None]]) -> pd.DataFrame:
    """Build a raw DataFrame (like pd.read_excel header=None) from a list of rows."""
    n_cols = max(len(r) for r in rows)
    padded = [r + [None] * (n_cols - len(r)) for r in rows]
    return pd.DataFrame(padded, dtype=object)


_SIMPLE_ALIASES: dict[str, list[str]] = {
    "insured_name": ["họ tên", "ho ten", "tên"],
    "insured_dob": ["ngày sinh", "ngay sinh"],
    "insured_id_number": ["cccd", "cmnd"],
    "buyer_name": ["tên khách hàng", "ten khach hang"],
    "buyer_dob": ["ngày sinh người mua", "dob bmbh"],
    "buyer_id_number": ["số cmnd", "so cmnd"],
    "buyer_relation": ["quan hệ", "quan he bmbh"],
}


# ---------------------------------------------------------------------------
# detect_group_layout
# ---------------------------------------------------------------------------


class TestDetectGroupLayout:
    def test_bmbh_first_detected(self) -> None:
        df = _make_df(
            [
                ["STT", "Bên mua bảo hiểm", None, None, None, None, "Người được bảo hiểm"],
                ["STT", "Tên khách hàng", "Ngày sinh", "CMND", None, None, "Họ tên"],
            ]
        )
        layout = detect_group_layout(df)
        assert layout.order == "bmbh_first"

    def test_insured_first_detected(self) -> None:
        df = _make_df(
            [
                ["STT", "Người được bảo hiểm", None, None, None, None, "Bên mua bảo hiểm"],
                ["STT", "Họ tên", "Ngày sinh", "CCCD", None, None, "Tên khách hàng"],
            ]
        )
        layout = detect_group_layout(df)
        assert layout.order == "insured_first"

    def test_unknown_when_no_group_headers(self) -> None:
        df = _make_df(
            [
                ["STT", "Họ tên", "Ngày sinh", "CCCD"],
                [None, "A", "01/01/1990", "012345678901"],
            ]
        )
        layout = detect_group_layout(df)
        assert layout.order == "unknown"

    def test_bmbh_cols_correct(self) -> None:
        # BMBH group spans cols 2-6, NDBH starts at col 7
        df = _make_df(
            [
                ["X", "Bên mua bảo hiểm", None, None, None, None, "Người được bảo hiểm"],
            ]
        )
        layout = detect_group_layout(df)
        assert 2 in layout.bmbh_cols
        assert 6 in layout.bmbh_cols
        assert 7 not in layout.bmbh_cols

    def test_insured_cols_correct(self) -> None:
        df = _make_df(
            [
                ["X", "Bên mua bảo hiểm", None, None, "Người được bảo hiểm", None],
            ]
        )
        layout = detect_group_layout(df)
        assert 5 in layout.insured_cols
        assert 2 not in layout.insured_cols

    def test_bmbh_abbreviation_detected(self) -> None:
        df = _make_df(
            [
                ["A", "BMBH", None, "NDBH"],
            ]
        )
        layout = detect_group_layout(df)
        assert layout.order == "bmbh_first"

    def test_group_layout_is_frozen(self) -> None:
        layout = GroupLayout(order="unknown")
        with pytest.raises((AttributeError, TypeError)):
            layout.order = "bmbh_first"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# build_group_aware_col_map
# ---------------------------------------------------------------------------


class TestBuildGroupAwareColMap:
    def _bmbh_first_layout(self, bmbh_range: range, insured_range: range) -> GroupLayout:
        return GroupLayout(
            order="bmbh_first",
            bmbh_cols=frozenset(bmbh_range),
            insured_cols=frozenset(insured_range),
        )

    def test_ngay_sinh_in_bmbh_col_maps_to_buyer_dob(self) -> None:
        headers = ["STT", "Tên khách hàng", "Ngày sinh", "Họ tên", "Ngày sinh"]
        layout = self._bmbh_first_layout(range(2, 4), range(4, 6))
        col_map = build_group_aware_col_map(headers, _SIMPLE_ALIASES, layout)
        assert col_map.get(3) == "buyer_dob"

    def test_ngay_sinh_in_insured_col_maps_to_insured_dob(self) -> None:
        headers = ["STT", "Tên khách hàng", "Ngày sinh", "Họ tên", "Ngày sinh"]
        layout = self._bmbh_first_layout(range(2, 4), range(4, 6))
        col_map = build_group_aware_col_map(headers, _SIMPLE_ALIASES, layout)
        assert col_map.get(5) == "insured_dob"

    def test_two_ngay_sinh_get_different_canonicals(self) -> None:
        headers = ["STT", "Tên khách hàng", "Ngày sinh", "Họ tên", "Ngày sinh"]
        layout = self._bmbh_first_layout(range(2, 4), range(4, 6))
        col_map = build_group_aware_col_map(headers, _SIMPLE_ALIASES, layout)
        assert col_map.get(3) != col_map.get(5)
        assert col_map.get(3) == "buyer_dob"
        assert col_map.get(5) == "insured_dob"

    def test_non_ambiguous_field_unaffected(self) -> None:
        headers = ["STT", "Tên khách hàng"]
        layout = self._bmbh_first_layout(range(2, 5), range(5, 10))
        col_map = build_group_aware_col_map(headers, _SIMPLE_ALIASES, layout)
        assert col_map.get(2) == "buyer_name"

    def test_unknown_layout_falls_back_to_standard_alias(self) -> None:
        headers = ["Ngày sinh"]
        layout = GroupLayout(order="unknown")
        col_map = build_group_aware_col_map(headers, _SIMPLE_ALIASES, layout)
        assert col_map.get(1) == "insured_dob"

    def test_col_not_in_any_group_uses_standard_alias(self) -> None:
        # Col 10 is outside both BMBH(2-4) and NDBH(5-7)
        headers = ["X"] * 9 + ["Ngày sinh"]
        layout = self._bmbh_first_layout(range(2, 5), range(5, 8))
        col_map = build_group_aware_col_map(headers, _SIMPLE_ALIASES, layout)
        assert col_map.get(10) == "insured_dob"


# ---------------------------------------------------------------------------
# Acceptance test: read sample_suc_khoe.xlsx
# ---------------------------------------------------------------------------


class TestSampleSucKhoeAcceptance:
    """8.3 acceptance: same pipeline reads both BMBH-first (Affina) and NDBH-first formats."""

    SAMPLE_PATH = Path("sample_capdon/sample_suc_khoe.xlsx")

    @pytest.fixture()
    def df(self) -> pd.DataFrame:
        from auto_fill.mapper.aliases_loader import load_aliases
        from auto_fill.reader.excel_reader import read_excel

        aliases = load_aliases()
        return read_excel(self.SAMPLE_PATH, aliases)

    def test_insured_dob_column_present(self, df: pd.DataFrame) -> None:
        assert "insured_dob" in df.columns

    def test_buyer_dob_column_present(self, df: pd.DataFrame) -> None:
        assert "buyer_dob" in df.columns

    def test_no_dup_suffix_in_dob_columns(self, df: pd.DataFrame) -> None:
        dup_cols = [c for c in df.columns if "dob_dup" in c]
        assert not dup_cols, f"Unexpected _dup columns: {dup_cols}"

    def test_self_buyer_row_same_dob(self, df: pd.DataFrame) -> None:
        """Pattern 1: Nguyễn Thị Tuyết Linh — insured_dob == buyer_dob."""
        row = df[df["insured_name"].str.contains("Tuy", na=False)].iloc[0]
        assert row["insured_dob"] == row["buyer_dob"]

    def test_pattern2_child_and_mother_have_different_dob(self, df: pd.DataFrame) -> None:
        """Pattern 2: Phúc (child 2018-12-12) bought by Thuận (mother 1988-08-30)."""
        from datetime import date

        row = df[df["insured_name"].str.contains("Ph", na=False)].iloc[0]
        insured = pd.to_datetime(row["insured_dob"]).date()
        buyer = pd.to_datetime(row["buyer_dob"]).date()
        assert insured == date(2018, 12, 12)
        assert buyer == date(1988, 8, 30)
        assert insured != buyer
