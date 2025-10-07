"""
Compatibility shim for the unified GitHound FastAPI application.

All v2-style endpoints are now defined on the single app instance in
githound.web.api. This module re-exports that app to preserve import paths
in tests and external callers without duplicating implementation.
"""

from .api import app

__all__ = ["app"]