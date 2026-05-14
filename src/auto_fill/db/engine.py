"""SQLAlchemy engine factory.

Tao engine tu db_path (SQLite) hoac DATABASE_URL (Postgres / bat ky RDBMS nao).
Goi get_engine() de lay engine singleton (cached).
Goi create_tables() de tao schema lan dau (idempotent).

DATABASE_URL priority:
  1. Truyen truc tiep vao get_engine() duoi dang full URL (co "://")
  2. settings.database_url (.env DATABASE_URL=postgresql://...)
  3. settings.db_path -> sqlite:///path  (mac dinh)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine

from auto_fill.db.models import Base


def _build_url(db_path_or_url: str) -> str:
    """Chuyen doi db_path hoac full URL thanh SQLAlchemy URL string."""
    if "://" in db_path_or_url:
        return db_path_or_url
    path = Path(db_path_or_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


@lru_cache(maxsize=1)
def get_engine(db_path: str) -> Engine:
    """Tra engine singleton.

    db_path co the la:
    - Duong dan file SQLite (vi du: "data/db/autofill.db")
    - Full SQLAlchemy URL (vi du: "postgresql+psycopg2://user:pass@host/db")
    """
    url = _build_url(db_path)
    return create_engine(url, echo=False)


def create_tables(engine: Engine) -> None:
    """Tao tat ca tables neu chua ton tai (idempotent)."""
    Base.metadata.create_all(engine)


def get_db_url_from_settings() -> str:
    """Lay SQLAlchemy URL tu settings (DATABASE_URL hoac db_path)."""
    from auto_fill.config.settings import settings

    if settings.database_url:
        return settings.database_url
    return _build_url(str(settings.db_path))
