"""Search-related MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context
from git import GitCommandError

from ...git_handler import get_repository
from ...models import SearchQuery
from ...search_engine import (
    AuthorSearcher,
    CommitHashSearcher,
    ContentSearcher,
    DateRangeSearcher,
    FilePathSearcher,
    FileTypeSearcher,
    FuzzySearcher,
    MessageSearcher,
    SearchOrchestrator,
)
from ..models import AdvancedSearchInput, ContentSearchInput, FuzzySearchInput

# Initialize search orchestrator with all searchers
_search_orchestrator: SearchOrchestrator | None = None


def get_search_orchestrator() -> SearchOrchestrator:
    """Get or create the search orchestrator with all searchers registered."""
    global _search_orchestrator
    if _search_orchestrator is None:
        _search_orchestrator = SearchOrchestrator()

        # Register all available searchers
        _search_orchestrator.register_searcher(CommitHashSearcher())
        _search_orchestrator.register_searcher(AuthorSearcher())
        _search_orchestrator.register_searcher(MessageSearcher())
        _search_orchestrator.register_searcher(DateRangeSearcher())
        _search_orchestrator.register_searcher(FilePathSearcher())
        _search_orchestrator.register_searcher(FileTypeSearcher())
        _search_orchestrator.register_searcher(ContentSearcher())
        _search_orchestrator.register_searcher(FuzzySearcher())

    return _search_orchestrator


async def advanced_search(input_data: AdvancedSearchInput, ctx: Context) -> dict[str, Any]:
    """
    Perform advanced multi-modal search across the repository.

    Supports searching by content, commit hash, author, message, date range,
    file patterns, and more. Uses GitHound's powerful search engine with
    fuzzy matching and intelligent result ranking.
    """
    try:
        await ctx.info(f"Starting advanced search in repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery from input
        query = SearchQuery(
            content_pattern=input_data.content_pattern,
            commit_hash=input_data.commit_hash,
            author_pattern=input_data.author_pattern,
            message_pattern=input_data.message_pattern,
            date_from=datetime.fromisoformat(input_data.date_from.replace(
                "Z", "+00:00")) if input_data.date_from else None,
            date_to=datetime.fromisoformat(input_data.date_to.replace(
                "Z", "+00:00")) if input_data.date_to else None,
            file_path_pattern=input_data.file_path_pattern,
            file_extensions=input_data.file_extensions,
            case_sensitive=input_data.case_sensitive,
            fuzzy_search=input_data.fuzzy_search,
            fuzzy_threshold=input_data.fuzzy_threshold,
            include_globs=input_data.include_globs,
            exclude_globs=input_data.exclude_globs,
            max_file_size=input_data.max_file_size,
            min_commit_size=input_data.min_commit_size,
            max_commit_size=input_data.max_commit_size,
        )

        # Perform search
        results: list[Any] = []
        result_count = 0

        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=input_data.max_results,
        ):
            results.append({
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "line_number": result.line_number,
                "matching_line": result.matching_line,
                "search_type": result.search_type.value,
                "relevance_score": result.relevance_score,
                "match_context": result.match_context,
                "commit_info": {
                    "author_name": result.commit_info.author_name if result.commit_info else None,
                    "author_email": result.commit_info.author_email if result.commit_info else None,
                    "date": result.commit_info.date.isoformat() if result.commit_info and result.commit_info.date else None,
                    "message": result.commit_info.message if result.commit_info else None,
                } if result.commit_info else None,
            })
            result_count += 1

            if result_count % 10 == 0:
                await ctx.info(f"Found {result_count} results so far...")

        await ctx.info(f"Advanced search complete: {len(results)} results found")

        return {
            "status": "success",
            "results": results,
            "total_count": len(results),
            "search_criteria": input_data.dict(),
            "search_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during advanced search: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during advanced search: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def fuzzy_search(input_data: FuzzySearchInput, ctx: Context) -> dict[str, Any]:
    """
    Perform fuzzy search with configurable similarity threshold.

    Searches across multiple dimensions (content, authors, messages, file paths)
    using fuzzy string matching to find approximate matches.
    """
    try:
        await ctx.info(f"Starting fuzzy search for '{input_data.search_term}' with threshold {input_data.threshold}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for fuzzy search
        query = SearchQuery(
            content_pattern=input_data.search_term,
            commit_hash=None,
            author_pattern=input_data.search_term,
            message_pattern=input_data.search_term,
            date_from=None,
            date_to=None,
            file_path_pattern=input_data.search_term,
            file_extensions=None,
            case_sensitive=False,
            fuzzy_search=True,
            fuzzy_threshold=input_data.threshold,
            include_globs=None,
            exclude_globs=None,
            max_file_size=None,
            min_commit_size=None,
            max_commit_size=None,
        )

        # Perform search
        results: list[Any] = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=input_data.max_results,
        ):
            results.append({
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "line_number": result.line_number,
                "matching_line": result.matching_line,
                "search_type": result.search_type.value,
                "relevance_score": result.relevance_score,
                "match_context": result.match_context,
                # For fuzzy search, relevance is similarity
                "similarity_score": result.relevance_score,
            })

        await ctx.info(f"Fuzzy search complete: {len(results)} results found")

        return {
            "status": "success",
            "results": results,
            "total_count": len(results),
            "search_term": input_data.search_term,
            "threshold": input_data.threshold,
            "search_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during fuzzy search: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during fuzzy search: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def content_search(input_data: ContentSearchInput, ctx: Context) -> dict[str, Any]:
    """
    Perform content-specific search with advanced pattern matching.

    Searches file content using regex patterns with support for file type
    filtering, case sensitivity, and whole word matching.
    """
    try:
        await ctx.info(f"Starting content search for pattern '{input_data.pattern}'")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for content search
        query = SearchQuery(
            content_pattern=input_data.pattern,
            commit_hash=None,
            author_pattern=None,
            message_pattern=None,
            date_from=None,
            date_to=None,
            file_path_pattern=None,
            file_extensions=input_data.file_extensions,
            case_sensitive=input_data.case_sensitive,
            fuzzy_search=False,
            fuzzy_threshold=0.8,
            include_globs=None,
            exclude_globs=None,
            max_file_size=None,
            min_commit_size=None,
            max_commit_size=None,
        )

        # Perform search
        results: list[Any] = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=input_data.max_results,
        ):
            results.append({
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "line_number": result.line_number,
                "matching_line": result.matching_line,
                "match_context": result.match_context,
                "relevance_score": result.relevance_score,
            })

        await ctx.info(f"Content search complete: {len(results)} results found")

        return {
            "status": "success",
            "results": results,
            "total_count": len(results),
            "pattern": input_data.pattern,
            "search_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during content search: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during content search: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}
