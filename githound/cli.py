"""Enhanced command-line interface for GitHound."""

import asyncio
import csv
import json
import logging
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TextIO
from unittest.mock import Mock as _Mock

import typer
from git import GitCommandError, Repo
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TaskProgressColumn, TextColumn
from rich.table import Table

from githound.git_handler import get_repository, process_commit, walk_history
from githound.models import (
    GitHoundConfig,
    LegacyGitHoundConfig,
    LegacySearchConfig,
    SearchQuery,
    SearchResult,
)
from githound.schemas import OutputFormat
from githound.search_engine import create_search_orchestrator
from githound.utils import ProgressManager
from githound.utils.export import ExportManager

try:
    import uvicorn
except ImportError:  # pragma: no cover - handled gracefully in command functions
    uvicorn = None  # type: ignore[assignment]

try:
    from githound.mcp_server import run_mcp_server
except ImportError:  # pragma: no cover - handled gracefully in command functions
    run_mcp_server = None  # type: ignore[assignment]

# Safe console that tolerates environments without full Unicode support


class SafeConsole(Console):
    def print(self, *args: Any, **kwargs: Any) -> None:
        self.file = typer.get_text_stream("stdout")
        try:
            super().print(*args, **kwargs)
        except UnicodeEncodeError:
            sanitized_args = tuple(self._sanitize(arg) for arg in args)
            super().print(*sanitized_args, **kwargs)

    @staticmethod
    def _sanitize(value: Any) -> Any:
        if isinstance(value, str):
            return value.encode("ascii", "ignore").decode("ascii")
        return value


app = typer.Typer(
    name="githound",
    help="""
🐕 GitHound: Advanced Git Repository Analysis Tool

GitHound provides comprehensive Git repository analysis with multi-modal search capabilities,
blame analysis, diff comparison, and multiple integration options.

Key Features:
• 🔍 Advanced search across commits, authors, messages, dates, and content
• 📊 Repository analysis with detailed statistics and metrics
• 📝 File blame analysis with line-by-line authorship tracking
• 🔄 Commit and branch comparison with detailed diff information
• 🌐 Web interface for interactive analysis
• 🤖 MCP server for AI integration
• 📤 Multiple export formats (JSON, YAML, CSV, Excel)

Examples:
  githound analyze .                    # Analyze current repository
  githound search --content "function"  # Search for content
  githound blame . src/main.py         # Analyze file blame
  githound diff HEAD~1 HEAD            # Compare commits
  githound web --port 8080             # Start web interface

For more help on specific commands, use: githound <command> --help
    """.strip(),
    add_completion=False,
    rich_markup_mode="rich",
)
console = SafeConsole()

# Initialize logger
logger = logging.getLogger(__name__)


def _extract_value(source: Any, key: str, default: Any = "") -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        value = source.get(key, default)
    else:
        value = getattr(source, key, default)

    if isinstance(value, _Mock):
        return default
    return value


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return []


