"""Search-related MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context
from git import GitCommandError

from ...git_handler import get_repository
from ...models import SearchQuery
from ...search_engine import (
    SearchEngineFactory,
    SearchOrchestrator,
    create_search_orchestrator,
    get_global_registry,
)
from ..models import (
    AdvancedSearchInput,
    BranchAnalysisInput,
    ContentSearchInput,
    DiffAnalysisInput,
    FuzzySearchInput,
    PatternDetectionInput,
    SearchAnalyticsQueryInput,
    SearchEngineConfigInput,
    SearcherRegistryQueryInput,
    StatisticalAnalysisInput,
    TagAnalysisInput,
)

# Initialize search orchestrator with all searchers
_search_orchestrator: SearchOrchestrator | None = None


def get_search_orchestrator() -> SearchOrchestrator:
    """Get or create the search orchestrator with all searchers registered."""
    global _search_orchestrator
    if _search_orchestrator is None:
        # Use factory for consistent configuration
        _search_orchestrator = create_search_orchestrator(enable_advanced=True)

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
            date_from=(
                datetime.fromisoformat(input_data.date_from.replace("Z", "+00:00"))
                if input_data.date_from
                else None
            ),
            date_to=(
                datetime.fromisoformat(input_data.date_to.replace("Z", "+00:00"))
                if input_data.date_to
                else None
            ),
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

        # Perform search with progress reporting
        results: list[Any] = []
        result_count = 0
        max_results = input_data.max_results

        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=max_results,
        ):
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path),
                    "line_number": result.line_number,
                    "matching_line": result.matching_line,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                    "commit_info": (
                        {
                            "author_name": (
                                result.commit_info.author_name if result.commit_info else None
                            ),
                            "author_email": (
                                result.commit_info.author_email if result.commit_info else None
                            ),
                            "date": (
                                result.commit_info.date.isoformat()
                                if result.commit_info and result.commit_info.date
                                else None
                            ),
                            "message": result.commit_info.message if result.commit_info else None,
                        }
                        if result.commit_info
                        else None
                    ),
                }
            )
            result_count += 1

            # Report progress with FastMCP 2.x context
            if result_count % 10 == 0:
                await ctx.report_progress(
                    progress=result_count,
                    total=max_results,
                    message=f"Found {result_count} results",
                )
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
        await ctx.info(
            f"Starting fuzzy search for '{input_data.search_term}' with threshold {input_data.threshold}"
        )

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
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path),
                    "line_number": result.line_number,
                    "matching_line": result.matching_line,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                    # For fuzzy search, relevance is similarity
                    "similarity_score": result.relevance_score,
                }
            )

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
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path),
                    "line_number": result.line_number,
                    "matching_line": result.matching_line,
                    "match_context": result.match_context,
                    "relevance_score": result.relevance_score,
                }
            )

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


# Advanced Search Engine Tools


async def create_search_engine(input_data: SearchEngineConfigInput, ctx: Context) -> dict[str, Any]:
    """
    Create a customized search engine with specific configuration.

    Allows fine-tuned control over search engine behavior, performance settings,
    and feature enablement for optimal repository analysis.
    """
    try:
        await ctx.info("Creating customized search engine configuration")

        from ...models import SearchEngineConfig

        # Create configuration from input
        config = SearchEngineConfig(
            enable_advanced_searchers=input_data.enable_advanced_searchers,
            enable_basic_searchers=input_data.enable_basic_searchers,
            enable_caching=input_data.enable_caching,
            enable_ranking=input_data.enable_ranking,
            enable_analytics=input_data.enable_analytics,
            enable_fuzzy_search=input_data.enable_fuzzy_search,
            enable_pattern_detection=input_data.enable_pattern_detection,
            max_workers=input_data.max_workers,
            cache_backend=input_data.cache_backend,
            cache_ttl_seconds=input_data.cache_ttl_seconds,
        )

        # Create factory with custom configuration
        factory = SearchEngineFactory(config)
        orchestrator = factory.create_orchestrator()

        # Get orchestrator statistics
        searcher_count = len(orchestrator._searchers)
        searcher_names = [s.name for s in orchestrator._searchers]

        await ctx.info(f"Search engine created with {searcher_count} searchers")

        return {
            "status": "success",
            "configuration": {
                "advanced_searchers_enabled": config.enable_advanced_searchers,
                "basic_searchers_enabled": config.enable_basic_searchers,
                "caching_enabled": config.enable_caching,
                "ranking_enabled": config.enable_ranking,
                "analytics_enabled": config.enable_analytics,
                "max_workers": config.max_workers,
                "cache_backend": config.cache_backend,
            },
            "orchestrator_info": {
                "searcher_count": searcher_count,
                "available_searchers": searcher_names,
            },
            "creation_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error creating search engine: {str(e)}")
        return {"status": "error", "error": f"Failed to create search engine: {str(e)}"}


async def query_searcher_registry(
    input_data: SearcherRegistryQueryInput, ctx: Context
) -> dict[str, Any]:
    """
    Query the searcher registry for available searchers and their capabilities.

    Provides detailed information about registered searchers, their capabilities,
    performance characteristics, and compatibility with different search types.
    """
    try:
        await ctx.info(f"Querying searcher registry for repository {input_data.repo_path}")

        registry = get_global_registry()

        # Get all searchers or filter by criteria
        if input_data.search_types or input_data.capabilities:
            from ...models import SearchQuery

            # Create a mock query to test searcher compatibility
            query = SearchQuery()
            if input_data.search_types:
                # Set query fields based on search types
                for search_type in input_data.search_types:
                    if search_type.lower() == "content":
                        query.content_pattern = "test"
                    elif search_type.lower() == "author":
                        query.author_pattern = "test"
                    # Add more mappings as needed

            matching_searchers = registry.get_searchers_for_query(query)
        else:
            matching_searchers = registry.list_searchers(enabled_only=input_data.enabled_only)

        # Get detailed information for each searcher
        searcher_details = []
        for searcher_name in matching_searchers:
            metadata = registry.get_metadata(searcher_name)
            if metadata:
                searcher_details.append(
                    {
                        "name": metadata.name,
                        "description": metadata.description,
                        "search_types": [st.value for st in metadata.search_types],
                        "capabilities": metadata.capabilities,
                        "priority": metadata.priority,
                        "enabled": metadata.enabled,
                        "requires_advanced": metadata.requires_advanced,
                        "performance_cost": metadata.performance_cost,
                        "memory_usage": metadata.memory_usage,
                        "dependencies": metadata.dependencies,
                    }
                )

        # Get registry statistics
        stats = registry.get_registry_stats()

        await ctx.info(f"Found {len(searcher_details)} matching searchers")

        return {
            "status": "success",
            "searchers": searcher_details,
            "registry_stats": stats,
            "query_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error querying searcher registry: {str(e)}")
        return {"status": "error", "error": f"Failed to query registry: {str(e)}"}


async def get_search_analytics(
    input_data: SearchAnalyticsQueryInput, ctx: Context
) -> dict[str, Any]:
    """
    Retrieve search performance analytics and usage patterns.

    Provides insights into search performance, usage patterns, optimization
    opportunities, and system health metrics.
    """
    try:
        await ctx.info("Retrieving search analytics data")

        # Note: Global analytics functionality not yet implemented
        # Returning basic placeholder data
        result = {
            "status": "success",
            "query_timestamp": datetime.now().isoformat(),
            "time_range_hours": input_data.time_range_hours,
            "message": "Analytics feature is not yet fully implemented",
        }

        if input_data.include_performance:
            result["performance_metrics"] = {
                "total_searches": 0,
                "avg_duration_ms": 0.0,
                "median_duration_ms": 0.0,
                "p95_duration_ms": 0.0,
                "avg_results_per_search": 0.0,
                "cache_hit_rate": 0.0,
                "error_rate": 0.0,
                "avg_memory_usage_mb": 0.0,
                "peak_concurrent_searches": 0,
            }

        if input_data.include_usage_patterns:
            result["usage_patterns"] = {}

        # Get optimization recommendations
        result["optimization_recommendations"] = []

        await ctx.info(
            f"Analytics placeholder returned for {input_data.time_range_hours} hour period"
        )

        return result

    except Exception as e:
        await ctx.error(f"Error retrieving analytics: {str(e)}")
        return {"status": "error", "error": f"Failed to retrieve analytics: {str(e)}"}


async def analyze_branches(input_data: BranchAnalysisInput, ctx: Context) -> dict[str, Any]:
    """
    Perform comprehensive branch analysis including metrics and comparisons.

    Analyzes branch structure, commit patterns, merge history, and provides
    insights into branch health and development patterns.
    """
    try:
        await ctx.info(f"Starting branch analysis for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for branch analysis
        from ...models import SearchQuery

        query = SearchQuery(branch_analysis=True, max_results=input_data.max_commits)

        # Perform branch analysis search
        results: list[dict[str, Any]] = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch_name,
            max_results=input_data.max_commits,
        ):
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path) if result.file_path else None,
                    "commit_info": result.commit_info.dict() if result.commit_info else None,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                }
            )

        # Get branch-specific metrics if requested
        branch_metrics = {}
        if input_data.include_metrics:
            branch_metrics = {
                "total_commits": len(results),
                "analyzed_branch": input_data.branch_name or "current",
                "analysis_timestamp": datetime.now().isoformat(),
            }

        await ctx.info(f"Branch analysis complete: analyzed {len(results)} commits")

        return {
            "status": "success",
            "results": results,
            "branch_metrics": branch_metrics,
            "total_count": len(results),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during branch analysis: {str(e)}")
        return {"status": "error", "error": f"Branch analysis failed: {str(e)}"}


async def analyze_diffs(input_data: DiffAnalysisInput, ctx: Context) -> dict[str, Any]:
    """
    Perform detailed diff analysis between references.

    Analyzes changes between commits, branches, or tags with detailed
    statistics and change patterns.
    """
    try:
        await ctx.info(f"Starting diff analysis: {input_data.from_ref} -> {input_data.to_ref}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for diff analysis
        from ...models import SearchQuery

        query = SearchQuery(
            diff_analysis=True,
            file_path_pattern=(
                "|".join(input_data.file_patterns) if input_data.file_patterns else None
            ),
        )

        # Perform diff analysis search
        results: list[dict[str, Any]] = []
        async for result in orchestrator.search(repo=repo, query=query):
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path) if result.file_path else None,
                    "line_number": result.line_number,
                    "matching_line": result.matching_line,
                    "commit_info": result.commit_info.dict() if result.commit_info else None,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                }
            )

        # Calculate diff statistics if requested
        diff_stats = {}
        if input_data.include_stats:
            diff_stats = {
                "total_changes": len(results),
                "from_ref": input_data.from_ref,
                "to_ref": input_data.to_ref,
                "files_analyzed": len(set(r["file_path"] for r in results if r["file_path"])),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        await ctx.info(f"Diff analysis complete: found {len(results)} changes")

        return {
            "status": "success",
            "results": results,
            "diff_statistics": diff_stats,
            "total_count": len(results),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during diff analysis: {str(e)}")
        return {"status": "error", "error": f"Diff analysis failed: {str(e)}"}


async def detect_patterns(input_data: PatternDetectionInput, ctx: Context) -> dict[str, Any]:
    """
    Detect code patterns, anti-patterns, and potential issues.

    Analyzes code for common patterns, security issues, code smells,
    and best practice violations.
    """
    try:
        await ctx.info(f"Starting pattern detection for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for pattern detection
        from ...models import SearchQuery

        query = SearchQuery(
            pattern_detection=True,
            file_extensions=input_data.file_extensions,
            max_results=input_data.max_files,
        )

        # Perform pattern detection search
        results: list[dict[str, Any]] = []
        async for result in orchestrator.search(repo=repo, query=query):
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path) if result.file_path else None,
                    "line_number": result.line_number,
                    "matching_line": result.matching_line,
                    "commit_info": result.commit_info.dict() if result.commit_info else None,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                }
            )

        # Group results by pattern type
        pattern_summary: dict[str, int] = {}
        for result_dict in results:
            # result_dict is already dict[str, Any] from the search results
            match_context = result_dict.get("match_context") or {}
            if isinstance(match_context, dict):
                pattern_type = match_context.get("pattern_type", "unknown")
            else:
                pattern_type = "unknown"
            if pattern_type not in pattern_summary:
                pattern_summary[pattern_type] = 0
            pattern_summary[pattern_type] += 1

        await ctx.info(f"Pattern detection complete: found {len(results)} patterns")

        return {
            "status": "success",
            "results": results,
            "pattern_summary": pattern_summary,
            "total_count": len(results),
            "severity_threshold": input_data.severity_threshold,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during pattern detection: {str(e)}")
        return {"status": "error", "error": f"Pattern detection failed: {str(e)}"}


async def analyze_statistics(input_data: StatisticalAnalysisInput, ctx: Context) -> dict[str, Any]:
    """
    Perform statistical analysis of repository data.

    Provides comprehensive statistical insights including commit patterns,
    author contributions, file change frequencies, and trend analysis.
    """
    try:
        await ctx.info(f"Starting statistical analysis for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for statistical analysis
        from ...models import SearchQuery

        query = SearchQuery(
            statistical_analysis=True, max_results=1000  # Analyze more data for statistics
        )

        # Perform statistical analysis search
        results: list[dict[str, Any]] = []
        async for result in orchestrator.search(repo=repo, query=query):
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path) if result.file_path else None,
                    "commit_info": result.commit_info.dict() if result.commit_info else None,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                }
            )

        # Calculate statistical metrics
        statistics = {
            "total_analyzed_commits": len(results),
            "time_range_days": input_data.time_range_days,
            "group_by": input_data.group_by,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        # Group results by specified criteria
        grouped_data: dict[str, list[dict[str, Any]]] = {}
        for result_dict in results:
            # result_dict is already dict[str, Any] from the search results
            if input_data.group_by == "author" and result_dict.get("commit_info"):
                commit_info = result_dict.get("commit_info")
                if isinstance(commit_info, dict) and commit_info.get("author_name"):
                    key = commit_info.get("author_name") or "unknown"
                else:
                    key = "unknown"
            elif input_data.group_by == "file" and result_dict.get("file_path"):
                key = str(result_dict.get("file_path"))
            else:
                key = "all"

            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(result_dict)

        statistics["grouped_results"] = {key: len(items) for key, items in grouped_data.items()}

        await ctx.info(f"Statistical analysis complete: analyzed {len(results)} items")

        return {
            "status": "success",
            "results": results,
            "statistics": statistics,
            "grouped_data": grouped_data,
            "total_count": len(results),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during statistical analysis: {str(e)}")
        return {"status": "error", "error": f"Statistical analysis failed: {str(e)}"}


async def analyze_tags(input_data: TagAnalysisInput, ctx: Context) -> dict[str, Any]:
    """
    Analyze repository tags and version information.

    Provides insights into versioning patterns, release history,
    and tag-based development workflows.
    """
    try:
        await ctx.info(f"Starting tag analysis for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for tag analysis
        from ...models import SearchQuery

        query = SearchQuery(tag_analysis=True, content_pattern=input_data.tag_pattern)

        # Perform tag analysis search
        results: list[dict[str, Any]] = []
        async for result in orchestrator.search(repo=repo, query=query):
            results.append(
                {
                    "commit_hash": result.commit_hash,
                    "file_path": str(result.file_path) if result.file_path else None,
                    "commit_info": result.commit_info.dict() if result.commit_info else None,
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "match_context": result.match_context,
                }
            )

        # Extract tag information
        tag_info = {
            "total_tags_analyzed": len(results),
            "tag_pattern": input_data.tag_pattern,
            "include_releases": input_data.include_releases,
            "compare_versions": input_data.compare_versions,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        await ctx.info(f"Tag analysis complete: analyzed {len(results)} tags")

        return {
            "status": "success",
            "results": results,
            "tag_info": tag_info,
            "total_count": len(results),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during tag analysis: {str(e)}")
        return {"status": "error", "error": f"Tag analysis failed: {str(e)}"}
