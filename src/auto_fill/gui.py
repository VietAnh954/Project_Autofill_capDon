"""GUI Tkinter cho non-tech user — Bang dieu khien AutoFill Cap Don.

Chay: python -m auto_fill.gui

Chuc nang:
  - Run Once  : chay pipeline 1 lan
  - Dry Run   : preview khong ghi du lieu
  - Schedule  : bat / tat scheduler tu dong
  - Log viewer: xem 200 dong log gan nhat
  - Status bar: trang thai pipeline hien tai
"""

from __future__ import annotations

import contextlib
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk


class _PipelineRunner:
    """Chay pipeline trong thread rieng, feed output vao queue."""

    def __init__(self, log_queue: queue.Queue[str]) -> None:
        self._q = log_queue
        self._proc: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None

    def _emit(self, line: str) -> None:
        self._q.put(line)

    def run(self, dry_run: bool = False) -> None:
        if self._thread and self._thread.is_alive():
            self._emit("[warn] Pipeline dang chay, vui long cho...\n")
            return
        self._thread = threading.Thread(target=self._do_run, args=(dry_run,), daemon=True)
        self._thread.start()

    def _do_run(self, dry_run: bool) -> None:
        python = sys.executable
        cmd = [python, "-m", "auto_fill", "run"]
        if dry_run:
            cmd.append("--dry-run")
        self._emit(f"[start] {' '.join(cmd)}\n")
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                self._emit(line)
            self._proc.wait()
            self._emit(f"[done] exit code={self._proc.returncode}\n")
        except Exception as exc:
            self._emit(f"[error] {exc}\n")

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())


class _SchedulerController:
    """Bat / tat subprocess scheduler."""

    def __init__(self, log_queue: queue.Queue[str], interval: int = 15) -> None:
        self._q = log_queue
        self._interval = interval
        self._proc: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None

    def _emit(self, line: str) -> None:
        self._q.put(line)

    def start(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._emit("[warn] Scheduler dang chay.\n")
            return
        python = sys.executable
        cmd = [python, "-m", "auto_fill", "schedule", "--interval", str(self._interval)]
        self._emit(f"[scheduler] Bat dau moi {self._interval} phut.\n")
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._thread = threading.Thread(target=self._read_output, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._emit("[scheduler] Da dung.\n")
        else:
            self._emit("[scheduler] Khong co scheduler dang chay.\n")

    def _read_output(self) -> None:
        if self._proc and self._proc.stdout:
            for line in self._proc.stdout:
                self._emit(line)

    @property
    def is_running(self) -> bool:
        return bool(self._proc and self._proc.poll() is None)


class AutoFillApp(tk.Tk):
    """Cua so chinh cua ung dung GUI."""

    _LOG_MAX_LINES = 500

    def __init__(self) -> None:
        super().__init__()
        self.title("AutoFill Cap Don")
        self.resizable(True, True)
        self.minsize(640, 480)

        self._log_q: queue.Queue[str] = queue.Queue()
        self._runner = _PipelineRunner(self._log_q)
        self._scheduler: _SchedulerController | None = None

        self._build_ui()
        self._poll_queue()

    # ------------------------------------------------------------------ #
    # UI layout                                                            #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        # Top toolbar
        toolbar = ttk.Frame(self, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Run Once", command=self._on_run).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Dry Run", command=self._on_dry_run).pack(side=tk.LEFT, padx=4)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Label(toolbar, text="Interval (phut):").pack(side=tk.LEFT)
        self._interval_var = tk.IntVar(value=15)
        ttk.Spinbox(toolbar, from_=5, to=120, textvariable=self._interval_var, width=5).pack(
            side=tk.LEFT, padx=4
        )

        self._sched_btn = ttk.Button(
            toolbar, text="Bat Scheduler", command=self._on_toggle_scheduler
        )
        self._sched_btn.pack(side=tk.LEFT, padx=4)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(toolbar, text="Xoa Log", command=self._clear_log).pack(side=tk.LEFT, padx=4)

        # Log area
        log_frame = ttk.LabelFrame(self, text="Log", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))

        self._log_text = scrolledtext.ScrolledText(
            log_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 9),
            background="#1e1e1e",
            foreground="#d4d4d4",
            insertbackground="white",
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # Tag colours
        self._log_text.tag_config("error", foreground="#f44747")
        self._log_text.tag_config("warn", foreground="#ce9178")
        self._log_text.tag_config("done", foreground="#4ec9b0")
        self._log_text.tag_config("start", foreground="#569cd6")

        # Status bar
        status_frame = ttk.Frame(self, padding=(8, 4))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self._status_var = tk.StringVar(value="San sang.")
        ttk.Label(status_frame, textvariable=self._status_var, anchor=tk.W).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

    # ------------------------------------------------------------------ #
    # Button handlers                                                      #
    # ------------------------------------------------------------------ #

    def _on_run(self) -> None:
        self._status_var.set("Dang chay pipeline...")
        self._runner.run(dry_run=False)

    def _on_dry_run(self) -> None:
        self._status_var.set("Dry run — khong ghi du lieu.")
        self._runner.run(dry_run=True)

    def _on_toggle_scheduler(self) -> None:
        interval = self._interval_var.get()
        if self._scheduler is None or not self._scheduler.is_running:
            self._scheduler = _SchedulerController(self._log_q, interval=interval)
            self._scheduler.start()
            self._sched_btn.config(text="Tat Scheduler")
            self._status_var.set(f"Scheduler dang chay (moi {interval} phut).")
        else:
            self._scheduler.stop()
            self._sched_btn.config(text="Bat Scheduler")
            self._status_var.set("Scheduler da dung.")

    def _clear_log(self) -> None:
        self._log_text.config(state=tk.NORMAL)
        self._log_text.delete("1.0", tk.END)
        self._log_text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------ #
    # Log polling                                                          #
    # ------------------------------------------------------------------ #

    def _poll_queue(self) -> None:
        try:
            while True:
                line = self._log_q.get_nowait()
                self._append_log(line)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

    def _append_log(self, line: str) -> None:
        self._log_text.config(state=tk.NORMAL)

        tag = ""
        lo = line.lower()
        if "[error]" in lo:
            tag = "error"
        elif "[warn]" in lo:
            tag = "warn"
        elif "[done]" in lo or "passed" in lo:
            tag = "done"
        elif "[start]" in lo or "[scheduler]" in lo:
            tag = "start"

        self._log_text.insert(tk.END, line, tag)

        # Trim old lines
        lines = int(self._log_text.index(tk.END).split(".")[0])
        if lines > self._LOG_MAX_LINES:
            self._log_text.delete("1.0", f"{lines - self._LOG_MAX_LINES}.0")

        self._log_text.see(tk.END)
        self._log_text.config(state=tk.DISABLED)

        # Update status bar from last log line
        stripped = line.strip()
        if stripped:
            self._status_var.set(stripped[:100])

    def _load_recent_log(self) -> None:
        """Doc 200 dong log file gan nhat vao text area khi khoi dong."""
        from auto_fill.config.settings import settings

        log_dir = settings.log_dir
        log_files = sorted(Path(log_dir).glob("*.log"), key=lambda p: p.stat().st_mtime)
        if not log_files:
            return
        latest = log_files[-1]
        try:
            lines = latest.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
            for line in lines:
                self._append_log(line + "\n")
        except OSError:
            pass


def main() -> None:
    app = AutoFillApp()
    with contextlib.suppress(Exception):
        app._load_recent_log()
    app.mainloop()


if __name__ == "__main__":
    main()
