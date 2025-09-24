"""Utility modules for GitHound."""

# Lazy import for ExportManager to avoid pandas dependency issues
from typing import Any

from .progress import CancellationToken, ProgressManager


def get_export_manager() -> type[Any]:
    """Get ExportManager with lazy import.

    Returns the ExportManager class type. We avoid importing at module import
    time to prevent optional dependency issues (e.g., pandas).
    """
    from .export import ExportManager

    return ExportManager  # [return-value]


# Direct import for ExportManager (needed for backward compatibility)
try:
    from .export import ExportManager as _ExportManager

    ExportManager: type[Any] | None = _ExportManager
except ImportError:
    # If pandas is not available, ExportManager won't be available
    ExportManager = None

__all__ = ["ProgressManager", "CancellationToken", "get_export_manager", "ExportManager"]
