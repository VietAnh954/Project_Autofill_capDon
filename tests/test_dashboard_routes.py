"""Tests cho web dashboard routes va pipeline control endpoints."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from auto_fill.api.app import app
from auto_fill.api.pipeline_state import state as pipeline_state


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_pipeline_state() -> Generator[None, None, None]:
    """Dam bao pipeline state sach giua cac test."""
    pipeline_state.status = "idle"
    pipeline_state.started_at = None
    pipeline_state.finished_at = None
    pipeline_state.error = None
    pipeline_state.logs.clear()
    yield
    pipeline_state.status = "idle"
    pipeline_state.logs.clear()


# ── Dashboard HTML pages ────────────────────────────────────────────────── #


def test_root_redirects_to_dashboard(client: TestClient) -> None:
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (301, 302, 307, 308)
    assert "/dashboard" in r.headers["location"]


def test_dashboard_page_returns_html(client: TestClient) -> None:
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "AutoFill" in r.text


def test_records_page_returns_html(client: TestClient) -> None:
    r = client.get("/dashboard/records")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


# ── Pipeline status ─────────────────────────────────────────────────────── #


def test_pipeline_status_initial(client: TestClient) -> None:
    r = client.get("/pipeline/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "idle"
    assert data["error"] is None


def test_pipeline_status_after_state_change(client: TestClient) -> None:
    pipeline_state.status = "done"
    pipeline_state.error = None
    r = client.get("/pipeline/status")
    assert r.json()["status"] == "done"


# ── Pipeline run ────────────────────────────────────────────────────────── #


def test_pipeline_run_starts_when_idle(client: TestClient) -> None:
    with patch("auto_fill.api.app.run_pipeline", return_value=True) as mock_run:
        r = client.post("/pipeline/run", json={"dry_run": True})
        assert r.status_code == 200
        data = r.json()
        assert data["started"] is True
        mock_run.assert_called_once_with(dry_run=True)


def test_pipeline_run_blocked_when_running(client: TestClient) -> None:
    with patch("auto_fill.api.app.run_pipeline", return_value=False):
        r = client.post("/pipeline/run", json={"dry_run": False})
        assert r.status_code == 200
        assert r.json()["started"] is False


def test_pipeline_run_default_dry_run_false(client: TestClient) -> None:
    with patch("auto_fill.api.app.run_pipeline", return_value=True) as mock_run:
        r = client.post("/pipeline/run", json={})
        assert r.status_code == 200
        mock_run.assert_called_once_with(dry_run=False)


# ── Pipeline logs SSE ───────────────────────────────────────────────────── #


def test_pipeline_logs_stream_endpoint_registered(client: TestClient) -> None:
    """SSE endpoint phai duoc dang ky (khong tra 404/405).

    Khong consume stream de tranh hang trong test do infinite generator.
    """
    from auto_fill.api.app import app as fastapi_app

    routes = [getattr(r, "path", "") for r in fastapi_app.routes]
    assert "/pipeline/logs/stream" in routes


def test_pipeline_state_add_log(client: TestClient) -> None:
    """pipeline_state.logs ghi nhan va tra ve dung."""
    pipeline_state.logs.clear()
    pipeline_state.logs.append("[10:00:00] Test entry")
    assert len(pipeline_state.logs) == 1
    assert "Test entry" in pipeline_state.logs[0]

    # Status endpoint phai tra ve log_count dung
    r = client.get("/pipeline/status")
    assert r.json()["log_count"] == 1


# ── Existing API still works ────────────────────────────────────────────── #


def test_health_endpoint(client: TestClient) -> None:
    r = client.get("/health")
    # DB may not be present in CI; 200 or 503 both acceptable
    assert r.status_code in (200, 503)


def test_stats_endpoint(client: TestClient) -> None:
    r = client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
