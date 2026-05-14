"""Windows Service wrapper dung pywin32.

Cho phep chay scheduler nhu Windows Service (khong can NSSM).
Phai chay voi quyen Administrator.

Usage:
    python -m auto_fill.windows_service install
    python -m auto_fill.windows_service start
    python -m auto_fill.windows_service stop
    python -m auto_fill.windows_service remove
    python -m auto_fill.windows_service debug   # chay truc tiep trong terminal
"""

from __future__ import annotations

import contextlib
import os
import sys

try:
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil

    _WIN32_AVAILABLE = True
except ImportError:
    _WIN32_AVAILABLE = False

_SERVICE_NAME = "AutoFillCapDon"
_SERVICE_DISPLAY_NAME = "AutoFill Cap Don"
_SERVICE_DESCRIPTION = "Tu dong nhap phieu cap don bao hiem tu Outlook vao Excel."


if _WIN32_AVAILABLE:

    class AutoFillService(win32serviceutil.ServiceFramework):  # type: ignore[misc]
        _svc_name_ = _SERVICE_NAME
        _svc_display_name_ = _SERVICE_DISPLAY_NAME
        _svc_description_ = _SERVICE_DESCRIPTION

        def __init__(self, args: list[str]) -> None:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._interval_minutes = int(os.environ.get("AUTOFILL_INTERVAL", "15"))

        def SvcStop(self) -> None:  # noqa: N802
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._stop_event)

        def SvcDoRun(self) -> None:  # noqa: N802
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self._run()
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, ""),
            )

        def _run(self) -> None:
            from auto_fill.config.settings import settings
            from auto_fill.scheduler import run_pipeline_once
            from auto_fill.utils.logger import setup_logging

            setup_logging(log_dir=settings.log_dir, level=settings.log_level, json=True)
            interval_ms = self._interval_minutes * 60 * 1000

            while True:
                with contextlib.suppress(Exception):
                    run_pipeline_once()
                result = win32event.WaitForSingleObject(self._stop_event, interval_ms)
                if result == win32event.WAIT_OBJECT_0:
                    break


def main() -> None:
    """Entry point cho service management (install/start/stop/remove/debug)."""
    if not _WIN32_AVAILABLE:
        print(
            "[error] pywin32 khong co san. Chay: pip install pywin32",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AutoFillService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AutoFillService)


if __name__ == "__main__":
    main()
