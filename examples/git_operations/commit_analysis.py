#!/usr/bin/env python3
"""
Git Commit Analysis Examples

This example demonstrates detailed commit analysis using GitHound's functionality
including commit metadata extraction, history filtering, and commit comparisons.

Usage:
    python examples/git_operations/commit_analysis.py /path/to/repository [commit_hash]

This example covers:
- Individual commit metadata extraction
- Commit history filtering and analysis
- Commit comparison and diff analysis
- File change tracking across commits
- Author and date-based filtering
- Commit message analysis patterns
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

from githound.git_handler import (
    get_repository, extract_commit_metadata, get_commits_with_filters
)
from githound.git_diff import compare_commits
from githound.models import CommitInfo


# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommitAnalyzer:
    """Comprehensive commit analysis tool."""
    
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
    
    def analyze_specific_commit(self, commit_hash: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a specific commit in detail."""
        logger.info("\n=== Specific Commit Analysis ===")
        
        if not self.repo:
            return {"error": "Repository not loaded"}
        
        try:
            # Get commit object
            if commit_hash:
                commit = self.repo.commit(commit_hash)
                logger.info(f"Analyzing commit: {commit_hash}")
            else:
                commit = self.repo.head.commit
                logger.info("Analyzing HEAD commit")
            
            # Extract detailed metadata
            commit_info = extract_commit_metadata(commit)
            commit_data = commit_info.model_dump()
            
            # Display basic information
            logger.info(f"Commit Hash: {commit_info.hash}")
            logger.info(f"Short Hash: {commit_info.hash[:8]}")
            logger.info(f"Author: {commit_info.author_name} <{commit_info.author_email}>")
            logger.info(f"Date: {commit_info.timestamp}")
            logger.info(f"Message: {commit_info.message}")
            
            # File changes analysis
            logger.info(f"Files Changed: {len(commit_info.files_changed)}")
            logger.info(f"Insertions: {commit_info.insertions}")
            logger.info(f"Deletions: {commit_info.deletions}")
            
            if commit_info.files_changed:
                logger.info("Changed Files:")
                for i, file_path in enumerate(commit_info.files_changed[:10]):  # Show first 10
                    logger.info(f"  {i+1}. {file_path}")
                if len(commit_info.files_changed) > 10:
                    logger.info(f"  ... and {len(commit_info.files_changed) - 10} more files")
            
            # Parent commits
            if commit_info.parent_hashes:
                logger.info(f"Parent Commits: {len(commit_info.parent_hashes)}")
                for i, parent_hash in enumerate(commit_info.parent_hashes):
                    logger.info(f"  Parent {i+1}: {parent_hash[:8]}")
            
            # Additional analysis
            commit_analysis = self._analyze_commit_patterns(commit_info)
            commit_data.update(commit_analysis)
            
            self.analysis_results['specific_commit'] = commit_data
            return commit_data
            
        except Exception as e:
            logger.error(f"✗ Commit analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_commit_patterns(self, commit_info: CommitInfo) -> Dict[str, Any]:
        """Analyze patterns in commit data."""
        analysis: dict[str, Any] = {}
        
        # Message analysis
        message = commit_info.message.lower()
        
        # Categorize commit type based on message
        if any(word in message for word in ['fix', 'bug', 'issue', 'error']):
            commit_type = "bugfix"
        elif any(word in message for word in ['feat', 'feature', 'add', 'new']):
            commit_type = "feature"
        elif any(word in message for word in ['refactor', 'cleanup', 'improve']):
            commit_type = "refactor"
        elif any(word in message for word in ['doc', 'readme', 'comment']):
            commit_type = "documentation"
        elif any(word in message for word in ['test', 'spec']):
            commit_type = "test"
        else:
            commit_type = "other"
        
        analysis['commit_type'] = commit_type
        
        # Size analysis
        total_changes = commit_info.insertions + commit_info.deletions
        if total_changes < 10:
            size_category = "small"
        elif total_changes < 100:
            size_category = "medium"
        elif total_changes < 500:
            size_category = "large"
        else:
            size_category = "very_large"
        
        analysis['size_category'] = size_category
        analysis['total_changes'] = total_changes
        
        # File type analysis
        file_types: dict[str, Any] = {}
        for file_path in commit_info.files_changed:
            ext = Path(file_path).suffix.lower()
            if not ext:
                ext = "no_extension"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        analysis['file_types'] = file_types
        
        return analysis
    
    def analyze_commit_history(self, days: int = 30, max_commits: int = 100) -> Dict[str, Any]:
        """Analyze commit history patterns over time."""
        logger.info(f"\n=== Commit History Analysis (last {days} days) ===")
        
        if not self.repo:
            return {"error": "Repository not loaded"}
        
        try:
            # Get commits from the last N days
            since_date = datetime.now() - timedelta(days=days)
            
            commits = get_commits_with_filters(
                repo=self.repo,
                max_count=max_commits,
                since=since_date
            )
            
            commit_list: list[Any] = []
            history_stats = {
                "total_commits": 0,
                "authors": {},
                "commit_types": {},
                "size_categories": {},
                "file_types": {},
                "daily_activity": {},
                "hourly_activity": [0] * 24,
                "weekday_activity": [0] * 7
            }
            
            for commit in commits:
                try:
                    commit_info = extract_commit_metadata(commit)
                    commit_data = commit_info.model_dump()
                    
                    # Add pattern analysis
                    patterns = self._analyze_commit_patterns(commit_info)
                    commit_data.update(patterns)
                    
                    commit_list.append(commit_data)
                    
                    # Update statistics
                    history_stats["total_commits"] += 1
                    
                    # Author statistics
                    author = commit_info.author_name
                    if author not in history_stats["authors"]:
                        history_stats["authors"][author] = {
                            "commits": 0,
                            "insertions": 0,
                            "deletions": 0,
                            "files": set()
                        }
                    
                    history_stats["authors"][author]["commits"] += 1
                    history_stats["authors"][author]["insertions"] += commit_info.insertions
                    history_stats["authors"][author]["deletions"] += commit_info.deletions
                    history_stats["authors"][author]["files"].update(commit_info.files_changed)
                    
                    # Commit type statistics
                    commit_type = patterns.get("commit_type", "other")
                    history_stats["commit_types"][commit_type] = history_stats["commit_types"].get(commit_type, 0) + 1
                    
                    # Size category statistics
                    size_category = patterns.get("size_category", "unknown")
                    history_stats["size_categories"][size_category] = history_stats["size_categories"].get(size_category, 0) + 1
                    
                    # File type statistics
                    for file_type, count in patterns.get("file_types", {}).items():
                        history_stats["file_types"][file_type] = history_stats["file_types"].get(file_type, 0) + count
                    
                    # Time-based statistics
                    try:
                        commit_date = datetime.fromisoformat(commit_info.timestamp.replace('Z', '+00:00'))
                        
                        # Daily activity
                        day_key = commit_date.strftime('%Y-%m-%d')
                        history_stats["daily_activity"][day_key] = history_stats["daily_activity"].get(day_key, 0) + 1
                        
                        # Hourly activity
                        history_stats["hourly_activity"][commit_date.hour] += 1
                        
                        # Weekday activity (Monday = 0)
                        history_stats["weekday_activity"][commit_date.weekday()] += 1
                        
                    except:
                        pass  # Skip time analysis if date parsing fails
                
                except Exception as e:
                    logger.warning(f"Failed to process commit {commit.hexsha[:8]}: {e}")
                    continue
            
            # Convert sets to counts for JSON serialization
            for author_data in history_stats["authors"].values():
                author_data["unique_files"] = len(author_data["files"])
                author_data["files"] = list(author_data["files"])[:10]  # Keep only first 10 for brevity
            
            # Calculate additional metrics
            if history_stats["total_commits"] > 0:
                # Most active author
                most_active_author = max(
                    history_stats["authors"].items(),
                    key=lambda x: x[1]["commits"]
                )[0] if history_stats["authors"] else "None"
                
                # Most common commit type
                most_common_type = max(
                    history_stats["commit_types"].items(),
                    key=lambda x: x[1]
                )[0] if history_stats["commit_types"] else "None"
                
                # Average commits per day
                unique_days = len(history_stats["daily_activity"])
                avg_commits_per_day = history_stats["total_commits"] / max(unique_days, 1)
                
                history_stats["summary"] = {
                    "most_active_author": most_active_author,
                    "most_common_commit_type": most_common_type,
                    "average_commits_per_day": round(avg_commits_per_day, 2),
                    "active_days": unique_days,
                    "most_active_hour": history_stats["hourly_activity"].index(max(history_stats["hourly_activity"])),
                    "most_active_weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][
                        history_stats["weekday_activity"].index(max(history_stats["weekday_activity"]))
                    ]
                }
            
            logger.info(f"Analyzed {history_stats['total_commits']} commits")
            logger.info(f"Authors: {len(history_stats['authors'])}")
            logger.info(f"Active days: {len(history_stats['daily_activity'])}")
            
            if "summary" in history_stats:
                summary = history_stats["summary"]
                logger.info(f"Most active author: {summary['most_active_author']}")
                logger.info(f"Most common commit type: {summary['most_common_commit_type']}")
                logger.info(f"Average commits/day: {summary['average_commits_per_day']}")
                logger.info(f"Most active hour: {summary['most_active_hour']}:00")
                logger.info(f"Most active weekday: {summary['most_active_weekday']}")
            
            result = {
                "commits": commit_list,
                "statistics": history_stats,
                "analysis_period": {
                    "days": days,
                    "since_date": since_date.isoformat(),
                    "max_commits": max_commits
                }
            }
            
            self.analysis_results['commit_history'] = result
            return result
            
        except Exception as e:
            logger.error(f"✗ Commit history analysis failed: {e}")
            return {"error": str(e)}
    
    def compare_commits(self, from_commit: str, to_commit: str) -> Dict[str, Any]:
        """Compare two commits and analyze differences."""
        logger.info(f"\n=== Commit Comparison: {from_commit[:8]} -> {to_commit[:8]} ===")
        
        if not self.repo:
            return {"error": "Repository not loaded"}
        
        try:
            # Perform comparison
            diff_result = compare_commits(
                repo=self.repo,
                from_commit=from_commit,
                to_commit=to_commit
            )
            
            # Convert to dictionary
            comparison_data = diff_result.model_dump()
            
            logger.info(f"Files changed: {diff_result.files_changed}")
            logger.info(f"Total additions: {diff_result.total_additions}")
            logger.info(f"Total deletions: {diff_result.total_deletions}")
            logger.info(f"Net change: {diff_result.total_additions - diff_result.total_deletions}")
            
            # Analyze file changes
            if diff_result.file_diffs:
                logger.info("File changes:")
                for i, file_diff in enumerate(diff_result.file_diffs[:10]):  # Show first 10
                    change_type = file_diff.change_type.value if hasattr(file_diff.change_type, 'value') else str(file_diff.change_type)
                    logger.info(f"  {i+1}. {file_diff.file_path} ({change_type}): +{file_diff.additions}/-{file_diff.deletions}")
                
                if len(diff_result.file_diffs) > 10:
                    logger.info(f"  ... and {len(diff_result.file_diffs) - 10} more files")
            
            # Additional analysis
            comparison_analysis = self._analyze_diff_patterns(diff_result)
            comparison_data.update(comparison_analysis)
            
            self.analysis_results['commit_comparison'] = comparison_data
            return comparison_data
            
        except Exception as e:
            logger.error(f"✗ Commit comparison failed: {e}")
            return {"error": str(e)}
    
    def _analyze_diff_patterns(self, diff_result) -> Dict[str, Any]:
        """Analyze patterns in diff data."""
        analysis: dict[str, Any] = {}
        
        # Change magnitude
        total_changes = diff_result.total_additions + diff_result.total_deletions
        if total_changes < 50:
            magnitude = "small"
        elif total_changes < 200:
            magnitude = "medium"
        elif total_changes < 1000:
            magnitude = "large"
        else:
            magnitude = "very_large"
        
        analysis['change_magnitude'] = magnitude
        analysis['total_changes'] = total_changes
        analysis['net_change'] = diff_result.total_additions - diff_result.total_deletions
        
        # File type analysis
        file_types: dict[str, Any] = {}
        change_types: dict[str, Any] = {}
        
        for file_diff in diff_result.file_diffs:
            # File extension
            ext = Path(file_diff.file_path).suffix.lower()
            if not ext:
                ext = "no_extension"
            file_types[ext] = file_types.get(ext, 0) + 1
            
            # Change type
            change_type = file_diff.change_type.value if hasattr(file_diff.change_type, 'value') else str(file_diff.change_type)
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        analysis['file_types_changed'] = file_types
        analysis['change_types'] = change_types
        
        # Ratio analysis
        if diff_result.total_deletions > 0:
            analysis['addition_deletion_ratio'] = round(diff_result.total_additions / diff_result.total_deletions, 2)
        else:
            analysis['addition_deletion_ratio'] = float('inf') if diff_result.total_additions > 0 else 0
        
        return analysis


