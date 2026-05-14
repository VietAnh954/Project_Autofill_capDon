"""Unit tests cho FastAPI endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from auto_fill.db.engine import create_tables, get_engine
from auto_fill.db.models import TravelInsurance


@pytest.fixture()
def db_path(tmp_path: Path) -> Generator[str, None, None]:
    get_engine.cache_clear()
    path = str(tmp_path / "test.db")
    engine = get_engine(path)
    create_tables(engine)

    with Session(engine) as s:
        s.add(
            TravelInsurance(
                issued_date=date(2026, 5, 1),
                insured_name="Nguyen Van A",
                insured_id_number="111222333",
                trip_start=date(2026, 6, 1),
                trip_end=date(2026, 6, 10),
                destination="Japan",
                premium=500_000.0,
            )
        )
        s.commit()

    yield path
    get_engine.cache_clear()


@pytest.fixture()
def client(db_path: str) -> Generator[TestClient, None, None]:
    from auto_fill.api.app import app

    with patch("auto_fill.api.app.get_db_url_from_settings", return_value=db_path):
        yield TestClient(app)


class TestHealthEndpoint:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"


class TestStatsEndpoint:
    def test_stats_returns_counts(self, client: TestClient) -> None:
        resp = client.get("/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["travel"] == 1
        assert body["total"] >= 1

    def test_stats_has_all_sheets(self, client: TestClient) -> None:
        resp = client.get("/stats")
        body = resp.json()
        for sheet in ("travel", "auto", "motorbike", "health", "bhyt_bhxh", "student"):
            assert sheet in body


class TestRecordsEndpoint:
    def test_list_travel_records(self, client: TestClient) -> None:
        resp = client.get("/records/travel")
        assert resp.status_code == 200
        records = resp.json()
        assert len(records) == 1
        assert records[0]["sheet"] == "travel"
        assert records[0]["data"]["destination"] == "Japan"

    def test_list_unknown_sheet_404(self, client: TestClient) -> None:
        resp = client.get("/records/unknown_sheet")
        assert resp.status_code == 404

    def test_get_record_by_id(self, client: TestClient) -> None:
        resp = client.get("/records/travel/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_record_not_found(self, client: TestClient) -> None:
        resp = client.get("/records/travel/9999")
        assert resp.status_code == 404

    def test_filter_by_name(self, client: TestClient) -> None:
        resp = client.get("/records/travel?insured_name=Nguyen")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filter_by_name_no_match(self, client: TestClient) -> None:
        resp = client.get("/records/travel?insured_name=XYZNotExist")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_skip_limit(self, client: TestClient) -> None:
        resp = client.get("/records/travel?skip=1&limit=10")
        assert resp.status_code == 200
        assert len(resp.json()) == 0  # only 1 record, skip=1


class TestExportEndpoint:
    def test_export_sheet_xlsx(self, client: TestClient) -> None:
        resp = client.get("/export/travel")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]
        assert len(resp.content) > 0

    def test_export_all_xlsx(self, client: TestClient) -> None:
        resp = client.get("/export")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    def test_export_unknown_sheet_404(self, client: TestClient) -> None:
        resp = client.get("/export/unknown_sheet")
        assert resp.status_code == 404


class TestCliServeCommand:
    def test_serve_command_registered(self) -> None:
        from auto_fill.__main__ import cli

        assert "serve" in cli.commands
