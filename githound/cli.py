"""Command-line interface for GitHound."""

import json
from pathlib import Path
from typing import List, Literal

import typer
from git import GitCommandError

from githound.git_handler import get_repository, walk_history, process_commit
from githound.models import GitHoundConfig, SearchResult, SearchConfig


app = typer.Typer()


def print_results_text(results: List[SearchResult]):
    """Prints search results in a human-readable text format."""
    for result in results:
        print(
            f"Commit: {result.commit_hash}\n"
            f"File:   {result.file_path}\n"
            f"Line:   {result.matching_line}\n"
        )


def print_results_json(results: List[SearchResult]):
    """Prints search results in JSON format."""
    json_results = [
        {
            "commit_hash": r.commit_hash,
            "file_path": str(r.file_path),
            "line_number": r.line_number,
            "matching_line": r.matching_line,
        }
        for r in results
    ]
    print(json.dumps(json_results, indent=2))


def search_and_print(config: GitHoundConfig):
    """The main function to run the search and print results."""
    try:
        repo = get_repository(config.repo_path)
        all_results: List[SearchResult] = []

        for commit in walk_history(repo, config):
            commit_results = process_commit(commit, config)
            all_results.extend(commit_results)

        if config.output_format == "json":
            print_results_json(all_results)
        else:
            print_results_text(all_results)

    except GitCommandError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def main(
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
    output_format: Literal["text", "json"] = typer.Option(
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
):
    """
    GitHound: A high-performance tool to search Git history for a regex pattern.
    """
    search_config = SearchConfig(
        include_globs=include_glob,
        exclude_globs=exclude_glob,
        case_sensitive=case_sensitive,
    )
    config = GitHoundConfig(
        repo_path=repo_path,
        search_query=search_query,
        branch=branch,
        output_format=output_format,
        search_config=search_config,
    )
    search_and_print(config)


if __name__ == "__main__":
    app()