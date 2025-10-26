"""
Common utilities for GitHound development scripts.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root (no pyproject.toml found)")


def check_python_version(min_version: tuple[int, int] = (3, 11)) -> bool:
    """Check if Python version meets minimum requirements."""
    current_version = sys.version_info[:2]
    return current_version >= min_version


def check_virtual_env() -> bool:
    """Check if running in a virtual environment."""
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def run_command(
    command: str | list[str],
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """
    Run a command with proper error handling.

    Args:
        command: Command to run (string or list)
        cwd: Working directory
        check: Whether to raise exception on non-zero exit
        capture_output: Whether to capture stdout/stderr
        env: Environment variables

    Returns:
        CompletedProcess instance
    """
    if isinstance(command, str):
        command = command.split()

    try:
        result = subprocess.run(
            command, cwd=cwd, check=check, capture_output=capture_output, text=True, env=env
        )
        return result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nError: {e}") from e
    except FileNotFoundError as e:
        raise RuntimeError(f"Command not found: {command[0]}") from e


def run_command_with_output(
    command: str | list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, and stderr.

    Args:
        command: Command to run
        cwd: Working directory
        env: Environment variables

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if isinstance(command, str):
        command = command.split()

    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=env)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {command[0]}"


def get_git_info() -> dict[str, str]:
    """Get Git repository information."""
    project_root = get_project_root()
    info: dict[str, Any] = {}

    try:
        # Get current branch
        result = run_command_with_output(["git", "branch", "--show-current"], cwd=project_root)
        if result[0] == 0:
            info["branch"] = result[1].strip()

        # Get commit hash
        result = run_command_with_output(["git", "rev-parse", "HEAD"], cwd=project_root)
        if result[0] == 0:
            info["commit"] = result[1].strip()[:8]

        # Get remote URL
        result = run_command_with_output(["git", "remote", "get-url", "origin"], cwd=project_root)
        if result[0] == 0:
            info["remote"] = result[1].strip()

        # Check for uncommitted changes
        result = run_command_with_output(["git", "status", "--porcelain"], cwd=project_root)
        if result[0] == 0:
            info["dirty"] = bool(result[1].strip())

    except Exception:
        pass  # Git info is optional

    return info


def find_files_by_pattern(directory: Path, pattern: str) -> list[Path]:
    """Find files matching a pattern in directory."""
    return list(directory.rglob(pattern))


def get_directory_size(directory: Path) -> int:
    """Get total size of directory in bytes."""
    total_size = 0
    try:
        for path in directory.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
    except (OSError, PermissionError):
        pass
    return total_size


def format_bytes(bytes_count: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def safe_remove_directory(path: Path) -> bool:
    """Safely remove directory and contents."""
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            return True
    except (OSError, PermissionError):
        pass
    return False


def safe_remove_file(path: Path) -> bool:
    """Safely remove file."""
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True
    except (OSError, PermissionError):
        pass
    return False


def get_python_info() -> dict[str, str]:
    """Get Python environment information."""
    return {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "executable": sys.executable,
        "virtual_env": os.environ.get("VIRTUAL_ENV", ""),
        "platform": sys.platform,
        "implementation": sys.implementation.name,
    }


def check_port_available(port: int, host: str = "localhost") -> bool:
    """Check if a port is available."""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False


def get_free_port(start_port: int = 8000, max_attempts: int = 100) -> int | None:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    return None
