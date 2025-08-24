"""Utility modules for GitHound."""

from .progress import CancellationToken, ProgressManager


# Lazy import for ExportManager to avoid pandas dependency issues
from typing import Any, TypeVar

TExportManager = TypeVar("TExportManager")


def get_export_manager() -> type[TExportManager]:
    """Get ExportManager with lazy import.

    Returns the ExportManager class type. We avoid importing at module import
    time to prevent optional dependency issues (e.g., pandas).
    """
    from .export import ExportManager

    return ExportManager  # type: ignore[return-value]


# Direct import for ExportManager (needed for backward compatibility)
try:
    from .export import ExportManager as _ExportManager
    ExportManager: type[Any] | None = _ExportManager
except ImportError:
    # If pandas is not available, ExportManager won't be available
    ExportManager = None

__all__ = ["ProgressManager", "CancellationToken",
           "get_export_manager", "ExportManager"]
