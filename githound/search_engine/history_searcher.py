"""Temporal and historical analysis searchers for GitHound."""

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    from ._pandas_compat import mock_pd
    pd = mock_pd

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class HistorySearcher(CacheableSearcher):
    """Searcher focused on temporal patterns and trends in repository history."""

    def __init__(self) -> None:
        super().__init__("history", "history")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle temporal queries."""
        # Handle queries with date ranges or temporal analysis requests
        return (
            query.date_from is not None or 
            query.date_to is not None or
            hasattr(query, 'temporal_analysis') and query.temporal_analysis
        )

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on date range and repository size."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=3000))
            return min(len(commits), 3000)
        except Exception:
            return 800

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform temporal analysis and return historical insights."""
        self._report_progress(context, "Starting temporal analysis...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "temporal_analysis")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached temporal results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform temporal analysis
        results: list[SearchResult] = []
        
        # Collect temporal data
        self._report_progress(context, "Collecting temporal data...", 0.2)
        temporal_data = await self._collect_temporal_data(context)
        
        # Analyze trends
        self._report_progress(context, "Analyzing activity trends...", 0.4)
        trend_results = await self._analyze_activity_trends(temporal_data, context)
        results.extend(trend_results)
        
        # Analyze release patterns
        self._report_progress(context, "Analyzing release patterns...", 0.6)
        release_results = await self._analyze_release_patterns(temporal_data, context)
        results.extend(release_results)
        
        # Analyze development cycles
        self._report_progress(context, "Analyzing development cycles...", 0.8)
        cycle_results = await self._analyze_development_cycles(temporal_data, context)
        results.extend(cycle_results)

        # Cache results
        await self._set_cache(context, cache_key, results)
        
        # Yield results
        for result in results:
            yield result
            
        self._report_progress(context, "Temporal analysis completed", 1.0)

    async def _collect_temporal_data(self, context: SearchContext) -> dict[str, Any]:
        """Collect temporal data from repository history."""
        branch = context.branch or context.repo.active_branch.name
        query = context.query
        
        commits_data = []
        tags_data = []
        
        # Filter commits by date range if specified
        since = query.date_from
        until = query.date_to
        
        commits_processed = 0
        for commit in context.repo.iter_commits(branch, since=since, until=until):
            commits_processed += 1
            if commits_processed > 3000:  # Limit for performance
                break
                
            commit_date = datetime.fromtimestamp(commit.committed_date)
            
            commit_info = {
                'hash': commit.hexsha,
                'short_hash': commit.hexsha[:8],
                'author_name': commit.author.name,
                'author_email': commit.author.email,
                'date': commit_date,
                'message': commit.message.strip(),
                'files_changed': len(commit.stats.files),
                'insertions': commit.stats.total.get('insertions', 0),
                'deletions': commit.stats.total.get('deletions', 0),
                'hour': commit_date.hour,
                'day_of_week': commit_date.weekday(),
                'week': commit_date.isocalendar()[1],
                'month': commit_date.month,
                'year': commit_date.year,
                'quarter': (commit_date.month - 1) // 3 + 1,
            }
            commits_data.append(commit_info)

        # Collect tag information for release analysis
        try:
            for tag in context.repo.tags:
                try:
                    tag_commit = tag.commit
                    tag_date = datetime.fromtimestamp(tag_commit.committed_date)
                    
                    tag_info = {
                        'name': tag.name,
                        'commit_hash': tag_commit.hexsha,
                        'date': tag_date,
                        'message': tag.tag.message if hasattr(tag, 'tag') and tag.tag else '',
                    }
                    tags_data.append(tag_info)
                except Exception:
                    # Skip problematic tags
                    continue
        except Exception:
            # Repository might not have tags
            pass

        self._update_metrics(total_commits_searched=commits_processed)
        
        return {
            'commits': pd.DataFrame(commits_data) if commits_data else pd.DataFrame(),
            'tags': pd.DataFrame(tags_data) if tags_data else pd.DataFrame(),
        }

    async def _analyze_activity_trends(self, temporal_data: dict[str, Any], context: SearchContext) -> list[SearchResult]:
        """Analyze activity trends over time."""
        results: list[SearchResult] = []
        commits_df = temporal_data['commits']
        
        if commits_df.empty:
            return results

        # Monthly activity trends
        monthly_activity = commits_df.groupby(['year', 'month']).agg({
            'hash': 'count',
            'insertions': 'sum',
            'deletions': 'sum',
            'files_changed': 'sum'
        }).reset_index()
        monthly_activity.columns = ['year', 'month', 'commits', 'insertions', 'deletions', 'files_changed']
        
        # Calculate trends
        if len(monthly_activity) > 1:
            recent_months = monthly_activity.tail(6)
            older_months = monthly_activity.head(max(1, len(monthly_activity) - 6))
            
            recent_avg_commits = recent_months['commits'].mean()
            older_avg_commits = older_months['commits'].mean()
            
            trend_direction = "increasing" if recent_avg_commits > older_avg_commits else "decreasing"
            trend_percentage = abs((recent_avg_commits - older_avg_commits) / older_avg_commits * 100) if older_avg_commits > 0 else 0
        else:
            trend_direction = "stable"
            trend_percentage = 0

        # Weekly patterns
        weekly_activity = commits_df.groupby('day_of_week')['hash'].count()
        most_active_day = weekly_activity.idxmax()
        least_active_day = weekly_activity.idxmin()
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Hourly patterns
        hourly_activity = commits_df.groupby('hour')['hash'].count()
        peak_hour = hourly_activity.idxmax()
        quiet_hour = hourly_activity.idxmin()

        # Generate insights
        insights = [
            f"Activity trend: {trend_direction} by {trend_percentage:.1f}% over recent months",
            f"Most active day: {day_names[most_active_day]} ({weekly_activity[most_active_day]} commits)",
            f"Least active day: {day_names[least_active_day]} ({weekly_activity[least_active_day]} commits)",
            f"Peak activity hour: {peak_hour}:00 ({hourly_activity[peak_hour]} commits)",
            f"Quietest hour: {quiet_hour}:00 ({hourly_activity[quiet_hour]} commits)",
            f"Total commits analyzed: {len(commits_df)}",
            f"Date range: {commits_df['date'].min().strftime('%Y-%m-%d')} to {commits_df['date'].max().strftime('%Y-%m-%d')}",
        ]
        
        for i, insight in enumerate(insights):
            result = SearchResult(
                commit_hash="temporal_analysis",
                file_path=Path(f"history/activity_trends_{i}.txt"),
                line_number=1,
                matching_line=insight,
                commit_info=None,
                search_type=SearchType.DATE_RANGE,
                relevance_score=1.0,
                match_context={
                    "analysis_type": "activity_trends",
                    "insight": insight,
                    "data_points": len(commits_df)
                }
            )
            results.append(result)
        
        return results

    async def _analyze_release_patterns(self, temporal_data: dict[str, Any], context: SearchContext) -> list[SearchResult]:
        """Analyze release patterns and cycles."""
        results: list[SearchResult] = []
        tags_df = temporal_data['tags']
        commits_df = temporal_data['commits']
        
        if tags_df.empty:
            # No tags found, analyze based on commit patterns
            result = SearchResult(
                commit_hash="temporal_analysis",
                file_path=Path("history/release_patterns_0.txt"),
                line_number=1,
                matching_line="No release tags found in repository",
                commit_info=None,
                search_type=SearchType.DATE_RANGE,
                relevance_score=0.5,
                match_context={
                    "analysis_type": "release_patterns",
                    "insight": "No release tags found",
                    "data_points": 0
                }
            )
            results.append(result)
            return results

        # Sort tags by date
        tags_df = tags_df.sort_values('date')
        
        # Calculate release intervals
        if len(tags_df) > 1:
            tags_df['prev_date'] = tags_df['date'].shift(1)
            tags_df['interval_days'] = (tags_df['date'] - tags_df['prev_date']).dt.days
            
            avg_interval = tags_df['interval_days'].mean()
            median_interval = tags_df['interval_days'].median()
            
            # Recent release activity
            recent_releases = tags_df[tags_df['date'] > datetime.now() - timedelta(days=365)]
            releases_this_year = len(recent_releases)
        else:
            avg_interval = 0
            median_interval = 0
            releases_this_year = len(tags_df)

        # Generate insights
        insights = [
            f"Total releases: {len(tags_df)}",
            f"Releases in last year: {releases_this_year}",
            f"Latest release: {tags_df.iloc[-1]['name']} ({tags_df.iloc[-1]['date'].strftime('%Y-%m-%d')})",
        ]
        
        if len(tags_df) > 1:
            insights.extend([
                f"Average release interval: {avg_interval:.1f} days",
                f"Median release interval: {median_interval:.1f} days",
                f"First release: {tags_df.iloc[0]['name']} ({tags_df.iloc[0]['date'].strftime('%Y-%m-%d')})",
            ])
        
        for i, insight in enumerate(insights):
            result = SearchResult(
                commit_hash="temporal_analysis",
                file_path=Path(f"history/release_patterns_{i}.txt"),
                line_number=1,
                matching_line=insight,
                commit_info=None,
                search_type=SearchType.DATE_RANGE,
                relevance_score=1.0,
                match_context={
                    "analysis_type": "release_patterns",
                    "insight": insight,
                    "data_points": len(tags_df)
                }
            )
            results.append(result)
        
        return results

    async def _analyze_development_cycles(self, temporal_data: dict[str, Any], context: SearchContext) -> list[SearchResult]:
        """Analyze development cycles and patterns."""
        results: list[SearchResult] = []
        commits_df = temporal_data['commits']
        
        if commits_df.empty:
            return results

        # Quarterly analysis
        quarterly_activity = commits_df.groupby(['year', 'quarter']).agg({
            'hash': 'count',
            'insertions': 'sum',
            'deletions': 'sum'
        }).reset_index()
        quarterly_activity.columns = ['year', 'quarter', 'commits', 'insertions', 'deletions']
        
        # Find most/least active quarters
        if not quarterly_activity.empty:
            most_active_quarter = quarterly_activity.loc[quarterly_activity['commits'].idxmax()]
            least_active_quarter = quarterly_activity.loc[quarterly_activity['commits'].idxmin()]
        
        # Author activity cycles
        author_monthly = commits_df.groupby(['author_name', 'year', 'month']).size().reset_index()
        author_monthly.columns = ['author', 'year', 'month', 'commits']
        
        # Identify development phases (periods of high/low activity)
        monthly_commits = commits_df.groupby(['year', 'month']).size()
        if len(monthly_commits) > 3:
            # Simple moving average to identify trends
            rolling_avg = monthly_commits.rolling(window=3).mean()
            high_activity_threshold = rolling_avg.quantile(0.75)
            low_activity_threshold = rolling_avg.quantile(0.25)
            
            high_activity_periods = rolling_avg[rolling_avg > high_activity_threshold]
            low_activity_periods = rolling_avg[rolling_avg < low_activity_threshold]
        else:
            high_activity_periods = pd.Series([], dtype=float)
            low_activity_periods = pd.Series([], dtype=float)

        # Generate insights
        insights = [
            f"Development span: {commits_df['date'].min().strftime('%Y-%m-%d')} to {commits_df['date'].max().strftime('%Y-%m-%d')}",
        ]
        
        if not quarterly_activity.empty:
            insights.extend([
                f"Most active quarter: Q{most_active_quarter['quarter']} {most_active_quarter['year']} ({most_active_quarter['commits']} commits)",
                f"Least active quarter: Q{least_active_quarter['quarter']} {least_active_quarter['year']} ({least_active_quarter['commits']} commits)",
            ])
        
        insights.extend([
            f"High activity periods identified: {len(high_activity_periods)}",
            f"Low activity periods identified: {len(low_activity_periods)}",
            f"Unique contributors: {commits_df['author_name'].nunique()}",
        ])
        
        for i, insight in enumerate(insights):
            result = SearchResult(
                commit_hash="temporal_analysis",
                file_path=Path(f"history/development_cycles_{i}.txt"),
                line_number=1,
                matching_line=insight,
                commit_info=None,
                search_type=SearchType.DATE_RANGE,
                relevance_score=1.0,
                match_context={
                    "analysis_type": "development_cycles",
                    "insight": insight,
                    "data_points": len(commits_df)
                }
            )
            results.append(result)
        
        return results
