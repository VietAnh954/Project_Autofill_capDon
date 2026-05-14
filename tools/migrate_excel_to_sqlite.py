"""1-shot migration: doc tung sheet Excel → insert vao SQLite DB.

Chay:
    python tools/migrate_excel_to_sqlite.py
    python tools/migrate_excel_to_sqlite.py --excel path/to/master.xlsx --db path/to/autofill.db

Truoc khi chay, dam bao:
    alembic upgrade head  (da tao tables)
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click

# Ensure src/ on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto_fill.config.settings import settings  # noqa: E402
from auto_fill.db.engine import create_tables, get_engine  # noqa: E402
from auto_fill.db.models import (  # noqa: E402
    AutoInsurance,
    BhytBhxhInsurance,
    HealthInsurance,
    MotorbikeInsurance,
    StudentInsurance,
    TravelInsurance,
)
from auto_fill.mapper.aliases_loader import load_aliases  # noqa: E402
from auto_fill.mapper.normalizer import (  # noqa: E402
    normalize_date,
    normalize_id_number,
    normalize_money,
    normalize_name,
)
from auto_fill.reader.excel_reader import read_excel  # noqa: E402

logger = logging.getLogger(__name__)

# (sheet_name, model_class, field_map)
# field_map: canonical_field -> model attribute name (None = skip)
_SHEET_CONFIG: list[tuple[str, type[Any], dict[str, str | None]]] = [
    (
        "Du lịch",
        TravelInsurance,
        {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "insured_dob": "insured_dob",
            "insured_id_number": "insured_id_number",
            "payment_date": "payment_date",
            "trip_start": "trip_start",
            "trip_end": "trip_end",
            "destination": "destination",
            "scope": "scope",
            "plan": "plan",
            "premium": "premium",
            "buyer_name": "buyer_name",
        },
    ),
    (
        "Bao hiem oto",
        AutoInsurance,
        {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "phone": "phone",
            "email": "email",
            "address": "address",
            "plate_number": "plate_number",
            "frame_number": "frame_number",
            "engine_number": "engine_number",
            "payload": "payload",
            "seats": "seats",
            "vehicle_type": "vehicle_type",
            "brand": "brand",
            "vehicle_value": "vehicle_value",
            "purpose": "purpose",
            "premium": "premium",
        },
    ),
    (
        "Thông tin cấp Bảo hiểm xe máy",
        MotorbikeInsurance,
        {
            "issued_date": "issued_date",
            "plate_number": "plate_number",
            "frame_number": "frame_number",
            "engine_number": "engine_number",
            "customer_name": "customer_name",
            "premium_tnds": "premium_tnds",
            "premium_accident": "premium_accident",
            "years": "years",
            "total_premium": "total_premium",
            "trip_start": "start_date",
            "trip_end": "end_date",
            "vehicle_type": "vehicle_type",
            "brand": "brand",
        },
    ),
    (
        "Sức khỏe",
        HealthInsurance,
        {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "insured_dob": "insured_dob",
            "insured_id_number": "insured_id_number",
            "effective_from": "effective_from",
            "outpatient": "outpatient",
            "dental": "dental",
            "maternity": "maternity",
            "premium": "premium",
            "buyer_name": "buyer_name",
            "buyer_dob": "buyer_dob",
            "buyer_id_number": "buyer_id_number",
            "buyer_relation": "buyer_relation",
        },
    ),
    (
        "BHYTBHXH",
        BhytBhxhInsurance,
        {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "insured_id_number": "insured_id_number",
            "effective_from": "effective_from",
            "buyer_name": "buyer_name",
            "buyer_dob": "buyer_dob",
            "buyer_relation": "buyer_relation",
            "premium": "premium",
        },
    ),
    (
        "HSSV",
        StudentInsurance,
        {
            "issued_date": "issued_date",
            "insured_name": "insured_name",
            "insured_dob": "insured_dob",
            "insured_id_number": "insured_id_number",
            "school": "school",
            "class_name": "class_name",
            "effective_from": "effective_from",
            "premium": "premium",
            "buyer_name": "buyer_name",
        },
    ),
]

_DATE_FIELDS = frozenset(
    {
        "issued_date",
        "insured_dob",
        "payment_date",
        "trip_start",
        "trip_end",
        "start_date",
        "end_date",
        "effective_from",
        "buyer_dob",
    }
)
_MONEY_FIELDS = frozenset(
    {
        "premium",
        "premium_tnds",
        "premium_accident",
        "total_premium",
        "vehicle_value",
        "outpatient",
        "dental",
        "maternity",
    }
)
_NAME_FIELDS = frozenset(
    {
        "insured_name",
        "customer_name",
        "buyer_name",
        "destination",
        "scope",
        "plan",
        "school",
        "class_name",
        "address",
        "vehicle_type",
        "brand",
        "purpose",
        "email",
        "phone",
        "buyer_relation",
    }
)
_ID_FIELDS = frozenset({"insured_id_number", "buyer_id_number"})


def _normalize(attr: str, value: object) -> object:
    import contextlib

    if value is None:
        return None
    if attr in _DATE_FIELDS:
        with contextlib.suppress(Exception):
            return normalize_date(value)
    elif attr in _MONEY_FIELDS:
        with contextlib.suppress(Exception):
            return normalize_money(value)
    elif attr in _NAME_FIELDS:
        with contextlib.suppress(Exception):
            return normalize_name(str(value))
    elif attr in _ID_FIELDS:
        with contextlib.suppress(Exception):
            return normalize_id_number(value)
    return value


def _migrate_sheet(
    excel_path: Path,
    db_path: Path,
    sheet_name: str,
    model_cls: type[Any],
    field_map: Mapping[str, str | None],
    dry_run: bool,
) -> tuple[int, int]:
    """Doc 1 sheet, insert vao DB. Tra ve (inserted, skipped)."""
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    aliases = load_aliases()
    try:
        df = read_excel(excel_path, aliases=aliases, sheet_name=sheet_name)
    except Exception as exc:
        click.echo(f"  [warn] Khong doc duoc sheet '{sheet_name}': {exc}", err=True)
        return 0, 0

    engine = get_engine(str(db_path))
    inserted = skipped = 0

    for _, row in df.iterrows():
        record = dict(row)
        kwargs: dict[str, object] = {}
        for canonical, attr in field_map.items():
            if attr is None:
                continue
            val = record.get(canonical)
            if val is not None:
                kwargs[attr] = _normalize(attr, val)

        if not dry_run:
            try:
                with Session(engine) as s:
                    s.add(model_cls(**kwargs))
                    s.commit()
                inserted += 1
            except IntegrityError:
                skipped += 1
        else:
            click.echo(
                f"  [dry-run] {model_cls.__tablename__}: {kwargs.get('insured_name') or kwargs.get('customer_name') or kwargs.get('plate_number')}"
            )
            inserted += 1

    return inserted, skipped


@click.command()
@click.option(
    "--excel",
    default=None,
    type=click.Path(exists=True),
    help="Duong dan file Excel tong (default: settings.master_file_path).",
)
@click.option(
    "--db",
    "db_path",
    default=None,
    type=click.Path(),
    help="Duong dan SQLite DB (default: settings.db_path).",
)
@click.option("--dry-run", is_flag=True, help="Parse nhung KHONG ghi vao DB.")
def main(excel: str | None, db_path: str | None, dry_run: bool) -> None:
    """1-shot migration: doc tung sheet Excel, insert vao SQLite."""
    logging.basicConfig(level=logging.WARNING)

    excel_path = Path(excel) if excel else settings.master_file_path
    db = Path(db_path) if db_path else settings.db_path

    if not excel_path.exists():
        click.echo(f"[error] File Excel khong ton tai: {excel_path}", err=True)
        sys.exit(1)

    click.echo(f"[migrate] Excel: {excel_path}")
    click.echo(f"[migrate] DB:    {db}  dry_run={dry_run}")

    if not dry_run:
        engine = get_engine(str(db))
        create_tables(engine)

    total_inserted = total_skipped = 0
    for sheet_name, model_cls, field_map in _SHEET_CONFIG:
        click.echo(f"\n[sheet] {sheet_name} => {model_cls.__tablename__}")
        ins, skip = _migrate_sheet(
            excel_path=excel_path,
            db_path=db,
            sheet_name=sheet_name,
            model_cls=model_cls,
            field_map=field_map,
            dry_run=dry_run,
        )
        click.echo(f"  inserted={ins}  skipped_dup={skip}")
        total_inserted += ins
        total_skipped += skip

    click.echo(f"\n[done] total inserted={total_inserted}  skipped_dup={total_skipped}")


if __name__ == "__main__":
    main()
