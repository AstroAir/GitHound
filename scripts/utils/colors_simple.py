"""
Simple console output utilities without external dependencies.
"""

from typing import Any, Optional


def print_info(message: str, **kwargs) -> None:
    """Print an info message."""
    print(f"ℹ️  {message}")


def print_success(message: str, **kwargs) -> None:
    """Print a success message."""
    print(f"✅ {message}")


def print_warning(message: str, **kwargs) -> None:
    """Print a warning message."""
    print(f"⚠️  {message}")


def print_error(message: str, **kwargs) -> None:
    """Print an error message."""
    print(f"❌ {message}")


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print(f"{'='*60}")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n🔧 {title}")
    print("─" * (len(title) + 3))


def print_step(step: str, status: str = "running") -> None:
    """Print a step with status."""
    if status == "running":
        print(f"⏳ {step}...")
    elif status == "success":
        print(f"✅ {step}")
    elif status == "error":
        print(f"❌ {step}")
    elif status == "skip":
        print(f"⏭️  {step} (skipped)")


class StatusContext:
    """Simple context manager for status updates."""

    def __init__(self, message: str):
        self.message = message

    def __enter__(self):
        print(f"⏳ {self.message}...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print_success(f"{self.message} completed")
        else:
            print_error(f"{self.message} failed")


def confirm(message: str, default: bool = True) -> bool:
    """Ask for user confirmation."""
    default_text = "Y/n" if default else "y/N"
    response = input(f"❓ {message} ({default_text}): ")

    if not response:
        return default

    return response.lower().startswith('y')


def prompt(message: str, default: Optional[str] = None) -> str:
    """Prompt user for input."""
    if default:
        response = input(f"❓ {message} [{default}]: ")
        return response or default
    else:
        return input(f"❓ {message}: ")


# For compatibility with the full colors module
console = None