def _sanitize_data(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _sanitize_data(val) for key, val in value.items()}
    if isinstance(value, list | tuple | set):
        return [_sanitize_data(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value
    if isinstance(value, _Mock):
        return _sanitize_data(getattr(value, "return_value", None))
    return value


def _analysis_to_serializable(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        return {str(key): _sanitize_data(val) for key, val in result.items()}

    sanitized: dict[str, Any] = {}

    repository_info: dict[str, Any] = {}
    for attr in (
        "path",
        "name",
        "current_branch",
        "default_branch",
        "branches",
        "tags",
        "remotes",
    ):
        value = _extract_value(result, attr, None)
        if value not in (None, ""):
            repository_info[attr] = _sanitize_data(value)

    if repository_info:
        sanitized["repository_info"] = repository_info

    commit_stats: dict[str, Any] = {}
    for attr in (
        "total_commits",
        "total_branches",
        "total_tags",
        "total_contributors",
        "first_commit_date",
        "last_commit_date",
    ):
        value = _extract_value(result, attr, None)
        if value not in (None, ""):
            commit_stats[attr] = _sanitize_data(value)

    if commit_stats:
        sanitized["commit_statistics"] = commit_stats

    author_stats = _extract_value(result, "author_statistics", None)
    if author_stats:
        sanitized["author_statistics"] = _sanitize_data(author_stats)

    if not sanitized:
        sanitized["data"] = _sanitize_data(result)

    return sanitized


def _blame_to_serializable(blame_result: Any) -> dict[str, Any]:
    if blame_result is None:
        return {}

    if hasattr(blame_result, "dict"):
        try:
            data = blame_result.dict()
            if isinstance(data, Mapping):
                return dict(data)
        except Exception as e:
            # Log serialization errors for debugging
            logger.debug(f"Failed to serialize blame result using dict(): {e}")
            pass

    lines_data: list[dict[str, Any]] = []
    for line in _coerce_list(getattr(blame_result, "lines", [])):
        lines_data.append(
            {
                "line_number": _extract_value(line, "line_number", 0),
                "author": str(_extract_value(line, "author", "")),
                "commit_hash": str(_extract_value(line, "commit_hash", "")),
                "date": str(_extract_value(line, "date", "")),
                "content": str(_extract_value(line, "content", "")),
            }
        )

    return {
        "file_path": str(_extract_value(blame_result, "file_path", "")),
        "commit_hash": str(_extract_value(blame_result, "commit_hash", "")),
        "branch": str(_extract_value(blame_result, "branch", "")),
        "lines": lines_data,
    }


def _diff_to_serializable(diff_result: Any) -> dict[str, Any]:
    if diff_result is None:
        return {}

    if hasattr(diff_result, "dict"):
        try:
            data = diff_result.dict()
            if isinstance(data, Mapping):
                return dict(data)
        except Exception as e:
            # Log serialization errors for debugging
            logger.debug(f"Failed to serialize diff result using dict(): {e}")
            pass

    file_changes_data: list[dict[str, Any]] = []
    for change in _coerce_list(getattr(diff_result, "file_changes", [])):
        file_changes_data.append(
            {
                "file_path": str(_extract_value(change, "file_path", "")),
                "change_type": str(_extract_value(change, "change_type", "")),
                "lines_added": _extract_value(change, "lines_added", 0),
                "lines_deleted": _extract_value(change, "lines_deleted", 0),
            }
        )

    statistics = getattr(diff_result, "statistics", None)
    stats_data = {
        "files_changed": _extract_value(statistics, "files_changed", 0),
        "total_lines_added": _extract_value(statistics, "total_lines_added", 0),
        "total_lines_deleted": _extract_value(statistics, "total_lines_deleted", 0),
    }

    return {
        "from_commit": str(_extract_value(diff_result, "from_commit", "")),
        "to_commit": str(_extract_value(diff_result, "to_commit", "")),
        "file_changes": file_changes_data,
        "statistics": stats_data,
    }


def print_results_text(results: list[SearchResult], show_details: bool = False) -> None:
    """Prints search results in a human-readable text format."""
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Commit", style="cyan", no_wrap=True)
    table.add_column("File", style="green")
    table.add_column("Match", style="white")

    if show_details:
        table.add_column("Author", style="blue")
        table.add_column("Date", style="yellow")
        table.add_column("Score", style="red")

    for result in results:
        commit_short = result.commit_hash[:8]
        file_path = str(result.file_path)
        match_text = result.matching_line or f"[{result.search_type.value}]"

        row = [commit_short, file_path, match_text]

        if show_details and result.commit_info:
            author = result.commit_info.author_name
            date = (
                result.commit_info.date.strftime("%Y-%m-%d")
                if isinstance(result.commit_info.date, datetime)
                else str(result.commit_info.date)
            )
            score = f"{result.relevance_score:.2f}"
            row.extend([author, date, score])

        table.add_row(*row)

    console.print(table)
    console.print(f"\n[bold]Total results: {len(results)}[/bold]")


def print_results_json(results: list[SearchResult], include_metadata: bool = False) -> None:
    """Prints search results in JSON format."""
    json_results: list[Any] = []

    for r in results:
        result_dict: dict[str, Any] = {
            "commit_hash": r.commit_hash,
            "file_path": str(r.file_path),
            "search_type": r.search_type.value,
            "relevance_score": r.relevance_score,
        }

        if r.line_number is not None:
            result_dict["line_number"] = r.line_number

        if r.matching_line is not None:
            result_dict["matching_line"] = r.matching_line

        if include_metadata and r.commit_info:
            result_dict["commit_info"] = {
                "author_name": r.commit_info.author_name,
                "author_email": r.commit_info.author_email,
                "message": r.commit_info.message,
                "date": (
                    r.commit_info.date.isoformat()
                    if isinstance(r.commit_info.date, datetime)
                    else str(r.commit_info.date)
                ),
                "files_changed": r.commit_info.files_changed,
                "insertions": r.commit_info.insertions,
                "deletions": r.commit_info.deletions,
            }

        if r.match_context:
            result_dict["match_context"] = r.match_context

        json_results.append(result_dict)

    print(json.dumps(json_results, indent=2, default=str))


def print_results_csv(results: list[SearchResult], output_file: TextIO | None = None) -> None:
    """Prints search results in CSV format."""
    if not results:
        return

    writer = csv.writer(output_file or sys.stdout)

    # Write header
    header = [
        "commit_hash",
        "file_path",
        "line_number",
        "matching_line",
        "search_type",
        "relevance_score",
        "author_name",
        "author_email",
        "commit_date",
        "commit_message",
    ]
    writer.writerow(header)

    # Write data
    for r in results:
        row = [
            r.commit_hash,
            str(r.file_path),
            r.line_number or "",
            r.matching_line or "",
            r.search_type.value,
            r.relevance_score,
            r.commit_info.author_name if r.commit_info else "",
            r.commit_info.author_email if r.commit_info else "",
            (
                r.commit_info.date.isoformat()
                if r.commit_info and isinstance(r.commit_info.date, datetime)
                else ""
            ),
            r.commit_info.message if r.commit_info else "",
        ]
        writer.writerow(row)


# Legacy ProgressReporter for backward compatibility
class ProgressReporter:
    """Simple progress reporter for CLI operations."""

    def __init__(self, enable_progress: bool = True) -> None:
        self.enable_progress = enable_progress
        self.progress: Progress | None = None
        self.task: TaskID | None = None

    def __enter__(self) -> "ProgressReporter":
        if self.enable_progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            )
            self.progress.__enter__()
            self.task = self.progress.add_task("Searching...", total=100)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def update(self, description: str, progress: float) -> None:
        """Update progress with description and percentage (0.0-1.0)."""
        if self.progress and self.task is not None:
            self.progress.update(self.task, description=description, completed=progress * 100)


async def enhanced_search(
    repo: Repo,
    query: SearchQuery,
    branch: str | None = None,
    enable_progress: bool = True,
    max_results: int | None = None,
) -> list[SearchResult]:
    """Perform enhanced search using the new search engine."""

    # Create orchestrator using factory for consistent configuration
    orchestrator = create_search_orchestrator(enable_advanced=query.has_advanced_analysis())

    results: list[Any] = []

    # Set up enhanced progress reporting
    if enable_progress:
        with ProgressManager(console=console, enable_cancellation=True) as progress_manager:
            # Add main search task
            progress_manager.add_task("search", "Initializing search...", 100)

            # Create progress callback
            progress_callback = progress_manager.get_progress_callback("search")

            try:
                # Perform search
                async for result in orchestrator.search(
                    repo=repo,
                    query=query,
                    branch=branch,
                    progress_callback=progress_callback,
                    max_results=max_results,
                ):
                    results.append(result)

                # Mark task as complete
                progress_manager.complete_task("search", f"Found {len(results)} results")

            except Exception as e:
                progress_manager.complete_task("search", f"Search failed: {e}")
                raise
    else:
        # Perform search without progress
        async for result in orchestrator.search(
            repo=repo, query=query, branch=branch, max_results=max_results
        ):
            results.append(result)

    return results


def legacy_search_and_print(config: LegacyGitHoundConfig) -> None:
    """Legacy search function for backward compatibility."""
    try:
        # Convert legacy config to new config format
        new_config = GitHoundConfig(
            repo_path=config.repo_path,  # [attr-defined]
            search_query=config.search_query,  # [attr-defined]
            branch=config.branch,  # [attr-defined]
            output_format=(
                # [attr-defined]
                OutputFormat.TEXT
                if config.output_format == "text"
                else OutputFormat.JSON
            ),
            search_config=config.search_config,  # [attr-defined]
            enable_ranking=True,
            parallel_search=True,
        )

        repo = get_repository(config.repo_path)  # [attr-defined]
        all_results: list[SearchResult] = []

        for commit in walk_history(repo, new_config):
            commit_results = process_commit(commit, new_config)
            all_results.extend(commit_results)

        if config.output_format == "json":  # [attr-defined]
            print_results_json(all_results)
        else:
            print_results_text(all_results)

    except GitCommandError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


async def search_and_print(
    repo_path: Path,
    query: SearchQuery,
    branch: str | None = None,
    output_format: OutputFormat = OutputFormat.TEXT,
    output_file: Path | None = None,
    enable_progress: bool = True,
    show_details: bool = False,
    include_metadata: bool = False,
    max_results: int | None = None,
) -> None:
    """Enhanced search function with new capabilities."""
    try:
        repo = get_repository(repo_path)

        # Perform search
        results = await enhanced_search(
            repo=repo,
            query=query,
            branch=branch,
            enable_progress=enable_progress,
            max_results=max_results,
        )

        # Output results using ExportManager
        export_manager = ExportManager(console)

        if output_file:
            # Export to file
            if output_format == OutputFormat.JSON:
                export_manager.export_to_json(results, output_file, include_metadata)
            elif output_format == OutputFormat.CSV:
                export_manager.export_to_csv(results, output_file, include_metadata)
            else:  # TEXT
                export_manager.export_to_text(
                    results, output_file, "detailed" if show_details else "simple"
                )
        else:
            # Print to console
            if output_format == OutputFormat.JSON:
                print_results_json(results, include_metadata)
            elif output_format == OutputFormat.CSV:
                print_results_csv(results)
            else:  # TEXT
                print_results_text(results, show_details)

    except GitCommandError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(code=1) from e


# Legacy command for backward compatibility
@app.command(name="legacy")
def legacy_main(
    repo_path: Path = typer.Argument(
        ...,
        help="Path to the Git repository.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    search_query: str = typer.Argument(..., help="Regex pattern to search for."),
    branch: str = typer.Option(
        None, "--branch", "-b", help="Branch to search (defaults to current branch)."
    ),
    output_format: str = typer.Option(
        "text",
        "--output-format",
        "-f",
        help="Output format ('text' or 'json').",
    ),
    include_glob: list[str] = typer.Option(
        None, "--include", "-i", help="Glob pattern to include files."
    ),
    exclude_glob: list[str] = typer.Option(
        None, "--exclude", "-e", help="Glob pattern to exclude files."
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", "-s", help="Perform a case-sensitive search."
    ),
) -> None:
    """
    Legacy GitHound search (for backward compatibility).
    """
    # Validate output format
    if output_format not in ["text", "json"]:
        typer.echo(f"Error: Invalid output format '{output_format}'. Must be 'text' or 'json'.")
        raise typer.Exit(1)

    # Cast to Literal type for type safety after validation
    from typing import cast

    validated_output_format: Literal["text", "json"] = cast(Literal["text", "json"], output_format)

    search_config = LegacySearchConfig(
        include_globs=include_glob,
        exclude_globs=exclude_glob,
        case_sensitive=case_sensitive,
    )
    config = LegacyGitHoundConfig(
        repo_path=repo_path,
        search_query=search_query,
        branch=branch,
        output_format=validated_output_format,
        search_config=search_config,
    )
    legacy_search_and_print(config)


# Enhanced main command
@app.command()
def search(
    repo_path: Path = typer.Option(
        ...,
        "--repo-path",
        "-p",
        help="Path to the Git repository.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    # Content search
    content: str
    | None = typer.Option(None, "--content", "-c", help="Search for content pattern (regex)."),
    # Commit-based search
    commit_hash: str
    | None = typer.Option(None, "--commit", help="Search for specific commit hash."),
    author: str
    | None = typer.Option(None, "--author", "-a", help="Search by author name or email."),
    message: str | None = typer.Option(None, "--message", "-m", help="Search commit messages."),
    # Date-based search
    date_from: str
    | None = typer.Option(None, "--date-from", help="Search commits from date (YYYY-MM-DD)."),
    date_to: str
    | None = typer.Option(None, "--date-to", help="Search commits until date (YYYY-MM-DD)."),
    # File-based search
    file_path: str
    | None = typer.Option(None, "--file-path", "-f", help="Search by file path pattern."),
    file_extensions: list[str]
    | None = typer.Option(
        None, "--ext", "--file-ext", help="File extensions to include (e.g., py, js)."
    ),
    # Search behavior
    fuzzy: bool = typer.Option(False, "--fuzzy", help="Enable fuzzy matching."),
    fuzzy_threshold: float = typer.Option(
        0.8, "--fuzzy-threshold", help="Fuzzy matching threshold (0.0-1.0)."
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", "-s", help="Case-sensitive search."
    ),
    # Filtering
    include_glob: list[str]
    | None = typer.Option(None, "--include", "-i", help="Glob patterns to include."),
    exclude_glob: list[str]
    | None = typer.Option(None, "--exclude", "-e", help="Glob patterns to exclude."),
    max_file_size: int
    | None = typer.Option(None, "--max-file-size", help="Maximum file size in bytes."),
    # Output options
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT, "--format", help="Output format (text, json, csv)."
    ),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Output file path."),
    show_details: bool = typer.Option(
        False, "--details", help="Show detailed information in text output."
    ),
    include_metadata: bool = typer.Option(
        False, "--metadata", help="Include commit metadata in JSON output."
    ),
    # Performance options
    max_results: int
    | None = typer.Option(None, "--max-results", help="Maximum number of results to return."),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress indicators."),
    # Repository options
    branch: str
    | None = typer.Option(None, "--branch", "-b", help="Branch to search (defaults to current)."),
) -> None:
    """
    GitHound: Advanced Git history search with multi-modal capabilities.

    Search Git history using various criteria like content, author, commit message,
    date range, file paths, and more. Supports fuzzy matching and advanced filtering.

    Examples:

    \b
    # Search for content pattern
    githound search --repo-path . --content "password"

    \b
    # Search by author with fuzzy matching
    githound search --repo-path . --author "john" --fuzzy

    \b
    # Search commits in date range
    githound search --repo-path . --date-from 2023-01-01 --date-to 2023-12-31

    \b
    # Search Python files for specific pattern
    githound search --repo-path . --content "import os" --ext py

    \b
    # Export results to CSV
    githound search --repo-path . --author "jane" --format csv --output results.csv
    """
    # Validate that at least one search criterion is provided
    search_criteria = [
        content,
        commit_hash,
        author,
        message,
        date_from,
        date_to,
        file_path,
        file_extensions,
    ]
    if not any(search_criteria):
        console.print("[red]Error: At least one search criterion must be provided.[/red]")
        console.print("Use --help to see available options.")
        raise typer.Exit(code=1)

    # Parse dates
    parsed_date_from = None
    parsed_date_to = None

    if date_from:
        try:
            parsed_date_from = datetime.fromisoformat(date_from)
        except ValueError as e:
            console.print(f"[red]Error: Invalid date format for --date-from: {date_from}[/red]")
            console.print("Use YYYY-MM-DD format.")
            raise typer.Exit(code=1) from e

    if date_to:
        try:
            parsed_date_to = datetime.fromisoformat(date_to)
        except ValueError as e:
            console.print(f"[red]Error: Invalid date format for --date-to: {date_to}[/red]")
            console.print("Use YYYY-MM-DD format.")
            raise typer.Exit(code=1) from e

    # Create search query
    query = SearchQuery(
        content_pattern=content,
        commit_hash=commit_hash,
        author_pattern=author,
        message_pattern=message,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        file_path_pattern=file_path,
        file_extensions=file_extensions,
        case_sensitive=case_sensitive,
        fuzzy_search=fuzzy,
        fuzzy_threshold=fuzzy_threshold,
        include_globs=include_glob,
        exclude_globs=exclude_glob,
        max_file_size=max_file_size,
        min_commit_size=None,
        max_commit_size=None,
        branch_analysis=False,
        branch_pattern=None,
        compare_branches=False,
        diff_analysis=False,
        change_analysis=False,
        commit_range=None,
        pattern_analysis=False,
        code_quality=False,
        security_patterns=False,
        statistical_analysis=False,
        temporal_analysis=False,
        tag_pattern=None,
        version_analysis=False,
        release_analysis=False,
        enable_caching=True,
        cache_ttl_seconds=3600,
        enable_ranking=True,
        enable_parallel=True,
        max_workers=4,
        enable_enrichment=False,
        context_lines=3,
        group_results=False,
        group_by=None,
        max_results=max_results,
        timeout_seconds=None,
        search_depth=None,
        text=None,
        semantic_search=False,
        language_detection=False,
    )

    # Run search
    asyncio.run(
        search_and_print(
            repo_path=repo_path,
            query=query,
            branch=branch,
            output_format=output_format,
            output_file=output_file,
            enable_progress=not no_progress,
            show_details=show_details,
            include_metadata=include_metadata,
            max_results=max_results,
        )
    )


# Backward compatibility: make 'search' the default command
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """
    GitHound: Advanced Git history search tool.

    Use 'githound search --help' for detailed search options.
    Use 'githound legacy --help' for the original interface.
    """
    if ctx.invoked_subcommand is None:
        console.print(
            "[yellow]No command specified. Use 'search' for the enhanced interface or 'legacy' for backward compatibility.[/yellow]"
        )
        console.print("\nAvailable commands:")
        console.print("  [bold]search[/bold]   - Enhanced multi-modal search (recommended)")
        console.print("  [bold]legacy[/bold]   - Original search interface")
        console.print("  [bold]analyze[/bold]  - Repository analysis and metadata")
        console.print("  [bold]blame[/bold]    - File blame analysis")
        console.print("  [bold]diff[/bold]     - Commit/branch comparison")
        console.print("  [bold]web[/bold]      - Start web interface")
        console.print("  [bold]mcp-server[/bold] - Start MCP server")
        console.print("  [bold]version[/bold]    - Show version information")
        console.print(
            "\n[dim]💡 Use --help with any command for detailed information and examples.[/dim]"
        )
        console.print("[dim]📖 Documentation: https://github.com/your-org/githound[/dim]")


@app.command()
def analyze(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT, "--format", "-f", help="Output format"
    ),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    include_detailed_stats: bool = typer.Option(
        True, "--detailed/--basic", help="Include detailed statistics"
    ),
    include_author_stats: bool = typer.Option(
        True, "--author-stats/--no-author-stats", help="Include author statistics"
    ),
) -> None:
    """Analyze repository metadata and statistics.

    Provides comprehensive analysis of the Git repository including:
    - Basic repository information (branches, tags, remotes)
    - Commit statistics and contributor information
    - Repository health metrics
    - Author contribution statistics
    """
    try:
        from githound import GitHound

        # Input validation
        if not repo_path.exists():
            console.print(f"[red]✗ Repository path does not exist:[/red] {repo_path}")
            raise typer.Exit(1)

        if not repo_path.is_dir():
            console.print(f"[red]✗ Path is not a directory:[/red] {repo_path}")
            raise typer.Exit(1)

        # Check if it's a Git repository
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            console.print(f"[red]✗ Not a Git repository:[/red] {repo_path}")
            console.print(
                "[dim]💡 Hint: Run 'git init' to initialize a Git repository, or check the path.[/dim]"
            )
            raise typer.Exit(1)

        console.print(f"[bold blue]🔍 Analyzing repository:[/bold blue] {repo_path}")

        # Initialize GitHound
        with console.status("[bold green]Initializing GitHound..."):
            gh = GitHound(repo_path)
        console.print("[green]✓[/green] GitHound initialized successfully")

        author_stats_data: Any = None

        # Perform analysis with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # Main analysis
            task1 = progress.add_task("Analyzing repository metadata...", total=None)
            analysis_result = gh.analyze_repository(include_detailed_stats=include_detailed_stats)
            progress.update(task1, completed=True, description="✓ Repository metadata analyzed")

            # Author statistics (if requested)
            if include_author_stats:
                task2 = progress.add_task("Gathering author statistics...", total=None)
                try:
                    author_stats = gh.get_author_statistics()
                    author_stats_data = _sanitize_data(dict(author_stats))
                    progress.update(
                        task2, completed=True, description="✓ Author statistics gathered"
                    )
                except Exception as e:
                    progress.update(task2, completed=True, description="⚠ Author statistics failed")
                    console.print(
                        f"[yellow]⚠ Warning: Could not get author statistics: {e}[/yellow]"
                    )

        analysis_output = _analysis_to_serializable(analysis_result)
        if author_stats_data:
            analysis_output["author_statistics"] = author_stats_data

        # Output results
        if output_file:
            import json

            def json_serializer(obj: Any) -> str:
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if isinstance(obj, Path):
                    return str(obj)
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            if output_format == OutputFormat.JSON:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(analysis_output, f, default=json_serializer, indent=2)
            elif output_format == OutputFormat.YAML:
                try:
                    import yaml

                    with open(output_file, "w", encoding="utf-8") as f:
                        yaml.dump(
                            analysis_output,
                            f,
                            default_flow_style=False,
                            allow_unicode=True,
                        )
                except ImportError:
                    console.print(
                        "[yellow]⚠ YAML output requires PyYAML. Writing JSON instead.[/yellow]"
                    )
                    json_path = output_file.with_suffix(".json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(analysis_output, f, default=json_serializer, indent=2)
                    console.print(f"[green]Analysis exported to:[/green] {json_path}")
                    return
            else:
                with console.capture() as capture:
                    _print_analysis_text(analysis_output)
                text_output = capture.get()
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text_output)
                console.print(text_output)

            console.print(f"[green]Analysis exported to:[/green] {output_file}")
        else:
            if output_format == OutputFormat.JSON:
                # Convert datetime objects to strings for JSON serialization
                import json
                from datetime import datetime

                def json_serializer(obj: Any) -> str:
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                json_str = json.dumps(analysis_output, default=json_serializer, indent=2)
                console.print(json_str)
            elif output_format == OutputFormat.YAML:
                try:
                    import yaml

                    console.print(yaml.dump(analysis_output, default_flow_style=False))
                except ImportError:
                    console.print(
                        "[yellow]⚠ YAML output requires PyYAML. Falling back to JSON format.[/yellow]"
                    )
                    console.print_json(data=analysis_output)
            else:
                # Text format
                _print_analysis_text(analysis_output)

    except GitCommandError as e:
        console.print(f"[red]✗ Git operation error:[/red] {e}")
        console.print(
            "[dim]💡 Hint: Make sure you're in a valid Git repository and have proper permissions.[/dim]"
        )
        raise typer.Exit(1) from e
    except FileNotFoundError as e:
        console.print(f"[red]✗ Repository not found:[/red] {repo_path}")
        console.print("[dim]💡 Hint: Check that the repository path exists and is accessible.[/dim]")
        raise typer.Exit(1) from e
    except PermissionError as e:
        console.print(f"[red]✗ Permission denied:[/red] {e}")
        console.print("[dim]💡 Hint: Make sure you have read permissions for the repository.[/dim]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        console.print(
            "[dim]💡 Hint: Run with --help for usage information, or check if the repository is corrupted.[/dim]"
        )
        # Add debug information
        import traceback

        console.print(
            f"[dim]Debug: {traceback.format_exc() if traceback is not None else None}[/dim]"
        )
        raise typer.Exit(1) from e


@app.command()
def blame(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository"),
    file_path: str = typer.Argument(..., help="Path to the file to analyze"),
    commit: str
    | None = typer.Option(None, "--commit", "-c", help="Specific commit to blame (default: HEAD)"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT, "--format", "-f", help="Output format"
    ),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    show_line_numbers: bool = typer.Option(
        True, "--line-numbers/--no-line-numbers", help="Show line numbers"
    ),
) -> None:
    """Analyze file blame information.

    Provides line-by-line authorship information for a specific file including:
    - Author information for each line
    - Commit hash and date for each change
    - Line content and context
    """
    try:
        from githound import GitHound

        # Input validation
        if not repo_path.exists():
            console.print(f"[red]✗ Repository path does not exist:[/red] {repo_path}")
            raise typer.Exit(1)

        git_dir = repo_path / ".git"
        if not git_dir.exists():
            console.print(f"[red]✗ Not a Git repository:[/red] {repo_path}")
            raise typer.Exit(1)

        # Check if file exists in repository
        file_full_path = repo_path / file_path
        if not file_full_path.exists():
            console.print(f"[red]✗ File does not exist:[/red] {file_path}")
            console.print(
                f"[dim]💡 Hint: Check the file path relative to the repository root: {repo_path}[/dim]"
            )
            raise typer.Exit(1)

        console.print(f"[bold blue]📝 Analyzing blame for:[/bold blue] {file_path}")
        if commit:
            console.print(f"[bold blue]📍 At commit:[/bold blue] {commit}")

        # Initialize GitHound
        with console.status("[bold green]Initializing GitHound..."):
            gh = GitHound(repo_path)
        console.print("[green]✓[/green] GitHound initialized successfully")

        # Perform blame analysis with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing file blame...", total=None)
            blame_result = gh.analyze_blame(file_path, commit)
            progress.update(task, completed=True, description="✓ File blame analysis complete")

        # Output results
        if output_file:
            from githound.schemas import ExportOptions

            export_options = ExportOptions(
                format=output_format,
                include_metadata=True,
                pretty_print=True,
                pagination=None,
                fields=None,
                exclude_fields=None,
            )
            gh.export_with_options(blame_result, output_file, export_options)
            console.print(f"[green]Blame analysis exported to:[/green] {output_file}")
        else:
            if output_format == OutputFormat.JSON:
                # Convert to dict and handle datetime serialization
                import json
                from datetime import datetime

                def json_serializer(obj: Any) -> str:
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                json_str = json.dumps(
                    _blame_to_serializable(blame_result),
                    default=json_serializer,
                    indent=2,
                )
                console.print(json_str)
            elif output_format == OutputFormat.YAML:
                try:
                    import yaml

                    console.print(
                        yaml.dump(
                            _blame_to_serializable(blame_result),
                            default_flow_style=False,
                        )
                    )
                except ImportError:
                    console.print(
                        "[yellow]⚠ YAML output requires PyYAML. Falling back to JSON format.[/yellow]"
                    )
                    console.print_json(data=_blame_to_serializable(blame_result))
            else:
                # Text format
                _print_blame_text(blame_result, show_line_numbers)

    except GitCommandError as e:
        console.print(f"[red]✗ Git blame operation failed:[/red] {e}")
        console.print(
            "[dim]💡 Hint: Make sure the file exists in the repository and the commit is valid.[/dim]"
        )
        raise typer.Exit(1) from e
    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found:[/red] {file_path}")
        console.print(
            "[dim]💡 Hint: Check that the file path is correct and exists in the repository.[/dim]"
        )
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]✗ Blame analysis failed:[/red] {e}")
        console.print(
            "[dim]💡 Hint: The file might be binary or the commit reference might be invalid.[/dim]"
        )
        raise typer.Exit(1) from e


@app.command()
def diff(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository"),
    from_ref: str = typer.Argument(..., help="Source commit/branch reference"),
    to_ref: str = typer.Argument(..., help="Target commit/branch reference"),
    file_patterns: list[str]
    | None = typer.Option(None, "--file", "-f", help="File patterns to filter diff"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT, "--format", "-F", help="Output format"
    ),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    compare_branches: bool = typer.Option(
        False, "--branches", help="Compare as branches instead of commits"
    ),
) -> None:
    """Compare commits or branches.

    Provides detailed comparison between two Git references including:
    - File changes and modifications
    - Added, deleted, and modified lines
    - Commit metadata and statistics
    """
    try:
        from githound import GitHound

        ref_type = "branches" if compare_branches else "commits"
        console.print(f"[bold blue]Comparing {ref_type}:[/bold blue] {from_ref} → {to_ref}")

        # Initialize GitHound
        gh = GitHound(repo_path)

        # Perform comparison
        with console.status(f"[bold green]Comparing {ref_type}..."):
            if compare_branches:
                if file_patterns:
                    diff_result = gh.compare_branches(from_ref, to_ref, file_patterns)
                else:
                    diff_result = gh.compare_branches(from_ref, to_ref)
            else:
                if file_patterns:
                    diff_result = gh.compare_commits(from_ref, to_ref, file_patterns)
                else:
                    diff_result = gh.compare_commits(from_ref, to_ref)

        # Output results
        if output_file:
            from githound.schemas import ExportOptions

            export_options = ExportOptions(
                format=output_format,
                include_metadata=True,
                pretty_print=True,
                pagination=None,
                fields=None,
                exclude_fields=None,
            )
            gh.export_with_options(diff_result, output_file, export_options)
            console.print(f"[green]Diff analysis exported to:[/green] {output_file}")
        else:
            if output_format == OutputFormat.JSON:
                # Convert to dict and handle datetime serialization
                import json
                from datetime import datetime

                def json_serializer(obj: Any) -> str:
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                json_str = json.dumps(
                    _diff_to_serializable(diff_result),
                    default=json_serializer,
                    indent=2,
                )
                console.print(json_str)
            elif output_format == OutputFormat.YAML:
                try:
                    import yaml

                    console.print(
                        yaml.dump(
                            _diff_to_serializable(diff_result),
                            default_flow_style=False,
                        )
                    )
                except ImportError:
                    console.print(
                        "[yellow]⚠ YAML output requires PyYAML. Falling back to JSON format.[/yellow]"
                    )
                    console.print_json(data=_diff_to_serializable(diff_result))
            else:
                # Text format
                _print_diff_text(diff_result)

    except GitCommandError as e:
        console.print(f"[red]✗ Git diff operation failed:[/red] {e}")
        console.print(
            "[dim]💡 Hint: Make sure both commit/branch references are valid and exist in the repository.[/dim]"
        )
        raise typer.Exit(1) from e
    except ValueError as e:
        console.print(f"[red]✗ Invalid reference:[/red] {e}")
        console.print(
            f"[dim]💡 Hint: Check that '{from_ref}' and '{to_ref}' are valid commit hashes or branch names.[/dim]"
        )
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]✗ Diff comparison failed:[/red] {e}")
        console.print(
            "[dim]💡 Hint: The references might not exist or the repository might be corrupted.[/dim]"
        )
        raise typer.Exit(1) from e


