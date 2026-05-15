"""Tests for ProcessedTracker — anti-double-processing layer 2."""

from __future__ import annotations

from pathlib import Path

from auto_fill.mail.processed_tracker import ProcessedTracker


class TestLoadAndPersist:
    def test_new_tracker_is_empty(self, tmp_path: Path) -> None:
        tracker = ProcessedTracker(tmp_path / "ids.txt")
        assert len(tracker) == 0

    def test_mark_and_check(self, tmp_path: Path) -> None:
        tracker = ProcessedTracker(tmp_path / "ids.txt")
        tracker.mark_processed("entry-001")
        assert tracker.is_processed("entry-001")

    def test_unknown_id_not_processed(self, tmp_path: Path) -> None:
        tracker = ProcessedTracker(tmp_path / "ids.txt")
        assert not tracker.is_processed("entry-999")

    def test_persists_to_file(self, tmp_path: Path) -> None:
        state = tmp_path / "ids.txt"
        tracker = ProcessedTracker(state)
        tracker.mark_processed("entry-abc")
        assert state.exists()
        assert "entry-abc" in state.read_text(encoding="utf-8")

    def test_reloads_from_file(self, tmp_path: Path) -> None:
        state = tmp_path / "ids.txt"
        t1 = ProcessedTracker(state)
        t1.mark_processed("entry-abc")
        t2 = ProcessedTracker(state)
        assert t2.is_processed("entry-abc")

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        state = tmp_path / "sub1" / "sub2" / "ids.txt"
        tracker = ProcessedTracker(state)
        tracker.mark_processed("x")
        assert state.exists()

    def test_duplicate_mark_does_not_duplicate_line(self, tmp_path: Path) -> None:
        state = tmp_path / "ids.txt"
        tracker = ProcessedTracker(state)
        tracker.mark_processed("entry-dup")
        tracker.mark_processed("entry-dup")
        lines = [line for line in state.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert lines.count("entry-dup") == 1

    def test_multiple_ids(self, tmp_path: Path) -> None:
        tracker = ProcessedTracker(tmp_path / "ids.txt")
        for i in range(5):
            tracker.mark_processed(f"id-{i:03d}")
        assert len(tracker) == 5
        assert tracker.is_processed("id-003")

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        tracker = ProcessedTracker(tmp_path / "nonexistent.txt")
        assert len(tracker) == 0


class TestFetcherIntegration:
    """Integration: fetcher skips already-tracked IDs."""

    def test_fetcher_skips_tracked_mail(self, tmp_path: Path) -> None:
        from collections.abc import Iterator
        from datetime import datetime
        from typing import cast
        from unittest.mock import MagicMock

        from auto_fill.mail.fetcher import MailFetcher
        from auto_fill.mail.outlook_client import MailMessage, OutlookClient

        already_done = MailMessage(
            entry_id="id-already",
            subject="Cấp đơn du lịch",
            sender_email="sale@pti.com.vn",
            received_at=datetime(2026, 5, 14),
        )
        new_mail = MailMessage(
            entry_id="id-new",
            subject="Cấp đơn du lịch",
            sender_email="sale@pti.com.vn",
            received_at=datetime(2026, 5, 15),
        )

        client = MagicMock(spec=OutlookClient)

        def _iter(folder: object = None) -> Iterator[MailMessage]:
            yield already_done
            yield new_mail

        cast(MagicMock, client.iter_unread).side_effect = _iter
        cast(MagicMock, client.resolve_folder).return_value = MagicMock()

        tracker = ProcessedTracker(tmp_path / "ids.txt")
        tracker.mark_processed("id-already")

        fetcher = MailFetcher(client, {"sale@pti.com.vn"}, r"c[áaấ]p", tracker=tracker)
        result = list(fetcher.fetch_matching())
        assert len(result) == 1
        assert result[0].entry_id == "id-new"
