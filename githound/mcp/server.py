"""Main GitHound MCP server setup and orchestration."""

import logging

from fastmcp import FastMCP, Context

from .config import configure_logging
from .tools import search_tools, analysis_tools, blame_tools, export_tools, management_tools, web_tools
from .direct_wrappers import MockContext
from .resources import (
    get_repository_config,
    get_repository_branches,
    get_repository_contributors,
    get_repository_summary,
    get_file_history_resource,
    get_commit_details_resource,
    get_file_blame_resource,
)
from .prompts import investigate_bug, prepare_code_review, analyze_performance_regression


def get_mcp_server() -> FastMCP:
    """Create and configure the GitHound MCP server with FastMCP 2.0."""
    return FastMCP("GitHound MCP Server")


def ensure_context(ctx):
    """Ensure we have a valid context object."""
    return ctx if ctx is not None else MockContext()


# Global MCP server instance
mcp: FastMCP = get_mcp_server()


# Register all MCP tools
@mcp.tool
async def advanced_search(
    repo_path: str,
    branch: str = None,
    content_pattern: str = None,
    commit_hash: str = None,
    author_pattern: str = None,
    message_pattern: str = None,
    date_from: str = None,
    date_to: str = None,
    file_path_pattern: str = None,
    file_extensions: list[str] = None,
    case_sensitive: bool = False,
    fuzzy_search: bool = False,
    fuzzy_threshold: float = 0.8,
    max_results: int = 100,
    include_globs: list[str] = None,
    exclude_globs: list[str] = None,
    max_file_size: int = None,
    min_commit_size: int = None,
    max_commit_size: int = None,
    ctx = None
):
    """Advanced multi-modal search across the repository."""
    from .models import AdvancedSearchInput

    input_data = AdvancedSearchInput(
        repo_path=repo_path,
        branch=branch,
        content_pattern=content_pattern,
        commit_hash=commit_hash,
        author_pattern=author_pattern,
        message_pattern=message_pattern,
        date_from=date_from,
        date_to=date_to,
        file_path_pattern=file_path_pattern,
        file_extensions=file_extensions,
        case_sensitive=case_sensitive,
        fuzzy_search=fuzzy_search,
        fuzzy_threshold=fuzzy_threshold,
        max_results=max_results,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        max_file_size=max_file_size,
        min_commit_size=min_commit_size,
        max_commit_size=max_commit_size
    )
    return await search_tools.advanced_search(input_data, ensure_context(ctx))


@mcp.tool
async def fuzzy_search(
    repo_path: str,
    search_term: str,
    threshold: float = 0.8,
    search_types: list[str] = None,
    branch: str = None,
    max_results: int = 50,
    ctx = None
):
    """Fuzzy search with configurable similarity threshold."""
    from .models import FuzzySearchInput

    input_data = FuzzySearchInput(
        repo_path=repo_path,
        search_term=search_term,
        threshold=threshold,
        search_types=search_types,
        branch=branch,
        max_results=max_results
    )
    return await search_tools.fuzzy_search(input_data, ensure_context(ctx))


@mcp.tool
async def content_search(
    repo_path: str,
    pattern: str,
    file_extensions: list[str] = None,
    case_sensitive: bool = False,
    max_results: int = 100,
    ctx = None
):
    """Content-specific search with advanced pattern matching."""
    from .models import ContentSearchInput

    input_data = ContentSearchInput(
        repo_path=repo_path,
        pattern=pattern,
        file_extensions=file_extensions,
        case_sensitive=case_sensitive,
        max_results=max_results
    )
    return await search_tools.content_search(input_data, ensure_context(ctx))


@mcp.tool
async def analyze_repository(repo_path: str, ctx = None):
    """Analyze a Git repository and return comprehensive metadata."""
    from .models import RepositoryInput

    input_data = RepositoryInput(repo_path=repo_path)
    return await analysis_tools.analyze_repository(input_data, ensure_context(ctx))


@mcp.tool
async def analyze_commit(repo_path: str, commit_hash: str = None, ctx = None):
    """Analyze a specific commit and return detailed metadata."""
    from .models import CommitAnalysisInput

    input_data = CommitAnalysisInput(repo_path=repo_path, commit_hash=commit_hash)
    return await analysis_tools.analyze_commit(input_data, ensure_context(ctx))


@mcp.tool
async def get_filtered_commits(
    repo_path: str,
    branch: str = None,
    author: str = None,
    since: str = None,
    until: str = None,
    message_pattern: str = None,
    file_patterns: list[str] = None,
    max_count: int = 100,
    ctx = None
):
    """Retrieve commits with advanced filtering options."""
    from .models import CommitFilterInput

    input_data = CommitFilterInput(
        repo_path=repo_path,
        branch=branch,
        author=author,
        since=since,
        until=until,
        message_pattern=message_pattern,
        file_patterns=file_patterns,
        max_count=max_count
    )
    return await analysis_tools.get_filtered_commits(input_data, ensure_context(ctx))


