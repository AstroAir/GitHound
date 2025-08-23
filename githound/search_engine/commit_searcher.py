"""Commit-based searchers for GitHound."""

import re
from collections.abc import AsyncGenerator
from datetime import datetime

from rapidfuzz import fuzz

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class CommitHashSearcher(CacheableSearcher):
    """Searcher for exact commit hash matching."""

    def __init__(self) -> None:
        super().__init__("commit_hash", "commit_hash")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.commit_hash is not None

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for specific commit hash."""
        commit_hash = context.query.commit_hash
        if not commit_hash:
            return

        self._report_progress(
            context, f"Searching for commit {commit_hash[:8]}...", 0.0)

        try:
            # Try to find the commit
            commit = context.repo.commit(commit_hash)

            # Create commit info
            commit_info = CommitInfo(
                hash=commit.hexsha,
                short_hash=commit.hexsha[:8],
                author_name=commit.author.name,
                author_email=commit.author.email,
                committer_name=commit.committer.name,
                committer_email=commit.committer.email,
                message=commit.message.strip(),
                date=datetime.fromtimestamp(commit.committed_date),
                files_changed=len(commit.stats.files),
                insertions=commit.stats.total["insertions"],
                deletions=commit.stats.total["deletions"],
                parents=[parent.hexsha for parent in commit.parents],
            )

            # Create search result
            result = SearchResult(
                commit_hash=commit.hexsha,
                file_path=context.repo.working_dir,  # Repository root
                line_number=None,
                matching_line=None,
                search_type=SearchType.COMMIT_HASH,
                relevance_score=1.0,  # Exact match
                commit_info=commit_info,
                match_context={"search_term": commit_hash},
                search_time_ms=None,
            )

            self._update_metrics(total_commits_searched=1,
                                 total_results_found=1)
            self._report_progress(context, "Found commit", 1.0)

            yield result

        except Exception as e:
            self._report_progress(context, f"Commit not found: {e}", 1.0)
            return


class AuthorSearcher(CacheableSearcher):
    """Searcher for author names and emails with fuzzy matching."""

    def __init__(self) -> None:
        super().__init__("author", "author")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.author_pattern is not None

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size."""
        try:
            # Get approximate commit count
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=1000))
            return min(len(commits), 1000)
        except:
            return 100  # Default estimate

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for commits by author."""
        author_pattern = context.query.author_pattern
        if not author_pattern:
            return

        self._report_progress(
            context, f"Searching for author '{author_pattern}'...", 0.0)

        # Get branch to search
        branch = context.branch or context.repo.active_branch.name

        # Compile regex pattern if not using fuzzy search
        regex_pattern = None
        if not context.query.fuzzy_search:
            try:
                flags = 0 if context.query.case_sensitive else re.IGNORECASE
                regex_pattern = re.compile(author_pattern, flags)
            except re.error:
                # If regex is invalid, fall back to simple string matching
                pass

        commits_searched = 0
        results_found = 0

        try:
            # Iterate through commits
            for commit in context.repo.iter_commits(branch):
                commits_searched += 1

                # Check author name and email
                author_name = commit.author.name
                author_email = commit.author.email

                match_score = 0.0
                match_field = None

                if context.query.fuzzy_search:
                    # Use fuzzy matching
                    name_score = fuzz.ratio(
                        author_pattern.lower(), author_name.lower()) / 100.0
                    email_score = fuzz.ratio(
                        author_pattern.lower(), author_email.lower()) / 100.0

                    if name_score >= context.query.fuzzy_threshold:
                        match_score = name_score
                        match_field = "name"
                    elif email_score >= context.query.fuzzy_threshold:
                        match_score = email_score
                        match_field = "email"
                else:
                    # Use regex or string matching
                    if regex_pattern:
                        if regex_pattern.search(author_name) or regex_pattern.search(author_email):
                            match_score = 1.0
                            match_field = "name" if regex_pattern.search(
                                author_name) else "email"
                    else:
                        # Simple string matching
                        search_term = (
                            author_pattern
                            if context.query.case_sensitive
                            else author_pattern.lower()
                        )
                        name_check = (
                            author_name if context.query.case_sensitive else author_name.lower()
                        )
                        email_check = (
                            author_email if context.query.case_sensitive else author_email.lower()
                        )

                        if search_term in name_check:
                            match_score = 1.0
                            match_field = "name"
                        elif search_term in email_check:
                            match_score = 1.0
                            match_field = "email"

                if match_score > 0:
                    # Create commit info
                    commit_info = CommitInfo(
                        hash=commit.hexsha,
                        short_hash=commit.hexsha[:8],
                        author_name=author_name,
                        author_email=author_email,
                        committer_name=commit.committer.name,
                        committer_email=commit.committer.email,
                        message=commit.message.strip(),
                        date=datetime.fromtimestamp(commit.committed_date),
                        files_changed=len(commit.stats.files),
                        insertions=commit.stats.total["insertions"],
                        deletions=commit.stats.total["deletions"],
                        parents=[parent.hexsha for parent in commit.parents],
                    )

                    # Create search result
                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=context.repo.working_dir,
                        line_number=None,
                        matching_line=None,
                        search_type=SearchType.AUTHOR,
                        relevance_score=match_score,
                        commit_info=commit_info,
                        match_context={
                            "search_term": author_pattern,
                            "matched_field": match_field,
                            "matched_value": author_name if match_field == "name" else author_email,
                        },
                        search_time_ms=None,
                    )

                    results_found += 1
                    yield result

                # Report progress every 100 commits
                if commits_searched % 100 == 0:
                    # Cap at 90% until done
                    progress = min(commits_searched / 1000, 0.9)
                    self._report_progress(
                        context,
                        f"Searched {commits_searched} commits, found {results_found} matches",
                        progress,
                    )

        except Exception as e:
            self._report_progress(
                context, f"Error searching authors: {e}", 1.0)

        finally:
            self._update_metrics(
                total_commits_searched=commits_searched, total_results_found=results_found
            )
            self._report_progress(
                context,
                f"Author search completed: {results_found} matches in {commits_searched} commits",
                1.0,
            )


class MessageSearcher(CacheableSearcher):
    """Searcher for commit messages with regex and fuzzy matching."""

    def __init__(self) -> None:
        super().__init__("message", "message")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.message_pattern is not None

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=1000))
            return min(len(commits), 1000)
        except:
            return 100

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for commits by message content."""
        message_pattern = context.query.message_pattern
        if not message_pattern:
            return

        self._report_progress(
            context, f"Searching commit messages for '{message_pattern}'...", 0.0)

        branch = context.branch or context.repo.active_branch.name

        # Compile regex pattern if not using fuzzy search
        regex_pattern = None
        if not context.query.fuzzy_search:
            try:
                flags = 0 if context.query.case_sensitive else re.IGNORECASE
                regex_pattern = re.compile(message_pattern, flags)
            except re.error:
                pass

        commits_searched = 0
        results_found = 0

        try:
            for commit in context.repo.iter_commits(branch):
                commits_searched += 1

                message = commit.message.strip()
                match_score = 0.0

                if context.query.fuzzy_search:
                    # Use fuzzy matching
                    score = fuzz.partial_ratio(
                        message_pattern.lower(), message.lower()) / 100.0
                    if score >= context.query.fuzzy_threshold:
                        match_score = score
                else:
                    # Use regex or string matching
                    if regex_pattern:
                        if regex_pattern.search(message):
                            match_score = 1.0
                    else:
                        search_term = (
                            message_pattern
                            if context.query.case_sensitive
                            else message_pattern.lower()
                        )
                        message_check = message if context.query.case_sensitive else message.lower()
                        if search_term in message_check:
                            match_score = 1.0

                if match_score > 0:
                    commit_info = CommitInfo(
                        hash=commit.hexsha,
                        short_hash=commit.hexsha[:8],
                        author_name=commit.author.name,
                        author_email=commit.author.email,
                        committer_name=commit.committer.name,
                        committer_email=commit.committer.email,
                        message=message,
                        date=datetime.fromtimestamp(commit.committed_date),
                        files_changed=len(commit.stats.files),
                        insertions=commit.stats.total["insertions"],
                        deletions=commit.stats.total["deletions"],
                        parents=[parent.hexsha for parent in commit.parents],
                    )

                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=context.repo.working_dir,
                        line_number=None,
                        matching_line=None,
                        search_type=SearchType.MESSAGE,
                        relevance_score=match_score,
                        commit_info=commit_info,
                        match_context={
                            "search_term": message_pattern, "matched_message": message},
                        search_time_ms=None,
                    )

                    results_found += 1
                    yield result

                if commits_searched % 100 == 0:
                    progress = min(commits_searched / 1000, 0.9)
                    self._report_progress(
                        context,
                        f"Searched {commits_searched} commits, found {results_found} matches",
                        progress,
                    )

        except Exception as e:
            self._report_progress(
                context, f"Error searching messages: {e}", 1.0)

        finally:
            self._update_metrics(
                total_commits_searched=commits_searched, total_results_found=results_found
            )
            self._report_progress(
                context,
                f"Message search completed: {results_found} matches in {commits_searched} commits",
                1.0,
            )


