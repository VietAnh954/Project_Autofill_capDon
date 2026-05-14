"""Unit tests cho db/models.py va db/engine.py."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.orm import Session

from auto_fill.db.engine import create_tables, get_engine
from auto_fill.db.models import (
    ALL_MODELS,
    AutoInsurance,
    BhytBhxhInsurance,
    HealthInsurance,
    MotorbikeInsurance,
    StudentInsurance,
    TravelInsurance,
)


@pytest.fixture()
def engine(tmp_path: Path) -> Generator[Engine, None, None]:
    get_engine.cache_clear()
    eng = get_engine(str(tmp_path / "test.db"))
    create_tables(eng)
    yield eng
    get_engine.cache_clear()


class TestCreateTables:
    def test_all_tables_created(self, engine: Engine) -> None:
        insp = inspect(engine)
        table_names = insp.get_table_names()
        expected = {
            "travel_insurance",
            "auto_insurance",
            "motorbike_insurance",
            "health_insurance",
            "bhyt_bhxh_insurance",
            "student_insurance",
        }
        assert expected.issubset(set(table_names))

    def test_create_tables_idempotent(self, engine: Engine) -> None:
        create_tables(engine)
        create_tables(engine)
        insp = inspect(engine)
        assert len(insp.get_table_names()) == 6


class TestTravelInsurance:
    def test_insert_and_query(self, engine: Engine) -> None:
        row = TravelInsurance(
            issued_date=date(2026, 5, 1),
            insured_name="Nguyen Van A",
            trip_start=date(2026, 6, 1),
            trip_end=date(2026, 6, 10),
            destination="Japan",
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(TravelInsurance).first()
        assert result is not None
        assert result.insured_name == "Nguyen Van A"
        assert result.destination == "Japan"

    def test_unique_constraint_duplicate(self, engine: Engine) -> None:
        from sqlalchemy.exc import IntegrityError

        r1 = TravelInsurance(
            issued_date=date(2026, 5, 1),
            insured_name="Nguyen Van A",
            trip_start=date(2026, 6, 1),
            trip_end=date(2026, 6, 10),
            insured_id_number="123456789",
            destination="Japan",
        )
        r2 = TravelInsurance(
            issued_date=date(2026, 5, 2),
            insured_name="Nguyen Van A",
            trip_start=date(2026, 6, 1),
            trip_end=date(2026, 6, 10),
            insured_id_number="123456789",
            destination="Japan",
        )
        with Session(engine) as s:
            s.add(r1)
            s.commit()

        with pytest.raises(IntegrityError), Session(engine) as s:
            s.add(r2)
            s.commit()

    def test_audit_fields_nullable(self, engine: Engine) -> None:
        row = TravelInsurance(
            issued_date=date(2026, 5, 1),
            insured_name="Test",
            trip_start=date(2026, 6, 1),
            trip_end=date(2026, 6, 5),
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(TravelInsurance).first()
        assert result is not None
        assert result.source_email_id is None
        assert result.source_attachment is None


class TestAutoInsurance:
    def test_insert(self, engine: Engine) -> None:
        row = AutoInsurance(
            issued_date=date(2026, 5, 1),
            plate_number="51A-123.45",
            insured_name="Tran Van B",
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(AutoInsurance).first()
        assert result is not None
        assert result.plate_number == "51A-123.45"

    def test_unique_plate_date(self, engine: Engine) -> None:
        from sqlalchemy.exc import IntegrityError

        r1 = AutoInsurance(issued_date=date(2026, 5, 1), plate_number="51A-000.01")
        r2 = AutoInsurance(issued_date=date(2026, 5, 1), plate_number="51A-000.01")
        with Session(engine) as s:
            s.add(r1)
            s.commit()
        with pytest.raises(IntegrityError), Session(engine) as s:
            s.add(r2)
            s.commit()


class TestMotorbikeInsurance:
    def test_insert(self, engine: Engine) -> None:
        row = MotorbikeInsurance(
            issued_date=date(2026, 5, 1),
            plate_number="59P1-12345",
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(MotorbikeInsurance).first()
        assert result is not None
        assert result.plate_number == "59P1-12345"


class TestHealthInsurance:
    def test_insert(self, engine: Engine) -> None:
        row = HealthInsurance(
            insured_name="Le Thi C",
            insured_id_number="999888777",
            effective_from=date(2026, 1, 1),
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(HealthInsurance).first()
        assert result is not None
        assert result.insured_name == "Le Thi C"


class TestBhytBhxhInsurance:
    def test_insert(self, engine: Engine) -> None:
        row = BhytBhxhInsurance(
            insured_name="Pham Van D",
            insured_id_number="111222333",
            effective_from=date(2026, 1, 1),
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(BhytBhxhInsurance).first()
        assert result is not None


class TestStudentInsurance:
    def test_insert(self, engine: Engine) -> None:
        row = StudentInsurance(
            issued_date=date(2026, 9, 1),
            insured_name="Nguyen Thi E",
            school="THPT Nguyen Du",
        )
        with Session(engine) as s:
            s.add(row)
            s.commit()
            result = s.query(StudentInsurance).first()
        assert result is not None
        assert result.school == "THPT Nguyen Du"


class TestAllModels:
    def test_all_models_in_registry(self) -> None:
        assert len(ALL_MODELS) == 6

    def test_all_models_have_id_pk(self) -> None:
        for model in ALL_MODELS:
            assert hasattr(model, "id")

    def test_all_models_have_audit_fields(self) -> None:
        for model in ALL_MODELS:
            assert hasattr(model, "source_email_id")
            assert hasattr(model, "created_at")