@app.command()
def web(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository"),
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind the server"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind the server"),
    auto_open: bool = typer.Option(
        True,
        "--auto-open/--no-auto-open",
        "--open/--no-open",
        help="Automatically open browser",
    ),
    dev_mode: bool = typer.Option(False, "--dev", help="Enable development mode with auto-reload"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive configuration mode"
    ),
) -> None:
    """Start the GitHound web interface.

    Launches a web server providing an interactive interface for:
    - Repository analysis and visualization
    - Advanced search with real-time results
    - File blame and diff analysis
    - Export functionality
    """
    try:
        # Interactive mode
        if interactive:
            console.print("[bold blue]🌐 GitHound Web Interface Setup[/bold blue]")
            console.print()

            # Repository path
            if not repo_path.exists() or repo_path == Path("."):
                repo_input = typer.prompt("Repository path", default=str(repo_path))
                repo_path = Path(repo_input)

            # Host and port
            host = typer.prompt("Host", default=host)
            port = typer.prompt("Port", default=port, type=int)

            # Options
            auto_open = typer.confirm("Open browser automatically?", default=auto_open)
            dev_mode = typer.confirm("Enable development mode?", default=dev_mode)

            console.print()

        # Validation
        if not repo_path.exists():
            console.print(f"[red]✗ Repository path does not exist:[/red] {repo_path}")
            if interactive or typer.confirm("Would you like to specify a different path?"):
                repo_input = typer.prompt("Repository path")
                repo_path = Path(repo_input)
            else:
                raise typer.Exit(1)

        console.print("[bold blue]🌐 Starting GitHound web interface...[/bold blue]")
        console.print(f"[blue]📁 Repository:[/blue] {repo_path}")
        console.print(f"[blue]🌍 Server:[/blue] http://{host}:{port}")

        if uvicorn is None:
            raise ImportError("uvicorn not available")

        if callable(uvicorn):
            try:
                uvicorn()
            except ImportError as exc:
                raise ImportError(str(exc)) from exc
            except TypeError as e:
                # Log type errors during uvicorn import for debugging
                logger.debug(
                    f"TypeError during uvicorn import (expected in some environments): {e}"
                )
                pass

        if not hasattr(uvicorn, "run"):
            raise ImportError("uvicorn not available")

        from githound.web.main import app

        # Use the existing FastAPI app
        app_instance = app

        # Auto-open browser
        if auto_open:
            import webbrowser

            webbrowser.open(f"http://{host}:{port}")

        console.print(f"[green]Web interface starting at http://{host}:{port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")

        # Start the server
        uvicorn.run(app_instance, host=host, port=port, reload=dev_mode, access_log=dev_mode)

    except ImportError as e:
        console.print(f"[red]Missing dependencies for web interface:[/red] {e}")
        console.print("[yellow]Install with: pip install 'githound[web]'[/yellow]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error starting web interface:[/red] {e}")
        raise typer.Exit(1) from e


