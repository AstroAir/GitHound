"""Query optimization and planning for GitHound search engine.

This module provides intelligent query analysis and optimization
to improve search performance and accuracy.
"""

import re
from typing import Any

from ..models import SearchQuery


class QueryOptimizer:
    """Optimizes search queries for better performance and accuracy."""

    def __init__(self) -> None:
        # Query rewrite rules
        self.rewrite_rules = [
            # Common typo corrections
            (r"\bcomit\b", "commit"),
            (r"\bfiel\b", "file"),
            (r"\bfunciton\b", "function"),
            (r"\bcalss\b", "class"),
        ]

        # Stop words to ignore (can be expanded)
        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
        }

    def optimize(self, query: SearchQuery) -> SearchQuery:
        """Optimize a search query.

        Args:
            query: Original search query

        Returns:
            Optimized search query
        """
        optimized = query

        # Apply query rewriting
        if query.content_pattern:
            optimized.content_pattern = self._rewrite_query(query.content_pattern)

        if query.message_pattern:
            optimized.message_pattern = self._rewrite_query(query.message_pattern)

        if query.author_pattern:
            optimized.author_pattern = self._rewrite_query(query.author_pattern)

        # Normalize file path patterns
        if query.file_path_pattern:
            optimized.file_path_pattern = self._normalize_path_pattern(query.file_path_pattern)

        # Enable fuzzy search for short queries (likely to have typos)
        if not query.fuzzy_search:
            if self._should_enable_fuzzy(query):
                optimized.fuzzy_search = True
                optimized.fuzzy_threshold = 0.75  # Moderate threshold

        # Adjust max results based on query complexity
        if not query.max_results:
            optimized.max_results = self._estimate_max_results(query)

        return optimized

    def _rewrite_query(self, query_text: str) -> str:
        """Apply query rewriting rules."""
        result = query_text.lower()

        # Apply typo corrections
        for pattern, replacement in self.rewrite_rules:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Remove excessive whitespace
        result = " ".join(result.split())

        return result

    def _normalize_path_pattern(self, pattern: str) -> str:
        """Normalize file path patterns."""
        # Convert backslashes to forward slashes
        pattern = pattern.replace("\\", "/")

        # Remove leading/trailing slashes
        pattern = pattern.strip("/")

        return pattern

    def _should_enable_fuzzy(self, query: SearchQuery) -> bool:
        """Determine if fuzzy search should be enabled."""
        # Enable fuzzy for short queries (likely to have typos)
        if query.content_pattern and len(query.content_pattern) < 10:
            return True

        if query.message_pattern and len(query.message_pattern) < 10:
            return True

        if query.author_pattern and len(query.author_pattern) < 15:
            return True

        return False

    def _estimate_max_results(self, query: SearchQuery) -> int:
        """Estimate appropriate max results based on query."""
        # More specific queries can have fewer results
        specificity = 0

        if query.commit_hash:
            specificity += 5
        if query.author_pattern:
            specificity += 2
        if query.message_pattern:
            specificity += 2
        if query.content_pattern:
            specificity += 3
        if query.file_path_pattern:
            specificity += 3
        if query.file_extensions:
            specificity += 1
        if query.date_after or query.date_before:
            specificity += 2

        # More specific = fewer results needed
        if specificity >= 10:
            return 50
        elif specificity >= 5:
            return 100
        else:
            return 500

    def analyze_query(self, query: SearchQuery) -> dict[str, Any]:
        """Analyze a query and provide insights.

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "complexity": "simple",
            "estimated_cost": "low",
            "requires_index": False,
            "can_use_cache": True,
            "suggested_optimizations": [],
        }

        # Determine complexity
        criteria_count = sum(
            [
                bool(query.commit_hash),
                bool(query.author_pattern),
                bool(query.message_pattern),
                bool(query.content_pattern),
                bool(query.file_path_pattern),
                bool(query.file_extensions),
                bool(query.date_after or query.date_before),
            ]
        )

        if criteria_count >= 4:
            analysis["complexity"] = "complex"
            analysis["estimated_cost"] = "high"
        elif criteria_count >= 2:
            analysis["complexity"] = "moderate"
            analysis["estimated_cost"] = "medium"

        # Check if index would help
        if query.content_pattern or query.message_pattern:
            analysis["requires_index"] = True
            if not query.fuzzy_search:
                analysis["suggested_optimizations"].append(
                    "Consider using inverted index for faster text search"
                )

        # Check if fuzzy search is needed
        if query.fuzzy_search and not (query.author_pattern or query.message_pattern):
            analysis["suggested_optimizations"].append(
                "Fuzzy search is enabled but no text patterns provided"
            )

        # Check for overly broad queries
        if not query.max_results or query.max_results > 1000:
            analysis["suggested_optimizations"].append(
                "Consider limiting max_results to improve performance"
            )

        # Check for cache-unfriendly patterns
        if query.date_after and not query.date_before:
            analysis["can_use_cache"] = False
            analysis["suggested_optimizations"].append("Open-ended date ranges are harder to cache")

        return analysis


class QueryPlanner:
    """Plans optimal execution strategy for search queries."""

    def __init__(self) -> None:
        self.optimizer = QueryOptimizer()

    def plan_execution(self, query: SearchQuery) -> dict[str, Any]:
        """Create an execution plan for a query.

        Returns:
            Execution plan with ordered steps
        """
        plan = {
            "optimized_query": self.optimizer.optimize(query),
            "execution_order": [],
            "estimated_time_ms": 0,
            "can_parallelize": False,
        }

        # Determine execution order (most selective first)
        steps = []

        # 1. Exact commit hash (most selective)
        if query.commit_hash:
            steps.append(
                {
                    "searcher": "commit_hash",
                    "priority": 1,
                    "estimated_time_ms": 10,
                    "selectivity": "very_high",
                }
            )

        # 2. Date range filter (high selectivity)
        if query.date_after or query.date_before:
            steps.append(
                {
                    "searcher": "date_range",
                    "priority": 2,
                    "estimated_time_ms": 50,
                    "selectivity": "high",
                }
            )

        # 3. File path pattern (medium selectivity)
        if query.file_path_pattern:
            steps.append(
                {
                    "searcher": "file_path",
                    "priority": 3,
                    "estimated_time_ms": 200,
                    "selectivity": "medium",
                }
            )

        # 4. Author search (medium selectivity)
        if query.author_pattern:
            steps.append(
                {
                    "searcher": "author",
                    "priority": 4,
                    "estimated_time_ms": 150,
                    "selectivity": "medium",
                }
            )

        # 5. Message search (lower selectivity)
        if query.message_pattern:
            steps.append(
                {
                    "searcher": "message",
                    "priority": 5,
                    "estimated_time_ms": 300,
                    "selectivity": "low",
                }
            )

        # 6. Content search (lowest selectivity, most expensive)
        if query.content_pattern:
            steps.append(
                {
                    "searcher": "content",
                    "priority": 6,
                    "estimated_time_ms": 1000,
                    "selectivity": "very_low",
                }
            )

        # Sort by priority
        steps.sort(key=lambda x: x["priority"])

        plan["execution_order"] = steps
        plan["estimated_time_ms"] = sum(s["estimated_time_ms"] for s in steps)

        # Can parallelize if multiple independent searches
        plan["can_parallelize"] = len(steps) > 1

        return plan


class SearchCache:
    """Cache for search results to avoid redundant queries."""

    def __init__(self, max_size: int = 1000) -> None:
        self.cache: dict[str, Any] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, query_key: str) -> Any | None:
        """Get cached results for a query."""
        if query_key in self.cache:
            self.hits += 1
            return self.cache[query_key]
        else:
            self.misses += 1
            return None

    def set(self, query_key: str, results: Any) -> None:
        """Cache results for a query."""
        # Simple LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[query_key] = results

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }
