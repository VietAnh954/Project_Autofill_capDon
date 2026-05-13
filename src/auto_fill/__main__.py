"""CLI entry point cho auto-fill-capdon.

Chạy: `python -m auto_fill <command>`
"""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Auto-fill Cấp Đơn — pipeline tự động nhập phiếu cấp đơn vào file tổng."""


@cli.command()
@click.option("--dry-run", is_flag=True, help="Đọc & parse nhưng KHÔNG ghi vào file tổng.")
def run(dry_run: bool) -> None:
    """Chạy pipeline 1 lần: fetch mail → parse → fill master."""
    click.echo(f"[run] dry_run={dry_run}")
    # TODO 1.15: wire pipeline
    raise NotImplementedError("Sẽ implement ở task 1.15.")


@cli.command()
@click.option("--to", "to_file", required=True, type=click.Path(exists=True))
def rollback(to_file: str) -> None:
    """Khôi phục master file từ backup snapshot."""
    click.echo(f"[rollback] restoring from {to_file}")
    # TODO 2.8
    raise NotImplementedError("Sẽ implement ở Phase 2 task 2.8.")


if __name__ == "__main__":
    cli()
