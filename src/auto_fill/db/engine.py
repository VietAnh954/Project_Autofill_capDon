"""SQLAlchemy engine factory.

Tạo engine SQLite từ đường dẫn DB trong settings.
Gọi `get_engine()` để lấy engine singleton (cached).
Gọi `create_tables()` để tạo schema lần đầu (idempotent).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine

from auto_fill.db.models import Base


@lru_cache(maxsize=1)
def get_engine(db_path: str) -> Engine:
    """Trả engine SQLite singleton cho db_path."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", echo=False)


def create_tables(engine: Engine) -> None:
    """Tạo tất cả tables nếu chưa tồn tại (idempotent)."""
    Base.metadata.create_all(engine)
