"""Tests for GitHound progress utilities."""

import threading
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest

from githound.utils.progress import CancellationToken, ProgressManager, SimpleProgressReporter


class TestCancellationToken:
    """Test CancellationToken class."""

    def test_cancellation_token_creation(self) -> None:
        """Test creating a CancellationToken."""
        token = CancellationToken()

        assert not token.is_cancelled
        assert token.cancellation_reason is None

    def test_cancellation_token_cancel(self) -> None:
        """Test cancelling a token."""
        token = CancellationToken()
        reason = "User requested cancellation"

        token.cancel(reason)

        assert token.is_cancelled
        assert token.cancellation_reason == reason

    def test_cancellation_token_check_cancelled(self) -> None:
        """Test check_cancelled method."""
        token = CancellationToken()

        # Should not raise when not cancelled
        token.check_cancelled()

        # Should raise when cancelled
        token.cancel("Test cancellation")
        with pytest.raises(Exception, match="Test cancellation"):
            token.check_cancelled()

    def test_cancellation_token_thread_safety(self) -> None:
        """Test that CancellationToken is thread-safe."""
        token = CancellationToken()
        results: list[Any] = []

        def cancel_token() -> None:
            time.sleep(0.1)
            token.cancel("Thread cancellation")
            results.append("cancelled")

        def check_token() -> None:
            time.sleep(0.2)
            results.append(token.is_cancelled)

        thread1 = threading.Thread(target=cancel_token)
        thread2 = threading.Thread(target=check_token)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        assert "cancelled" in results
        assert True in results  # Token should be cancelled when checked


