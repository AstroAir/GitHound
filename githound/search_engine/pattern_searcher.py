"""Code pattern detection searchers for GitHound."""

import re
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class CodePatternSearcher(CacheableSearcher):
    """Searcher that detects code patterns, anti-patterns, and common coding issues."""

    def __init__(self) -> None:
        super().__init__("code_pattern", "patterns")
        self._pattern_definitions = self._initialize_patterns()

    def _initialize_patterns(self) -> dict[str, dict[str, Any]]:
        """Initialize code pattern definitions."""
        return {
            # Security patterns
            "hardcoded_secrets": {
                "patterns": [
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    r"api_key\s*=\s*['\"][^'\"]+['\"]",
                    r"secret\s*=\s*['\"][^'\"]+['\"]",
                    r"token\s*=\s*['\"][^'\"]+['\"]",
                ],
                "severity": "high",
                "description": "Hardcoded secrets or credentials",
                "file_types": [".py", ".js", ".java", ".cs", ".php", ".rb"],
            },
            "sql_injection": {
                "patterns": [
                    r"execute\s*\(\s*['\"].*%.*['\"]",
                    r"query\s*\(\s*['\"].*\+.*['\"]",
                    r"SELECT.*\+.*FROM",
                ],
                "severity": "high",
                "description": "Potential SQL injection vulnerability",
                "file_types": [".py", ".java", ".cs", ".php"],
            },
            
            # Code quality patterns
            "long_functions": {
                "patterns": [
                    r"def\s+\w+\s*\([^)]*\):",  # Python functions
                    r"function\s+\w+\s*\([^)]*\)\s*{",  # JavaScript functions
                    r"public\s+\w+\s+\w+\s*\([^)]*\)\s*{",  # Java methods
                ],
                "severity": "medium",
                "description": "Potentially long functions (need line count analysis)",
                "file_types": [".py", ".js", ".java", ".cs"],
                "requires_line_analysis": True,
            },
            "magic_numbers": {
                "patterns": [
                    r"\b(?<![\w.])\d{2,}\b(?![\w.])",  # Numbers with 2+ digits
                ],
                "severity": "low",
                "description": "Magic numbers that should be constants",
                "file_types": [".py", ".js", ".java", ".cs", ".cpp", ".c"],
                "exclude_patterns": [
                    r"#.*\d+",  # Comments
                    r"//.*\d+",  # Comments
                    r"return\s+\d+",  # Return statements
                ],
            },
            
            # Performance patterns
            "nested_loops": {
                "patterns": [
                    r"for\s+.*:\s*\n\s*for\s+.*:",  # Python nested loops
                    r"for\s*\([^)]*\)\s*{\s*for\s*\([^)]*\)",  # C-style nested loops
                ],
                "severity": "medium",
                "description": "Nested loops that may impact performance",
                "file_types": [".py", ".js", ".java", ".cs", ".cpp", ".c"],
            },
            
            # Design patterns
            "singleton_pattern": {
                "patterns": [
                    r"class\s+\w+.*:\s*\n.*_instance\s*=\s*None",
                    r"private\s+static\s+\w+\s+instance",
                ],
                "severity": "info",
                "description": "Singleton pattern implementation",
                "file_types": [".py", ".java", ".cs"],
            },
            
            # Documentation patterns
            "missing_docstrings": {
                "patterns": [
                    r"def\s+\w+\s*\([^)]*\):\s*\n(?!\s*['\"])",  # Python functions without docstrings
                ],
                "severity": "low",
                "description": "Functions missing documentation",
                "file_types": [".py"],
            },
            
            # Error handling patterns
            "bare_except": {
                "patterns": [
                    r"except\s*:",  # Bare except clauses
                    r"catch\s*\(\s*\)",  # Empty catch blocks
                ],
                "severity": "medium",
                "description": "Bare except clauses or empty catch blocks",
                "file_types": [".py", ".java", ".cs"],
            },
        }

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle pattern detection queries."""
        # Handle queries that request pattern analysis
        return bool(
            (hasattr(query, 'pattern_analysis') and query.pattern_analysis) or
            (hasattr(query, 'code_quality') and query.code_quality) or
            (query.content_pattern and any(keyword in query.content_pattern.lower()
                                         for keyword in ['pattern', 'anti-pattern', 'smell', 'quality']))
        )

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size and file types."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=1000))
            return min(len(commits) * 2, 2000)  # Pattern analysis is more intensive
        except Exception:
            return 500

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform code pattern detection and analysis."""
        self._report_progress(context, "Starting pattern analysis...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "pattern_analysis")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached pattern results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform pattern analysis
        results: list[SearchResult] = []
        
        # Analyze patterns in repository
        self._report_progress(context, "Scanning for code patterns...", 0.2)
        pattern_results = await self._scan_for_patterns(context)
        results.extend(pattern_results)

        # Cache results
        await self._set_cache(context, cache_key, results)
        
        # Yield results
        for result in results:
            yield result
            
        self._report_progress(context, "Pattern analysis completed", 1.0)

    async def _scan_for_patterns(self, context: SearchContext) -> list[SearchResult]:
        """Scan repository for code patterns."""
        results: list[SearchResult] = []
        branch = context.branch or context.repo.active_branch.name
        
        commits_processed = 0
        files_analyzed = 0
        
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 1000:  # Limit for performance
                break
                
            # Analyze files in this commit
            for file_path in commit.stats.files:
                if self._should_analyze_file(file_path):
                    file_results = await self._analyze_file_patterns(
                        commit, file_path, context
                    )
                    results.extend(file_results)
                    files_analyzed += 1

        self._update_metrics(
            total_commits_searched=commits_processed,
            total_files_searched=files_analyzed
        )
        
        return results

    def _should_analyze_file(self, file_path: str) -> bool:
        """Determine if a file should be analyzed for patterns."""
        file_ext = Path(file_path).suffix.lower()
        
        # Check if any pattern supports this file type
        for pattern_info in self._pattern_definitions.values():
            if file_ext in pattern_info.get("file_types", []):
                return True
        
        return False

    async def _analyze_file_patterns(
        self, commit: Any, file_path: str, context: SearchContext
    ) -> list[SearchResult]:
        """Analyze a specific file for code patterns."""
        results: list[SearchResult] = []
        
        try:
            # Get file content at this commit
            file_content = commit.tree[file_path].data_stream.read().decode('utf-8', errors='ignore')
            lines = file_content.split('\n')
            file_ext = Path(file_path).suffix.lower()
            
            # Check each pattern
            for pattern_name, pattern_info in self._pattern_definitions.items():
                if file_ext not in pattern_info.get("file_types", []):
                    continue
                    
                pattern_results = await self._check_pattern_in_file(
                    pattern_name, pattern_info, file_content, lines, 
                    commit, file_path, context
                )
                results.extend(pattern_results)
                
        except (UnicodeDecodeError, KeyError, AttributeError):
            # Skip files that can't be read or don't exist
            pass
            
        return results

    async def _check_pattern_in_file(
        self, pattern_name: str, pattern_info: dict[str, Any], 
        file_content: str, lines: list[str], commit: Any, 
        file_path: str, context: SearchContext
    ) -> list[SearchResult]:
        """Check for a specific pattern in a file."""
        results: list[SearchResult] = []
        
        patterns = pattern_info["patterns"]
        exclude_patterns = pattern_info.get("exclude_patterns", [])
        severity = pattern_info["severity"]
        description = pattern_info["description"]
        
        for pattern in patterns:
            try:
                regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                
                for line_num, line in enumerate(lines, 1):
                    matches = regex.finditer(line)
                    
                    for match in matches:
                        # Check exclude patterns
                        if self._should_exclude_match(line, exclude_patterns):
                            continue
                            
                        # Special handling for patterns requiring line analysis
                        if pattern_info.get("requires_line_analysis"):
                            if not self._analyze_function_length(lines, line_num):
                                continue
                        
                        # Create commit info
                        commit_info = self._create_commit_info(commit)
                        
                        # Calculate relevance based on severity
                        relevance_score = self._calculate_pattern_relevance(severity)
                        
                        result = SearchResult(
                            commit_hash=commit.hexsha,
                            file_path=Path(file_path),
                            line_number=line_num,
                            matching_line=line.strip(),
                            commit_info=commit_info,
                            search_type=SearchType.CONTENT,
                            relevance_score=relevance_score,
                            match_context={
                                "pattern_name": pattern_name,
                                "pattern_description": description,
                                "severity": severity,
                                "matched_text": match.group(),
                                "analysis_type": "code_pattern"
                            },
                            search_time_ms=None
                        )
                        results.append(result)
                        
            except re.error:
                # Skip invalid regex patterns
                continue
                
        return results

    def _should_exclude_match(self, line: str, exclude_patterns: list[str]) -> bool:
        """Check if a match should be excluded based on exclude patterns."""
        for exclude_pattern in exclude_patterns:
            try:
                if re.search(exclude_pattern, line, re.IGNORECASE):
                    return True
            except re.error:
                continue
        return False

    def _analyze_function_length(self, lines: list[str], start_line: int) -> bool:
        """Analyze if a function is too long (simple heuristic)."""
        # Simple heuristic: count lines until next function or class definition
        function_lines = 0
        indent_level = None
        
        for i in range(start_line, min(start_line + 100, len(lines))):
            line = lines[i].rstrip()
            if not line:
                continue
                
            # Determine initial indent level
            if indent_level is None:
                indent_level = len(line) - len(line.lstrip())
                
            current_indent = len(line) - len(line.lstrip())
            
            # If we hit a line with same or less indentation that starts a new definition
            if (current_indent <= indent_level and 
                (line.strip().startswith('def ') or 
                 line.strip().startswith('class ') or
                 line.strip().startswith('function '))):
                break
                
            function_lines += 1
            
        # Consider functions with more than 50 lines as potentially too long
        return function_lines > 50

    def _calculate_pattern_relevance(self, severity: str) -> float:
        """Calculate relevance score based on pattern severity."""
        severity_scores = {
            "high": 1.0,
            "medium": 0.8,
            "low": 0.6,
            "info": 0.4,
        }
        return severity_scores.get(severity, 0.5)

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
