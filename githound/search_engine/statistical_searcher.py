"""Statistical analysis searchers for GitHound."""

import asyncio
from collections import Counter, defaultdict
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    from ._pandas_compat import mock_pd
    pd = mock_pd

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class StatisticalSearcher(CacheableSearcher):
    """Searcher that provides statistical analysis of repository data."""

    def __init__(self) -> None:
        super().__init__("statistical", "stats")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle statistical queries."""
        # Handle queries that request statistical analysis
        # This could be extended to support specific statistical query syntax
        return hasattr(query, 'statistical_analysis') and query.statistical_analysis

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=5000))
            return min(len(commits), 5000)
        except Exception:
            return 1000

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform statistical analysis and return insights as search results."""
        self._report_progress(context, "Starting statistical analysis...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "statistical_analysis")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached statistical results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform statistical analysis
        results: list[SearchResult] = []
        
        # Collect repository data
        self._report_progress(context, "Collecting repository data...", 0.2)
        repo_data = await self._collect_repository_data(context)
        
        # Generate statistical insights
        self._report_progress(context, "Analyzing commit patterns...", 0.4)
        commit_stats = await self._analyze_commit_patterns(repo_data, context)
        results.extend(commit_stats)
        
        self._report_progress(context, "Analyzing author statistics...", 0.6)
        author_stats = await self._analyze_author_statistics(repo_data, context)
        results.extend(author_stats)
        
        self._report_progress(context, "Analyzing file change patterns...", 0.8)
        file_stats = await self._analyze_file_patterns(repo_data, context)
        results.extend(file_stats)

        # Cache results
        await self._set_cache(context, cache_key, results)
        
        # Yield results
        for result in results:
            yield result
            
        self._report_progress(context, "Statistical analysis completed", 1.0)

    async def _collect_repository_data(self, context: SearchContext) -> dict[str, Any]:
        """Collect comprehensive repository data for analysis."""
        branch = context.branch or context.repo.active_branch.name
        
        commits_data = []
        files_data = []
        authors_data = []
        
        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 5000:  # Limit for performance
                break
                
            commit_date = datetime.fromtimestamp(commit.committed_date)
            
            # Collect commit data
            commit_info = {
                'hash': commit.hexsha,
                'author_name': commit.author.name,
                'author_email': commit.author.email,
                'committer_name': commit.committer.name,
                'committer_email': commit.committer.email,
                'date': commit_date,
                'message': commit.message.strip(),
                'files_changed': len(commit.stats.files),
                'insertions': commit.stats.total.get('insertions', 0),
                'deletions': commit.stats.total.get('deletions', 0),
                'hour': commit_date.hour,
                'day_of_week': commit_date.weekday(),
                'month': commit_date.month,
                'year': commit_date.year,
            }
            commits_data.append(commit_info)
            
            # Collect file data
            for file_path, file_stats in commit.stats.files.items():
                file_info = {
                    'commit_hash': commit.hexsha,
                    'file_path': file_path,
                    'insertions': file_stats.get('insertions', 0),
                    'deletions': file_stats.get('deletions', 0),
                    'lines_changed': file_stats.get('lines', 0),
                    'date': commit_date,
                    'author': commit.author.name,
                    'file_extension': self._get_file_extension(file_path),
                }
                files_data.append(file_info)
            
            # Collect author data
            author_info = {
                'name': commit.author.name,
                'email': commit.author.email,
                'commit_hash': commit.hexsha,
                'date': commit_date,
                'files_changed': len(commit.stats.files),
                'insertions': commit.stats.total.get('insertions', 0),
                'deletions': commit.stats.total.get('deletions', 0),
            }
            authors_data.append(author_info)

        self._update_metrics(total_commits_searched=commits_processed)
        
        return {
            'commits': pd.DataFrame(commits_data) if commits_data else pd.DataFrame(),
            'files': pd.DataFrame(files_data) if files_data else pd.DataFrame(),
            'authors': pd.DataFrame(authors_data) if authors_data else pd.DataFrame(),
        }

    async def _analyze_commit_patterns(self, repo_data: dict[str, Any], context: SearchContext) -> list[SearchResult]:
        """Analyze commit patterns and generate insights."""
        results: list[SearchResult] = []
        commits_df = repo_data['commits']
        
        if commits_df.empty:
            return results

        # Commit frequency analysis
        daily_commits = commits_df.groupby(commits_df['date'].dt.date).size()
        avg_commits_per_day = daily_commits.mean()
        
        # Peak activity hours
        hourly_commits = commits_df.groupby('hour').size()
        peak_hour = hourly_commits.idxmax()
        
        # Day of week patterns
        dow_commits = commits_df.groupby('day_of_week').size()
        peak_day = dow_commits.idxmax()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Commit size patterns
        avg_files_per_commit = commits_df['files_changed'].mean()
        avg_insertions = commits_df['insertions'].mean()
        avg_deletions = commits_df['deletions'].mean()
        
        # Create statistical insights as search results
        insights = [
            f"Average commits per day: {avg_commits_per_day:.2f}",
            f"Peak activity hour: {peak_hour}:00",
            f"Most active day: {day_names[peak_day]}",
            f"Average files per commit: {avg_files_per_commit:.2f}",
            f"Average insertions per commit: {avg_insertions:.2f}",
            f"Average deletions per commit: {avg_deletions:.2f}",
        ]
        
        for i, insight in enumerate(insights):
            result = SearchResult(
                commit_hash="statistical_analysis",
                file_path=Path(f"stats/commit_patterns_{i}.txt"),
                line_number=1,
                matching_line=insight,
                commit_info=None,
                search_type=SearchType.COMBINED,
                relevance_score=1.0,
                match_context={
                    "analysis_type": "commit_patterns",
                    "insight": insight,
                    "data_points": len(commits_df)
                }
            )
            results.append(result)
        
        return results

    async def _analyze_author_statistics(self, repo_data: dict[str, Any], context: SearchContext) -> list[SearchResult]:
        """Analyze author statistics and contributions."""
        results: list[SearchResult] = []
        authors_df = repo_data['authors']
        
        if authors_df.empty:
            return results

        # Author contribution analysis
        author_commits = authors_df.groupby('name').size().sort_values(ascending=False)
        author_insertions = authors_df.groupby('name')['insertions'].sum().sort_values(ascending=False)
        author_deletions = authors_df.groupby('name')['deletions'].sum().sort_values(ascending=False)
        
        # Top contributors
        top_contributors = author_commits.head(10)
        
        # Author activity patterns
        author_activity = authors_df.groupby(['name', authors_df['date'].dt.date]).size().reset_index()
        author_activity.columns = ['author', 'date', 'commits']
        
        # Generate insights
        insights = [
            f"Total unique authors: {len(author_commits)}",
            f"Most active author: {top_contributors.index[0]} ({top_contributors.iloc[0]} commits)",
            f"Top contributor by insertions: {author_insertions.index[0]} ({author_insertions.iloc[0]} lines)",
            f"Top contributor by deletions: {author_deletions.index[0]} ({author_deletions.iloc[0]} lines)",
        ]
        
        # Add top 5 contributors
        for i, (author, commits) in enumerate(top_contributors.head(5).items()):
            insights.append(f"#{i+1} contributor: {author} ({commits} commits)")
        
        for i, insight in enumerate(insights):
            result = SearchResult(
                commit_hash="statistical_analysis",
                file_path=Path(f"stats/author_statistics_{i}.txt"),
                line_number=1,
                matching_line=insight,
                commit_info=None,
                search_type=SearchType.COMBINED,
                relevance_score=1.0,
                match_context={
                    "analysis_type": "author_statistics",
                    "insight": insight,
                    "data_points": len(authors_df)
                }
            )
            results.append(result)
        
        return results

    async def _analyze_file_patterns(self, repo_data: dict[str, Any], context: SearchContext) -> list[SearchResult]:
        """Analyze file change patterns and hotspots."""
        results: list[SearchResult] = []
        files_df = repo_data['files']
        
        if files_df.empty:
            return results

        # File change frequency
        file_changes = files_df.groupby('file_path').size().sort_values(ascending=False)
        
        # File extension analysis
        extension_changes = files_df.groupby('file_extension').size().sort_values(ascending=False)
        
        # File size analysis
        file_insertions = files_df.groupby('file_path')['insertions'].sum().sort_values(ascending=False)
        file_deletions = files_df.groupby('file_path')['deletions'].sum().sort_values(ascending=False)
        
        # Hotspot analysis (files changed most frequently)
        hotspots = file_changes.head(10)
        
        # Generate insights
        insights = [
            f"Total files tracked: {len(file_changes)}",
            f"Most changed file: {hotspots.index[0]} ({hotspots.iloc[0]} changes)",
            f"Most common file type: {extension_changes.index[0]} ({extension_changes.iloc[0]} changes)",
            f"File with most insertions: {file_insertions.index[0]} ({file_insertions.iloc[0]} lines)",
            f"File with most deletions: {file_deletions.index[0]} ({file_deletions.iloc[0]} lines)",
        ]
        
        # Add top 5 hotspots
        for i, (file_path, changes) in enumerate(hotspots.head(5).items()):
            insights.append(f"Hotspot #{i+1}: {file_path} ({changes} changes)")
        
        for i, insight in enumerate(insights):
            result = SearchResult(
                commit_hash="statistical_analysis",
                file_path=Path(f"stats/file_patterns_{i}.txt"),
                line_number=1,
                matching_line=insight,
                commit_info=None,
                search_type=SearchType.COMBINED,
                relevance_score=1.0,
                match_context={
                    "analysis_type": "file_patterns",
                    "insight": insight,
                    "data_points": len(files_df)
                }
            )
            results.append(result)
        
        return results

    def _get_file_extension(self, file_path: str) -> str:
        """Extract file extension from file path."""
        if '.' in file_path:
            return file_path.split('.')[-1].lower()
        return 'no_extension'
