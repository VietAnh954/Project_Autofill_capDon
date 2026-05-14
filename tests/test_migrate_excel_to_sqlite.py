"""Unit tests cho tools/migrate_excel_to_sqlite.py."""

from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
import pytest

# Ensure tools/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from migrate_excel_to_sqlite import _SHEET_CONFIG, _migrate_sheet, _normalize  # noqa: E402


@pytest.fixture()
def travel_excel(tmp_path: Path) -> Path:
    path = tmp_path / "test.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Du lịch"
    ws.append(
        [
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
    )
    ws.append(
        [
            "2026-05-01",
            1,
            "Nguyen Van A",
            "1990-01-01",
            "123456789",
            None,
            "2026-06-01",
            "2026-06-10",
            9,
            "Japan",
            "Toan cau",
            "Ca nhan",
            "PlanA",
            500000,
            "Nguyen Van B",
        ]
    )
    wb.save(path)
    return path


class TestNormalize:
    def test_date_field_normalizes(self) -> None:
        result = _normalize("issued_date", "01/05/2026")
        from datetime import date

        assert result == date(2026, 5, 1)

    def test_money_field_normalizes(self) -> None:
        result = _normalize("premium", "1,000,000")
        assert result == 1_000_000.0

    def test_none_returns_none(self) -> None:
        assert _normalize("issued_date", None) is None

    def test_unknown_field_passthrough(self) -> None:
        assert _normalize("unknown_field", "hello") == "hello"


class TestMigrateSheet:
    def test_dry_run_returns_count(self, tmp_path: Path, travel_excel: Path) -> None:
        field_map = {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "trip_start": "trip_start",
            "trip_end": "trip_end",
        }
        from auto_fill.db.models import TravelInsurance

        ins, skip = _migrate_sheet(
            excel_path=travel_excel,
            db_path=tmp_path / "test.db",
            sheet_name="Du lịch",
            model_cls=TravelInsurance,
            field_map=field_map,
            dry_run=True,
        )
        assert ins == 1
        assert skip == 0

    def test_missing_sheet_warns_and_returns_zero(self, tmp_path: Path, travel_excel: Path) -> None:
        from auto_fill.db.models import TravelInsurance

        ins, skip = _migrate_sheet(
            excel_path=travel_excel,
            db_path=tmp_path / "test.db",
            sheet_name="NonExistent",
            model_cls=TravelInsurance,
            field_map={"insured_name": "insured_name"},
            dry_run=True,
        )
        assert ins == 0
        assert skip == 0

    def test_real_insert(self, tmp_path: Path, travel_excel: Path) -> None:
        from sqlalchemy.orm import Session

        from auto_fill.db.engine import create_tables, get_engine
        from auto_fill.db.models import TravelInsurance

        get_engine.cache_clear()
        db_path = tmp_path / "real.db"
        engine = get_engine(str(db_path))
        create_tables(engine)

        field_map = {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "insured_id_number": "insured_id_number",
            "trip_start": "trip_start",
            "trip_end": "trip_end",
            "destination": "destination",
        }
        ins, skip = _migrate_sheet(
            excel_path=travel_excel,
            db_path=db_path,
            sheet_name="Du lịch",
            model_cls=TravelInsurance,
            field_map=field_map,
            dry_run=False,
        )
        assert ins == 1
        assert skip == 0

        with Session(engine) as s:
            row = s.query(TravelInsurance).first()
        assert row is not None
        assert row.insured_name == "Nguyen Van A"
        get_engine.cache_clear()

    def test_duplicate_skipped(self, tmp_path: Path, travel_excel: Path) -> None:
        from auto_fill.db.engine import create_tables, get_engine
        from auto_fill.db.models import TravelInsurance

        get_engine.cache_clear()
        db_path = tmp_path / "dup.db"
        engine = get_engine(str(db_path))
        create_tables(engine)

        field_map = {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "insured_id_number": "insured_id_number",
            "trip_start": "trip_start",
            "trip_end": "trip_end",
            "destination": "destination",
        }
        _migrate_sheet(
            excel_path=travel_excel,
            db_path=db_path,
            sheet_name="Du lịch",
            model_cls=TravelInsurance,
            field_map=field_map,
            dry_run=False,
        )
        ins, skip = _migrate_sheet(
            excel_path=travel_excel,
            db_path=db_path,
            sheet_name="Du lịch",
            model_cls=TravelInsurance,
            field_map=field_map,
            dry_run=False,
        )
        assert ins == 0
        assert skip == 1
        get_engine.cache_clear()


class TestSheetConfig:
    def test_all_6_sheets_configured(self) -> None:
        assert len(_SHEET_CONFIG) == 6

    def test_each_entry_has_3_elements(self) -> None:
        for entry in _SHEET_CONFIG:
            assert len(entry) == 3

    def test_field_maps_not_empty(self) -> None:
        for _, _, field_map in _SHEET_CONFIG:
            assert len(field_map) > 0