async def main() -> None:
    """Main analysis function."""
    
    if len(sys.argv) < 2:
        print("Usage: python commit_analysis.py /path/to/repository [commit_hash]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    commit_hash = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(repo_path).exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("GitHound - Comprehensive Commit Analysis")
    print("=" * 70)
    print(f"Repository: {repo_path}")
    if commit_hash:
        print(f"Target Commit: {commit_hash}")
    print()
    
    analyzer = CommitAnalyzer(repo_path)
    
    try:
        # Load repository
        if not analyzer.load_repository():
            sys.exit(1)
        
        # Run analyses
        analyzer.analyze_specific_commit(commit_hash)
        analyzer.analyze_commit_history(days=30, max_commits=50)
        
        # If we have a specific commit, compare it with its parent
        if commit_hash:
            try:
                commit = analyzer.repo.commit(commit_hash)
                if commit.parents:
                    parent_hash = commit.parents[0].hexsha
                    analyzer.compare_commits(parent_hash, commit_hash)
                else:
                    logger.info("Commit has no parents (initial commit)")
            except Exception as e:
                logger.warning(f"Could not perform commit comparison: {e}")
        
        print("\n" + "=" * 70)
        print("Commit analysis completed successfully!")
        print("=" * 70)
        
        # Save results
        output_file = f"commit_analysis_{Path(repo_path).name}.json"
        with open(output_file, 'w') as f:
            json.dump(analyzer.analysis_results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Commit analysis failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
