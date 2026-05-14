"""Unit tests cho gui.py — chay khong can display (mock Tkinter)."""

from __future__ import annotations

import queue
from unittest.mock import MagicMock, patch

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _make_mock_tk() -> MagicMock:
    """Tao mock Tkinter module de tranh loi 'no display'."""
    mock_tk = MagicMock()
    mock_tk.Tk = MagicMock
    mock_tk.END = "end"
    mock_tk.TOP = "top"
    mock_tk.BOTTOM = "bottom"
    mock_tk.LEFT = "left"
    mock_tk.X = "x"
    mock_tk.Y = "y"
    mock_tk.BOTH = "both"
    mock_tk.WORD = "word"
    mock_tk.DISABLED = "disabled"
    mock_tk.NORMAL = "normal"
    mock_tk.W = "w"
    mock_tk.StringVar = MagicMock
    mock_tk.IntVar = MagicMock
    return mock_tk


# --------------------------------------------------------------------------- #
# _PipelineRunner                                                              #
# --------------------------------------------------------------------------- #


class TestPipelineRunner:
    def _make_runner(self) -> tuple[object, queue.Queue[str]]:
        from auto_fill.gui import _PipelineRunner

        q: queue.Queue[str] = queue.Queue()
        return _PipelineRunner(q), q

    def test_is_running_false_initially(self) -> None:
        runner, _ = self._make_runner()
        from auto_fill.gui import _PipelineRunner

        assert not isinstance(runner, type(None))
        r: _PipelineRunner = runner  # type: ignore[assignment]
        assert r.is_running is False

    def test_run_emits_start_line(self) -> None:
        from auto_fill.gui import _PipelineRunner

        q: queue.Queue[str] = queue.Queue()
        runner = _PipelineRunner(q)

        mock_proc = MagicMock()
        mock_proc.stdout = iter(["line1\n", "line2\n"])
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc):
            runner._do_run(dry_run=False)

        lines = []
        while not q.empty():
            lines.append(q.get())

        assert any("[start]" in ln for ln in lines)
        assert any("[done]" in ln for ln in lines)

    def test_dry_run_adds_flag(self) -> None:
        from auto_fill.gui import _PipelineRunner

        q: queue.Queue[str] = queue.Queue()
        runner = _PipelineRunner(q)

        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.returncode = 0

        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            runner._do_run(dry_run=True)

        cmd = mock_popen.call_args[0][0]
        assert "--dry-run" in cmd

    def test_warn_if_already_running(self) -> None:
        from auto_fill.gui import _PipelineRunner

        q: queue.Queue[str] = queue.Queue()
        runner = _PipelineRunner(q)

        # Simulate a running thread
        fake_thread = MagicMock()
        fake_thread.is_alive.return_value = True
        runner._thread = fake_thread

        runner.run(dry_run=False)
        lines = []
        while not q.empty():
            lines.append(q.get())
        assert any("[warn]" in ln for ln in lines)


# --------------------------------------------------------------------------- #
# _SchedulerController                                                         #
# --------------------------------------------------------------------------- #


class TestSchedulerController:
    def test_start_spawns_process(self) -> None:
        from auto_fill.gui import _SchedulerController

        q: queue.Queue[str] = queue.Queue()
        ctrl = _SchedulerController(q, interval=15)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdout = iter([])

        with patch("subprocess.Popen", return_value=mock_proc):
            ctrl.start()

        assert ctrl._proc is not None

    def test_stop_terminates_process(self) -> None:
        from auto_fill.gui import _SchedulerController

        q: queue.Queue[str] = queue.Queue()
        ctrl = _SchedulerController(q, interval=15)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        ctrl._proc = mock_proc

        ctrl.stop()
        mock_proc.terminate.assert_called_once()

    def test_is_running_false_when_no_proc(self) -> None:
        from auto_fill.gui import _SchedulerController

        q: queue.Queue[str] = queue.Queue()
        ctrl = _SchedulerController(q)
        assert ctrl.is_running is False

    def test_warn_if_already_running(self) -> None:
        from auto_fill.gui import _SchedulerController

        q: queue.Queue[str] = queue.Queue()
        ctrl = _SchedulerController(q)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        ctrl._proc = mock_proc

        mock_proc2 = MagicMock()
        with patch("subprocess.Popen", return_value=mock_proc2):
            ctrl.start()

        lines = []
        while not q.empty():
            lines.append(q.get())
        assert any("[warn]" in ln for ln in lines)


# --------------------------------------------------------------------------- #
# Module-level smoke                                                           #
# --------------------------------------------------------------------------- #


class TestGuiModuleImport:
    def test_module_importable(self) -> None:
        import auto_fill.gui as gui_mod

        assert hasattr(gui_mod, "AutoFillApp")
        assert hasattr(gui_mod, "main")

    def test_cli_gui_command_registered(self) -> None:
        from auto_fill.__main__ import cli

        assert "gui" in cli.commands
