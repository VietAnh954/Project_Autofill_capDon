"""Scheduler — chay pipeline tu dong moi N phut dung APScheduler.

Chay: `python -m auto_fill schedule --interval 15`

APScheduler dung BackgroundScheduler (chay trong thread rieng).
Main thread block vong lap Sleep -> KeyboardInterrupt de dung.
"""

from __future__ import annotations

import logging
import signal
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL_MINUTES = 15


def run_pipeline_once() -> None:
    """Ham duoc APScheduler goi moi interval.

    Import CLI run command va goi truc tiep (khong qua sys.argv).
    """
    from auto_fill.config.settings import settings
    from auto_fill.utils.logger import setup_logging

    setup_logging(log_dir=settings.log_dir, level=settings.log_level, json=True)
    logger.info("scheduler_tick_start")

    try:
        import contextlib

        from auto_fill.filler.backup import snapshot
        from auto_fill.mail.downloader import download_attachments
        from auto_fill.mail.fetcher import MailFetcher
        from auto_fill.mail.marker import mark_processed
        from auto_fill.mail.outlook_client import OutlookClient
        from auto_fill.reporter.daily_report import RunStats, render_report

        client = OutlookClient(
            profile=settings.outlook_profile,
            inbox_folder=settings.outlook_inbox_folder,
        )
        client.connect()

        if settings.backup_every_run:
            with contextlib.suppress(FileNotFoundError):
                snapshot(settings.master_file_path, settings.data_root / "backup")

        fetcher = MailFetcher(
            client=client,
            sender_allowlist=settings.sender_allowlist_set,
            subject_pattern=settings.subject_pattern,
        )

        stats = RunStats()
        any_mail = False

        for mail in fetcher.fetch_matching():
            any_mail = True
            ns = client._namespace  # type: ignore[attr-defined]
            inbox_dir = settings.data_root / "inbox"
            inbox_dir.mkdir(parents=True, exist_ok=True)
            paths = download_attachments(mail, inbox_dir, ns, settings.max_attachment_mb)
            stats.processed += len(paths)

            for file_path in paths:
                try:
                    _process_one(file_path, mail, settings, stats)
                except Exception as exc:
                    logger.warning(
                        "scheduler_file_skip", extra={"file": str(file_path), "error": str(exc)}
                    )
                    stats.add_error(f"`{file_path.name}`: {exc}")

            mark_processed(ns, mail.entry_id, settings.outlook_processed_folder.split("\\")[-1])

        if any_mail:
            render_report(stats, settings.data_root / "reports")

        logger.info(
            "scheduler_tick_done",
            extra={
                "processed": stats.processed,
                "written": stats.written,
                "errors": stats.errors,
            },
        )

    except Exception as exc:
        logger.error("scheduler_tick_error", extra={"error": str(exc)})


def _normalize_record(
    record: dict[str, object],
    normalize_date: object,
    normalize_id_number: object,
    normalize_money: object,
    normalize_name: object,
) -> None:
    """Normalize tat ca cac truong trong record (in-place). Dung contextlib.suppress."""
    import contextlib
    from typing import Any

    nd: Any = normalize_date
    ni: Any = normalize_id_number
    nm: Any = normalize_money
    nn: Any = normalize_name

    for f in ("issued_date", "insured_dob", "trip_start", "trip_end", "effective_from"):
        if record.get(f) is not None:
            with contextlib.suppress(Exception):
                record[f] = nd(record[f])
    if record.get("insured_id_number"):
        with contextlib.suppress(Exception):
            record["insured_id_number"] = ni(record["insured_id_number"])
    if record.get("premium"):
        with contextlib.suppress(Exception):
            record["premium"] = nm(record["premium"])
    for f in ("insured_name", "destination", "scope", "plan", "buyer_name"):
        if record.get(f):
            with contextlib.suppress(Exception):
                record[f] = nn(str(record[f]))


def _process_one(file_path: object, mail: object, settings: object, stats: object) -> None:
    """Inline helper — classify, read, normalize, validate, dedup, fill."""
    from typing import Any

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

    file_path_: Any = file_path
    mail_: Any = mail
    settings_: Any = settings
    stats_: Any = stats

    sheet_info = classify(mail_.subject, mail_.sender_email)
    aliases = load_aliases()

    suffix = file_path_.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        df = read_excel(file_path_, aliases=aliases)
    elif suffix == ".csv":
        df = read_csv(file_path_, aliases=aliases)
    else:
        raise ValueError(f"Dinh dang khong ho tro: {suffix}")

    for _, row in df.iterrows():
        record: dict[str, Any] = dict(row)
        _normalize_record(
            record, normalize_date, normalize_id_number, normalize_money, normalize_name
        )
        validate_and_raise(record, sheet_info.alias)
        if is_duplicate(record, settings_.master_file_path, sheet_name=sheet_info.excel_name):
            stats_.add_duplicate()
            continue
        append_travel_rows([record], settings_.master_file_path, sheet_name=sheet_info.excel_name)
        stats_.add_written(sheet_info.alias)


def start_scheduler(interval_minutes: int = _DEFAULT_INTERVAL_MINUTES) -> None:
    """Khoi dong scheduler va block cho den khi nhan SIGINT/KeyboardInterrupt.

    Args:
        interval_minutes: Khoang thoi gian giua cac lan chay (phut).
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_pipeline_once,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="pipeline_poll",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("scheduler_started", extra={"interval_minutes": interval_minutes})
    print(f"[scheduler] Chay moi {interval_minutes} phut. Nhan Ctrl+C de dung.")

    def _handle_shutdown(signum: int, frame: object) -> None:
        logger.info("scheduler_stopping")
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, _handle_shutdown)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("scheduler_stopping")
        scheduler.shutdown(wait=False)
        print("[scheduler] Dung.")
