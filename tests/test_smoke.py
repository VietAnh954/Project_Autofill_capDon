"""Smoke test: import được mọi module top-level."""

from __future__ import annotations


def test_import_main() -> None:
    from auto_fill import __main__  # noqa: F401


def test_import_sheet_registry() -> None:
    from auto_fill.config.sheet_registry import SHEET_REGISTRY

    assert "travel" in SHEET_REGISTRY
    assert SHEET_REGISTRY["travel"].enabled_in_mvp is True


def test_import_errors() -> None:
    from auto_fill.utils.errors import AutoFillError, ReaderError

    assert issubclass(ReaderError, AutoFillError)
