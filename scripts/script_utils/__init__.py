"""
GitHound Utility Scripts - Shared Utilities

This package contains shared utilities for GitHound development scripts.
"""

from .common import (
    check_command_exists,
    check_python_version,
    check_virtual_env,
    get_project_root,
    run_command,
    run_command_with_output,
)

# Try to import rich-based colors, fall back to simple version
try:
    from .colors import (
        StatusContext,
        confirm,
        console,
        print_error,
        print_header,
        print_info,
        print_section,
        print_step,
        print_success,
        print_warning,
        prompt,
    )
except ImportError:
    from .colors_simple import (
        StatusContext,
        confirm,
        console,
        print_error,
        print_header,
        print_info,
        print_section,
        print_step,
        print_success,
        print_warning,
        prompt,
    )

from .platform import get_platform_info, get_python_executable, get_shell_command, is_windows

__all__ = [
    # Common utilities
    "check_command_exists",
    "check_python_version",
    "check_virtual_env",
    "get_project_root",
    "run_command",
    "run_command_with_output",
    # Console output
    "console",
    "print_error",
    "print_info",
    "print_success",
    "print_warning",
    "print_header",
    "print_section",
    "print_step",
    "StatusContext",
    "confirm",
    "prompt",
    # Platform utilities
    "get_platform_info",
    "is_windows",
    "get_shell_command",
    "get_python_executable",
]
