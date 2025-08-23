"""Utility modules for GitHound."""

from .progress import CancellationToken, ProgressManager


# Lazy import for ExportManager to avoid pandas dependency issues
def get_export_manager():
    """Get ExportManager with lazy import."""
    from .export import ExportManager

    return ExportManager


# Direct import for ExportManager (needed for backward compatibility)
try:
    from .export import ExportManager
except ImportError:
    # If pandas is not available, ExportManager won't be available
    ExportManager = None  # type: ignore[assignment,misc]

__all__ = ["ProgressManager", "CancellationToken", "get_export_manager", "ExportManager"]
