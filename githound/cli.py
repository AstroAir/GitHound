"""Enhanced command-line interface for GitHound."""

import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TextIO, Dict, Any, Literal

import typer
from git import GitCommandError, Repo
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TaskID
from rich.table import Table

from githound.git_handler import get_repository, walk_history, process_commit
from githound.models import (
    GitHoundConfig, SearchResult, SearchConfig, SearchQuery,
    OutputFormat, SearchType, LegacyGitHoundConfig, LegacySearchConfig
)
from githound.search_engine import (
    SearchOrchestrator, CommitHashSearcher, AuthorSearcher, MessageSearcher,
    DateRangeSearcher, FilePathSearcher, FileTypeSearcher, ContentSearcher, FuzzySearcher
)
from githound.utils import ProgressManager, ExportManager


app = typer.Typer(
    name="githound",
    help="GitHound: Advanced Git history search tool with multi-modal search capabilities.",
    add_completion=False
)
console = Console()


def print_results_text(results: List[SearchResult], show_details: bool = False) -> None:
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
            date = result.commit_info.date.strftime("%Y-%m-%d") if isinstance(result.commit_info.date, datetime) else str(result.commit_info.date)
            score = f"{result.relevance_score:.2f}"
            row.extend([author, date, score])

        table.add_row(*row)

    console.print(table)
    console.print(f"\n[bold]Total results: {len(results)}[/bold]")


def print_results_json(results: List[SearchResult], include_metadata: bool = False) -> None:
    """Prints search results in JSON format."""
    json_results = []

    for r in results:
        result_dict: Dict[str, Any] = {
            "commit_hash": r.commit_hash,
            "file_path": str(r.file_path),
            "search_type": r.search_type.value,
            "relevance_score": r.relevance_score
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
                "date": r.commit_info.date.isoformat() if isinstance(r.commit_info.date, datetime) else str(r.commit_info.date),
                "files_changed": r.commit_info.files_changed,
                "insertions": r.commit_info.insertions,
                "deletions": r.commit_info.deletions
            }

        if r.match_context:
            result_dict["match_context"] = r.match_context

        json_results.append(result_dict)

    print(json.dumps(json_results, indent=2, default=str))


def print_results_csv(results: List[SearchResult], output_file: Optional[TextIO] = None) -> None:
    """Prints search results in CSV format."""
    if not results:
        return

    writer = csv.writer(output_file or sys.stdout)

    # Write header
    header = [
        "commit_hash", "file_path", "line_number", "matching_line",
        "search_type", "relevance_score", "author_name", "author_email",
        "commit_date", "commit_message"
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
            r.commit_info.date.isoformat() if r.commit_info and isinstance(r.commit_info.date, datetime) else "",
            r.commit_info.message if r.commit_info else ""
        ]
        writer.writerow(row)


# Legacy ProgressReporter for backward compatibility
class ProgressReporter:
    """Simple progress reporter for CLI operations."""

    def __init__(self, enable_progress: bool = True):
        self.enable_progress = enable_progress
        self.progress: Optional[Progress] = None
        self.task: Optional[TaskID] = None

    def __enter__(self) -> "ProgressReporter":
        if self.enable_progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
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
            self.progress.update(
                self.task,
                description=description,
                completed=progress * 100
            )


async def enhanced_search(
    repo: Repo,
    query: SearchQuery,
    branch: Optional[str] = None,
    enable_progress: bool = True,
    max_results: Optional[int] = None
) -> List[SearchResult]:
    """Perform enhanced search using the new search engine."""

    # Create and configure search orchestrator
    orchestrator = SearchOrchestrator()

    # Register all searchers
    orchestrator.register_searcher(CommitHashSearcher())
    orchestrator.register_searcher(AuthorSearcher())
    orchestrator.register_searcher(MessageSearcher())
    orchestrator.register_searcher(DateRangeSearcher())
    orchestrator.register_searcher(FilePathSearcher())
    orchestrator.register_searcher(FileTypeSearcher())
    orchestrator.register_searcher(ContentSearcher())
    orchestrator.register_searcher(FuzzySearcher())

    results = []

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
                    max_results=max_results
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
            repo=repo,
            query=query,
            branch=branch,
            max_results=max_results
        ):
            results.append(result)

    return results


def legacy_search_and_print(config: LegacyGitHoundConfig) -> None:
    """Legacy search function for backward compatibility."""
    try:
        # Convert legacy config to new config format
        new_config = GitHoundConfig(
            repo_path=config.repo_path,
            search_query=config.search_query,
            branch=config.branch,
            output_format=OutputFormat.TEXT if config.output_format == "text" else OutputFormat.JSON,
            search_config=config.search_config
        )

        repo = get_repository(config.repo_path)
        all_results: List[SearchResult] = []

        for commit in walk_history(repo, new_config):
            commit_results = process_commit(commit, new_config)
            all_results.extend(commit_results)

        if config.output_format == "json":
            print_results_json(all_results)
        else:
            print_results_text(all_results)

    except GitCommandError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


