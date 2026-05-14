"""Push du lieu tu SQLite local len Postgres (hoac bat ky RDBMS nao).

Usage:
    python tools/push_to_postgres.py --src data/db/autofill.db --dst postgresql+psycopg2://user:pass@host/db
    python tools/push_to_postgres.py --dst postgresql+psycopg2://user:pass@host/db  # dung db_path tu settings
    python tools/push_to_postgres.py --dry-run  # kiem tra ket noi va dem ban ghi

Luu y:
  - Script nay THEM ban ghi vao DB dich (INSERT, bo qua duplicate).
  - Khong xoa du lieu hien co tren DB dich.
  - Chay 'alembic upgrade head' voi DATABASE_URL tro den Postgres truoc khi push.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Ensure src/ is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto_fill.db.engine import create_tables, get_engine  # noqa: E402
from auto_fill.db.models import ALL_MODELS  # noqa: E402


def _push_table(
    src_session: Session,
    dst_session: Session,
    model_cls: type,
    dry_run: bool,
) -> tuple[int, int]:
    """Copy ban ghi tu src sang dst cho 1 model. Tra (inserted, skipped)."""
    mapper = model_cls.__mapper__  # type: ignore[attr-defined]
    col_keys = [col.key for col in mapper.columns if col.key != "id"]

    # Fetch all rows as plain dicts (detached from src session)
    raw_rows: list[Any] = src_session.query(model_cls).all()
    row_dicts: list[dict[str, Any]] = [
        {k: getattr(row, k, None) for k in col_keys} for row in raw_rows
    ]

    inserted = skipped = 0
    for d in row_dicts:
        if dry_run:
            inserted += 1
            continue

        obj = model_cls(**d)
        try:
            dst_session.add(obj)
            dst_session.flush()
            inserted += 1
        except IntegrityError:
            dst_session.rollback()
            skipped += 1

    if not dry_run:
        dst_session.commit()

    return inserted, skipped


@click.command()
@click.option(
    "--src",
    default=None,
    help="SQLite source path. Mac dinh: lay tu settings.db_path.",
)
@click.option(
    "--dst",
    default=None,
    help="Target DB URL (vi du: postgresql+psycopg2://user:pass@host/db). Mac dinh: settings.database_url.",
)
@click.option("--dry-run", is_flag=True, help="Kiem tra ket noi va dem ban ghi, khong ghi.")
def main(src: str | None, dst: str | None, dry_run: bool) -> None:
    """Copy du lieu tu SQLite sang Postgres (hoac DB dich bat ky)."""
    from auto_fill.config.settings import settings
    from auto_fill.db.engine import _build_url

    src_url = _build_url(src) if src else _build_url(str(settings.db_path))
    dst_url = dst or settings.database_url
    if not dst_url:
        click.echo(
            "[error] Chua co DST URL. Set DATABASE_URL trong .env hoac truyen --dst.",
            err=True,
        )
        sys.exit(1)

    click.echo(f"[push] src={src_url}")
    click.echo(f"[push] dst={dst_url}")
    click.echo(f"[push] dry_run={dry_run}")

    src_engine = get_engine(src_url)
    get_engine.cache_clear()  # allow dst engine
    dst_engine = get_engine(dst_url)

    if not dry_run:
        create_tables(dst_engine)

    total_ins = total_skip = 0
    with Session(src_engine) as src_s, Session(dst_engine) as dst_s:
        for model_cls in ALL_MODELS:
            ins, skip = _push_table(src_s, dst_s, model_cls, dry_run)
            table = model_cls.__tablename__
            click.echo(f"  {table}: inserted={ins} skipped={skip}")
            total_ins += ins
            total_skip += skip

    click.echo(f"[push] Hoan tat. Total inserted={total_ins} skipped={total_skip}")
    if dry_run:
        click.echo("[push] (dry-run: khong co gi duoc ghi)")


if __name__ == "__main__":
    main()
