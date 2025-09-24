"""Advanced result processing and filtering for GitHound search results."""

import asyncio
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    from ._pandas_compat import mock_pd

    pd = mock_pd  # type: ignore[assignment]

from ..models import SearchQuery, SearchResult, SearchType
from .base import SearchContext


class ResultProcessor:
    """Advanced processor for search results with filtering, grouping, and enrichment."""

    def __init__(self) -> None:
        self.filters: list[Callable[[SearchResult], bool]] = []
        self.enrichers: list[Callable[[SearchResult, SearchContext], SearchResult]] = []
        self.groupers: dict[str, Callable[[SearchResult], str]] = {}

    def add_filter(self, filter_func: Callable[[SearchResult], bool]) -> None:
        """Add a filter function to the processor."""
        self.filters.append(filter_func)

    def add_enricher(
        self, enricher_func: Callable[[SearchResult, SearchContext], SearchResult]
    ) -> None:
        """Add an enricher function to the processor."""
        self.enrichers.append(enricher_func)

    def add_grouper(self, name: str, grouper_func: Callable[[SearchResult], str]) -> None:
        """Add a grouping function to the processor."""
        self.groupers[name] = grouper_func

    async def process_results(
        self, results: list[SearchResult], query: SearchQuery, context: SearchContext
    ) -> list[SearchResult]:
        """Process search results and return filtered/enriched results."""
        # Apply filters
        filtered_results = await self._apply_filters(results)

        # Apply enrichment
        enriched_results = await self._apply_enrichment(filtered_results, context)

        # Apply sorting based on query preferences
        processing_options = query.get_processing_options()
        final_results = await self._apply_sorting_and_limiting(enriched_results, processing_options)

        return final_results

    async def process_results_detailed(
        self,
        results: list[SearchResult],
        context: SearchContext,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process search results with filtering, enrichment, and grouping."""
        options = options or {}

        # Apply filters
        filtered_results = await self._apply_filters(results)

        # Apply enrichment
        enriched_results = await self._apply_enrichment(filtered_results, context)

        # Apply grouping
        grouped_results = await self._apply_grouping(enriched_results, options)

        # Generate statistics
        statistics = await self._generate_statistics(enriched_results)

        # Apply sorting and limiting
        final_results = await self._apply_sorting_and_limiting(enriched_results, options)

        return {
            "results": final_results,
            "grouped_results": grouped_results,
            "statistics": statistics,
            "total_count": len(results),
            "filtered_count": len(filtered_results),
            "final_count": len(final_results),
        }

    async def _apply_filters(self, results: list[SearchResult]) -> list[SearchResult]:
        """Apply all registered filters to the results."""
        filtered_results = results.copy()

        for filter_func in self.filters:
            filtered_results = [r for r in filtered_results if filter_func(r)]

        return filtered_results

    async def _apply_enrichment(
        self, results: list[SearchResult], context: SearchContext
    ) -> list[SearchResult]:
        """Apply all registered enrichers to the results."""
        enriched_results = []

        for result in results:
            enriched_result = result
            for enricher_func in self.enrichers:
                enriched_result = enricher_func(enriched_result, context)
            enriched_results.append(enriched_result)

        return enriched_results

    async def _apply_grouping(
        self, results: list[SearchResult], options: dict[str, Any]
    ) -> dict[str, dict[str, list[SearchResult]]]:
        """Apply grouping to the results."""
        grouped_results: dict[str, dict[str, list[SearchResult]]] = {}

        group_by = options.get("group_by", [])
        if not group_by:
            return {"all": {"all": results}}

        for group_name in group_by:
            if group_name in self.groupers:
                grouper_func = self.groupers[group_name]
                groups: dict[str, list[SearchResult]] = defaultdict(list)

                for result in results:
                    group_key = grouper_func(result)
                    groups[group_key].append(result)

                grouped_results[group_name] = dict(groups)

        return grouped_results

    async def _generate_statistics(self, results: list[SearchResult]) -> dict[str, Any]:
        """Generate comprehensive statistics about the results."""
        if not results:
            return {}

        # Convert to DataFrame for easier analysis
        df_data = []
        for result in results:
            df_data.append(
                {
                    "search_type": result.search_type.value,
                    "relevance_score": result.relevance_score,
                    "file_path": str(result.file_path),
                    "file_extension": Path(result.file_path).suffix.lower(),
                    "commit_hash": result.commit_hash,
                    "line_number": result.line_number,
                    "has_commit_info": result.commit_info is not None,
                    "commit_date": result.commit_info.date if result.commit_info else None,
                    "author": result.commit_info.author_name if result.commit_info else None,
                }
            )

        df = pd.DataFrame(df_data)

        statistics = {
            "total_results": len(results),
            "search_types": df["search_type"].value_counts().to_dict(),
            "file_extensions": df["file_extension"].value_counts().head(10).to_dict(),
            "relevance_stats": {
                "mean": df["relevance_score"].mean(),
                "median": df["relevance_score"].median(),
                "std": df["relevance_score"].std(),
                "min": df["relevance_score"].min(),
                "max": df["relevance_score"].max(),
            },
            "unique_files": df["file_path"].nunique(),
            "unique_commits": df["commit_hash"].nunique(),
            "results_with_line_numbers": df["line_number"].notna().sum(),
            "results_with_commit_info": df["has_commit_info"].sum(),
        }

        # Add temporal statistics if commit dates are available
        if df["commit_date"].notna().any():
            commit_dates = pd.to_datetime(df["commit_date"].dropna())
            statistics["temporal_stats"] = {
                "earliest_commit": commit_dates.min().isoformat(),
                "latest_commit": commit_dates.max().isoformat(),
                "date_range_days": (commit_dates.max() - commit_dates.min()).days,
            }

        # Add author statistics if available
        if df["author"].notna().any():
            author_counts = df["author"].value_counts()
            statistics["author_stats"] = {
                "unique_authors": len(author_counts),
                "top_authors": author_counts.head(5).to_dict(),
            }

        return statistics

    async def _apply_sorting_and_limiting(
        self, results: list[SearchResult], options: dict[str, Any]
    ) -> list[SearchResult]:
        """Apply sorting and limiting to the results."""
        # Sort results
        sort_by = options.get("sort_by", "relevance_score")
        sort_order = options.get("sort_order", "desc")

        if sort_by == "relevance_score":
            results.sort(key=lambda r: r.relevance_score, reverse=(sort_order == "desc"))
        elif sort_by == "date" and results and results[0].commit_info:
            results.sort(
                key=lambda r: r.commit_info.date if r.commit_info else datetime.min,
                reverse=(sort_order == "desc"),
            )
        elif sort_by == "file_path":
            results.sort(key=lambda r: str(r.file_path), reverse=(sort_order == "desc"))
        elif sort_by == "line_number":
            results.sort(key=lambda r: r.line_number or 0, reverse=(sort_order == "desc"))

        # Apply limit
        limit = options.get("limit")
        if limit and limit > 0:
            results = results[:limit]

        return results

    # Predefined filters
    @staticmethod
    def create_relevance_filter(min_score: float) -> Callable[[SearchResult], bool]:
        """Create a filter for minimum relevance score."""

        def filter_func(result: SearchResult) -> bool:
            return result.relevance_score >= min_score

        return filter_func

    @staticmethod
    def create_file_type_filter(extensions: list[str]) -> Callable[[SearchResult], bool]:
        """Create a filter for specific file types."""
        extensions_lower = [ext.lower() for ext in extensions]

        def filter_func(result: SearchResult) -> bool:
            file_ext = Path(result.file_path).suffix.lower()
            return file_ext in extensions_lower

        return filter_func

    @staticmethod
    def create_search_type_filter(search_types: list[SearchType]) -> Callable[[SearchResult], bool]:
        """Create a filter for specific search types."""

        def filter_func(result: SearchResult) -> bool:
            return result.search_type in search_types

        return filter_func

    @staticmethod
    def create_date_range_filter(
        start_date: datetime | None = None, end_date: datetime | None = None
    ) -> Callable[[SearchResult], bool]:
        """Create a filter for date range."""

        def filter_func(result: SearchResult) -> bool:
            if not result.commit_info:
                return False

            commit_date = result.commit_info.date
            if start_date and commit_date < start_date:
                return False
            if end_date and commit_date > end_date:
                return False

            return True

        return filter_func

    # Predefined enrichers
    @staticmethod
    def create_file_info_enricher() -> Callable[[SearchResult, SearchContext], SearchResult]:
        """Create an enricher that adds file information."""

        def enricher_func(result: SearchResult, context: SearchContext) -> SearchResult:
            if not result.match_context:
                result.match_context = {}

            file_path = Path(result.file_path)
            result.match_context.update(
                {
                    "file_name": file_path.name,
                    "file_extension": file_path.suffix.lower(),
                    "file_directory": str(file_path.parent),
                    "file_size_category": "unknown",  # Could be enhanced with actual file size
                }
            )

            return result

        return enricher_func

    @staticmethod
    def create_context_enricher(
        context_lines: int = 3,
    ) -> Callable[[SearchResult, SearchContext], SearchResult]:
        """Create an enricher that adds context lines around matches."""

        def enricher_func(result: SearchResult, context: SearchContext) -> SearchResult:
            if not result.line_number or not result.commit_info:
                return result

            try:
                # Get file content at the commit
                commit = context.repo.commit(result.commit_hash)
                file_content = (
                    commit.tree[str(result.file_path)]
                    .data_stream.read()
                    .decode("utf-8", errors="ignore")
                )
                lines = file_content.split("\n")

                line_idx = result.line_number - 1  # Convert to 0-based index
                start_idx = max(0, line_idx - context_lines)
                end_idx = min(len(lines), line_idx + context_lines + 1)

                context_before = lines[start_idx:line_idx]
                context_after = lines[line_idx + 1 : end_idx]

                if not result.match_context:
                    result.match_context = {}

                result.match_context.update(
                    {
                        "context_before": context_before,
                        "context_after": context_after,
                        "context_lines_count": context_lines,
                    }
                )

            except Exception:
                # If we can't get context, just continue without it
                pass

            return result

        return enricher_func

    # Predefined groupers
    @staticmethod
    def create_file_type_grouper() -> Callable[[SearchResult], str]:
        """Create a grouper that groups by file type."""

        def grouper_func(result: SearchResult) -> str:
            file_ext = Path(result.file_path).suffix.lower()
            return file_ext if file_ext else "no_extension"

        return grouper_func

    @staticmethod
    def create_search_type_grouper() -> Callable[[SearchResult], str]:
        """Create a grouper that groups by search type."""

        def grouper_func(result: SearchResult) -> str:
            return result.search_type.value

        return grouper_func

    @staticmethod
    def create_author_grouper() -> Callable[[SearchResult], str]:
        """Create a grouper that groups by author."""

        def grouper_func(result: SearchResult) -> str:
            if result.commit_info:
                return result.commit_info.author_name
            return "unknown"

        return grouper_func

    @staticmethod
    def create_directory_grouper() -> Callable[[SearchResult], str]:
        """Create a grouper that groups by directory."""

        def grouper_func(result: SearchResult) -> str:
            return str(Path(result.file_path).parent)

        return grouper_func
