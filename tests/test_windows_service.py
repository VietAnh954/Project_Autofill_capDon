"""Unit tests cho windows_service.py.

Tat ca tests deu chay khong can pywin32 thuc su cai dat hay quyen Admin.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

import auto_fill.windows_service as svc


class TestWin32Availability:
    def test_module_imports_cleanly(self) -> None:
        assert hasattr(svc, "_WIN32_AVAILABLE")

    def test_service_constants(self) -> None:
        assert svc._SERVICE_NAME == "AutoFillCapDon"
        assert svc._SERVICE_DISPLAY_NAME == "AutoFill Cap Don"
        assert svc._SERVICE_DESCRIPTION != ""


class TestMainWithoutWin32:
    def test_main_exits_1_when_no_win32(self) -> None:
        with patch.object(svc, "_WIN32_AVAILABLE", False), pytest.raises(SystemExit) as exc:
            svc.main()
        assert exc.value.code == 1

    def test_main_prints_error_when_no_win32(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch.object(svc, "_WIN32_AVAILABLE", False), pytest.raises(SystemExit):
            svc.main()
        captured = capsys.readouterr()
        assert "pywin32" in captured.err


class TestMainWithWin32:
    def test_main_no_args_calls_ctrl_dispatcher(self) -> None:
        mock_sm = MagicMock()
        mock_wu = MagicMock()
        with (
            patch.object(svc, "_WIN32_AVAILABLE", True),
            patch.dict("sys.modules", {"servicemanager": mock_sm, "win32serviceutil": mock_wu}),
            patch("auto_fill.windows_service.servicemanager", mock_sm, create=True),
            patch("auto_fill.windows_service.win32serviceutil", mock_wu, create=True),
            patch.object(sys, "argv", ["windows_service.py"]),
        ):
            svc.main()
        mock_sm.Initialize.assert_called_once()
        mock_sm.StartServiceCtrlDispatcher.assert_called_once()

    def test_main_with_args_calls_handle_command_line(self) -> None:
        mock_wu = MagicMock()
        mock_sm = MagicMock()
        with (
            patch.object(svc, "_WIN32_AVAILABLE", True),
            patch("auto_fill.windows_service.servicemanager", mock_sm, create=True),
            patch("auto_fill.windows_service.win32serviceutil", mock_wu, create=True),
            patch.object(sys, "argv", ["windows_service.py", "install"]),
        ):
            svc.main()
        mock_wu.HandleCommandLine.assert_called_once()


class TestAutoFillServiceClass:
    """Tests cho AutoFillService — chay khi pywin32 co san."""

    @pytest.mark.skipif(not svc._WIN32_AVAILABLE, reason="pywin32 khong co san")
    def test_service_class_defined(self) -> None:
        assert hasattr(svc, "AutoFillService")

    @pytest.mark.skipif(not svc._WIN32_AVAILABLE, reason="pywin32 khong co san")
    def test_service_class_attributes(self) -> None:
        cls = svc.AutoFillService
        assert cls._svc_name_ == "AutoFillCapDon"
        assert cls._svc_display_name_ == "AutoFill Cap Don"
        assert cls._svc_description_ != ""

    def test_service_class_absent_without_win32(self) -> None:
        if not svc._WIN32_AVAILABLE:
            assert not hasattr(svc, "AutoFillService")

    @pytest.mark.skipif(not svc._WIN32_AVAILABLE, reason="pywin32 khong co san")
    def test_svc_stop_signals_stop_event(self) -> None:
        mock_base = MagicMock()
        mock_we = MagicMock()
        mock_ws = MagicMock()

        with (
            patch("auto_fill.windows_service.win32serviceutil.ServiceFramework", mock_base),
            patch("auto_fill.windows_service.win32event", mock_we, create=True),
            patch("auto_fill.windows_service.win32service", mock_ws, create=True),
        ):
            instance = svc.AutoFillService.__new__(svc.AutoFillService)
            instance._stop_event = MagicMock()
            instance.ReportServiceStatus = MagicMock()

            instance.SvcStop()

        instance.ReportServiceStatus.assert_called_once_with(mock_ws.SERVICE_STOP_PENDING)
        mock_we.SetEvent.assert_called_once_with(instance._stop_event)