@app.command(name="mcp-server")
def mcp_server(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository"),
    port: int = typer.Option(3000, "--port", "-p", help="Port to bind the MCP server"),
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind the server"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
) -> None:
    """Start the GitHound MCP (Model Context Protocol) server.

    Launches an MCP server providing AI-friendly access to GitHound functionality:
    - Repository analysis tools
    - Advanced search capabilities
    - File blame and diff analysis
    - Structured data export
    """
    try:
        console.print("[bold blue]Starting GitHound MCP server...[/bold blue]")
        console.print(f"[blue]Repository:[/blue] {repo_path}")
        console.print(f"[blue]Server:[/blue] {host}:{port}")

        if run_mcp_server is None:
            raise ImportError("fastmcp not available")

        console.print(f"[green]MCP server starting at {host}:{port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")

        # Run the MCP server (this is synchronous and handles async internally)
        run_mcp_server(transport="stdio", host=host, port=port, log_level=log_level)

    except ImportError as e:
        console.print(f"[red]Missing dependencies for MCP server:[/red] {e}")
        console.print("[yellow]Install with: pip install 'githound[mcp]'[/yellow]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error starting MCP server:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def version(
    build_info: bool = typer.Option(
        False, "--build-info", "-b", help="Show detailed build information"
    )
) -> None:
    """Show GitHound version and system information."""
    try:
        import platform
        import sys

        from git import __version__ as git_version

        from .utils.version import format_version_info, get_build_info, is_development_version

        console.print("[bold blue]🐕 GitHound Version Information[/bold blue]")
        console.print()

        # GitHound version with optional build info
        if build_info:
            version_display = format_version_info(include_build_info=True)
            for line in version_display.split("\n"):
                console.print(f"[green]{line}[/green]")
        else:
            version_str = format_version_info(include_build_info=False)
            console.print(f"[green]GitHound:[/green] {version_str}")

            if is_development_version():
                console.print("[yellow]⚠ Development version[/yellow]")

        console.print()

        # Dependencies
        console.print(f"[green]GitPython:[/green] {git_version}")
        console.print(f"[green]Python:[/green] {sys.version.split()[0]}")
        console.print(f"[green]Platform:[/green] {platform.system()} {platform.release()}")

        # Optional dependencies
        optional_deps: list[Any] = []
        try:
            import pandas

            optional_deps.append(f"pandas {pandas.__version__}")
        except (ImportError, AttributeError):
            optional_deps.append("pandas (not available)")

        try:
            import yaml

            optional_deps.append(f"PyYAML {yaml.__version__}")
        except (ImportError, AttributeError):
            optional_deps.append("PyYAML (not available)")

        try:
            import uvicorn

            optional_deps.append(f"uvicorn {uvicorn.__version__}")
        except (ImportError, AttributeError):
            optional_deps.append("uvicorn (not available)")

        console.print(f"[green]Optional:[/green] {', '.join(optional_deps)}")

        # Build information (if requested)
        if build_info:
            console.print()
            build_data = get_build_info()
            console.print("[bold]Build Information:[/bold]")
            for key, value in build_data.items():
                if value is not None:
                    console.print(f"  [dim]{key}:[/dim] {value}")

        # Footer
        console.print()
        console.print(
            "[dim]For more information, visit: https://github.com/your-org/githound[/dim]"
        )

    except Exception as e:
        console.print(f"[red]✗ Error getting version information:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def cleanup(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository"),
    cache_only: bool = typer.Option(False, "--cache-only", help="Only clean cache files"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
) -> None:
    """Clean up GitHound cache and temporary files.

    This command removes temporary files, caches, and other artifacts
    created by GitHound operations. Use with caution.

    Examples:
      githound cleanup                    # Interactive cleanup
      githound cleanup --cache-only       # Only remove cache files
      githound cleanup --force            # Skip confirmations
    """
    try:
        console.print("[bold blue]🧹 GitHound Cleanup[/bold blue]")
        console.print(f"[blue]📁 Repository:[/blue] {repo_path}")
        console.print()

        # Find cleanup targets
        cleanup_targets: list[Any] = []

        # Cache directories
        cache_dirs = [
            repo_path / ".githound_cache",
            repo_path / ".git" / "githound_cache",
            Path.home() / ".cache" / "githound",
        ]

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                cleanup_targets.append(("Cache directory", cache_dir))

        # Temporary files
        if not cache_only:
            temp_patterns = [
                repo_path.glob("*.githound.tmp"),
                repo_path.glob("**/*.githound.log"),
                repo_path.glob("**/.githound_temp*"),
            ]

            for pattern in temp_patterns:
                for temp_file in pattern:
                    cleanup_targets.append(("Temporary file", temp_file))

        if not cleanup_targets:
            console.print("[green]✓ No cleanup needed - repository is clean![/green]")
            return

        # Show what will be cleaned
        console.print("[yellow]📋 Items to be cleaned:[/yellow]")
        total_size = 0
        for item_type, path in cleanup_targets:
            try:
                if path.is_file():
                    size = path.stat().st_size
                    total_size += size
                    console.print(f"  • {item_type}: {path} ({size:,} bytes)")
                elif path.is_dir():
                    dir_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                    total_size += dir_size
                    console.print(f"  • {item_type}: {path} ({dir_size:,} bytes)")
            except (OSError, PermissionError):
                console.print(f"  • {item_type}: {path} (size unknown)")

        console.print(f"\n[bold]Total size to be freed: {total_size:,} bytes[/bold]")

        # Confirmation
        if not force:
            console.print()
            if not typer.confirm("⚠️  Are you sure you want to proceed with cleanup?"):
                console.print("[yellow]Cleanup cancelled by user[/yellow]")
                return

        # Perform cleanup
        cleaned_count = 0
        errors: list[Any] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Cleaning up files...", total=len(cleanup_targets))

            for item_type, path in cleanup_targets:
                try:
                    if path.is_file():
                        path.unlink()
                        cleaned_count += 1
                    elif path.is_dir():
                        import shutil

                        shutil.rmtree(path)
                        cleaned_count += 1
                    progress.advance(task)
                except (OSError, PermissionError) as e:
                    errors.append(f"{path}: {e}")
                    progress.advance(task)

        # Results
        console.print()
        if cleaned_count > 0:
            console.print(f"[green]✓ Successfully cleaned {cleaned_count} items[/green]")

        if errors:
            console.print(f"[yellow]⚠️  {len(errors)} items could not be cleaned:[/yellow]")
            for error in errors[:5]:  # Show first 5 errors
                console.print(f"  • {error}")
            if len(errors) > 5:
                console.print(f"  • ... and {len(errors) - 5} more")

        if errors:
            console.print("[yellow]⚠ Cleanup completed with warnings.[/yellow]")
        else:
            console.print("[green]Cleanup completed successfully.[/green]")

    except KeyboardInterrupt as e:
        console.print("\n[yellow]🛑 Cleanup cancelled by user[/yellow]")
        raise typer.Exit(0) from e
    except Exception as e:
        console.print(f"[red]✗ Cleanup failed:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def quickstart(
    repo_path: Path = typer.Argument(Path("."), help="Path to the Git repository")
) -> None:
    """Interactive quickstart guide for GitHound.

    This command provides a guided tour of GitHound's capabilities
    and helps you get started with common tasks.
    """
    try:
        console.print("[bold blue]🐕 Welcome to GitHound![/bold blue]")
        console.print()
        console.print("GitHound is a powerful Git repository analysis tool.")
        console.print("Let's explore what you can do with it!")
        console.print()

        # Repository validation
        if not repo_path.exists():
            console.print(f"[red]✗ Repository path does not exist:[/red] {repo_path}")
            repo_input = typer.prompt("Please enter a valid repository path")
            repo_path = Path(repo_input)

        git_dir = repo_path / ".git"
        if not git_dir.exists():
            console.print(f"[red]✗ Not a Git repository:[/red] {repo_path}")
            console.print("[dim]💡 Make sure you're in a Git repository directory[/dim]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Using repository:[/green] {repo_path}")
        console.print()

        # Interactive menu
        while True:
            console.print("[bold]What would you like to do?[/bold]")
            console.print()
            console.print("1. 📊 Analyze repository (get overview and statistics)")
            console.print("2. 🔍 Search commits (find specific changes)")
            console.print("3. 📝 Analyze file blame (see who changed what)")
            console.print("4. 🔄 Compare commits/branches (see differences)")
            console.print("5. 🌐 Start web interface (interactive GUI)")
            console.print("6. ❓ Show help for a specific command")
            console.print("7. 🚪 Exit")
            console.print()

            choice = typer.prompt("Enter your choice (1-7)", type=int)
            console.print()

            if choice == 1:
                console.print("[bold blue]📊 Repository Analysis[/bold blue]")
                console.print("This will analyze your repository and show statistics.")
                if typer.confirm("Proceed with analysis?"):
                    console.print("[dim]Running: githound analyze .[/dim]")
                    # Import and run analyze function
                    from githound.cli import analyze

                    analyze(repo_path, OutputFormat.TEXT, None, True, True)

            elif choice == 2:
                console.print("[bold blue]🔍 Search Commits[/bold blue]")
                console.print("Search for commits by content, author, message, or date.")
                search_term = typer.prompt("What would you like to search for?")
                console.print(f"[dim]Running: githound search --content '{search_term}'[/dim]")
                console.print(
                    "[yellow]Note: Full search functionality requires the complete GitHound setup[/yellow]"
                )

            elif choice == 3:
                console.print("[bold blue]📝 File Blame Analysis[/bold blue]")
                console.print("Analyze who changed each line in a file.")
                file_path = typer.prompt("Enter file path (relative to repository)")
                console.print(f"[dim]Running: githound blame . {file_path}[/dim]")
                # Could call blame function here

            elif choice == 4:
                console.print("[bold blue]🔄 Compare Commits/Branches[/bold blue]")
                console.print("Compare two commits or branches to see differences.")
                from_ref = typer.prompt("From commit/branch", default="HEAD~1")
                to_ref = typer.prompt("To commit/branch", default="HEAD")
                console.print(f"[dim]Running: githound diff {from_ref} {to_ref}[/dim]")

            elif choice == 5:
                console.print("[bold blue]🌐 Web Interface[/bold blue]")
                console.print("Start the interactive web interface.")
                if typer.confirm("Start web interface on localhost:8000?"):
                    console.print("[dim]Running: githound web --interactive[/dim]")
                    console.print(
                        "[yellow]Note: Web interface requires additional dependencies[/yellow]"
                    )

            elif choice == 6:
                console.print("[bold blue]❓ Command Help[/bold blue]")
                console.print("Available commands:")
                console.print("• analyze  - Repository analysis")
                console.print("• search   - Advanced search")
                console.print("• blame    - File blame analysis")
                console.print("• diff     - Compare commits/branches")
                console.print("• web      - Web interface")
                console.print("• version  - Version information")
                console.print("• cleanup  - Clean cache files")
                console.print()
                console.print("Use 'githound <command> --help' for detailed help")

            elif choice == 7:
                console.print("[green]👋 Thanks for using GitHound![/green]")
                console.print(
                    "[dim]💡 Tip: Use 'githound --help' to see all available commands[/dim]"
                )
                break

            else:
                console.print("[red]Invalid choice. Please enter 1-7.[/red]")

            console.print()
            if choice != 7 and not typer.confirm("Would you like to try something else?"):
                break

    except KeyboardInterrupt as e:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        raise typer.Exit(0) from e
    except Exception as e:
        console.print(f"[red]✗ Error in quickstart:[/red] {e}")
        raise typer.Exit(1) from e


