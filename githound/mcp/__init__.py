"""GitHound MCP (Model Context Protocol) module.

This module provides a modular implementation of the GitHound MCP server,
breaking down the functionality into focused, maintainable components.
"""

from .server import get_mcp_server, mcp, run_mcp_server

__all__ = [
    "get_mcp_server",
    "mcp",
    "run_mcp_server",
]
