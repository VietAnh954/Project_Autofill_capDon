"""Unit tests cho tools/push_to_postgres.py.

Dung hai SQLite in-memory (khong can Postgres thuc su).
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import push_to_postgres as ptp  # noqa: E402

from auto_fill.db.engine import create_tables, get_engine  # noqa: E402
from auto_fill.db.models import TravelInsurance  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_engine_cache() -> Generator[None, None, None]:
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()


def _make_sqlite(tmp_path: Path, name: str) -> str:
    path = str(tmp_path / name)
    eng = get_engine(path)
    create_tables(eng)
    get_engine.cache_clear()
    return path


def _insert_travel(db_path: str, insured_id: str = "111222333") -> None:
    eng = get_engine(db_path)
    with Session(eng) as s:
        s.add(
            TravelInsurance(
                issued_date=date(2026, 5, 1),
                insured_name="Nguyen Van A",
                insured_id_number=insured_id,
                trip_start=date(2026, 6, 1),
                trip_end=date(2026, 6, 10),
                destination="Japan",
            )
        )
        s.commit()
    get_engine.cache_clear()


class TestPushTable:
    def test_push_copies_row(self, tmp_path: Path) -> None:
        src = _make_sqlite(tmp_path, "src.db")
        dst = _make_sqlite(tmp_path, "dst.db")
        _insert_travel(src)

        src_eng = get_engine(src)
        get_engine.cache_clear()
        dst_eng = get_engine(dst)

        with Session(src_eng) as ss, Session(dst_eng) as ds:
            ins, skip = ptp._push_table(ss, ds, TravelInsurance, dry_run=False)

        assert ins == 1
        assert skip == 0

        get_engine.cache_clear()
        dst_eng2 = get_engine(dst)
        with Session(dst_eng2) as s:
            rows = s.query(TravelInsurance).all()
        assert len(rows) == 1
        assert rows[0].destination == "Japan"

    def test_push_dry_run_does_not_write(self, tmp_path: Path) -> None:
        src = _make_sqlite(tmp_path, "src.db")
        dst = _make_sqlite(tmp_path, "dst.db")
        _insert_travel(src)

        src_eng = get_engine(src)
        get_engine.cache_clear()
        dst_eng = get_engine(dst)

        with Session(src_eng) as ss, Session(dst_eng) as ds:
            ins, _skip = ptp._push_table(ss, ds, TravelInsurance, dry_run=True)

        assert ins == 1  # counted but not written
        get_engine.cache_clear()
        dst_eng2 = get_engine(dst)
        with Session(dst_eng2) as s:
            rows = s.query(TravelInsurance).all()
        assert len(rows) == 0

    def test_push_skips_duplicate(self, tmp_path: Path) -> None:
        src = _make_sqlite(tmp_path, "src.db")
        dst = _make_sqlite(tmp_path, "dst.db")
        _insert_travel(src, insured_id="AAA")
        _insert_travel(dst, insured_id="AAA")  # same unique key in dst

        src_eng = get_engine(src)
        get_engine.cache_clear()
        dst_eng = get_engine(dst)

        with Session(src_eng) as ss, Session(dst_eng) as ds:
            _ins, skip = ptp._push_table(ss, ds, TravelInsurance, dry_run=False)

        # duplicate skipped
        assert skip == 1


class TestCliMain:
    def test_dry_run_no_dst_exits_error(self, tmp_path: Path) -> None:
        src = _make_sqlite(tmp_path, "src.db")
        runner = CliRunner()
        from unittest.mock import MagicMock, patch

        mock_settings = MagicMock()
        mock_settings.db_path = Path(src)
        mock_settings.database_url = None

        with patch("push_to_postgres.Session"), patch(
            "auto_fill.config.settings.settings", mock_settings
        ):
            result = runner.invoke(ptp.main, ["--src", src])
        assert result.exit_code == 1

    def test_dry_run_succeeds(self, tmp_path: Path) -> None:
        src = _make_sqlite(tmp_path, "src.db")
        dst = _make_sqlite(tmp_path, "dst.db")
        _insert_travel(src)

        runner = CliRunner()
        result = runner.invoke(ptp.main, ["--src", src, "--dst", dst, "--dry-run"])
        assert result.exit_code == 0, result.output
        assert "dry-run" in result.output.lower()

    def test_full_push_sqlite_to_sqlite(self, tmp_path: Path) -> None:
        src = _make_sqlite(tmp_path, "src.db")
        dst = _make_sqlite(tmp_path, "dst.db")
        _insert_travel(src)

        runner = CliRunner()
        result = runner.invoke(ptp.main, ["--src", src, "--dst", dst])
        assert result.exit_code == 0, result.output
        assert "inserted=1" in result.output