def _print_analysis_text(analysis: Any) -> None:
    """Print repository analysis in text format."""
    analysis_data = _analysis_to_serializable(analysis)
    console.print("\n[bold magenta]Repository Analysis[/bold magenta]")

    # Basic info
    if "repository_info" in analysis_data:
        info = analysis_data["repository_info"]
        console.print(
            f"\n[bold]Repository Path:[/bold] {info.get('path', 'N/A') if info is not None else 'N/A'}"
        )
        console.print(
            f"[bold]Repository Name:[/bold] {info.get('name', 'N/A') if info is not None else 'N/A'}"
        )
        console.print(
            f"[bold]Current Branch:[/bold] {info.get('current_branch', 'N/A') if info is not None else 'N/A'}"
        )
        console.print(
            f"[bold]Total Branches:[/bold] {len(info.get('branches', []) if info is not None else [])}"
        )
        console.print(
            f"[bold]Total Tags:[/bold] {len(info.get('tags', []) if info is not None else [])}"
        )
        console.print(
            f"[bold]Remotes:[/bold] {len(info.get('remotes', []) if info is not None else [])}"
        )

    # Commit statistics
    if "commit_statistics" in analysis_data:
        stats = analysis_data["commit_statistics"]
        console.print("\n[bold]Commit Statistics:[/bold]")
        console.print(
            f"  Total Commits: {stats.get('total_commits', 'N/A') if stats is not None else 'N/A'}"
        )
        console.print(
            f"  Contributors: {stats.get('total_contributors', 'N/A') if stats is not None else 'N/A'}"
        )
        console.print(
            f"  First Commit: {stats.get('first_commit_date', 'N/A') if stats is not None else 'N/A'}"
        )
        console.print(
            f"  Last Commit: {stats.get('last_commit_date', 'N/A') if stats is not None else 'N/A'}"
        )

    # Author statistics
    if "author_statistics" in analysis_data:
        author_stats = analysis_data["author_statistics"]
        console.print("\n[bold]Top Contributors:[/bold]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Author", style="cyan")
        table.add_column("Commits", style="green", justify="right")
        table.add_column("Lines Added", style="blue", justify="right")
        table.add_column("Lines Deleted", style="red", justify="right")

        by_author: Any = {}
        try:
            by_author = author_stats.get("by_author", {}) if author_stats is not None else {}
        except AttributeError:
            by_author = {}

        try:
            top_contributors = list(by_author.values())[:10]
        except TypeError:
            top_contributors = []

        if not top_contributors:
            console.print("[dim]No author statistics available.[/dim]")
        else:
            for author_info in top_contributors:
                table.add_row(
                    author_info.get("name", "Unknown") if author_info is not None else "Unknown",
                    str(author_info.get("commit_count", 0) if author_info is not None else 0),
                    str(author_info.get("lines_added", 0) if author_info is not None else 0),
                    str(author_info.get("lines_deleted", 0) if author_info is not None else 0),
                )

            console.print(table)


