"""GitHound MCP (Model Context Protocol) module.

This module provides a modular implementation of the GitHound MCP server,
breaking down the functionality into focused, maintainable components.
"""

from typing import Any

# Handle MCP imports gracefully for Pydantic v1 compatibility
try:
    from .server import get_mcp_server, mcp, run_mcp_server

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    def get_mcp_server() -> Any:
        raise ImportError("MCP functionality not available due to Pydantic compatibility issues")

    def run_mcp_server(
        transport: str = "stdio", host: str = "localhost", port: int = 3000, log_level: str = "INFO"
    ) -> None:
        raise ImportError("MCP functionality not available due to Pydantic compatibility issues")

    mcp = None

__all__ = [
    "get_mcp_server",
    "mcp",
    "run_mcp_server",
    "MCP_AVAILABLE",
]

# Export context helpers for advanced usage
try:
    from .context_helpers import (  # noqa: F401
        ProgressTracker,
        log_operation_metrics,
        read_mcp_resource,
        report_operation_progress,
        request_llm_analysis,
        safe_execute_with_logging,
        stream_results_with_progress,
    )

    __all__.extend(
        [
            "ProgressTracker",
            "report_operation_progress",
            "stream_results_with_progress",
            "safe_execute_with_logging",
            "log_operation_metrics",
            "request_llm_analysis",
            "read_mcp_resource",
        ]
    )
except ImportError:
    pass
