"""Logger — cau hinh loguru JSON cho toan pipeline.

Goi setup_logging() mot lan khi khoi dong (CLI entry).
Cac module khac dung stdlib logging nhu binh thuong;
loguru intercept va format lai thanh JSON.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger

_LOGURU_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}"


class _InterceptHandler(logging.Handler):
    """Chuyen stdlib logging records sang loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(
    log_dir: Path | None = None,
    level: str = "INFO",
    json: bool = True,
    rotation: str = "00:00",
    retention: str = "30 days",
) -> None:
    """Cau hinh loguru: console + file JSON.

    Args:
        log_dir: Thu muc chua file log. None = chi log ra console.
        level: Log level (DEBUG/INFO/WARNING/ERROR).
        json: True = serialize log line thanh JSON (cho production).
              False = human-readable (cho dev / test).
        rotation: Thoi diem xoay vong file log (loguru format).
        retention: Giu file log bao lau truoc khi xoa.
    """
    logger.remove()

    # Console sink
    logger.add(
        sys.stderr,
        level=level,
        format=_LOGURU_FORMAT,
        colorize=not json,
        serialize=False,
    )

    # File sink (JSON)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "auto_fill_{time:YYYY-MM-DD}.log",
            level=level,
            rotation=rotation,
            retention=retention,
            serialize=json,
            encoding="utf-8",
        )

    # Intercept stdlib logging
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in logging.root.manager.loggerDict:
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True
