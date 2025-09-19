"""Tests for GitHound web server."""

import pytest
import sys
from unittest.mock import Mock, patch, call
from typer.testing import CliRunner

from githound.web.server import app, serve, dev, prod


class TestWebServer:
    """Test GitHound web server commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('githound.web.server.uvicorn.run')
    def test_serve_command_defaults(self, mock_uvicorn_run) -> None:
        """Test serve command with default parameters."""
        result = self.runner.invoke(app, ['serve'])

        assert result.exit_code == 0
        mock_uvicorn_run.assert_called_once_with(
            "githound.web.api:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
            workers=1,
            access_log=True,
        )

    @patch('githound.web.server.uvicorn.run')
    def test_serve_command_custom_params(self, mock_uvicorn_run) -> None:
        """Test serve command with custom parameters."""
        result = self.runner.invoke(app, [
            'serve',
            '--host', '127.0.0.1',
            '--port', '8080',
            '--reload',
            '--log-level', 'debug',
            '--workers', '4'
        ])

        assert result.exit_code == 0
        mock_uvicorn_run.assert_called_once_with(
            "githound.web.api:app",
            host="127.0.0.1",
            port=8080,
            reload=True,
            log_level="debug",
            workers=1,  # Should be 1 when reload is True
            access_log=True,
        )

    @patch('githound.web.server.uvicorn.run')
    def test_serve_command_with_workers_no_reload(self, mock_uvicorn_run) -> None:
        """Test serve command with multiple workers and no reload."""
        result = self.runner.invoke(app, [
            'serve',
            '--workers', '4'
        ])

        assert result.exit_code == 0
        mock_uvicorn_run.assert_called_once_with(
            "githound.web.api:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
            workers=4,  # Should use specified workers when reload is False
            access_log=True,
        )

    @patch('githound.web.server.uvicorn.run')
    def test_serve_command_keyboard_interrupt(self, mock_uvicorn_run) -> None:
        """Test serve command handling KeyboardInterrupt."""
        mock_uvicorn_run.side_effect = KeyboardInterrupt()

        result = self.runner.invoke(app, ['serve'])

        assert result.exit_code == 0
        assert "GitHound server stopped" in result.output

    @patch('githound.web.server.uvicorn.run')
    @patch('githound.web.server.sys.exit')
    def test_serve_command_exception(self, mock_sys_exit, mock_uvicorn_run) -> None:
        """Test serve command handling general exceptions."""
        mock_uvicorn_run.side_effect = Exception("Server failed to start")

        result = self.runner.invoke(app, ['serve'])

        # sys.exit may be called multiple times by the CLI framework
        # Check that it was called with code 1 at some point
        assert mock_sys_exit.call_count >= 1
        assert any(call.args[0] == 1 for call in mock_sys_exit.call_args_list)
        assert "Failed to start server" in result.output

    @patch('githound.web.server.serve')
    def test_dev_command(self, mock_serve) -> None:
        """Test dev command."""
        result = self.runner.invoke(app, ['dev'])

        assert result.exit_code == 0
        mock_serve.assert_called_once_with(
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="debug",
            workers=1
        )

    @patch('githound.web.server.serve')
    def test_prod_command_defaults(self, mock_serve) -> None:
        """Test prod command with default parameters."""
        result = self.runner.invoke(app, ['prod'])

        assert result.exit_code == 0
        mock_serve.assert_called_once_with(
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
            workers=4
        )

    @patch('githound.web.server.serve')
    def test_prod_command_custom_params(self, mock_serve) -> None:
        """Test prod command with custom parameters."""
        result = self.runner.invoke(app, [
            'prod',
            '--host', '192.168.1.100',
            '--port', '9000',
            '--workers', '8'
        ])

        assert result.exit_code == 0
        mock_serve.assert_called_once_with(
            host="192.168.1.100",
            port=9000,
            reload=False,
            log_level="info",
            workers=8
        )

    def test_serve_command_help(self) -> None:
        """Test serve command help output."""
        result = self.runner.invoke(app, ['serve', '--help'])

        assert result.exit_code == 0
        assert "Start the GitHound web server" in result.output
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--reload" in result.output
        assert "--log-level" in result.output
        assert "--workers" in result.output

    def test_dev_command_help(self) -> None:
        """Test dev command help output."""
        result = self.runner.invoke(app, ['dev', '--help'])

        assert result.exit_code == 0
        assert "Start the development server" in result.output

    def test_prod_command_help(self) -> None:
        """Test prod command help output."""
        result = self.runner.invoke(app, ['prod', '--help'])

        assert result.exit_code == 0
        assert "Start the production server" in result.output

    @patch('githound.web.server.uvicorn.run')
    def test_serve_output_messages(self, mock_uvicorn_run) -> None:
        """Test that serve command outputs expected messages."""
        result = self.runner.invoke(app, ['serve'])

        assert "🐕 Starting GitHound Web Server..." in result.output
        assert "Host: 0.0.0.0" in result.output
        assert "Port: 8000" in result.output
        assert "Workers: 1" in result.output
        assert "Reload: False" in result.output
        assert "Log Level: info" in result.output
        assert "Available endpoints:" in result.output
        assert "Web Interface: http://0.0.0.0:8000/" in result.output
        assert "API Docs: http://0.0.0.0:8000/api/docs" in result.output
        assert "Health Check: http://0.0.0.0:8000/health" in result.output

    @patch('githound.web.server.serve')
    def test_dev_output_messages(self, mock_serve) -> None:
        """Test that dev command outputs expected messages."""
        result = self.runner.invoke(app, ['dev'])

        assert "🚀 Starting GitHound Development Server..." in result.output

    @patch('githound.web.server.serve')
    def test_prod_output_messages(self, mock_serve) -> None:
        """Test that prod command outputs expected messages."""
        result = self.runner.invoke(app, ['prod'])

        assert "🏭 Starting GitHound Production Server..." in result.output

    def test_app_main_help(self) -> None:
        """Test main app help output."""
        result = self.runner.invoke(app, ['--help'])

        assert result.exit_code == 0
        assert "serve" in result.output
        assert "dev" in result.output
        assert "prod" in result.output

    @patch('githound.web.server.uvicorn.run')
    def test_serve_port_validation(self, mock_uvicorn_run) -> None:
        """Test serve command with different port values."""
        # Test with valid port
        result = self.runner.invoke(app, ['serve', '--port', '3000'])
        assert result.exit_code == 0

        # Test with port 0 (should be allowed)
        result = self.runner.invoke(app, ['serve', '--port', '0'])
        assert result.exit_code == 0

        # Test with high port number
        result = self.runner.invoke(app, ['serve', '--port', '65535'])
        assert result.exit_code == 0

    @patch('githound.web.server.uvicorn.run')
    def test_serve_host_validation(self, mock_uvicorn_run) -> None:
        """Test serve command with different host values."""
        # Test with localhost
        result = self.runner.invoke(app, ['serve', '--host', 'localhost'])
        assert result.exit_code == 0

        # Test with specific IP
        result = self.runner.invoke(app, ['serve', '--host', '192.168.1.100'])
        assert result.exit_code == 0

        # Test with IPv6
        result = self.runner.invoke(app, ['serve', '--host', '::1'])
        assert result.exit_code == 0

    @patch('githound.web.server.uvicorn.run')
    def test_serve_log_level_validation(self, mock_uvicorn_run) -> None:
        """Test serve command with different log levels."""
        log_levels = ['critical', 'error', 'warning', 'info', 'debug', 'trace']

        for level in log_levels:
            result = self.runner.invoke(app, ['serve', '--log-level', level])
            assert result.exit_code == 0
            mock_uvicorn_run.assert_called()

            # Check that the log level was passed correctly
            call_args = mock_uvicorn_run.call_args
            assert call_args[1]['log_level'] == level

            mock_uvicorn_run.reset_mock()

    @patch('githound.web.server.uvicorn.run')
    def test_serve_workers_validation(self, mock_uvicorn_run) -> None:
        """Test serve command with different worker counts."""
        # Test with 1 worker
        result = self.runner.invoke(app, ['serve', '--workers', '1'])
        assert result.exit_code == 0

        # Test with multiple workers
        result = self.runner.invoke(app, ['serve', '--workers', '8'])
        assert result.exit_code == 0

        # Test with 0 workers (should still work, uvicorn will handle it)
        result = self.runner.invoke(app, ['serve', '--workers', '0'])
        assert result.exit_code == 0
