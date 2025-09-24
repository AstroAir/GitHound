"""Branch-specific searchers for GitHound."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Dict, List

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class BranchSearcher(CacheableSearcher):
    """Searcher for branch-specific operations and analysis."""

    def __init__(self) -> None:
        super().__init__("branch", "branch")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle branch-related queries."""
        # Handle queries that mention branches or request branch analysis
        return (
            hasattr(query, "branch_pattern")
            and query.branch_pattern is not None
            or hasattr(query, "branch_analysis")
            and query.branch_analysis
            or hasattr(query, "compare_branches")
            and query.compare_branches
        )

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on number of branches."""
        try:
            branches = list(context.repo.branches)
            return min(len(branches) * 10, 500)  # Estimate 10 units per branch
        except Exception:
            return 100

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform branch analysis and search."""
        self._report_progress(context, "Starting branch analysis...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "branch_analysis")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached branch results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform branch analysis
        results: List[SearchResult] = []

        # Analyze branch structure
        self._report_progress(context, "Analyzing branch structure...", 0.2)
        branch_results = await self._analyze_branches(context)
        results.extend(branch_results)

        # Analyze branch relationships
        self._report_progress(context, "Analyzing branch relationships...", 0.5)
        relationship_results = await self._analyze_branch_relationships(context)
        results.extend(relationship_results)

        # Analyze branch activity
        self._report_progress(context, "Analyzing branch activity...", 0.8)
        activity_results = await self._analyze_branch_activity(context)
        results.extend(activity_results)

        # Cache results
        await self._set_cache(context, cache_key, results)

        # Yield results
        for result in results:
            yield result

        self._report_progress(context, "Branch analysis completed", 1.0)

    async def _analyze_branches(self, context: SearchContext) -> List[SearchResult]:
        """Analyze branch structure and information."""
        results: List[SearchResult] = []

        try:
            branches = list(context.repo.branches)
            remote_branches = list(context.repo.remote().refs) if context.repo.remotes else []

            # Basic branch information
            insights = [
                f"Total local branches: {len(branches)}",
                f"Total remote branches: {len(remote_branches)}",
            ]

            # Current branch information
            try:
                current_branch = context.repo.active_branch
                insights.append(f"Current branch: {current_branch.name}")

                # Get current branch commit info
                commit = current_branch.commit
                commit_info = self._create_commit_info(commit)

                result = SearchResult(
                    commit_hash=commit.hexsha,
                    file_path="branches/current_branch.txt",
                    line_number=1,
                    matching_line=f"Current branch: {current_branch.name}",
                    commit_info=commit_info,
                    search_type=SearchType.COMBINED,
                    relevance_score=1.0,
                    match_context={
                        "analysis_type": "branch_info",
                        "branch_name": current_branch.name,
                        "is_current": True,
                    },
                )
                results.append(result)

            except Exception:
                insights.append("Current branch: detached HEAD")

            # Branch details
            for i, branch in enumerate(branches[:10]):  # Limit to first 10 branches
                try:
                    commit = branch.commit
                    commit_info = self._create_commit_info(commit)

                    # Check if branch is ahead/behind master/main
                    ahead_behind = self._get_ahead_behind_info(context.repo, branch)

                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=f"branches/{branch.name}.txt",
                        line_number=1,
                        matching_line=f"Branch: {branch.name} - {commit.message.strip()[:50]}",
                        commit_info=commit_info,
                        search_type=SearchType.COMBINED,
                        relevance_score=0.8,
                        match_context={
                            "analysis_type": "branch_info",
                            "branch_name": branch.name,
                            "ahead_behind": ahead_behind,
                            "is_current": False,
                        },
                    )
                    results.append(result)

                except Exception:
                    continue

            # Add summary insights
            for i, insight in enumerate(insights):
                result = SearchResult(
                    commit_hash="branch_analysis",
                    file_path=f"branches/summary_{i}.txt",
                    line_number=1,
                    matching_line=insight,
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=1.0,
                    match_context={"analysis_type": "branch_summary", "insight": insight},
                )
                results.append(result)

        except Exception as e:
            # Error handling
            result = SearchResult(
                commit_hash="branch_analysis",
                file_path="branches/error.txt",
                line_number=1,
                matching_line=f"Error analyzing branches: {str(e)}",
                commit_info=None,
                search_type=SearchType.COMBINED,
                relevance_score=0.5,
                match_context={"analysis_type": "branch_error", "error": str(e)},
            )
            results.append(result)

        return results

    async def _analyze_branch_relationships(self, context: SearchContext) -> List[SearchResult]:
        """Analyze relationships between branches."""
        results: List[SearchResult] = []

        try:
            branches = list(context.repo.branches)

            # Find merge relationships
            merge_info = []
            for branch in branches[:5]:  # Limit analysis
                try:
                    # Get commits unique to this branch
                    commits = list(context.repo.iter_commits(branch.name, max_count=100))
                    merge_commits = [c for c in commits if len(c.parents) > 1]

                    if merge_commits:
                        merge_info.append(
                            f"Branch {branch.name} has {len(merge_commits)} merge commits"
                        )

                        # Create result for merge information
                        latest_merge = merge_commits[0]
                        commit_info = self._create_commit_info(latest_merge)

                        result = SearchResult(
                            commit_hash=latest_merge.hexsha,
                            file_path=f"branches/merges/{branch.name}.txt",
                            line_number=1,
                            matching_line=f"Latest merge in {branch.name}: {latest_merge.message.strip()[:50]}",
                            commit_info=commit_info,
                            search_type=SearchType.COMBINED,
                            relevance_score=0.7,
                            match_context={
                                "analysis_type": "branch_merges",
                                "branch_name": branch.name,
                                "merge_count": len(merge_commits),
                            },
                        )
                        results.append(result)

                except Exception:
                    continue

            # Add merge summary
            for i, info in enumerate(merge_info):
                result = SearchResult(
                    commit_hash="branch_analysis",
                    file_path=f"branches/merge_summary_{i}.txt",
                    line_number=1,
                    matching_line=info,
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=0.8,
                    match_context={"analysis_type": "merge_summary", "insight": info},
                )
                results.append(result)

        except Exception:
            pass

        return results

    async def _analyze_branch_activity(self, context: SearchContext) -> List[SearchResult]:
        """Analyze branch activity and freshness."""
        results: List[SearchResult] = []

        try:
            branches = list(context.repo.branches)
            now = datetime.now()

            # Analyze branch freshness
            fresh_branches = []
            stale_branches = []

            for branch in branches:
                try:
                    last_commit = branch.commit
                    commit_date = datetime.fromtimestamp(last_commit.committed_date)
                    days_old = (now - commit_date).days

                    if days_old <= 30:
                        fresh_branches.append((branch.name, days_old))
                    elif days_old > 90:
                        stale_branches.append((branch.name, days_old))

                except Exception:
                    continue

            # Create results for fresh branches
            if fresh_branches:
                insight = f"Fresh branches (≤30 days): {len(fresh_branches)}"
                result = SearchResult(
                    commit_hash="branch_analysis",
                    file_path="branches/fresh_branches.txt",
                    line_number=1,
                    matching_line=insight,
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=0.9,
                    match_context={
                        "analysis_type": "branch_freshness",
                        "category": "fresh",
                        "count": len(fresh_branches),
                        "branches": fresh_branches[:5],  # Top 5
                    },
                )
                results.append(result)

            # Create results for stale branches
            if stale_branches:
                insight = f"Stale branches (>90 days): {len(stale_branches)}"
                result = SearchResult(
                    commit_hash="branch_analysis",
                    file_path="branches/stale_branches.txt",
                    line_number=1,
                    matching_line=insight,
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=0.6,
                    match_context={
                        "analysis_type": "branch_freshness",
                        "category": "stale",
                        "count": len(stale_branches),
                        "branches": stale_branches[:5],  # Top 5
                    },
                )
                results.append(result)

        except Exception:
            pass

        return results

    def _get_ahead_behind_info(self, repo: Any, branch: Any) -> Dict[str, int]:
        """Get ahead/behind information for a branch relative to main/master."""
        try:
            # Try to find main or master branch
            main_branch = None
            for ref_name in ["main", "master"]:
                try:
                    main_branch = repo.heads[ref_name]
                    break
                except Exception:
                    continue

            if not main_branch or main_branch == branch:
                return {"ahead": 0, "behind": 0}

            # Calculate ahead/behind
            ahead = len(list(repo.iter_commits(f"{main_branch.name}..{branch.name}")))
            behind = len(list(repo.iter_commits(f"{branch.name}..{main_branch.name}")))

            return {"ahead": ahead, "behind": behind}

        except Exception:
            return {"ahead": 0, "behind": 0}

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
