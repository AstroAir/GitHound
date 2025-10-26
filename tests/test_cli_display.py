"""Tests for Rich-enhanced CLI display utilities."""

import pytest
from rich.console import Console

from githound.utils.cli_display import (
    create_command_table,
    create_startup_banner,
    display_version_info,
    display_welcome_message,
    format_error_message,
    format_success_message,
)


@pytest.fixture
def console() -> Console:
    """Create a Rich Console for testing."""
    return Console(force_terminal=False, width=120, legacy_windows=False)


def test_create_startup_banner(console: Console) -> None:
    """Test startup banner creation and rendering."""
    # Should not raise any exceptions
    create_startup_banner(console)


def test_display_version_info_basic(console: Console) -> None:
    """Test basic version info display."""
    # Should not raise any exceptions
    display_version_info(console, detailed=False)


def test_display_version_info_detailed(console: Console) -> None:
    """Test detailed version info display."""
    # Should not raise any exceptions
    display_version_info(console, detailed=True)


def test_display_welcome_message(console: Console) -> None:
    """Test welcome message display."""
    # Should not raise any exceptions
    display_welcome_message(console)


def test_create_command_table(console: Console) -> None:
    """Test command table creation."""
    commands = [
        {"icon": "🔍", "name": "search", "description": "Search repository"},
        {"icon": "📊", "name": "analyze", "description": "Analyze repository"},
    ]
    # Should not raise any exceptions
    create_command_table(commands, console)


def test_format_error_message() -> None:
    """Test error message formatting."""
    panel = format_error_message("Test error", hint="Test hint")
    assert panel is not None
    assert panel.title == "[bold red]Error[/bold red]"


def test_format_error_message_no_hint() -> None:
    """Test error message formatting without hint."""
    panel = format_error_message("Test error")
    assert panel is not None
    assert panel.title == "[bold red]Error[/bold red]"


def test_format_success_message() -> None:
    """Test success message formatting."""
    panel = format_success_message("Test success")
    assert panel is not None
    assert panel.border_style == "green"


def test_version_display_does_not_crash(console: Console) -> None:
    """Test that version display works without crashing in various scenarios."""
    # Test all combinations
    for detailed in [True, False]:
        display_version_info(console, detailed=detailed)


def test_banner_components_render(console: Console) -> None:
    """Test that banner components render without errors."""
    # Test banner
    create_startup_banner(console)

    # Test welcome
    display_welcome_message(console)

    # Test version displays
    display_version_info(console, detailed=False)
    display_version_info(console, detailed=True)
