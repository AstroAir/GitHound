"""
Platform-specific utilities for cross-platform compatibility.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Any


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system().lower() == "windows"


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system().lower() == "darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system().lower() == "linux"


def get_platform_info() -> dict[str, str]:
    """Get comprehensive platform information."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
    }


def get_shell_command() -> str:
    """Get the appropriate shell command for the platform."""
    if is_windows():
        return "cmd"
    else:
        return os.environ.get("SHELL", "/bin/bash")


def get_python_executable() -> str:
    """Get the Python executable path."""
    return sys.executable


def get_pip_executable() -> str:
    """Get the pip executable path."""
    if is_windows():
        # On Windows, pip might be pip.exe or pip3.exe
        candidates = ["pip", "pip3", "pip.exe", "pip3.exe"]
    else:
        candidates = ["pip", "pip3"]

    import shutil

    for candidate in candidates:
        if shutil.which(candidate):
            return candidate

    # Fallback to python -m pip
    return f"{get_python_executable()} -m pip"


def get_script_extension() -> str:
    """Get the appropriate script extension for the platform."""
    return ".bat" if is_windows() else ".sh"


def get_executable_extension() -> str:
    """Get the executable extension for the platform."""
    return ".exe" if is_windows() else ""


def get_path_separator() -> str:
    """Get the path separator for the platform."""
    return ";" if is_windows() else ":"


def normalize_path(path: str) -> str:
    """Normalize path for the current platform."""
    return str(Path(path).resolve())


def get_home_directory() -> Path:
    """Get the user's home directory."""
    return Path.home()


def get_temp_directory() -> Path:
    """Get the system temporary directory."""
    import tempfile

    return Path(tempfile.gettempdir())


def get_config_directory(app_name: str) -> Path:
    """Get the appropriate configuration directory for the app."""
    if is_windows():
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif is_macos():
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))  # [attr-defined]

    return base / app_name


def get_cache_directory(app_name: str) -> Path:
    """Get the appropriate cache directory for the app."""
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif is_macos():
        base = Path.home() / "Library" / "Caches"
    else:  # Linux and other Unix-like
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    return base / app_name


def get_data_directory(app_name: str) -> Path:
    """Get the appropriate data directory for the app."""
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif is_macos():
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    return base / app_name


def get_environment_variables() -> dict[str, str]:
    """Get relevant environment variables."""
    relevant_vars = [
        "PATH",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "CONDA_DEFAULT_ENV",
        "HOME",
        "USER",
        "USERNAME",
        "SHELL",
        "TERM",
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
    ]

    return {var: os.environ.get(var, "") for var in relevant_vars if os.environ.get(var)}


def get_system_info() -> dict[str, str]:
    """Get comprehensive system information."""
    info = get_platform_info()
    info.update(
        {
            "hostname": platform.node(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME", "unknown"),
            "shell": get_shell_command(),
            "python_executable": get_python_executable(),
            "pip_executable": get_pip_executable(),
        }
    )

    # Add CPU and memory info if available
    try:
        import psutil

        info.update(
            {
                "cpu_count": str(psutil.cpu_count()),
                "memory_total": f"{psutil.virtual_memory().total // (1024**3)} GB",
                "disk_usage": f"{psutil.disk_usage('/').percent:.1f}%",
            }
        )
    except ImportError:
        pass

    return info


def create_cross_platform_script(
    script_name: str, python_script: str, output_dir: Path, description: str = ""
) -> list[Path]:
    """
    Create cross-platform wrapper scripts for a Python script.

    Args:
        script_name: Name of the script (without extension)
        python_script: Path to the Python script (relative to output_dir)
        output_dir: Directory to create scripts in
        description: Description for the script

    Returns:
        List of created script paths
    """
    created_scripts: list[Any] = []

    # Create shell script for Unix-like systems
    shell_script = output_dir / f"{script_name}.sh"
    shell_content = f"""#!/bin/bash
# {description}
# Cross-platform wrapper for {python_script}

set -e

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
python "$SCRIPT_DIR/{python_script}" "$@"
"""

    shell_script.write_text(shell_content)
    shell_script.chmod(0o755)  # Make executable
    created_scripts.append(shell_script)

    # Create batch script for Windows
    batch_script = output_dir / f"{script_name}.bat"
    batch_content = f"""@echo off
REM {description}
REM Cross-platform wrapper for {python_script}

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%{python_script.replace('/', os.sep)}" %*
"""

    batch_script.write_text(batch_content)
    created_scripts.append(batch_script)

    return created_scripts


def get_terminal_size() -> tuple[int, int]:
    """Get terminal size (width, height)."""
    try:
        import shutil

        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        return 80, 24  # Default fallback


def supports_color() -> bool:
    """Check if terminal supports color output."""
    if is_windows():
        # Windows 10 and later support ANSI colors
        try:
            import sys

            return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        except Exception:
            return False
    else:
        # Unix-like systems
        return os.environ.get("TERM", "").lower() not in ["", "dumb"]


def get_available_ports(start: int = 8000, count: int = 10) -> list[int]:
    """Get a list of available ports."""
    import socket

    available: list[Any] = []

    for port in range(start, start + count * 10):  # Check more ports than needed
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                result = sock.connect_ex(("localhost", port))
                if result != 0:
                    available.append(port)
                    if len(available) >= count:
                        break
        except Exception:
            continue

    return available