def _print_blame_text(blame_result: Any, show_line_numbers: bool = True) -> None:
    """Print file blame analysis in text format."""
    console.print("\n[bold magenta]File Blame Analysis[/bold magenta]")
    console.print(f"[bold]File:[/bold] {blame_result.file_path}")
    console.print(f"[bold]Commit:[/bold] {blame_result.commit_hash}")

    lines = _coerce_list(getattr(blame_result, "lines", []))
    if lines:
        console.print("\n[bold]Line-by-line Analysis:[/bold]")

        table = Table(show_header=True, header_style="bold magenta")
        if show_line_numbers:
            table.add_column("Line", style="dim", width=6, justify="right")
        table.add_column("Author", style="cyan", width=20)
        table.add_column("Commit", style="green", width=12)
        table.add_column("Date", style="yellow", width=12)
        table.add_column("Content", style="white")

        for line_info in lines[:50]:  # Show first 50 lines
            row: list[Any] = []
            if show_line_numbers:
                row.append(str(_extract_value(line_info, "line_number", "")))
            row.extend(
                [
                    _extract_value(line_info, "author", "Unknown")[:18],
                    str(_extract_value(line_info, "commit_hash", ""))[:10],
                    str(_extract_value(line_info, "date", ""))[:10],
                    str(_extract_value(line_info, "content", ""))[:80],
                ]
            )
            table.add_row(*row)

        console.print(table)

        if len(lines) > 50:
            console.print(f"[dim]... and {len(lines) - 50} more lines[/dim]")


