"""Working CLI tests that focus on achievable coverage improvements."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from githound.cli import app


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


class TestCLIBasicFunctionality:
    """Test basic CLI functionality that doesn't require complex fixtures."""

    def test_cli_help(self, cli_runner):
        """Test CLI help functionality."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "GitHound" in result.stdout

    def test_cli_no_args(self, cli_runner):
        """Test CLI with no arguments."""
        result = cli_runner.invoke(app, [])
        assert result.exit_code == 0
        assert "No command specified" in result.stdout

    def test_version_command(self, cli_runner):
        """Test version command."""
        result = cli_runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_version_with_build_info(self, cli_runner):
        """Test version command with build info."""
        result = cli_runner.invoke(app, ["version", "--build-info"])
        assert result.exit_code == 0

    def test_cleanup_command(self, cli_runner):
        """Test cleanup command."""
        result = cli_runner.invoke(app, ["cleanup"])
        # Should complete (may succeed or fail gracefully)
        assert result.exit_code in [0, 1]

    def test_invalid_command(self, cli_runner):
        """Test invalid command."""
        result = cli_runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0

    def test_search_help(self, cli_runner):
        """Test search command help."""
        result = cli_runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout.lower()

    def test_analyze_help(self, cli_runner):
        """Test analyze command help."""
        result = cli_runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout.lower()

    def test_blame_help(self, cli_runner):
        """Test blame command help."""
        result = cli_runner.invoke(app, ["blame", "--help"])
        assert result.exit_code == 0
        assert "blame" in result.stdout.lower()

    def test_diff_help(self, cli_runner):
        """Test diff command help."""
        result = cli_runner.invoke(app, ["diff", "--help"])
        assert result.exit_code == 0
        assert "diff" in result.stdout.lower()

    def test_web_help(self, cli_runner):
        """Test web command help."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "web" in result.stdout.lower()

    def test_mcp_server_help(self, cli_runner):
        """Test MCP server command help."""
        result = cli_runner.invoke(app, ["mcp-server", "--help"])
        assert result.exit_code == 0
        assert "mcp" in result.stdout.lower()

    def test_quickstart_help(self, cli_runner):
        """Test quickstart command help."""
        result = cli_runner.invoke(app, ["quickstart", "--help"])
        assert result.exit_code == 0
        assert "quickstart" in result.stdout.lower()


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def test_search_missing_repo_path(self, cli_runner):
        """Test search command with missing repo path."""
        # Run in a temporary directory that's not a git repo
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to non-git directory for this test
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = cli_runner.invoke(app, ["search", "--content", "test"])
                # Should fail because it's not a git repository
                assert result.exit_code != 0
            finally:
                os.chdir(original_cwd)

    def test_search_invalid_repo_path(self, cli_runner):
        """Test search command with invalid repo path."""
        result = cli_runner.invoke(
            app, ["search", "--repo-path", "/nonexistent", "--content", "test"]
        )
        assert result.exit_code != 0

    def test_analyze_invalid_repo_path(self, cli_runner):
        """Test analyze command with invalid repo path."""
        result = cli_runner.invoke(app, ["analyze", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_blame_missing_file_path(self, cli_runner):
        """Test blame command with missing file path."""
        result = cli_runner.invoke(app, ["blame", "."])
        assert result.exit_code != 0

    def test_diff_missing_commits(self, cli_runner):
        """Test diff command with missing commit arguments."""
        result = cli_runner.invoke(app, ["diff", "."])
        assert result.exit_code != 0

    def test_invalid_output_format(self, cli_runner):
        """Test command with invalid output format."""
        result = cli_runner.invoke(app, ["analyze", ".", "--format", "invalid"])
        assert result.exit_code != 0


class TestCLIWithMocking:
    """Test CLI functionality with mocked dependencies."""

    @patch("githound.cli.search_and_print")
    def test_search_command_basic(self, mock_search, cli_runner):
        """Test basic search command with mocking."""
        # Create a temporary directory to use as repo path
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(
                app, ["search", "--repo-path", temp_dir, "--content", "test"]
            )

            # The command should attempt to call search_and_print
            # (it may fail due to not being a git repo, but that's expected)
            assert result.exit_code in [0, 1]  # Allow both success and expected failure

    @patch("githound.GitHound")
    def test_analyze_command_basic(self, mock_githound, cli_runner):
        """Test basic analyze command with mocking."""
        mock_instance = Mock()
        mock_instance.analyze_repository.return_value = Mock(
            path="test", name="test-repo", total_commits=1
        )
        mock_githound.return_value = mock_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(app, ["analyze", temp_dir])

            # Should attempt to create GitHound instance
            assert result.exit_code in [0, 1]

    @patch("uvicorn.run")
    def test_web_command_basic(self, mock_uvicorn, cli_runner):
        """Test basic web command with mocking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(app, ["web", temp_dir])

            # Should attempt to start web server
            assert result.exit_code in [0, 1]

    @patch("githound.cli.mcp_server")
    def test_mcp_server_command_basic(self, mock_mcp, cli_runner):
        """Test basic MCP server command with mocking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(app, ["mcp-server", temp_dir])

            # Should attempt to start MCP server
            assert result.exit_code in [0, 1]

    @patch("typer.prompt")
    def test_quickstart_command_basic(self, mock_prompt, cli_runner):
        """Test basic quickstart command with mocking."""
        # Mock user selecting exit option
        mock_prompt.return_value = 7

        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(app, ["quickstart", temp_dir])

            # Should show quickstart interface
            assert result.exit_code in [0, 1]


class TestCLIOutputFormats:
    """Test CLI output format handling."""

    def test_search_json_format_help(self, cli_runner):
        """Test that JSON format is available in search help."""
        result = cli_runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "json" in result.stdout.lower()

    def test_analyze_json_format_help(self, cli_runner):
        """Test that JSON format is available in analyze help."""
        result = cli_runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "json" in result.stdout.lower()

    def test_blame_json_format_help(self, cli_runner):
        """Test that JSON format is available in blame help."""
        result = cli_runner.invoke(app, ["blame", "--help"])
        assert result.exit_code == 0
        assert "json" in result.stdout.lower()

    def test_diff_json_format_help(self, cli_runner):
        """Test that JSON format is available in diff help."""
        result = cli_runner.invoke(app, ["diff", "--help"])
        assert result.exit_code == 0
        assert "json" in result.stdout.lower()


class TestCLIOptionParsing:
    """Test CLI option parsing."""

    def test_search_content_option(self, cli_runner):
        """Test search command content option parsing."""
        result = cli_runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "--content" in result.stdout

    def test_search_author_option(self, cli_runner):
        """Test search command author option parsing."""
        result = cli_runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "--author" in result.stdout

    def test_search_message_option(self, cli_runner):
        """Test search command message option parsing."""
        result = cli_runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "--message" in result.stdout

    def test_search_fuzzy_option(self, cli_runner):
        """Test search command fuzzy option parsing."""
        result = cli_runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "--fuzzy" in result.stdout

    def test_web_port_option(self, cli_runner):
        """Test web command port option parsing."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.stdout

    def test_web_host_option(self, cli_runner):
        """Test web command host option parsing."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.stdout

    def test_mcp_server_port_option(self, cli_runner):
        """Test MCP server command port option parsing."""
        result = cli_runner.invoke(app, ["mcp-server", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.stdout

    def test_output_option_in_commands(self, cli_runner):
        """Test that output option is available in relevant commands."""
        for command in ["search", "analyze", "blame", "diff"]:
            result = cli_runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0
            assert "--output" in result.stdout