class DateRangeSearcher(CacheableSearcher):
    """Searcher for commits within a date range."""

    def __init__(self) -> None:
        super().__init__("date_range", "date_range")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.date_from is not None or query.date_to is not None

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on date range."""
        try:
            branch = context.branch or context.repo.active_branch.name

            # If we have date constraints, estimate based on that
            if context.query.date_from or context.query.date_to:
                # Rough estimate: assume 10 commits per day
                if context.query.date_from and context.query.date_to:
                    days = (context.query.date_to -
                            context.query.date_from).days
                    return min(days * 10, 1000)

            commits = list(context.repo.iter_commits(branch, max_count=1000))
            return min(len(commits), 1000)
        except:
            return 100

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for commits within date range."""
        date_from = context.query.date_from
        date_to = context.query.date_to

        if not date_from and not date_to:
            return

        self._report_progress(
            context, "Searching commits by date range...", 0.0)

        branch = context.branch or context.repo.active_branch.name

        commits_searched = 0
        results_found = 0

        try:
            for commit in context.repo.iter_commits(branch):
                commits_searched += 1

                commit_date = datetime.fromtimestamp(commit.committed_date)

                # Check date range
                in_range = True
                if date_from and commit_date < date_from:
                    in_range = False
                if date_to and commit_date > date_to:
                    in_range = False

                if in_range:
                    commit_info = CommitInfo(
                        hash=commit.hexsha,
                        short_hash=commit.hexsha[:8],
                        author_name=commit.author.name,
                        author_email=commit.author.email,
                        committer_name=commit.committer.name,
                        committer_email=commit.committer.email,
                        message=commit.message.strip(),
                        date=commit_date,
                        files_changed=len(commit.stats.files),
                        insertions=commit.stats.total["insertions"],
                        deletions=commit.stats.total["deletions"],
                        parents=[parent.hexsha for parent in commit.parents],
                    )

                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=context.repo.working_dir,
                        line_number=None,
                        matching_line=None,
                        search_type=SearchType.DATE_RANGE,
                        relevance_score=1.0,  # All matches in range are equally relevant
                        commit_info=commit_info,
                        match_context={
                            "date_from": date_from.isoformat() if date_from else None,
                            "date_to": date_to.isoformat() if date_to else None,
                            "commit_date": commit_date.isoformat(),
                        },
                        search_time_ms=None,
                    )

                    results_found += 1
                    yield result

                if commits_searched % 100 == 0:
                    progress = min(commits_searched / 1000, 0.9)
                    self._report_progress(
                        context,
                        f"Searched {commits_searched} commits, found {results_found} matches",
                        progress,
                    )

        except Exception as e:
            self._report_progress(
                context, f"Error searching by date: {e}", 1.0)

        finally:
            self._update_metrics(
                total_commits_searched=commits_searched, total_results_found=results_found
            )
            self._report_progress(
                context,
                f"Date range search completed: {results_found} matches in {commits_searched} commits",
                1.0,
            )
