"""Unit tests cho Backup."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from auto_fill.filler.backup import snapshot


class TestSnapshot:
    def test_creates_backup_file(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"dummy")
        backup_root = tmp_path / "backup"
        dest = snapshot(source, backup_root, today=date(2026, 5, 14))
        assert dest.exists()
        assert dest.read_bytes() == b"dummy"

    def test_backup_dir_named_by_date(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "backup"
        dest = snapshot(source, backup_root, today=date(2026, 5, 14))
        assert dest.parent.name == "2026-05-14"

    def test_backup_filename_matches_source(self, tmp_path: Path) -> None:
        source = tmp_path / "Danh sach cap don.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "backup"
        dest = snapshot(source, backup_root, today=date(2026, 5, 14))
        assert dest.name == source.name

    def test_source_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            snapshot(tmp_path / "missing.xlsx", tmp_path / "backup")

    def test_backup_root_created_if_not_exists(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "deep" / "backup"
        snapshot(source, backup_root, today=date(2026, 5, 14))
        assert backup_root.exists()

    def test_old_backups_purged(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "backup"
        # Pre-create an old folder (35 days ago)
        old_dir = backup_root / "2026-04-09"
        old_dir.mkdir(parents=True)
        (old_dir / "master.xlsx").write_bytes(b"old")
        snapshot(source, backup_root, today=date(2026, 5, 14), max_days=30)
        assert not old_dir.exists()

    def test_recent_backups_kept(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "backup"
        # Pre-create a recent folder (5 days ago)
        recent_dir = backup_root / "2026-05-09"
        recent_dir.mkdir(parents=True)
        (recent_dir / "master.xlsx").write_bytes(b"recent")
        snapshot(source, backup_root, today=date(2026, 5, 14), max_days=30)
        assert recent_dir.exists()

    def test_invalid_dir_names_skipped(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "backup"
        junk_dir = backup_root / "not-a-date"
        junk_dir.mkdir(parents=True)
        snapshot(source, backup_root, today=date(2026, 5, 14), max_days=0)
        assert junk_dir.exists()

    def test_second_backup_same_day_overwrites(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"v1")
        backup_root = tmp_path / "backup"
        snapshot(source, backup_root, today=date(2026, 5, 14))
        source.write_bytes(b"v2")
        dest = snapshot(source, backup_root, today=date(2026, 5, 14))
        assert dest.read_bytes() == b"v2"

    def test_returns_correct_path(self, tmp_path: Path) -> None:
        source = tmp_path / "master.xlsx"
        source.write_bytes(b"x")
        backup_root = tmp_path / "backup"
        dest = snapshot(source, backup_root, today=date(2026, 5, 14))
        assert dest == backup_root / "2026-05-14" / "master.xlsx"