@mcp.tool
async def get_file_history_mcp(
    repo_path: str,
    file_path: str,
    branch: str = None,
    max_count: int = 50,
    ctx = None
):
    """Get the complete history of changes for a specific file."""
    from .models import FileHistoryInput

    input_data = FileHistoryInput(
        repo_path=repo_path,
        file_path=file_path,
        branch=branch,
        max_count=max_count
    )
    return await analysis_tools.get_file_history_mcp(input_data, ensure_context(ctx))


@mcp.tool
async def get_commit_history(
    repo_path: str,
    branch: str = None,
    max_count: int = 100,
    since: str = None,
    until: str = None,
    ctx = None
):
    """Get commit history with optional filtering and pagination."""
    from .models import CommitHistoryInput

    input_data = CommitHistoryInput(
        repo_path=repo_path,
        branch=branch,
        max_count=max_count,
        since=since,
        until=until
    )
    return await analysis_tools.get_commit_history(input_data, ensure_context(ctx))


@mcp.tool
async def analyze_file_blame(
    repo_path: str,
    file_path: str,
    commit: str = None,
    ctx = None
):
    """Analyze line-by-line authorship for a file using git blame."""
    from .models import BlameInput

    input_data = BlameInput(repo_path=repo_path, file_path=file_path, commit=commit)
    return await blame_tools.analyze_file_blame(input_data, ensure_context(ctx))


@mcp.tool
async def compare_commits_diff(
    repo_path: str,
    from_commit: str,
    to_commit: str,
    file_patterns: list[str] = None,
    ctx = None
):
    """Compare two commits and return detailed diff analysis."""
    from .models import DiffInput

    input_data = DiffInput(
        repo_path=repo_path,
        from_commit=from_commit,
        to_commit=to_commit,
        file_patterns=file_patterns
    )
    return await blame_tools.compare_commits_diff(input_data, ensure_context(ctx))


@mcp.tool
async def compare_branches_diff(
    repo_path: str,
    from_branch: str,
    to_branch: str,
    file_patterns: list[str] = None,
    ctx = None
):
    """Compare two branches and return detailed diff analysis."""
    from .models import BranchDiffInput

    input_data = BranchDiffInput(
        repo_path=repo_path,
        from_branch=from_branch,
        to_branch=to_branch,
        file_patterns=file_patterns
    )
    return await blame_tools.compare_branches_diff(input_data, ensure_context(ctx))


@mcp.tool
async def get_author_stats(
    repo_path: str,
    branch: str = None,
    since: str = None,
    until: str = None,
    ctx = None
):
    """Get comprehensive author statistics for the repository."""
    from .models import AuthorStatsInput

    input_data = AuthorStatsInput(
        repo_path=repo_path,
        branch=branch,
        since=since,
        until=until
    )
    return await blame_tools.get_author_stats(input_data, ensure_context(ctx))


@mcp.tool
async def get_file_blame(
    repo_path: str,
    file_path: str,
    commit: str = None,
    ctx = None
):
    """Get file blame information showing line-by-line authorship."""
    from .models import FileBlameInput

    input_data = FileBlameInput(repo_path=repo_path, file_path=file_path, commit=commit)
    return await blame_tools.get_file_blame(input_data, ensure_context(ctx))


@mcp.tool
async def compare_commits_mcp(
    repo_path: str,
    from_commit: str,
    to_commit: str,
    ctx = None
):
    """Compare two commits and return detailed diff information."""
    from .models import CommitComparisonInput

    input_data = CommitComparisonInput(
        repo_path=repo_path,
        from_commit=from_commit,
        to_commit=to_commit
    )
    return await blame_tools.compare_commits_mcp(input_data, ensure_context(ctx))


@mcp.tool
async def export_repository_data(
    repo_path: str,
    output_path: str,
    format: str = "json",
    include_metadata: bool = True,
    pagination: dict = None,
    fields: list[str] = None,
    exclude_fields: list[str] = None,
    ctx = None
):
    """Export repository analysis data in various formats."""
    from .models import ExportInput

    input_data = ExportInput(
        repo_path=repo_path,
        output_path=output_path,
        format=format,
        include_metadata=include_metadata,
        pagination=pagination,
        fields=fields,
        exclude_fields=exclude_fields
    )
    return await export_tools.export_repository_data(input_data, ensure_context(ctx))


@mcp.tool
async def list_branches(repo_path: str, ctx = None):
    """List all branches in the repository with detailed information."""
    from .models import RepositoryInput

    input_data = RepositoryInput(repo_path=repo_path)
    return await management_tools.list_branches(input_data, ensure_context(ctx))


@mcp.tool
async def list_tags(repo_path: str, ctx = None):
    """List all tags in the repository with metadata."""
    from .models import RepositoryInput

    input_data = RepositoryInput(repo_path=repo_path)
    return await management_tools.list_tags(input_data, ensure_context(ctx))


@mcp.tool
async def list_remotes(repo_path: str, ctx = None):
    """List all remote repositories with their URLs."""
    from .models import RepositoryInput

    input_data = RepositoryInput(repo_path=repo_path)
    return await management_tools.list_remotes(input_data, ensure_context(ctx))


