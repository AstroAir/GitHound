"""MCP tools module for GitHound Model Context Protocol server.

This module contains all MCP tool implementations organized by functionality,
providing 25+ tools for comprehensive Git repository analysis and search.

Tool Categories:
    - analysis_tools: Repository analysis, commit history, and statistics
    - search_tools: Advanced search, fuzzy matching, and pattern detection
    - blame_tools: File blame analysis and authorship tracking
    - management_tools: Repository management, validation, and configuration
    - export_tools: Data export in multiple formats (JSON, YAML, CSV, Excel)
    - web_tools: Web server integration and interface management

Each tool module contains FastMCP-compatible tool implementations that expose
GitHound's functionality through the standardized MCP protocol, enabling
AI assistants and applications to interact with Git repositories programmatically.

All tools are automatically registered with the MCP server when this module
is imported, providing a complete toolkit for Git repository analysis.
"""

# Import all tools to register them with the MCP server
from . import analysis_tools, blame_tools, export_tools, management_tools, search_tools, web_tools

__all__ = [
    "analysis_tools",
    "blame_tools",
    "export_tools",
    "management_tools",
    "search_tools",
    "web_tools",
]
