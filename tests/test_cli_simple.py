"""Simple CLI tests to verify basic functionality."""

import pytest
from typer.testing import CliRunner

from githound.cli import app


def test_cli_import():
    """Test that CLI module can be imported."""
    assert app is not None


def test_cli_runner_basic():
    """Test basic CLI runner functionality."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "GitHound" in result.stdout


def test_version_command():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
