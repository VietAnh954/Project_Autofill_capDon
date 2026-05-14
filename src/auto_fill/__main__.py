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
@click.option("--to", "to_file", required=True, type=click.Path(exists=True))
def rollback(to_file: str) -> None:
    """Khoi phuc master file tu backup snapshot."""
    click.echo(f"[rollback] restoring from {to_file}")
    raise NotImplementedError("Se implement o Phase 2 task 2.8.")


if __name__ == "__main__":
    cli()
