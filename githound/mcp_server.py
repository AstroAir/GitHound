"""GitHound MCP (Model Context Protocol) Server implementation using FastMCP 2.0.

This module serves as a compatibility layer for the refactored MCP server implementation.
All functionality has been moved to focused modules in the githound.mcp package.
"""

# Import the main server components from the new modular structure
from .mcp.server import get_mcp_server, mcp, run_mcp_server

# Import models for backward compatibility
from .mcp.models import (
    ServerConfig,
    User,
    RepositoryInput,
    CommitAnalysisInput,
    CommitFilterInput,
    FileHistoryInput,
    BlameInput,
    DiffInput,
    BranchDiffInput,
    ExportInput,
    CommitHistoryInput,
    FileBlameInput,
    CommitComparisonInput,
    AuthorStatsInput,
    AdvancedSearchInput,
    FuzzySearchInput,
    ContentSearchInput,
    RepositoryManagementInput,
    WebServerInput,
)

# Import auth functions for backward compatibility
from .mcp.auth import get_current_user, check_rate_limit

# Import direct wrapper functions for backward compatibility
from .mcp.direct_wrappers import (
    analyze_repository_direct,
    analyze_commit_direct,
    export_repository_data_direct,
    get_commit_history_direct,
    get_file_blame_direct,
    compare_commits_direct,
    get_author_stats_direct,
    get_repository_config_direct,
    get_repository_contributors_direct,
    get_repository_summary_direct,
)

# Import search orchestrator function
from .mcp.tools.search_tools import get_search_orchestrator

# Re-export everything for backward compatibility
__all__ = [
    # Main server components
    "get_mcp_server",
    "mcp", 
    "run_mcp_server",
    
    # Models
    "ServerConfig",
    "User",
    "RepositoryInput",
    "CommitAnalysisInput", 
    "CommitFilterInput",
    "FileHistoryInput",
    "BlameInput",
    "DiffInput",
    "BranchDiffInput",
    "ExportInput",
    "CommitHistoryInput",
    "FileBlameInput",
    "CommitComparisonInput",
    "AuthorStatsInput",
    "AdvancedSearchInput",
    "FuzzySearchInput",
    "ContentSearchInput",
    "RepositoryManagementInput",
    "WebServerInput",
    
    # Auth functions
    "get_current_user",
    "check_rate_limit",
    
    # Direct wrapper functions
    "analyze_repository_direct",
    "analyze_commit_direct",
    "export_repository_data_direct",
    "get_commit_history_direct",
    "get_file_blame_direct",
    "compare_commits_direct",
    "get_author_stats_direct",
    "get_repository_config_direct",
    "get_repository_contributors_direct",
    "get_repository_summary_direct",
]


# Main entry point for running the server
if __name__ == "__main__":
    import sys

    # Simple command line argument parsing
    transport = "stdio"
    host = "localhost"
    port = 3000
    log_level = "INFO"

    if len(sys.argv) > 1:
        if "--http" in sys.argv:
            transport = "http"
        elif "--sse" in sys.argv:
            transport = "sse"

        # Parse port
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
            elif arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
            elif arg == "--log-level" and i + 1 < len(sys.argv):
                log_level = sys.argv[i + 1]

    run_mcp_server(transport=transport, host=host, port=port, log_level=log_level)
