"""Shared pipeline execution state for the web dashboard.

A single process-level singleton tracks whether a pipeline run is in
progress, captures its log output, and stores the last result so the
SSE endpoint can replay recent lines to new subscribers.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PipelineState:
    status: str = "idle"  # idle | running | done | error
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    logs: deque[str] = field(default_factory=lambda: deque(maxlen=300))
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


# Module-level singleton
state = PipelineState()


def run_pipeline(dry_run: bool = False) -> bool:
    """Trigger a pipeline run in a background thread.

    Returns False if a run is already in progress.
    """
    with state._lock:
        if state.status == "running":
            return False
        state.status = "running"
        state.started_at = datetime.now()
        state.finished_at = None
        state.error = None
        state.logs.clear()

    thread = threading.Thread(target=_worker, args=(dry_run,), daemon=True)
    thread.start()
    return True


def _worker(dry_run: bool) -> None:
    cmd = [sys.executable, "-m", "auto_fill", "run"]
    if dry_run:
        cmd.append("--dry-run")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = raw_line.rstrip()
            if line:
                ts = datetime.now().strftime("%H:%M:%S")
                state.logs.append(f"[{ts}] {line}")
        proc.wait()
        if proc.returncode == 0:
            state.status = "done"
        else:
            state.status = "error"
            state.error = f"Tiến trình thoát với mã {proc.returncode}"
    except Exception as exc:
        state.status = "error"
        state.error = str(exc)
    finally:
        state.finished_at = datetime.now()
