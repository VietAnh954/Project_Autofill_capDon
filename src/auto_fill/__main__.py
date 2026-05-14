"""CLI entry point cho auto-fill-capdon.

Chay: `python -m auto_fill <command>`
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Any

import click


@click.group()
@click.option("--log-level", default=None, help="Override log level (DEBUG/INFO/WARNING).")
@click.pass_context
def cli(ctx: click.Context, log_level: str | None) -> None:
    """Auto-fill Cap Don -- pipeline tu dong nhap phieu cap don vao file tong."""
    from auto_fill.config.settings import settings
    from auto_fill.utils.logger import setup_logging

    level = log_level or settings.log_level
    setup_logging(log_dir=settings.log_dir, level=level, json=True)
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


@cli.command()
@click.option("--dry-run", is_flag=True, help="Doc & parse nhung KHONG ghi vao file tong.")
@click.pass_context
def run(ctx: click.Context, dry_run: bool) -> None:
    """Chay pipeline 1 lan: fetch mail -> parse -> fill master."""
    from auto_fill.config.settings import Settings
    from auto_fill.filler.backup import snapshot
    from auto_fill.mail.downloader import download_attachments
    from auto_fill.mail.fetcher import MailFetcher
    from auto_fill.mail.marker import mark_processed
    from auto_fill.mail.outlook_client import OutlookClient
    from auto_fill.reporter.daily_report import RunStats, render_report
    from auto_fill.utils.errors import ClassifierError, ValidationError

    settings: Settings = ctx.obj["settings"]
    effective_dry_run = dry_run or settings.dry_run

    click.echo(f"[run] dry_run={effective_dry_run}")
    stats = RunStats()

    client = OutlookClient(
        profile=settings.outlook_profile,
        inbox_folder=settings.outlook_inbox_folder,
    )
    try:
        client.connect()
    except Exception as exc:
        click.echo(f"[error] Khong ket noi duoc Outlook: {exc}", err=True)
        sys.exit(1)

    if not effective_dry_run and settings.backup_every_run:
        with contextlib.suppress(FileNotFoundError):
            snapshot(settings.master_file_path, settings.data_root / "backup")

    fetcher = MailFetcher(
        client=client,
        sender_allowlist=settings.sender_allowlist_set,
        subject_pattern=settings.subject_pattern,
    )

    for mail in fetcher.fetch_matching():
        ns: Any = client._namespace  # type: ignore[attr-defined]
        inbox_dir = settings.data_root / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        paths = download_attachments(mail, inbox_dir, ns, settings.max_attachment_mb)
        stats.processed += len(paths)

        for file_path in paths:
            try:
                sheet_alias = _process_file(
                    file_path=file_path,
                    mail_subject=mail.subject,
                    mail_sender=mail.sender_email,
                    settings=settings,
                    effective_dry_run=effective_dry_run,
                    stats=stats,
                )
                if sheet_alias:
                    stats.add_written(sheet_alias)
            except (ClassifierError, ValidationError, Exception) as exc:
                click.echo(f"[skip] {file_path.name}: {exc}", err=True)
                stats.add_error(f"`{file_path.name}`: {exc}")
                continue

        if not effective_dry_run:
            folder = settings.outlook_processed_folder.split("\\")[-1]
            mark_processed(ns, mail.entry_id, folder)

    click.echo(
        f"[done] processed={stats.processed} written={stats.written} "
        f"duplicates={stats.duplicates} errors={stats.errors}"
    )

    if not effective_dry_run:
        report_path = render_report(stats, settings.data_root / "reports")
        click.echo(f"[report] {report_path}")


def _process_file(
    file_path: Path,
    mail_subject: str,
    mail_sender: str,
    settings: Any,
    effective_dry_run: bool,
    stats: Any,
) -> str | None:
    """Xu ly 1 file attachment: classify -> read -> normalize -> validate -> dedup -> fill.

    Returns sheet alias neu ghi thanh cong, None neu khong co record nao.
    """
    from auto_fill.db.repository import insert_record
    from auto_fill.filler.excel_filler import append_travel_rows
    from auto_fill.mapper.aliases_loader import load_aliases
    from auto_fill.mapper.classifier import classify
    from auto_fill.mapper.dedup import is_duplicate
    from auto_fill.mapper.normalizer import (
        normalize_date,
        normalize_id_number,
        normalize_money,
        normalize_name,
    )
    from auto_fill.mapper.validator import validate_and_raise
    from auto_fill.reader.csv_reader import read_csv
    from auto_fill.reader.excel_reader import read_excel

    sheet_info = classify(mail_subject, mail_sender)
    aliases = load_aliases()

    suffix = file_path.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        df = read_excel(file_path, aliases=aliases)
    elif suffix == ".csv":
        df = read_csv(file_path, aliases=aliases)
    else:
        raise ValueError(f"Dinh dang khong ho tro: {suffix}")

    wrote_any = False
    for _, row in df.iterrows():
        record: dict[str, Any] = dict(row)
        _normalize_record(
            record, normalize_date, normalize_id_number, normalize_money, normalize_name
        )
        validate_and_raise(record, sheet_info.alias)
        if is_duplicate(record, settings.master_file_path, sheet_name=sheet_info.excel_name):
            click.echo(f"[dedup] Bo qua: {record.get('insured_id_number')}")
            stats.add_duplicate()
            continue
        if not effective_dry_run:
            # Ghi vao DB truoc (neu db_enabled)
            if getattr(settings, "db_enabled", True):
                insert_record(
                    record,
                    sheet_alias=sheet_info.alias,
                    db_path=str(settings.db_path),
                    source_attachment=file_path.name,
                )
            # Ghi vao Excel (backward compatible)
            append_travel_rows(
                [record], settings.master_file_path, sheet_name=sheet_info.excel_name
            )
            wrote_any = True
        else:
            click.echo(f"[dry-run] Se ghi: {record.get('insured_name')}")
            wrote_any = True

    return sheet_info.alias if wrote_any else None


def _normalize_record(
    record: dict[str, Any],
    normalize_date: Any,
    normalize_id_number: Any,
    normalize_money: Any,
    normalize_name: Any,
) -> None:
    date_fields = ("issued_date", "insured_dob", "trip_start", "trip_end", "effective_from")
    for f in date_fields:
        if record.get(f) is not None:
            with contextlib.suppress(Exception):
                record[f] = normalize_date(record[f])

    str_fields = ("insured_name", "destination", "scope", "plan", "buyer_name")
    for f in str_fields:
        if record.get(f) is not None:
            with contextlib.suppress(Exception):
                record[f] = normalize_name(str(record[f]))

    if record.get("insured_id_number") is not None:
        with contextlib.suppress(Exception):
            record["insured_id_number"] = normalize_id_number(record["insured_id_number"])

    if record.get("premium") is not None:
        with contextlib.suppress(Exception):
            record["premium"] = normalize_money(record["premium"])


@cli.command()
@click.option(
    "--interval",
    default=15,
    show_default=True,
    help="Khoang thoi gian poll (phut).",
)
def schedule(interval: int) -> None:
    """Chay scheduler poll Outlook moi --interval phut."""
    from auto_fill.scheduler import start_scheduler

    start_scheduler(interval_minutes=interval)


@cli.command()
@click.option(
    "--to",
    "to_file",
    required=True,
    type=click.Path(exists=True),
    help="Duong dan file backup (.xlsx) can khoi phuc.",
)
@click.option("--yes", "-y", is_flag=True, help="Xac nhan khong hoi lai.")
@click.pass_context
def rollback(ctx: click.Context, to_file: str, yes: bool) -> None:
    """Khoi phuc master file tu backup snapshot.

    Vi du: python -m auto_fill rollback --to data/backup/2026-05-14/master.xlsx
    """
    import shutil

    from auto_fill.config.settings import Settings

    settings: Settings = ctx.obj["settings"]
    src = Path(to_file)
    dst = settings.master_file_path

    if not yes:
        click.confirm(
            f"Ghi de {dst.name} bang {src}?\nCANH BAO: Hanh dong nay khong the hoan tac!",
            abort=True,
        )

    from auto_fill.filler.backup import snapshot

    snapshot(dst, settings.data_root / "backup")
    shutil.copy2(src, dst)
    click.echo(f"[rollback] Da khoi phuc: {src} -> {dst}")


@cli.command()
@click.option(
    "--folder",
    default=None,
    type=click.Path(exists=True),
    help="Thu muc chua file can replay (mac dinh: data/inbox/).",
)
@click.option("--dry-run", is_flag=True, help="Parse nhung KHONG ghi.")
@click.pass_context
def replay(ctx: click.Context, folder: str | None, dry_run: bool) -> None:
    """Re-process tat ca file trong thu muc (inbox hoac failed).

    Vi du: python -m auto_fill replay --folder data/failed/unknown_schema/
    """
    from auto_fill.config.settings import Settings
    from auto_fill.reporter.daily_report import RunStats, render_report
    from auto_fill.utils.errors import ClassifierError, ValidationError

    settings: Settings = ctx.obj["settings"]
    effective_dry_run = dry_run or settings.dry_run

    replay_dir = Path(folder) if folder else settings.data_root / "inbox"
    supported = {".xlsx", ".xls", ".xlsm", ".csv", ".pdf"}

    files = [f for f in sorted(replay_dir.iterdir()) if f.suffix.lower() in supported]
    if not files:
        click.echo(f"[replay] Khong co file nao trong {replay_dir}")
        return

    click.echo(
        f"[replay] Tim thay {len(files)} file trong {replay_dir}. dry_run={effective_dry_run}"
    )

    stats = RunStats()
    stats.processed = len(files)

    for file_path in files:
        try:
            sheet_alias = _process_file(
                file_path=file_path,
                mail_subject=file_path.stem,
                mail_sender="replay@local",
                settings=settings,
                effective_dry_run=effective_dry_run,
                stats=stats,
            )
            if sheet_alias:
                stats.add_written(sheet_alias)
                click.echo(f"[ok] {file_path.name} -> {sheet_alias}")
        except (ClassifierError, ValidationError, Exception) as exc:
            click.echo(f"[skip] {file_path.name}: {exc}", err=True)
            stats.add_error(f"`{file_path.name}`: {exc}")

    click.echo(
        f"[replay done] written={stats.written} duplicates={stats.duplicates} errors={stats.errors}"
    )
    if not effective_dry_run:
        report_path = render_report(stats, settings.data_root / "reports")
        click.echo(f"[report] {report_path}")


@cli.command("export")
@click.option(
    "--sheet",
    default=None,
    help="Ten alias sheet can xuat (travel/auto/motorbike/health/bhyt_bhxh/student). Mac dinh: tat ca.",
)
@click.option(
    "--to",
    "out_path",
    default=None,
    type=click.Path(),
    help="Duong dan file Excel dau ra. Mac dinh: data/exports/export_<date>.xlsx.",
)
@click.pass_context
def export_cmd(ctx: click.Context, sheet: str | None, out_path: str | None) -> None:
    """Xuat du lieu tu SQLite ra file Excel snapshot.

    Vi du: python -m auto_fill export --sheet travel --to data/exports/travel.xlsx
    """
    from datetime import date
    from pathlib import Path

    from auto_fill.config.settings import Settings
    from auto_fill.filler.db_exporter import export_daily_snapshot

    settings: Settings = ctx.obj["settings"]
    db_path = str(settings.db_path)

    if out_path:
        dest = Path(out_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        output_dir = dest.parent
    else:
        output_dir = settings.data_root / "exports"

    if sheet:
        click.echo(f"[export] sheet={sheet}  db={db_path}")
        _export_single_sheet(
            sheet, db_path, out_path or str(output_dir / f"export_{sheet}_{date.today()}.xlsx")
        )
    else:
        result = export_daily_snapshot(db_path=db_path, output_dir=output_dir)
        click.echo(f"[export] {result}")


def _export_single_sheet(sheet_alias: str, db_path: str, out_path: str) -> None:
    """Xuat 1 sheet ra file Excel doc lap."""
    import pandas as pd
    from sqlalchemy.orm import Session

    from auto_fill.db.engine import get_engine
    from auto_fill.db.repository import _ALIAS_TO_FIELDS, _ALIAS_TO_MODEL

    model_cls = _ALIAS_TO_MODEL[sheet_alias]
    columns = sorted(_ALIAS_TO_FIELDS[sheet_alias])

    engine = get_engine(db_path)
    with Session(engine) as s:
        rows = s.query(model_cls).all()

    data = [{col: getattr(r, col, None) for col in columns} for r in rows]
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(out_path, index=False, sheet_name=sheet_alias)
    click.echo(f"[export] {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    cli()
