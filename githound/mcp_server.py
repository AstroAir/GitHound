"""GitHound MCP (Model Context Protocol) Server implementation using FastMCP 2.0.

This module serves as a compatibility layer for the refactored MCP server implementation.
All functionality has been moved to focused modules in the githound.mcp package.
"""

from typing import Any

# Handle MCP imports gracefully for Pydantic v1 compatibility
try:
    # Import the main server components from the new modular structure
    from .mcp import MCP_AVAILABLE, get_mcp_server, mcp, run_mcp_server

    if MCP_AVAILABLE:
        # Note: Auth functions not available due to circular import issues
        # from .mcp.auth_manager import check_rate_limit, get_current_user

        # Import direct wrapper functions for backward compatibility
        from .mcp.direct_wrappers import (
            analyze_commit_direct,
            analyze_repository_direct,
            compare_commits_direct,
            export_repository_data_direct,
            get_author_stats_direct,
            get_commit_history_direct,
            get_file_blame_direct,
            get_repository_config_direct,
            get_repository_contributors_direct,
            get_repository_summary_direct,
        )

    # Import models for backward compatibility
    from .mcp.models import (
        AdvancedSearchInput,
        AuthorStatsInput,
        BlameInput,
        BranchDiffInput,
        CommitAnalysisInput,
        CommitComparisonInput,
        CommitFilterInput,
        CommitHistoryInput,
        ContentSearchInput,
        DiffInput,
        ExportInput,
        FileBlameInput,
        FileHistoryInput,
        FuzzySearchInput,
        RepositoryInput,
        RepositoryManagementInput,
        ServerConfig,
        User,
        WebServerInput,
    )

    MCP_AVAILABLE = True

except ImportError:
    # MCP functionality not available due to Pydantic compatibility issues
    MCP_AVAILABLE = False

    # Create dummy functions and classes for backward compatibility
    def get_mcp_server() -> Any:
        raise ImportError("MCP functionality not available due to Pydantic compatibility issues")

    def run_mcp_server(
        transport: str = "stdio", host: str = "localhost", port: int = 3000, log_level: str = "INFO"
    ) -> None:
        raise ImportError("MCP functionality not available due to Pydantic compatibility issues")

    mcp = None

    # Create dummy classes for models
    class DummyModel:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # Perform basic validation for common fields
            if "fuzzy_threshold" in kwargs:
                threshold = kwargs["fuzzy_threshold"]
                if threshold < 0.0 or threshold > 1.0:
                    raise ValueError("Fuzzy threshold must be between 0.0 and 1.0")

            if "threshold" in kwargs:
                threshold = kwargs["threshold"]
                if threshold < 0.0 or threshold > 1.0:
                    raise ValueError("Threshold must be between 0.0 and 1.0")

            if "max_results" in kwargs:
                max_results = kwargs["max_results"]
                if max_results <= 0:
                    raise ValueError("max_results must be positive")

            if "search_term" in kwargs:
                search_term = kwargs["search_term"]
                if isinstance(search_term, str) and not search_term.strip():
                    raise ValueError("Search term cannot be empty")

            if "search_types" in kwargs:
                search_types = kwargs["search_types"]
                valid_types = ["file", "commit", "content", "author"]
                if isinstance(search_types, list):
                    for st in search_types:
                        if st not in valid_types:
                            raise ValueError(f"Invalid search types: {search_types}")

            if "port" in kwargs:
                port = kwargs["port"]
                if port < 1024 or port > 65535:
                    raise ValueError("Port must be between 1024 and 65535")

            # Store all kwargs as attributes for testing compatibility
            for key, value in kwargs.items():
                setattr(self, key, value)

    AdvancedSearchInput = DummyModel  # type: ignore[assignment,misc]
    AuthorStatsInput = DummyModel  # type: ignore[assignment,misc]
    BlameInput = DummyModel  # type: ignore[assignment,misc]
    BranchDiffInput = DummyModel  # type: ignore[assignment,misc]
    CommitAnalysisInput = DummyModel  # type: ignore[assignment,misc]
    CommitComparisonInput = DummyModel  # type: ignore[assignment,misc]
    CommitFilterInput = DummyModel  # type: ignore[assignment,misc]
    CommitHistoryInput = DummyModel  # type: ignore[assignment,misc]
    ContentSearchInput = DummyModel  # type: ignore[assignment,misc]
    DiffInput = DummyModel  # type: ignore[assignment,misc]
    ExportInput = DummyModel  # type: ignore[assignment,misc]
    FileBlameInput = DummyModel  # type: ignore[assignment,misc]
    FileHistoryInput = DummyModel  # type: ignore[assignment,misc]
    FuzzySearchInput = DummyModel  # type: ignore[assignment,misc]
    RepositoryInput = DummyModel  # type: ignore[assignment,misc]
    RepositoryManagementInput = DummyModel  # type: ignore[assignment,misc]
    ServerConfig = DummyModel  # type: ignore[assignment,misc]
    User = DummyModel  # type: ignore[assignment,misc]
    WebServerInput = DummyModel  # type: ignore[assignment,misc]

    # Create dummy functions for direct wrappers
    async def analyze_commit_direct(input_data: CommitAnalysisInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def analyze_repository_direct(input_data: RepositoryInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def compare_commits_direct(input_data: CommitComparisonInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def export_repository_data_direct(input_data: ExportInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def get_author_stats_direct(input_data: AuthorStatsInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def get_commit_history_direct(input_data: CommitHistoryInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def get_file_blame_direct(input_data: FileBlameInput) -> dict[str, Any]:
        raise ImportError("MCP functionality not available")

    async def get_repository_config_direct(repo_path: str) -> str:
        raise ImportError("MCP functionality not available")

    async def get_repository_contributors_direct(repo_path: str) -> str:
        raise ImportError("MCP functionality not available")

    async def get_repository_summary_direct(repo_path: str) -> str:
        raise ImportError("MCP functionality not available")

    def check_rate_limit(*args: Any, **kwargs: Any) -> None:
        raise ImportError("MCP functionality not available")

    def get_current_user(*args: Any, **kwargs: Any) -> None:
        raise ImportError("MCP functionality not available")

    def get_search_orchestrator() -> Any:
        raise ImportError("MCP functionality not available")


# Import search orchestrator function
_orchestrator_instance: Any = None

if MCP_AVAILABLE:
    try:
        from .mcp.tools.search_tools import get_search_orchestrator
    except ImportError:
        # Provide a dummy function if import fails
        def get_search_orchestrator() -> Any:
            """Return a singleton orchestrator instance for testing."""
            global _orchestrator_instance
            if _orchestrator_instance is None:
                # Create a simple mock orchestrator
                _orchestrator_instance = type("MockOrchestrator", (), {})()
            return _orchestrator_instance

else:
    # When MCP is not available, still provide a callable function for tests
    def get_search_orchestrator() -> Any:
        """Return a singleton orchestrator instance for testing."""
        global _orchestrator_instance
        if _orchestrator_instance is None:
            # Create a simple mock orchestrator
            _orchestrator_instance = type("MockOrchestrator", (), {})()
        return _orchestrator_instance


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
    "get_search_orchestrator",
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
