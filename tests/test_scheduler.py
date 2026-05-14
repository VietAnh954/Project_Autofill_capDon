"""Unit tests cho scheduler module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from auto_fill.scheduler import start_scheduler


class TestStartScheduler:
    def test_scheduler_starts_and_stops_on_keyboard_interrupt(self) -> None:
        mock_scheduler = MagicMock()

        with (
            patch("auto_fill.scheduler.BackgroundScheduler", return_value=mock_scheduler),
            patch("auto_fill.scheduler.time.sleep", side_effect=KeyboardInterrupt),
        ):
            start_scheduler(interval_minutes=5)

        mock_scheduler.start.assert_called_once()
        mock_scheduler.add_job.assert_called_once()
        mock_scheduler.shutdown.assert_called_once_with(wait=False)

    def test_add_job_called_with_correct_interval(self) -> None:
        mock_scheduler = MagicMock()

        with (
            patch("auto_fill.scheduler.BackgroundScheduler", return_value=mock_scheduler),
            patch("auto_fill.scheduler.time.sleep", side_effect=KeyboardInterrupt),
        ):
            start_scheduler(interval_minutes=30)

        call_kwargs = mock_scheduler.add_job.call_args
        trigger = call_kwargs.kwargs.get("trigger") or call_kwargs.args[1]
        assert trigger.interval.total_seconds() == 30 * 60

    def test_max_instances_is_1(self) -> None:
        mock_scheduler = MagicMock()

        with (
            patch("auto_fill.scheduler.BackgroundScheduler", return_value=mock_scheduler),
            patch("auto_fill.scheduler.time.sleep", side_effect=KeyboardInterrupt),
        ):
            start_scheduler(interval_minutes=15)

        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        assert call_kwargs.get("max_instances") == 1

    def test_coalesce_is_true(self) -> None:
        mock_scheduler = MagicMock()

        with (
            patch("auto_fill.scheduler.BackgroundScheduler", return_value=mock_scheduler),
            patch("auto_fill.scheduler.time.sleep", side_effect=KeyboardInterrupt),
        ):
            start_scheduler(interval_minutes=15)

        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        assert call_kwargs.get("coalesce") is True


class TestSchedulerCLI:
    def test_schedule_command_exists(self) -> None:
        from click.testing import CliRunner

        from auto_fill.__main__ import schedule

        runner = CliRunner()
        with patch("auto_fill.scheduler.start_scheduler") as mock_start:
            result = runner.invoke(schedule, ["--interval", "10"])

        mock_start.assert_called_once_with(interval_minutes=10)
        assert result.exit_code == 0
