"""End-to-end pipeline tests for all 5 sample files.

Tests: read_excel → normalize → validate (→ pattern checks).
Fixture files live in tests/fixtures/sample_capdon/ so tests work
regardless of working directory (avoids pre-commit stash issues).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_capdon"

_DATE_FIELDS = (
    "issued_date",
    "insured_dob",
    "buyer_dob",
    "trip_start",
    "trip_end",
    "effective_from",
    "effective_to",
    "payment_date",
    "start_date",
    "end_date",
)
_MONEY_FIELDS = ("premium", "premium_tnds", "premium_accident", "vehicle_value")
_FLOAT_NUM_FIELDS = ("years",)  # validator expects int|float → normalize_money returns float
_ID_FIELDS = ("insured_id_number", "buyer_id_number")
_FLOAT_EXPECTED = frozenset(_MONEY_FIELDS + _FLOAT_NUM_FIELDS)


def _is_empty(v: Any) -> bool:
    import math

    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return str(v).strip().lower() in {"nan", "nat", "na", "n/a", "none", ""}


def _norm_fields(r: dict[str, Any], fields: tuple[str, ...], fn: Any) -> None:
    for f in fields:
        v = r.get(f)
        if _is_empty(v):
            r[f] = None
        else:
            try:
                r[f] = fn(v)
            except Exception:
                r[f] = None


def _nan_sweep(r: dict[str, Any]) -> None:
    import math

    for k, v in r.items():
        if isinstance(v, float):
            if math.isnan(v):
                r[k] = None
            elif k not in _FLOAT_EXPECTED:
                r[k] = str(int(v)) if v == int(v) else str(v)


def _normalize(record: dict[str, Any]) -> dict[str, Any]:
    """Lightweight normalization mirroring __main__._normalize_record."""
    from auto_fill.mapper.normalizer import (
        normalize_date,
        normalize_id_number,
        normalize_money,
        normalize_name,
    )

    r = dict(record)
    _norm_fields(r, _DATE_FIELDS, normalize_date)
    _norm_fields(r, _ID_FIELDS, normalize_id_number)
    _norm_fields(r, _MONEY_FIELDS + _FLOAT_NUM_FIELDS, normalize_money)
    _norm_fields(r, ("insured_name", "buyer_name", "destination", "scope", "plan"), normalize_name)
    _nan_sweep(r)
    return r


def _load(filename: str) -> Any:
    from auto_fill.mapper.aliases_loader import load_aliases
    from auto_fill.reader.excel_reader import read_excel

    p = FIXTURE_DIR / filename
    if not p.exists():
        pytest.skip(f"Fixture not found: {p}")
    aliases = load_aliases()
    return read_excel(p, aliases)


class TestDuLichSample:
    def test_reads_6_rows(self) -> None:
        df = _load("sample_du_lich.xlsx")
        assert len(df) >= 6

    def test_insured_name_present(self) -> None:
        df = _load("sample_du_lich.xlsx")
        assert "insured_name" in df.columns

    def test_buyer_name_present(self) -> None:
        df = _load("sample_du_lich.xlsx")
        assert "buyer_name" in df.columns

    def test_source_buyer_group_id_present(self) -> None:
        df = _load("sample_du_lich.xlsx")
        assert "source_buyer_group_id" in df.columns

    def test_pham_minh_cuong_group_shares_uuid(self) -> None:
        df = _load("sample_du_lich.xlsx")
        cuong = df[df["buyer_name"] == "Phạm Minh Cường"]
        assert len(cuong) >= 3
        assert cuong["source_buyer_group_id"].nunique() == 1

    def test_all_rows_pass_validate(self) -> None:
        from auto_fill.mapper.validator import validate_record

        df = _load("sample_du_lich.xlsx")
        for _, row in df.iterrows():
            result = validate_record(_normalize(row.to_dict()), "travel")
            assert result.is_valid, f"Row failed: {result.errors}"


class TestSucKhoeSample:
    def test_reads_5_rows(self) -> None:
        df = _load("sample_suc_khoe.xlsx")
        assert len(df) >= 5

    def test_insured_name_present(self) -> None:
        df = _load("sample_suc_khoe.xlsx")
        assert "insured_name" in df.columns

    def test_buyer_name_present(self) -> None:
        df = _load("sample_suc_khoe.xlsx")
        assert "buyer_name" in df.columns

    def test_self_buyer_row_names_match(self) -> None:
        df = _load("sample_suc_khoe.xlsx")
        if "buyer_relation" not in df.columns:
            pytest.skip("buyer_relation column not detected")
        self_rows = df[df["buyer_relation"].str.lower().str.strip() == "bản thân"]
        assert len(self_rows) >= 1
        row = self_rows.iloc[0]
        assert row["buyer_name"] == row["insured_name"]

    def test_dual_dob_pattern2_rows_differ(self) -> None:
        df = _load("sample_suc_khoe.xlsx")
        if "buyer_dob" not in df.columns or "insured_dob" not in df.columns:
            pytest.skip("DOB columns not detected")
        # Row 1: Đỗ Thị Thuận → con Phúc (different DOBs)
        con_rows = df[df["insured_name"].str.contains("Phúc", na=False)]
        if len(con_rows) == 0:
            pytest.skip("Phúc row not found")
        row = con_rows.iloc[0]
        assert (
            row["insured_dob"] != row["buyer_dob"]
        ), "Pattern 2: child DOB should differ from buyer DOB"

    def test_all_rows_pass_validate(self) -> None:
        from auto_fill.mapper.validator import validate_record

        df = _load("sample_suc_khoe.xlsx")
        for _, row in df.iterrows():
            result = validate_record(_normalize(row.to_dict()), "health")
            assert result.is_valid, f"Row failed: {result.errors}"


class TestOtoSample:
    def test_reads_rows(self) -> None:
        df = _load("sample_oto.xlsx")
        assert len(df) >= 1

    def test_plate_number_present(self) -> None:
        df = _load("sample_oto.xlsx")
        assert "plate_number" in df.columns

    def test_all_rows_pass_validate(self) -> None:
        from auto_fill.mapper.validator import validate_record

        df = _load("sample_oto.xlsx")
        for _, row in df.iterrows():
            result = validate_record(_normalize(row.to_dict()), "auto")
            assert result.is_valid, f"Row failed: {result.errors}"


class TestXeMaySample:
    def test_reads_rows(self) -> None:
        df = _load("sample_xe_may.xlsx")
        assert len(df) >= 1

    def test_plate_number_present(self) -> None:
        df = _load("sample_xe_may.xlsx")
        assert "plate_number" in df.columns

    def test_all_rows_pass_validate(self) -> None:
        from auto_fill.mapper.validator import validate_record

        df = _load("sample_xe_may.xlsx")
        for _, row in df.iterrows():
            result = validate_record(_normalize(row.to_dict()), "motorbike")
            assert result.is_valid, f"Row failed: {result.errors}"


class TestHSSVSample:
    def test_reads_6_rows(self) -> None:
        df = _load("sample_hssv.xlsx")
        assert len(df) >= 6

    def test_insured_name_present(self) -> None:
        df = _load("sample_hssv.xlsx")
        assert "insured_name" in df.columns

    def test_all_rows_pass_validate(self) -> None:
        from auto_fill.mapper.validator import validate_record

        df = _load("sample_hssv.xlsx")
        for _, row in df.iterrows():
            result = validate_record(_normalize(row.to_dict()), "student")
            assert result.is_valid, f"Row failed: {result.errors}"
