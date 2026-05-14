"""Unit tests cho db/repository.py."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from auto_fill.db.engine import create_tables, get_engine
from auto_fill.db.models import TravelInsurance
from auto_fill.db.repository import insert_record


@pytest.fixture()
def db_path(tmp_path: Path) -> Generator[str, None, None]:
    get_engine.cache_clear()
    path = str(tmp_path / "test.db")
    engine = get_engine(path)
    create_tables(engine)
    yield path
    get_engine.cache_clear()


_TRAVEL_RECORD = {
    "issued_date": date(2026, 5, 1),
    "insured_name": "Nguyen Van A",
    "insured_id_number": "123456789",
    "trip_start": date(2026, 6, 1),
    "trip_end": date(2026, 6, 10),
    "destination": "Japan",
    "premium": 500_000.0,
}


class TestInsertRecord:
    def test_insert_travel(self, db_path: str) -> None:
        result = insert_record(_TRAVEL_RECORD, "travel", db_path)
        assert result is True

        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(TravelInsurance).first()
        assert row is not None
        assert row.insured_name == "Nguyen Van A"
        assert row.destination == "Japan"

    def test_duplicate_returns_false(self, db_path: str) -> None:
        insert_record(_TRAVEL_RECORD, "travel", db_path)
        result = insert_record(_TRAVEL_RECORD, "travel", db_path)
        assert result is False

    def test_source_fields_stored(self, db_path: str) -> None:
        insert_record(
            _TRAVEL_RECORD,
            "travel",
            db_path,
            source_email_id="msg_001",
            source_attachment="attachment.xlsx",
        )
        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(TravelInsurance).first()
        assert row is not None
        assert row.source_email_id == "msg_001"
        assert row.source_attachment == "attachment.xlsx"

    def test_unknown_alias_raises(self, db_path: str) -> None:
        with pytest.raises(KeyError):
            insert_record(_TRAVEL_RECORD, "unknown_sheet", db_path)

    def test_insert_auto(self, db_path: str) -> None:
        from auto_fill.db.models import AutoInsurance

        record = {
            "issued_date": date(2026, 5, 1),
            "plate_number": "51A-123.45",
            "insured_name": "Tran Van B",
        }
        result = insert_record(record, "auto", db_path)
        assert result is True

        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(AutoInsurance).first()
        assert row is not None
        assert row.plate_number == "51A-123.45"

    def test_insert_motorbike(self, db_path: str) -> None:
        from auto_fill.db.models import MotorbikeInsurance

        record = {
            "issued_date": date(2026, 5, 1),
            "plate_number": "59P1-00001",
            "customer_name": "Le Van C",
        }
        result = insert_record(record, "motorbike", db_path)
        assert result is True

        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(MotorbikeInsurance).first()
        assert row is not None

    def test_insert_health(self, db_path: str) -> None:
        from auto_fill.db.models import HealthInsurance

        record = {
            "insured_name": "Pham Thi D",
            "insured_id_number": "987654321",
            "effective_from": date(2026, 1, 1),
        }
        result = insert_record(record, "health", db_path)
        assert result is True

        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(HealthInsurance).first()
        assert row is not None

    def test_insert_bhyt_bhxh(self, db_path: str) -> None:
        from auto_fill.db.models import BhytBhxhInsurance

        record = {
            "insured_name": "Vo Van E",
            "insured_id_number": "111222333",
            "effective_from": date(2026, 1, 1),
        }
        result = insert_record(record, "bhyt_bhxh", db_path)
        assert result is True

        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(BhytBhxhInsurance).first()
        assert row is not None

    def test_insert_student(self, db_path: str) -> None:
        from auto_fill.db.models import StudentInsurance

        record = {
            "issued_date": date(2026, 9, 1),
            "insured_name": "Nguyen Thi F",
            "school": "THPT ABC",
        }
        result = insert_record(record, "student", db_path)
        assert result is True

        engine = get_engine(db_path)
        with Session(engine) as s:
            row = s.query(StudentInsurance).first()
        assert row is not None
