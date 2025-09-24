#!/usr/bin/env python3
"""
Git Repository Analysis Examples

This example demonstrates comprehensive Git repository analysis using GitHound's
core functionality including metadata extraction, commit analysis, and statistics.

Usage:
    python examples/git_operations/repository_analysis.py /path/to/repository

This example covers:
- Repository metadata extraction
- Commit history analysis
- Author statistics and contributions
- Branch and tag analysis
- Repository health metrics
- Performance considerations
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

from githound.git_handler import (
    get_repository, get_repository_metadata, extract_commit_metadata,
    get_commits_with_filters
)
from githound.git_blame import get_author_statistics
from githound.models import CommitInfo


# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """Comprehensive repository analysis tool."""

    def __init__(self, repo_path: str) -> None:
        """Initialize analyzer with repository path."""
        self.repo_path = Path(repo_path)
        self.repo = None
        self.analysis_results: Dict[str, Any] = {
            "repository_path": str(repo_path),
            "analysis_timestamp": datetime.now().isoformat()
        }

    def load_repository(self) -> bool:
        """Load and validate the repository."""
        logger.info(f"Loading repository from: {self.repo_path}")

        try:
            self.repo = get_repository(self.repo_path)
            logger.info("✓ Repository loaded successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to load repository: {e}")
            self.analysis_results["error"] = str(e)
            return False

    def analyze_repository_metadata(self) -> Dict[str, Any]:
        """Analyze basic repository metadata."""
        logger.info("\n=== Repository Metadata Analysis ===")

        if not self.repo:
            return {"error": "Repository not loaded"}

        try:
            metadata = get_repository_metadata(self.repo)

            logger.info(f"Repository Name: {metadata.get if metadata is not None else None('name', 'N/A')}")
            logger.info(f"Total Commits: {metadata.get if metadata is not None else None('total_commits', 0)}")
            logger.info(f"Total Branches: {metadata.get if metadata is not None else None('total_branches', 0)}")
            logger.info(f"Total Tags: {metadata.get if metadata is not None else None('total_tags', 0)}")
            logger.info(f"Contributors: {len(metadata.get if metadata is not None else None('contributors', []))}")

            # Latest commit info
            latest_commit = metadata.get('latest_commit')
            if latest_commit:
                logger.info(f"Latest Commit: {latest_commit.get if latest_commit is not None else None('hash', 'N/A')[:8]}")
                logger.info(f"Latest Author: {latest_commit.get if latest_commit is not None else None('author_name', 'N/A')}")
                logger.info(f"Latest Date: {latest_commit.get if latest_commit is not None else None('date', 'N/A')}")

            # Repository age
            creation_date = metadata.get('creation_date')
            if creation_date:
                try:
                    created = datetime.fromisoformat(creation_date.replace if creation_date is not None else None('Z', '+00:00'))
                    age_days = (datetime.now().replace(tzinfo=created.tzinfo) - created).days
                    logger.info(f"Repository Age: {age_days} days")
                    metadata['age_days'] = age_days
                except:
                    pass

            self.analysis_results['metadata'] = metadata
            return metadata

        except Exception as e:
            logger.error(f"✗ Metadata analysis failed: {e}")
            return {"error": str(e)}

    def analyze_commit_history(self, max_commits: int = 100) -> Dict[str, Any]:
        """Analyze commit history patterns."""
        logger.info(f"\n=== Commit History Analysis (last {max_commits} commits) ===")

        if not self.repo:
            return {"error": "Repository not loaded"}

        try:
            # Get recent commits
            commits = get_commits_with_filters(
                repo=self.repo,
                max_count=max_commits
            )

            commit_list: list[Any] = []
            commit_stats = {
                "total_analyzed": 0,
                "authors": set(),
                "files_changed": set(),
                "total_insertions": 0,
                "total_deletions": 0,
                "commit_messages": [],
                "dates": []
            }

            for commit in commits:
                try:
                    commit_info = extract_commit_metadata(commit)
                    commit_data = commit_info.model_dump()
                    commit_list.append(commit_data)

                    # Update statistics
                    commit_stats["total_analyzed"] += 1
                    commit_stats["authors"].add(commit_info.author_name)
                    commit_stats["total_insertions"] += commit_info.insertions
                    commit_stats["total_deletions"] += commit_info.deletions
                    commit_stats["commit_messages"].append(commit_info.message)
                    commit_stats["dates"].append(commit_info.timestamp)

                    # Track files changed
                    for file_path in commit_info.files_changed:
                        commit_stats["files_changed"].add(file_path)

                except Exception as e:
                    logger.warning(f"Failed to process commit {commit.hexsha[:8]}: {e}")
                    continue

            # Convert sets to lists for JSON serialization
            commit_stats["authors"] = list(commit_stats["authors"])
            commit_stats["files_changed"] = list(commit_stats["files_changed"])

            # Calculate additional metrics
            if commit_stats["total_analyzed"] > 0:
                commit_stats["avg_insertions"] = commit_stats["total_insertions"] / commit_stats["total_analyzed"]
                commit_stats["avg_deletions"] = commit_stats["total_deletions"] / commit_stats["total_analyzed"]
                commit_stats["unique_authors"] = len(commit_stats["authors"])
                commit_stats["unique_files"] = len(commit_stats["files_changed"])

            logger.info(f"Analyzed Commits: {commit_stats['total_analyzed']}")
            logger.info(f"Unique Authors: {commit_stats['unique_authors']}")
            logger.info(f"Files Modified: {commit_stats['unique_files']}")
            logger.info(f"Total Insertions: {commit_stats['total_insertions']}")
            logger.info(f"Total Deletions: {commit_stats['total_deletions']}")

            if commit_stats['total_analyzed'] > 0:
                logger.info(f"Avg Insertions/Commit: {commit_stats['avg_insertions']:.1f}")
                logger.info(f"Avg Deletions/Commit: {commit_stats['avg_deletions']:.1f}")

            # Analyze commit frequency
            commit_frequency = self._analyze_commit_frequency(commit_stats["dates"])
            commit_stats.update(commit_frequency)

            result = {
                "commits": commit_list,
                "statistics": commit_stats
            }

            self.analysis_results['commit_history'] = result
            return result

        except Exception as e:
            logger.error(f"✗ Commit history analysis failed: {e}")
            return {"error": str(e)}

    def _analyze_commit_frequency(self, commit_dates: List[str]) -> Dict[str, Any]:
        """Analyze commit frequency patterns."""
        if not commit_dates:
            return {}

        try:
            # Parse dates
            parsed_dates: list[Any] = []
            for date_str in commit_dates:
                try:
                    # Handle different date formats
                    if 'T' in date_str:
                        date = datetime.fromisoformat(date_str.replace if date_str is not None else None('Z', '+00:00'))
                    else:
                        date = datetime.fromisoformat(date_str)
                    parsed_dates.append(date)
                except:
                    continue

            if not parsed_dates:
                return {}

            # Calculate frequency metrics
            parsed_dates.sort()
            date_range = (parsed_dates[0], parsed_dates[-1])
            total_days = (date_range[1] - date_range[0]).days + 1

            # Group by day of week
            weekday_counts = [0] * 7  # Monday = 0, Sunday = 6
            for date in parsed_dates:
                weekday_counts[date.weekday()] += 1

            # Group by hour
            hour_counts = [0] * 24
            for date in parsed_dates:
                hour_counts[date.hour] += 1

            return {
                "date_range": {
                    "start": date_range[0].isoformat(),
                    "end": date_range[1].isoformat(),
                    "total_days": total_days
                },
                "commits_per_day": len(parsed_dates) / max(total_days, 1),
                "weekday_distribution": {
                    "Monday": weekday_counts[0],
                    "Tuesday": weekday_counts[1],
                    "Wednesday": weekday_counts[2],
                    "Thursday": weekday_counts[3],
                    "Friday": weekday_counts[4],
                    "Saturday": weekday_counts[5],
                    "Sunday": weekday_counts[6]
                },
                "hour_distribution": dict(enumerate(hour_counts)),
                "most_active_weekday": ["Monday", "Tuesday", "Wednesday", "Thursday",
                                       "Friday", "Saturday", "Sunday"][weekday_counts.index(max(weekday_counts))],
                "most_active_hour": hour_counts.index(max(hour_counts))
            }

        except Exception as e:
            logger.warning(f"Failed to analyze commit frequency: {e}")
            return {}

    def analyze_author_contributions(self) -> Dict[str, Any]:
        """Analyze author contributions and statistics."""
        logger.info("\n=== Author Contribution Analysis ===")

        if not self.repo:
            return {"error": "Repository not loaded"}

        try:
            author_stats = get_author_statistics(self.repo)

            # Sort authors by commit count
            sorted_authors = sorted(
                author_stats.items(),
                key=lambda x: x[1].get('total_commits', 0),
                reverse=True
            )

            logger.info(f"Total Authors: {len(author_stats)}")

            # Show top contributors
            logger.info("Top Contributors:")
            for i, (author, stats) in enumerate(sorted_authors[:10]):
                commits = stats.get('total_commits', 0)
                files = stats.get('total_files', 0)
                logger.info(f"  {i+1:2d}. {author}: {commits} commits, {files} files")

            # Calculate contribution distribution
            total_commits = sum(stats.get('total_commits', 0) for stats in author_stats.values())

            contribution_analysis = {
                "total_authors": len(author_stats),
                "total_commits": total_commits,
                "top_contributors": []
            }

            for author, stats in sorted_authors[:10]:
                commits = stats.get('total_commits', 0)
                percentage = (commits / total_commits * 100) if total_commits > 0 else 0

                contribution_analysis["top_contributors"].append({
                    "author": author,
                    "commits": commits,
                    "files": stats.get('total_files', 0),
                    "percentage": round(percentage, 2)
                })

            # Analyze contribution patterns
            if len(sorted_authors) > 1:
                top_contributor_commits = sorted_authors[0][1].get('total_commits', 0)
                contribution_analysis["top_contributor_dominance"] = round(
                    (top_contributor_commits / total_commits * 100), 2
                ) if total_commits > 0 else 0

                # Bus factor (simplified): number of contributors needed for 50% of commits
                cumulative_commits = 0
                bus_factor = 0
                for author, stats in sorted_authors:
                    cumulative_commits += stats.get('total_commits', 0)
                    bus_factor += 1
                    if cumulative_commits >= total_commits * 0.5:
                        break

                contribution_analysis["bus_factor"] = bus_factor

            result = {
                "author_statistics": author_stats,
                "contribution_analysis": contribution_analysis
            }

            self.analysis_results['author_contributions'] = result
            return result

        except Exception as e:
            logger.error(f"✗ Author contribution analysis failed: {e}")
            return {"error": str(e)}

    def analyze_repository_health(self) -> Dict[str, Any]:
        """Analyze repository health metrics."""
        logger.info("\n=== Repository Health Analysis ===")

        health_metrics = {
            "overall_score": 0,
            "factors": {}
        }

        try:
            # Factor 1: Recent activity (last 30 days)
            recent_date = datetime.now() - timedelta(days=30)
            recent_commits = list(self.repo.iter_commits(since=recent_date))

            recent_activity_score = min(len(recent_commits) / 10, 1.0) * 100  # Max 100 for 10+ commits
            health_metrics["factors"]["recent_activity"] = {
                "score": round(recent_activity_score, 1),
                "commits_last_30_days": len(recent_commits),
                "description": "Recent development activity"
            }

            # Factor 2: Contributor diversity
            metadata = self.analysis_results.get('metadata', {})
            contributors_count = len(metadata.get('contributors', []))

            diversity_score = min(contributors_count / 5, 1.0) * 100  # Max 100 for 5+ contributors
            health_metrics["factors"]["contributor_diversity"] = {
                "score": round(diversity_score, 1),
                "total_contributors": contributors_count,
                "description": "Number of different contributors"
            }

            # Factor 3: Commit frequency consistency
            commit_history = self.analysis_results.get('commit_history', {})
            commit_stats = commit_history.get('statistics', {})
            commits_per_day = commit_stats.get('commits_per_day', 0)

            frequency_score = min(commits_per_day * 50, 100)  # Max 100 for 2+ commits/day
            health_metrics["factors"]["commit_frequency"] = {
                "score": round(frequency_score, 1),
                "commits_per_day": round(commits_per_day, 2),
                "description": "Consistency of development activity"
            }

            # Calculate overall score
            scores = [factor["score"] for factor in health_metrics["factors"].values()]
            health_metrics["overall_score"] = round(sum(scores) / len(scores), 1)

            # Health assessment
            if health_metrics["overall_score"] >= 80:
                health_status = "Excellent"
            elif health_metrics["overall_score"] >= 60:
                health_status = "Good"
            elif health_metrics["overall_score"] >= 40:
                health_status = "Fair"
            else:
                health_status = "Needs Attention"

            health_metrics["status"] = health_status

            logger.info(f"Overall Health Score: {health_metrics['overall_score']}/100 ({health_status})")
            logger.info("Health Factors:")
            for factor_name, factor_data in health_metrics["factors"].items():
                logger.info(f"  {factor_name}: {factor_data['score']}/100 - {factor_data['description']}")

            self.analysis_results['repository_health'] = health_metrics
            return health_metrics

        except Exception as e:
            logger.error(f"✗ Repository health analysis failed: {e}")
            return {"error": str(e)}

    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        logger.info("\n=== Summary Report ===")

        report_lines = [
            "# GitHound Repository Analysis Report",
            f"**Repository:** {self.repo_path}",
            f"**Analysis Date:** {self.analysis_results['analysis_timestamp']}",
            ""
        ]

        # Metadata summary
        metadata = self.analysis_results.get('metadata', {})
        if metadata and 'error' not in metadata:
            report_lines.extend([
                "## Repository Overview",
                f"- **Total Commits:** {metadata.get if metadata is not None else None('total_commits', 'N/A')}",
                f"- **Branches:** {metadata.get('total_branches', 'N/A')}",
                f"- **Tags:** {metadata.get('total_tags', 'N/A')}",
                f"- **Contributors:** {len(metadata.get('contributors', []))}",
                f"- **Age:** {metadata.get('age_days', 'N/A')} days",
                ""
            ])

        # Health summary
        health = self.analysis_results.get('repository_health', {})
        if health and 'error' not in health:
            report_lines.extend([
                "## Repository Health",
                f"- **Overall Score:** {health.get if health is not None else None('overall_score', 'N/A')}/100",
                f"- **Status:** {health.get('status', 'N/A')}",
                ""
            ])

        # Author contributions
        contributions = self.analysis_results.get('author_contributions', {})
        if contributions and 'error' not in contributions:
            analysis = contributions.get('contribution_analysis', {})
            top_contributors = analysis.get('top_contributors', [])

            if top_contributors:
                report_lines.extend([
                    "## Top Contributors",
                ])

                for i, contributor in enumerate(top_contributors[:5]):
                    author = contributor.get('author', 'N/A')
                    commits = contributor.get('commits', 0)
                    percentage = contributor.get('percentage', 0)
                    report_lines.append(f"{i+1}. **{author}:** {commits} commits ({percentage}%)")

                report_lines.append("")

        report = "\n".join(report_lines)
        logger.info("Summary report generated")

        return report


async def main() -> None:
    """Main analysis function."""

    if len(sys.argv) != 2:
        print("Usage: python repository_analysis.py /path/to/repository")
        sys.exit(1)

    repo_path = sys.argv[1]

    if not Path(repo_path).exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)

    print("=" * 70)
    print("GitHound - Comprehensive Repository Analysis")
    print("=" * 70)
    print(f"Repository: {repo_path}")
    print()

    analyzer = RepositoryAnalyzer(repo_path)

    try:
        # Load repository
        if not analyzer.load_repository():
            sys.exit(1)

        # Run all analyses
        analyzer.analyze_repository_metadata()
        analyzer.analyze_commit_history()
        analyzer.analyze_author_contributions()
        analyzer.analyze_repository_health()

        # Generate summary report
        summary_report = analyzer.generate_summary_report()

        print("\n" + "=" * 70)
        print("Repository analysis completed successfully!")
        print("=" * 70)

        # Save results
        output_file = f"repository_analysis_{Path(repo_path).name}.json"
        with open(output_file, 'w') as f:
            json.dump(analyzer.analysis_results, f, indent=2, default=str)

        # Save summary report
        report_file = f"repository_summary_{Path(repo_path).name}.md"
        with open(report_file, 'w') as f:
            f.write(summary_report)

        print(f"\nDetailed results saved to: {output_file}")
        print(f"Summary report saved to: {report_file}")

    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
