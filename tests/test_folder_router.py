"""Tests for folder_router.route_mail() — mail routing after pipeline."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from auto_fill.mail.folder_router import (
    FOLDER_NEEDS_REVIEW,
    FOLDER_PROCESSED,
    FOLDER_SKIPPED,
    _decide_folder,
    route_mail,
)

TODAY = date.today().strftime("%Y-%m-%d")


# ── _decide_folder unit tests ────────────────────────────────────────────────


class TestDecideFolder:
    def test_type_a_success(self) -> None:
        assert _decide_folder("A", True) == f"{FOLDER_PROCESSED}/{TODAY}"

    def test_type_b_success(self) -> None:
        assert _decide_folder("B", True) == f"{FOLDER_PROCESSED}/{TODAY}"

    def test_type_a_fail(self) -> None:
        assert _decide_folder("A", False) == FOLDER_NEEDS_REVIEW

    def test_type_b_fail(self) -> None:
        assert _decide_folder("B", False) == FOLDER_NEEDS_REVIEW

    def test_type_c(self) -> None:
        assert _decide_folder("C", True) == FOLDER_NEEDS_REVIEW
        assert _decide_folder("C", False) == FOLDER_NEEDS_REVIEW

    def test_type_d(self) -> None:
        assert _decide_folder("D", True) == f"{FOLDER_SKIPPED}/{TODAY}"
        assert _decide_folder("D", False) == f"{FOLDER_SKIPPED}/{TODAY}"

    def test_review(self) -> None:
        assert _decide_folder("review", True) == FOLDER_NEEDS_REVIEW

    def test_unknown_type(self) -> None:
        assert _decide_folder("X", True) == FOLDER_NEEDS_REVIEW


# ── route_mail integration tests ────────────────────────────────────────────


class TestRouteMail:
    def _make_client(self) -> MagicMock:
        client = MagicMock()
        client.move_to_nested_folder = MagicMock()
        return client

    def test_type_a_success_calls_move_to_processed(self) -> None:
        client = self._make_client()
        path = route_mail("entry-001", "A", True, client)
        assert path == f"{FOLDER_PROCESSED}/{TODAY}"
        client.move_to_nested_folder.assert_called_once_with(
            "entry-001", f"{FOLDER_PROCESSED}/{TODAY}"
        )

    def test_type_d_calls_move_to_skipped(self) -> None:
        client = self._make_client()
        path = route_mail("entry-002", "D", True, client)
        assert path == f"{FOLDER_SKIPPED}/{TODAY}"
        client.move_to_nested_folder.assert_called_once_with(
            "entry-002", f"{FOLDER_SKIPPED}/{TODAY}"
        )

    def test_type_c_calls_move_to_needs_review(self) -> None:
        client = self._make_client()
        path = route_mail("entry-003", "C", False, client)
        assert path == FOLDER_NEEDS_REVIEW
        client.move_to_nested_folder.assert_called_once_with("entry-003", FOLDER_NEEDS_REVIEW)

    def test_type_a_fail_calls_needs_review(self) -> None:
        client = self._make_client()
        path = route_mail("entry-004", "A", False, client)
        assert path == FOLDER_NEEDS_REVIEW

    def test_fallback_to_move_to_folder_when_no_nested(self) -> None:
        """When client lacks move_to_nested_folder, falls back to move_to_folder."""
        client = MagicMock(spec=["move_to_folder"])
        path = route_mail("entry-005", "A", True, client)
        assert path == f"{FOLDER_PROCESSED}/{TODAY}"
        client.move_to_folder.assert_called_once_with("entry-005", FOLDER_PROCESSED)

    def test_move_exception_does_not_raise(self) -> None:
        """Router should log and swallow move errors (don't crash the pipeline)."""
        client = MagicMock()
        client.move_to_nested_folder.side_effect = Exception("COM error")
        path = route_mail("entry-006", "B", True, client)
        assert path == f"{FOLDER_PROCESSED}/{TODAY}"