class TestProgressManager:
    """Test ProgressManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.console = Mock()
        # Make console support context manager protocol
        self.console.__enter__ = Mock(return_value=self.console)
        self.console.__exit__ = Mock(return_value=None)

    def test_progress_manager_creation(self) -> None:
        """Test creating a ProgressManager."""
        manager = ProgressManager(console=self.console, enable_cancellation=True)

        assert manager.console == self.console
        assert manager.enable_cancellation is True
        assert isinstance(manager.cancellation_token, CancellationToken)

    def test_progress_manager_context_manager(self) -> None:
        """Test ProgressManager as context manager."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress

            with ProgressManager(console=self.console) as manager:
                assert manager._progress == mock_progress
                mock_progress.__enter__.assert_called_once()

            mock_progress.__exit__.assert_called_once()

    def test_progress_manager_add_task(self) -> None:
        """Test adding a task to ProgressManager."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress
            mock_progress.add_task.return_value = "task_id_123"

            with ProgressManager(console=self.console) as manager:
                task_name = manager.add_task("test_task", "Testing...", 100)

                assert task_name == "test_task"
                assert "test_task" in manager._tasks
                assert "test_task" in manager._stats
                mock_progress.add_task.assert_called_once_with("Testing...", total=100)

    def test_progress_manager_update_task(self) -> None:
        """Test updating a task in ProgressManager."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress
            mock_progress.add_task.return_value = "task_id_123"

            with ProgressManager(console=self.console) as manager:
                manager.add_task("test_task", "Testing...", 100)
                manager.update_task("test_task", completed=50, description="Half done")

                mock_progress.update.assert_called()

    def test_progress_manager_advance_task(self) -> None:
        """Test advancing a task in ProgressManager."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress
            mock_progress.add_task.return_value = "task_id_123"

            with ProgressManager(console=self.console) as manager:
                manager.add_task("test_task", "Testing...", 100)
                manager.advance_task("test_task", 10)

                mock_progress.advance.assert_called()

    def test_progress_manager_complete_task(self) -> None:
        """Test completing a task in ProgressManager."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress
            mock_progress.add_task.return_value = "task_id_123"

            with ProgressManager(console=self.console) as manager:
                manager.add_task("test_task", "Testing...", 100)
                manager.complete_task("test_task", "Task completed")

                mock_progress.update.assert_called()

    def test_progress_manager_get_stats(self) -> None:
        """Test getting task statistics."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress
            mock_progress.add_task.return_value = "task_id_123"

            with ProgressManager(console=self.console) as manager:
                manager.add_task("test_task", "Testing...", 100)
                stats = manager.get_stats("test_task")

                assert "started" in stats
                assert "completed" in stats
                assert "total" in stats
                assert "description" in stats

    def test_progress_manager_get_all_stats(self) -> None:
        """Test getting all task statistics."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress
            mock_progress.add_task.return_value = "task_id_123"

            with ProgressManager(console=self.console) as manager:
                manager.add_task("task1", "Testing 1...", 100)
                manager.add_task("task2", "Testing 2...", 200)
                all_stats = manager.get_all_stats()

                assert "task1" in all_stats
                assert "task2" in all_stats
                assert "total_duration" in all_stats

    def test_progress_manager_without_context(self) -> None:
        """Test that operations fail when not used as context manager."""
        manager = ProgressManager(console=self.console)

        with pytest.raises(RuntimeError, match="ProgressManager not initialized"):
            manager.add_task("test_task", "Testing...", 100)

    def test_progress_manager_cancellation(self) -> None:
        """Test cancellation functionality."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_progress_class.return_value = mock_progress

            with ProgressManager(console=self.console, enable_cancellation=True) as manager:
                manager.cancellation_token.cancel("Test cancellation")

                with pytest.raises(Exception, match="Test cancellation"):
                    manager.check_cancellation()

    def test_progress_manager_signal_handling(self) -> None:
        """Test signal handling for cancellation."""
        with patch("githound.utils.progress.Progress") as mock_progress_class:
            with patch("signal.signal") as mock_signal:
                mock_progress = Mock()
                mock_progress.__enter__ = Mock(return_value=mock_progress)
                mock_progress.__exit__ = Mock(return_value=None)
                mock_progress_class.return_value = mock_progress

                with ProgressManager(console=self.console, enable_cancellation=True) as manager:
                    # Signal handler should be set
                    assert mock_signal.called


class TestSimpleProgressReporter:
    """Test SimpleProgressReporter class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.console = Mock()

    def test_simple_progress_reporter_creation(self) -> None:
        """Test creating a SimpleProgressReporter."""
        reporter = SimpleProgressReporter(console=self.console)

        assert reporter.console == self.console
        assert reporter._last_update == 0.0
        assert reporter._update_interval == 0.5

    def test_simple_progress_reporter_report_message_only(self) -> None:
        """Test reporting progress with message only."""
        reporter = SimpleProgressReporter(console=self.console)

        reporter.report("Processing files...")

        self.console.print.assert_called_once_with("[cyan]Processing files...[/cyan]")

    def test_simple_progress_reporter_report_with_progress(self) -> None:
        """Test reporting progress with percentage."""
        reporter = SimpleProgressReporter(console=self.console)

        reporter.report("Processing files...", 0.75)

        self.console.print.assert_called_once_with(
            "[cyan]Processing files...[/cyan] [yellow](75.0%)[/yellow]"
        )

    def test_simple_progress_reporter_throttling(self) -> None:
        """Test that progress updates are throttled."""
        reporter = SimpleProgressReporter(console=self.console)

        # First call should go through
        reporter.report("First message")
        assert self.console.print.call_count == 1

        # Immediate second call should be throttled
        reporter.report("Second message")
        assert self.console.print.call_count == 1

        # After waiting, call should go through
        with patch("time.time", return_value=time.time() + 1.0):
            reporter.report("Third message")
            assert self.console.print.call_count == 2

    def test_simple_progress_reporter_custom_interval(self) -> None:
        """Test SimpleProgressReporter with custom update interval."""
        reporter = SimpleProgressReporter(console=self.console)
        reporter._update_interval = 0.1  # Very short interval

        reporter.report("First message")
        assert self.console.print.call_count == 1

        # Should still be throttled immediately
        reporter.report("Second message")
        assert self.console.print.call_count == 1

    def test_simple_progress_reporter_zero_progress(self) -> None:
        """Test reporting with zero progress."""
        reporter = SimpleProgressReporter(console=self.console)

        reporter.report("Starting...", 0.0)

        self.console.print.assert_called_once_with(
            "[cyan]Starting...[/cyan] [yellow](0.0%)[/yellow]"
        )

    def test_simple_progress_reporter_complete_progress(self) -> None:
        """Test reporting with complete progress."""
        reporter = SimpleProgressReporter(console=self.console)

        reporter.report("Complete!", 1.0)

        self.console.print.assert_called_once_with(
            "[cyan]Complete![/cyan] [yellow](100.0%)[/yellow]"
        )

    def test_simple_progress_reporter_default_console(self) -> None:
        """Test SimpleProgressReporter with default console."""
        with patch("githound.utils.progress.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            reporter = SimpleProgressReporter()

            assert reporter.console == mock_console
            mock_console_class.assert_called_once()
