"""Advanced ranking engine for GitHound search results."""

import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from rapidfuzz import fuzz
except ImportError:
    # Use mock for testing when rapidfuzz is not available
    import sys
    from pathlib import Path as PathLib

    sys.path.insert(0, str(PathLib(__file__).parent.parent.parent))
    import mock_rapidfuzz

    fuzz = mock_rapidfuzz.fuzz  # type: ignore[assignment]

from ..models import SearchQuery, SearchResult, SearchType
from .base import SearchContext


class RankingEngine:
    """Sophisticated ranking engine for search results with multiple relevance factors."""

    def __init__(self) -> None:
        self.ranking_factors = {
            "query_match": 0.3,  # How well the result matches the query
            "recency": 0.2,  # How recent the commit is
            "file_importance": 0.15,  # Importance of the file type/location
            "author_relevance": 0.1,  # Author-based relevance
            "commit_quality": 0.1,  # Quality indicators of the commit
            "context_relevance": 0.1,  # Relevance of surrounding context
            "frequency": 0.05,  # How often this pattern appears
        }

    def set_ranking_weights(self, weights: dict[str, float]) -> None:
        """Set custom weights for ranking factors."""
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights to sum to 1.0
            weights = {k: v / total_weight for k, v in weights.items()}

        self.ranking_factors.update(weights)

    async def rank_results(
        self, results: list[SearchResult], query: SearchQuery, context: SearchContext
    ) -> list[SearchResult]:
        """Rank search results using multiple relevance factors."""
        if not results:
            return results

        # Calculate scores for each result
        scored_results = []
        for result in results:
            score = await self._calculate_relevance_score(result, query, context, results)
            result.relevance_score = score
            scored_results.append(result)

        # Sort by relevance score (descending)
        scored_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return scored_results

    async def _calculate_relevance_score(
        self,
        result: SearchResult,
        query: SearchQuery,
        context: SearchContext,
        all_results: list[SearchResult],
    ) -> float:
        """Calculate comprehensive relevance score for a search result."""
        scores = {}

        # Query match score
        scores["query_match"] = await self._calculate_query_match_score(result, query)

        # Recency score
        scores["recency"] = await self._calculate_recency_score(result)

        # File importance score
        scores["file_importance"] = await self._calculate_file_importance_score(result)

        # Author relevance score
        scores["author_relevance"] = await self._calculate_author_relevance_score(result, query)

        # Commit quality score
        scores["commit_quality"] = await self._calculate_commit_quality_score(result)

        # Context relevance score
        scores["context_relevance"] = await self._calculate_context_relevance_score(result, query)

        # Frequency score (inverse document frequency-like)
        scores["frequency"] = await self._calculate_frequency_score(result, all_results)

        # Calculate weighted final score
        final_score = 0.0
        for factor, weight in self.ranking_factors.items():
            if factor in scores:
                final_score += scores[factor] * weight

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, final_score))

    async def _calculate_query_match_score(self, result: SearchResult, query: SearchQuery) -> float:
        """Calculate how well the result matches the query."""
        score = 0.0
        match_count = 0

        # Content pattern matching
        if query.content_pattern and result.matching_line:
            if query.fuzzy_search:
                similarity = (
                    fuzz.partial_ratio(query.content_pattern.lower(), result.matching_line.lower())
                    / 100.0
                )
                score += similarity
            else:
                # Exact match gets higher score
                if query.content_pattern.lower() in result.matching_line.lower():
                    score += 1.0
                else:
                    score += 0.5
            match_count += 1

        # Author pattern matching
        if query.author_pattern and result.commit_info:
            author_text = (
                f"{result.commit_info.author_name} {result.commit_info.author_email}".lower()
            )
            if query.fuzzy_search:
                similarity = fuzz.partial_ratio(query.author_pattern.lower(), author_text) / 100.0
                score += similarity
            else:
                if query.author_pattern.lower() in author_text:
                    score += 1.0
                else:
                    score += 0.3
            match_count += 1

        # Message pattern matching
        if query.message_pattern and result.commit_info:
            message = result.commit_info.message.lower()
            if query.fuzzy_search:
                similarity = fuzz.partial_ratio(query.message_pattern.lower(), message) / 100.0
                score += similarity
            else:
                if query.message_pattern.lower() in message:
                    score += 1.0
                else:
                    score += 0.3
            match_count += 1

        # File path pattern matching
        if query.file_path_pattern:
            file_path = str(result.file_path).lower()
            if query.file_path_pattern.lower() in file_path:
                score += 1.0
                match_count += 1

        # Return average score if multiple criteria, otherwise the single score
        return score / max(1, match_count)

    async def _calculate_recency_score(self, result: SearchResult) -> float:
        """Calculate recency score based on commit date."""
        if not result.commit_info:
            return 0.5  # Neutral score for unknown dates

        commit_date = result.commit_info.date
        now = datetime.now()

        # Calculate days since commit
        days_ago = (now - commit_date).days

        # Score decreases exponentially with age
        # Recent commits (< 30 days) get high scores
        # Older commits get progressively lower scores
        if days_ago <= 7:
            return 1.0
        elif days_ago <= 30:
            return 0.9
        elif days_ago <= 90:
            return 0.7
        elif days_ago <= 365:
            return 0.5
        elif days_ago <= 730:  # 2 years
            return 0.3
        else:
            return 0.1

    async def _calculate_file_importance_score(self, result: SearchResult) -> float:
        """Calculate file importance based on file type and location."""
        file_path = Path(result.file_path)
        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()
        path_parts = file_path.parts

        score = 0.5  # Base score

        # File type importance
        important_extensions = {
            ".py": 0.9,
            ".js": 0.9,
            ".java": 0.9,
            ".cs": 0.9,
            ".cpp": 0.9,
            ".c": 0.9,
            ".ts": 0.8,
            ".go": 0.8,
            ".rs": 0.8,
            ".php": 0.8,
            ".rb": 0.8,
            ".md": 0.7,
            ".rst": 0.7,
            ".txt": 0.6,
            ".json": 0.6,
            ".yaml": 0.6,
            ".yml": 0.6,
            ".xml": 0.6,
            ".html": 0.5,
            ".css": 0.5,
            ".scss": 0.5,
        }

        if file_ext in important_extensions:
            score = important_extensions[file_ext]

        # Important file names
        important_files = {
            "readme.md": 0.9,
            "readme.txt": 0.9,
            "readme.rst": 0.9,
            "changelog.md": 0.8,
            "changelog.txt": 0.8,
            "license": 0.7,
            "license.txt": 0.7,
            "license.md": 0.7,
            "makefile": 0.8,
            "dockerfile": 0.8,
            "package.json": 0.8,
            "requirements.txt": 0.8,
            "setup.py": 0.8,
            "pyproject.toml": 0.8,
            "cargo.toml": 0.8,
        }

        if file_name in important_files:
            score = max(score, important_files[file_name])

        # Directory importance
        important_dirs = {"src", "lib", "core", "main", "app"}
        unimportant_dirs = {"test", "tests", "spec", "docs", "examples", "tmp", "temp"}

        for part in path_parts:
            part_lower = part.lower()
            if part_lower in important_dirs:
                score += 0.1
            elif part_lower in unimportant_dirs:
                score -= 0.1

        # Ensure score stays within bounds
        return max(0.1, min(1.0, score))

    async def _calculate_author_relevance_score(
        self, result: SearchResult, query: SearchQuery
    ) -> float:
        """Calculate author relevance score."""
        if not result.commit_info:
            return 0.5

        # If query specifically mentions an author, boost relevance
        if query.author_pattern:
            author_text = (
                f"{result.commit_info.author_name} {result.commit_info.author_email}".lower()
            )
            if query.author_pattern.lower() in author_text:
                return 1.0
            else:
                return 0.3

        # Otherwise, use neutral score
        return 0.5

    async def _calculate_commit_quality_score(self, result: SearchResult) -> float:
        """Calculate commit quality score based on commit characteristics."""
        if not result.commit_info:
            return 0.5

        score = 0.5  # Base score

        # Message quality indicators
        message = result.commit_info.message.lower()

        # Good commit message indicators
        good_indicators = [
            "fix",
            "add",
            "update",
            "improve",
            "refactor",
            "implement",
            "feature",
            "bug",
            "issue",
            "enhancement",
        ]

        # Poor commit message indicators
        poor_indicators = ["wip", "temp", "test", "debug", "tmp", "quick", "minor"]

        for indicator in good_indicators:
            if indicator in message:
                score += 0.1

        for indicator in poor_indicators:
            if indicator in message:
                score -= 0.1

        # Message length (not too short, not too long)
        message_length = len(result.commit_info.message)
        if 20 <= message_length <= 100:
            score += 0.1
        elif message_length < 10:
            score -= 0.2

        # Commit size (moderate changes are often better)
        files_changed = result.commit_info.files_changed
        if 1 <= files_changed <= 10:
            score += 0.1
        elif files_changed > 50:
            score -= 0.1

        # Ensure score stays within bounds
        return max(0.1, min(1.0, score))

    async def _calculate_context_relevance_score(
        self, result: SearchResult, query: SearchQuery
    ) -> float:
        """Calculate context relevance score."""
        if not result.match_context:
            return 0.5

        score = 0.5

        # Check for additional context matches
        context_text = str(result.match_context).lower()

        # If query patterns appear in context, boost score
        if query.content_pattern and query.content_pattern.lower() in context_text:
            score += 0.2

        if query.message_pattern and query.message_pattern.lower() in context_text:
            score += 0.2

        # Analysis type relevance
        analysis_type = result.match_context.get("analysis_type", "")
        if analysis_type in ["code_pattern", "security", "performance"]:
            score += 0.3

        return max(0.1, min(1.0, score))

    async def _calculate_frequency_score(
        self, result: SearchResult, all_results: list[SearchResult]
    ) -> float:
        """Calculate frequency score (inverse document frequency-like)."""
        if not all_results:
            return 0.5

        # Count how many results are from the same file
        same_file_count = sum(1 for r in all_results if str(r.file_path) == str(result.file_path))

        # Count how many results have the same search type
        same_type_count = sum(1 for r in all_results if r.search_type == result.search_type)

        total_results = len(all_results)

        # Calculate inverse frequency scores
        file_frequency = same_file_count / total_results
        type_frequency = same_type_count / total_results

        # Lower frequency (more unique) gets higher score
        file_score = 1.0 - file_frequency
        type_score = 1.0 - type_frequency

        # Combine scores
        frequency_score = (file_score + type_score) / 2

        return max(0.1, min(1.0, frequency_score))