async def search_and_print(
    repo_path: Path,
    query: SearchQuery,
    branch: Optional[str] = None,
    output_format: OutputFormat = OutputFormat.TEXT,
    output_file: Optional[Path] = None,
    enable_progress: bool = True,
    show_details: bool = False,
    include_metadata: bool = False,
    max_results: Optional[int] = None
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
            max_results=max_results
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
                export_manager.export_to_text(results, output_file, "detailed" if show_details else "simple")
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
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(code=1)


# Legacy command for backward compatibility
@app.command(name="legacy")
def legacy_main(
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
    search_query: str = typer.Option(
        ..., "--search-query", "-q", help="Regex pattern to search for."
    ),
    branch: str = typer.Option(
        None, "--branch", "-b", help="Branch to search (defaults to current branch)."
    ),
    output_format: str = typer.Option(
        "text",
        "--output-format",
        "-f",
        help="Output format ('text' or 'json').",
    ),
    include_glob: List[str] = typer.Option(
        None, "--include", "-i", help="Glob pattern to include files."
    ),
    exclude_glob: List[str] = typer.Option(
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

    # Cast to Literal type for type safety
    validated_output_format: Literal["text", "json"] = output_format  # type: ignore[assignment]

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
    content: Optional[str] = typer.Option(
        None, "--content", "-c", help="Search for content pattern (regex)."
    ),
    # Commit-based search
    commit_hash: Optional[str] = typer.Option(
        None, "--commit", help="Search for specific commit hash."
    ),
    author: Optional[str] = typer.Option(
        None, "--author", "-a", help="Search by author name or email."
    ),
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Search commit messages."
    ),
    # Date-based search
    date_from: Optional[str] = typer.Option(
        None, "--date-from", help="Search commits from date (YYYY-MM-DD)."
    ),
    date_to: Optional[str] = typer.Option(
        None, "--date-to", help="Search commits until date (YYYY-MM-DD)."
    ),
    # File-based search
    file_path: Optional[str] = typer.Option(
        None, "--file-path", "-f", help="Search by file path pattern."
    ),
    file_extensions: Optional[List[str]] = typer.Option(
        None, "--ext", help="File extensions to include (e.g., py, js)."
    ),
    # Search behavior
    fuzzy: bool = typer.Option(
        False, "--fuzzy", help="Enable fuzzy matching."
    ),
    fuzzy_threshold: float = typer.Option(
        0.8, "--fuzzy-threshold", help="Fuzzy matching threshold (0.0-1.0)."
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", "-s", help="Case-sensitive search."
    ),
    # Filtering
    include_glob: Optional[List[str]] = typer.Option(
        None, "--include", "-i", help="Glob patterns to include."
    ),
    exclude_glob: Optional[List[str]] = typer.Option(
        None, "--exclude", "-e", help="Glob patterns to exclude."
    ),
    max_file_size: Optional[int] = typer.Option(
        None, "--max-file-size", help="Maximum file size in bytes."
    ),
    # Output options
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT, "--format", help="Output format (text, json, csv)."
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path."
    ),
    show_details: bool = typer.Option(
        False, "--details", help="Show detailed information in text output."
    ),
    include_metadata: bool = typer.Option(
        False, "--metadata", help="Include commit metadata in JSON output."
    ),
    # Performance options
    max_results: Optional[int] = typer.Option(
        None, "--max-results", help="Maximum number of results to return."
    ),
    no_progress: bool = typer.Option(
        False, "--no-progress", help="Disable progress indicators."
    ),
    # Repository options
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Branch to search (defaults to current)."
    ),
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
    search_criteria = [content, commit_hash, author, message, date_from, date_to, file_path, file_extensions]
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
        except ValueError:
            console.print(f"[red]Error: Invalid date format for --date-from: {date_from}[/red]")
            console.print("Use YYYY-MM-DD format.")
            raise typer.Exit(code=1)

    if date_to:
        try:
            parsed_date_to = datetime.fromisoformat(date_to)
        except ValueError:
            console.print(f"[red]Error: Invalid date format for --date-to: {date_to}[/red]")
            console.print("Use YYYY-MM-DD format.")
            raise typer.Exit(code=1)

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
        max_commit_size=None
    )

    # Run search
    asyncio.run(search_and_print(
        repo_path=repo_path,
        query=query,
        branch=branch,
        output_format=output_format,
        output_file=output_file,
        enable_progress=not no_progress,
        show_details=show_details,
        include_metadata=include_metadata,
        max_results=max_results
    ))


# Backward compatibility: make 'search' the default command
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """
    GitHound: Advanced Git history search tool.

    Use 'githound search --help' for detailed search options.
    Use 'githound legacy --help' for the original interface.
    """
    if ctx.invoked_subcommand is None:
        console.print("[yellow]No command specified. Use 'search' for the enhanced interface or 'legacy' for backward compatibility.[/yellow]")
        console.print("\nAvailable commands:")
        console.print("  [bold]search[/bold]  - Enhanced multi-modal search (recommended)")
        console.print("  [bold]legacy[/bold]  - Original search interface")
        console.print("\nUse --help with any command for more information.")


if __name__ == "__main__":
    app()