"""Tag and release searchers for GitHound."""

import asyncio
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class TagSearcher(CacheableSearcher):
    """Searcher for tag and release analysis."""

    def __init__(self) -> None:
        super().__init__("tag", "tag")

        # Version patterns for semantic versioning
        self.version_patterns = [
            r"v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-\.]+))?(?:\+([a-zA-Z0-9\-\.]+))?",  # Semantic versioning
            r"v?(\d+)\.(\d+)(?:\.(\d+))?",  # Major.minor(.patch)
            r"(\d{4})\.(\d{1,2})\.(\d{1,2})",  # Date-based versioning
            r"release[_\-]?(\d+)\.(\d+)(?:\.(\d+))?",  # Release versioning
        ]

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle tag-related queries."""
        # Handle queries that mention tags, releases, or versions
        return (
            hasattr(query, "tag_pattern")
            and query.tag_pattern is not None
            or hasattr(query, "version_analysis")
            and query.version_analysis
            or hasattr(query, "release_analysis")
            and query.release_analysis
            or any(
                keyword in (query.text or "").lower() for keyword in ["tag", "release", "version"]
            )
        )

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on number of tags."""
        try:
            tags = list(context.repo.tags)
            return min(len(tags) * 5, 300)  # Estimate 5 units per tag
        except Exception:
            return 50

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform tag and release analysis."""
        self._report_progress(context, "Starting tag analysis...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "tag_analysis")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached tag results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform tag analysis
        results: List[SearchResult] = []

        # Analyze tags
        self._report_progress(context, "Analyzing tags...", 0.2)
        tag_results = await self._analyze_tags(context)
        results.extend(tag_results)

        # Analyze version patterns
        self._report_progress(context, "Analyzing version patterns...", 0.5)
        version_results = await self._analyze_version_patterns(context)
        results.extend(version_results)

        # Analyze release timeline
        self._report_progress(context, "Analyzing release timeline...", 0.8)
        timeline_results = await self._analyze_release_timeline(context)
        results.extend(timeline_results)

        # Cache results
        await self._set_cache(context, cache_key, results)

        # Yield results
        for result in results:
            yield result

        self._report_progress(context, "Tag analysis completed", 1.0)

    async def _analyze_tags(self, context: SearchContext) -> List[SearchResult]:
        """Analyze repository tags."""
        results: List[SearchResult] = []

        try:
            tags = list(context.repo.tags)

            if not tags:
                result = SearchResult(
                    commit_hash="tag_analysis",
                    file_path="tags/no_tags.txt",
                    line_number=1,
                    matching_line="No tags found in repository",
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=0.5,
                    match_context={"analysis_type": "tag_summary", "tag_count": 0},
                )
                results.append(result)
                return results

            # Basic tag information
            insights = [
                f"Total tags: {len(tags)}",
            ]

            # Analyze recent tags (last 10)
            recent_tags = sorted(
                tags, key=lambda t: self._get_tag_date(t) or datetime.min, reverse=True
            )[:10]

            for i, tag in enumerate(recent_tags):
                try:
                    commit = tag.commit
                    commit_info = self._create_commit_info(commit)
                    tag_date = self._get_tag_date(tag)

                    # Check if it's a version tag
                    is_version, version_info = self._parse_version(tag.name)

                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=f"tags/{tag.name}.txt",
                        line_number=1,
                        matching_line=f"Tag: {tag.name} - {commit.message.strip()[:50]}",
                        commit_info=commit_info,
                        search_type=SearchType.COMBINED,
                        relevance_score=1.0 - (i * 0.1),  # Recent tags get higher scores
                        match_context={
                            "analysis_type": "tag_info",
                            "tag_name": tag.name,
                            "tag_date": tag_date.isoformat() if tag_date else None,
                            "is_version": is_version,
                            "version_info": version_info,
                            "rank": i + 1,
                        },
                    )
                    results.append(result)

                except Exception:
                    continue

            # Add summary insights
            for i, insight in enumerate(insights):
                result = SearchResult(
                    commit_hash="tag_analysis",
                    file_path=f"tags/summary_{i}.txt",
                    line_number=1,
                    matching_line=insight,
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=1.0,
                    match_context={"analysis_type": "tag_summary", "insight": insight},
                )
                results.append(result)

        except Exception as e:
            # Error handling
            result = SearchResult(
                commit_hash="tag_analysis",
                file_path="tags/error.txt",
                line_number=1,
                matching_line=f"Error analyzing tags: {str(e)}",
                commit_info=None,
                search_type=SearchType.COMBINED,
                relevance_score=0.5,
                match_context={"analysis_type": "tag_error", "error": str(e)},
            )
            results.append(result)

        return results

    async def _analyze_version_patterns(self, context: SearchContext) -> List[SearchResult]:
        """Analyze version patterns in tags."""
        results: List[SearchResult] = []

        try:
            tags = list(context.repo.tags)
            version_tags = []

            # Find version tags
            for tag in tags:
                is_version, version_info = self._parse_version(tag.name)
                if is_version:
                    tag_date = self._get_tag_date(tag)
                    version_tags.append((tag, version_info, tag_date))

            if not version_tags:
                return results

            # Sort by version
            version_tags.sort(key=lambda x: self._version_sort_key(x[1]), reverse=True)

            # Analyze version progression
            if len(version_tags) > 1:
                latest_version = version_tags[0][1]
                previous_version = version_tags[1][1] if len(version_tags) > 1 else None

                # Latest version info
                latest_tag, latest_info, latest_date = version_tags[0]
                commit_info = self._create_commit_info(latest_tag.commit)

                result = SearchResult(
                    commit_hash=latest_tag.commit.hexsha,
                    file_path="versions/latest.txt",
                    line_number=1,
                    matching_line=f"Latest version: {latest_tag.name}",
                    commit_info=commit_info,
                    search_type=SearchType.COMBINED,
                    relevance_score=1.0,
                    match_context={
                        "analysis_type": "version_latest",
                        "version": latest_info,
                        "tag_name": latest_tag.name,
                        "release_date": latest_date.isoformat() if latest_date else None,
                    },
                )
                results.append(result)

                # Version progression analysis
                if previous_version:
                    version_jump = self._analyze_version_jump(previous_version, latest_version)

                    result = SearchResult(
                        commit_hash="version_analysis",
                        file_path="versions/progression.txt",
                        line_number=1,
                        matching_line=f"Version progression: {version_jump['type']} update",
                        commit_info=None,
                        search_type=SearchType.COMBINED,
                        relevance_score=0.8,
                        match_context={
                            "analysis_type": "version_progression",
                            "jump_type": version_jump["type"],
                            "previous_version": previous_version,
                            "current_version": latest_version,
                        },
                    )
                    results.append(result)

            # Version statistics
            major_versions = set()
            minor_versions = set()
            patch_versions = set()

            for _, version_info, _ in version_tags:
                if "major" in version_info:
                    major_versions.add(version_info["major"])
                if "minor" in version_info:
                    minor_versions.add(version_info["minor"])
                if "patch" in version_info:
                    patch_versions.add(version_info["patch"])

            stats = [
                f"Version tags: {len(version_tags)}",
                f"Major versions: {len(major_versions)}",
                f"Minor versions: {len(minor_versions)}",
                f"Patch versions: {len(patch_versions)}",
            ]

            for i, stat in enumerate(stats):
                result = SearchResult(
                    commit_hash="version_analysis",
                    file_path=f"versions/stats_{i}.txt",
                    line_number=1,
                    matching_line=stat,
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=0.7,
                    match_context={"analysis_type": "version_stats", "statistic": stat},
                )
                results.append(result)

        except Exception:
            pass

        return results

    async def _analyze_release_timeline(self, context: SearchContext) -> List[SearchResult]:
        """Analyze release timeline and frequency."""
        results: List[SearchResult] = []

        try:
            tags = list(context.repo.tags)
            if len(tags) < 2:
                return results

            # Get tag dates
            tag_dates = []
            for tag in tags:
                tag_date = self._get_tag_date(tag)
                if tag_date:
                    tag_dates.append((tag, tag_date))

            if len(tag_dates) < 2:
                return results

            # Sort by date
            tag_dates.sort(key=lambda x: x[1])

            # Calculate release frequency
            intervals = []
            for i in range(1, len(tag_dates)):
                prev_date = tag_dates[i - 1][1]
                curr_date = tag_dates[i][1]
                interval = (curr_date - prev_date).days
                intervals.append(interval)

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                min_interval = min(intervals)
                max_interval = max(intervals)

                timeline_info = [
                    f"Average release interval: {avg_interval:.1f} days",
                    f"Shortest interval: {min_interval} days",
                    f"Longest interval: {max_interval} days",
                ]

                for i, info in enumerate(timeline_info):
                    result = SearchResult(
                        commit_hash="timeline_analysis",
                        file_path=f"timeline/frequency_{i}.txt",
                        line_number=1,
                        matching_line=info,
                        commit_info=None,
                        search_type=SearchType.COMBINED,
                        relevance_score=0.6,
                        match_context={
                            "analysis_type": "release_timeline",
                            "metric": info,
                            "avg_interval": avg_interval,
                            "min_interval": min_interval,
                            "max_interval": max_interval,
                        },
                    )
                    results.append(result)

        except Exception:
            pass

        return results

    def _get_tag_date(self, tag: Any) -> Optional[datetime]:
        """Get the date of a tag."""
        try:
            # Try to get tag object date first (annotated tags)
            if hasattr(tag, "tag") and tag.tag:
                return datetime.fromtimestamp(tag.tag.tagged_date)
            # Fall back to commit date
            return datetime.fromtimestamp(tag.commit.committed_date)
        except Exception:
            return None

    def _parse_version(self, tag_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Parse version information from tag name."""
        for pattern in self.version_patterns:
            match = re.match(pattern, tag_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                version_info: Dict[str, Union[int, str]] = {
                    "major": int(groups[0]) if groups[0] else 0,
                    "minor": int(groups[1]) if groups[1] else 0,
                    "patch": int(groups[2]) if groups[2] and groups[2].isdigit() else 0,
                }

                if len(groups) > 3 and groups[3]:
                    version_info["prerelease"] = groups[3]
                if len(groups) > 4 and groups[4]:
                    version_info["build"] = groups[4]

                return True, version_info

        return False, {}

    def _version_sort_key(self, version_info: Dict[str, Any]) -> Tuple[int, int, int]:
        """Create a sort key for version comparison."""
        return (
            version_info.get("major", 0),
            version_info.get("minor", 0),
            version_info.get("patch", 0),
        )

    def _analyze_version_jump(
        self, prev_version: Dict[str, Any], curr_version: Dict[str, Any]
    ) -> Dict[str, str]:
        """Analyze the type of version jump between two versions."""
        prev_major = prev_version.get("major", 0)
        prev_minor = prev_version.get("minor", 0)
        prev_patch = prev_version.get("patch", 0)

        curr_major = curr_version.get("major", 0)
        curr_minor = curr_version.get("minor", 0)
        curr_patch = curr_version.get("patch", 0)

        if curr_major > prev_major:
            return {"type": "major", "description": "Breaking changes expected"}
        elif curr_minor > prev_minor:
            return {"type": "minor", "description": "New features added"}
        elif curr_patch > prev_patch:
            return {"type": "patch", "description": "Bug fixes and improvements"}
        else:
            return {"type": "unknown", "description": "Version relationship unclear"}

    def _create_commit_info(self, commit: Any) -> CommitInfo:
        """Create CommitInfo from git commit object."""
        return CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:8],
            author_name=commit.author.name,
            author_email=commit.author.email,
            committer_name=commit.committer.name,
            committer_email=commit.committer.email,
            message=commit.message.strip(),
            date=datetime.fromtimestamp(commit.committed_date),
            files_changed=len(commit.stats.files),
            insertions=commit.stats.total.get("insertions", 0),
            deletions=commit.stats.total.get("deletions", 0),
            parents=[parent.hexsha for parent in commit.parents],
        )