@mcp.tool
async def validate_repository(repo_path: str, ctx = None):
    """Validate repository integrity and check for issues."""
    from .models import RepositoryInput

    input_data = RepositoryInput(repo_path=repo_path)
    return await management_tools.validate_repository(input_data, ensure_context(ctx))


@mcp.tool
async def start_web_server(
    repo_path: str,
    host: str = "localhost",
    port: int = 8000,
    ctx = None
):
    """Start the GitHound web interface server."""
    from .models import WebServerInput

    input_data = WebServerInput(repo_path=repo_path, host=host, port=port)
    return await web_tools.start_web_server(input_data, ensure_context(ctx))


@mcp.tool
async def generate_repository_report(
    repo_path: str,
    output_format: str = "html",
    include_charts: bool = True,
    ctx = None
):
    """Generate a comprehensive repository analysis report."""
    from .models import RepositoryManagementInput

    input_data = RepositoryManagementInput(
        repo_path=repo_path,
        output_format=output_format,
        include_charts=include_charts
    )
    return await web_tools.generate_repository_report(input_data, ensure_context(ctx))


# Register MCP resources
@mcp.resource("githound://repository/{repo_path}/config")
async def get_repository_config_resource(repo_path: str, ctx: Context) -> str:
    """Get repository configuration information."""
    return await get_repository_config(repo_path, ctx)


@mcp.resource("githound://repository/{repo_path}/branches")
async def get_repository_branches_resource(repo_path: str, ctx: Context) -> str:
    """Get detailed information about all branches in the repository."""
    return await get_repository_branches(repo_path, ctx)


@mcp.resource("githound://repository/{repo_path}/contributors")
async def get_repository_contributors_resource(repo_path: str, ctx: Context) -> str:
    """Get information about all contributors to the repository."""
    return await get_repository_contributors(repo_path, ctx)


@mcp.resource("githound://repository/{repo_path}/summary")
async def get_repository_summary_resource(repo_path: str, ctx: Context) -> str:
    """Get a comprehensive summary of the repository."""
    return await get_repository_summary(repo_path, ctx)


@mcp.resource("githound://repository/{repo_path}/files/{file_path}/history")
async def get_file_history_resource_endpoint(repo_path: str, file_path: str, ctx: Context) -> str:
    """Get the complete history of changes for a specific file as a resource."""
    return await get_file_history_resource(repo_path, file_path, ctx)


@mcp.resource("githound://repository/{repo_path}/commits/{commit_hash}/details")
async def get_commit_details_resource_endpoint(repo_path: str, commit_hash: str, ctx: Context) -> str:
    """Get detailed information about a specific commit as a resource."""
    return await get_commit_details_resource(repo_path, commit_hash, ctx)


@mcp.resource("githound://repository/{repo_path}/blame/{file_path}")
async def get_file_blame_resource_endpoint(repo_path: str, file_path: str, ctx: Context) -> str:
    """Get file blame information as a resource."""
    return await get_file_blame_resource(repo_path, file_path, ctx)


# Register MCP prompts
@mcp.prompt
def investigate_bug_prompt(
    bug_description: str,
    suspected_files: str = "",
    time_frame: str = "last 30 days"
) -> str:
    """Generate a prompt for investigating a bug using GitHound's analysis capabilities."""
    return investigate_bug(bug_description, suspected_files, time_frame)


@mcp.prompt
def prepare_code_review_prompt(
    branch_name: str,
    base_branch: str = "main",
    focus_areas: str = ""
) -> str:
    """Generate a prompt for preparing a comprehensive code review."""
    return prepare_code_review(branch_name, base_branch, focus_areas)


@mcp.prompt
def analyze_performance_regression_prompt(
    performance_issue: str,
    suspected_timeframe: str = "last 2 weeks",
    affected_components: str = ""
) -> str:
    """Generate a prompt for analyzing performance regressions."""
    return analyze_performance_regression(performance_issue, suspected_timeframe, affected_components)


def run_mcp_server(
    transport: str = "stdio",
    host: str = "localhost",
    port: int = 3000,
    log_level: str = "INFO"
) -> None:
    """
    Run the GitHound MCP server with FastMCP 2.0.

    Args:
        transport: Transport type ("stdio", "http", "sse")
        host: Host to bind for HTTP/SSE transports
        port: Port to bind for HTTP/SSE transports
        log_level: Logging level
    """
    # Configure logging
    configure_logging(log_level)

    logger = logging.getLogger("githound.mcp_server")
    logger.info(f"Starting GitHound MCP Server 2.0 with {transport} transport")

    # Log server capabilities
    logger.info("Server capabilities:")
    logger.info("  🔍 Advanced multi-modal search")
    logger.info("  📊 Repository analysis and statistics")
    logger.info("  📝 File blame and history analysis")
    logger.info("  🔄 Commit and branch comparison")
    logger.info("  📤 Data export in multiple formats")
    logger.info("  📚 Dynamic resources and prompts")

    try:
        # Run the server with specified transport
        if transport == "stdio":
            mcp.run()
        elif transport == "http":
            mcp.run(transport="http", host=host, port=port)
        elif transport == "sse":
            mcp.run(transport="sse", host=host, port=port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