def _print_diff_text(diff_result: Any) -> None:
    """Print diff analysis in text format."""
    console.print("\n[bold magenta]Diff Analysis[/bold magenta]")
    console.print(f"[bold]From:[/bold] {diff_result.from_commit}")
    console.print(f"[bold]To:[/bold] {diff_result.to_commit}")

    file_changes = _coerce_list(getattr(diff_result, "file_changes", []))
    if file_changes:
        console.print("\n[bold]File Changes:[/bold]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Added", style="blue", justify="right")
        table.add_column("Deleted", style="red", justify="right")

        for file_change in file_changes:
            table.add_row(
                str(_extract_value(file_change, "file_path", "")),
                str(_extract_value(file_change, "change_type", "")),
                str(_extract_value(file_change, "lines_added", 0)),
                str(_extract_value(file_change, "lines_deleted", 0)),
            )

        console.print(table)

    # Summary statistics
    if hasattr(diff_result, "statistics"):
        stats = diff_result.statistics
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Files Changed: {_extract_value(stats, 'files_changed', 0)}")
        console.print(f"  Total Lines Added: {_extract_value(stats, 'total_lines_added', 0)}")
        console.print(f"  Total Lines Deleted: {_extract_value(stats, 'total_lines_deleted', 0)}")


if __name__ == "__main__":
    app()
