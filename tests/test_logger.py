"""Unit tests cho Logger setup."""

from __future__ import annotations

import logging
from pathlib import Path

from loguru import logger

from auto_fill.utils.logger import _InterceptHandler, setup_logging


class TestSetupLogging:
    def test_console_only_does_not_raise(self) -> None:
        setup_logging(log_dir=None, level="INFO", json=False)

    def test_creates_log_dir(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir, level="INFO", json=True)
        assert log_dir.exists()

    def test_log_file_created(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir, level="INFO", json=False)
        logger.info("test message")
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) >= 1

    def test_intercept_handler_installed(self) -> None:
        setup_logging(log_dir=None, level="INFO")
        root_handlers = logging.root.handlers
        assert any(isinstance(h, _InterceptHandler) for h in root_handlers)

    def test_stdlib_logging_does_not_raise(self) -> None:
        setup_logging(log_dir=None, level="INFO")
        lg = logging.getLogger("test_stdlib")
        lg.info("stdlib log message")

    def test_debug_level_accepted(self) -> None:
        setup_logging(log_dir=None, level="DEBUG")

    def test_nested_log_dir_created(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "deep" / "nested" / "logs"
        setup_logging(log_dir=log_dir, level="WARNING")
        assert log_dir.exists()


class TestInterceptHandler:
    def test_emit_info_does_not_raise(self) -> None:
        setup_logging(log_dir=None, level="DEBUG")
        handler = _InterceptHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

    def test_emit_unknown_level_does_not_raise(self) -> None:
        setup_logging(log_dir=None, level="DEBUG")
        handler = _InterceptHandler()
        record = logging.LogRecord(
            name="test",
            level=99,
            pathname=__file__,
            lineno=1,
            msg="custom level",
            args=(),
            exc_info=None,
        )
        handler.emit(record)
