"""Test fixtures for search engine testing."""

import tempfile
from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from git import Actor, Repo

from githound.models import CommitInfo, SearchQuery, SearchResult


@pytest.fixture
def complex_git_repo() -> Generator[Path, None, None]:
    """Create a complex Git repository for comprehensive search testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import os

        # Normalize path to handle Windows 8.3 short names
        repo_path = Path(os.path.realpath(temp_dir))
        repo = Repo.init(repo_path)

        # Configure user for commits
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

        # Create multiple authors
        authors = [
            Actor("Alice Developer", "alice@example.com"),
            Actor("Bob Developer", "bob@example.com"),
            Actor("Charlie Developer", "charlie@example.com"),
            Actor("Diana Developer", "diana@example.com"),
        ]

        # Create initial structure
        for i in range(10):
            # Create different types of files
            if i % 3 == 0:
                # Python files
                file_path = repo_path / f"src/module_{i}.py"
                file_path.parent.mkdir(exist_ok=True)
                content = f'''"""Module {i} for testing search functionality."""

import os
import sys
from typing import List, Dict, Optional

class Module{i}Class:
    """Class for module {i}."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.value = {i}

    def process_data(self, data: List[str]) -> Dict[str, int]:
        """Process data and return results."""
        result = {{}}
        for item in data:
            result[item] = len(item) * {i}
        return result

    def calculate(self, x: int, y: int) -> int:
        """Calculate something useful."""
        return (x + y) * {i}

def utility_function_{i}(param: str) -> str:
    """Utility function for module {i}."""
    return f"Processing {{param}} in module {i}"

# Constants
MODULE_{i}_CONSTANT = {i * 10}
DEBUG_MODE = {"True" if i % 2 == 0 else "False"}
'''
            elif i % 3 == 1:
                # JavaScript files
                file_path = repo_path / f"frontend/component_{i}.js"
                file_path.parent.mkdir(exist_ok=True)
                content = f"""/**
 * Component {i} for frontend testing
 */

class Component{i} {{
    constructor(name) {{
        this.name = name;
        this.value = {i};
    }}

    render() {{
        return `<div class="component-{i}">{{this.name}}</div>`;
    }}

    handleClick(event) {{
        console.log(`Component {i} clicked: {{event.target}}`);
        this.value += 1;
    }}
}}

function utilityFunction{i}(param) {{
    return `Processing ${{param}} in component {i}`;
}}

const COMPONENT_{i}_CONFIG = {{
    enabled: {"true" if i % 2 == 0 else "false"},
    priority: {i},
    features: ["feature1", "feature2", "feature{i}"]
}};

export default Component{i};
"""
            else:
                # Configuration files
                file_path = repo_path / f"config/config_{i}.yaml"
                file_path.parent.mkdir(exist_ok=True)
                content = f"""# Configuration file {i}
name: config_{i}
version: 1.{i}.0
enabled: {"true" if i % 2 == 0 else "false"}

database:
  host: localhost
  port: {5432 + i}
  name: test_db_{i}

features:
  - feature_{i}_1
  - feature_{i}_2
  - advanced_feature_{i}

logging:
  level: {"DEBUG" if i % 2 == 0 else "INFO"}
  file: logs/app_{i}.log
"""

            file_path.write_text(content)
            repo.index.add([str(file_path.relative_to(repo_path))])

            # Commit with different authors and messages
            author = authors[i % len(authors)]
            messages = [
                f"Add module {i} with core functionality",
                f"Implement feature {i} for better performance",
                f"Fix bug in component {i} handling",
                f"Update configuration for module {i}",
                f"Refactor module {i} for maintainability",
            ]
            message = messages[i % len(messages)]

            repo.index.commit(message, author=author)

        # Create branches with additional content
        feature_branch = repo.create_head("feature/search-enhancement")
        feature_branch.checkout()

        # Add search-related files
        search_file = repo_path / "src/search.py"
        search_file.write_text(
            '''"""Advanced search functionality."""

import re
from typing import List, Pattern, Optional

class SearchEngine:
    """Advanced search engine implementation."""

    def __init__(self) -> None:
        self.patterns: List[Pattern] = []
        self.case_sensitive = False

    def add_pattern(self, pattern: str) -> None:
        """Add a search pattern."""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self.patterns.append(re.compile(pattern, flags))

    def search(self, text: str) -> List[str]:
        """Search for patterns in text."""
        results = []
        for pattern in self.patterns:
            matches = pattern.findall(text)
            results.extend(matches)
        return results

    def fuzzy_search(self, text: str, threshold: float = 0.8) -> List[str]:
        """Perform fuzzy search with similarity threshold."""
        # Simplified fuzzy search implementation
        results = []
        words = text.split()
        for word in words:
            if len(word) >= 3:  # Minimum word length
                results.append(word)
        return results

def search_files(directory: str, pattern: str) -> List[str]:
    """Search for pattern in files within directory."""
    import os
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.js', '.yaml', '.yml')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern.lower() in content.lower():
                            results.append(file_path)
                except Exception:
                    continue
    return results
'''
        )
        repo.index.add(["src/search.py"])
        repo.index.commit("Add advanced search functionality", author=authors[0])

        # Switch back to main and create tags
        repo.heads.master.checkout()
        repo.create_tag("v1.0.0", message="Initial release")
        repo.create_tag("v1.1.0", message="Feature release")

        yield repo_path

        # Cleanup: Close repository to release file handles
        repo.close()


@pytest.fixture
def search_test_queries() -> dict:
    """Provide comprehensive search queries for testing."""
    base_date = datetime.now()
    return {
        "simple_content": SearchQuery(content_pattern="function", case_sensitive=False),
        "regex_content": SearchQuery(content_pattern=r"def\s+\w+\(", case_sensitive=False),
        "author_search": SearchQuery(author_pattern="Alice Developer"),
        "message_search": SearchQuery(message_pattern="Add.*functionality"),
        "date_range": SearchQuery(date_from=base_date - timedelta(days=7), date_to=base_date),
        "file_extension": SearchQuery(file_extensions=["py", "js"]),
        "file_path": SearchQuery(file_path_pattern="src/*.py"),
        "fuzzy_search": SearchQuery(
            content_pattern="functon", fuzzy_search=True, fuzzy_threshold=0.8  # Intentional typo
        ),
        "complex_query": SearchQuery(
            content_pattern="class.*:",
            author_pattern="Alice.*",
            file_extensions=["py"],
            case_sensitive=False,
            fuzzy_search=False,
        ),
        "case_sensitive": SearchQuery(content_pattern="DEBUG", case_sensitive=True),
    }


@pytest.fixture
def mock_search_results() -> list[SearchResult]:
    """Provide mock search results for testing."""
    return [
        SearchResult(
            commit_hash="abc123def456",
            file_path="src/module_0.py",
            line_number=15,
            content="def process_data(self, data: List[str]) -> Dict[str, int]:",
            author="Alice Developer",
            author_email="alice@example.com",
            message="Add module 0 with core functionality",
            date=datetime.now() - timedelta(days=2),
            relevance_score=0.95,
        ),
        SearchResult(
            commit_hash="def456ghi789",
            file_path="frontend/component_1.js",
            line_number=8,
            content="render() {",
            author="Bob Developer",
            author_email="bob@example.com",
            message="Implement feature 1 for better performance",
            date=datetime.now() - timedelta(days=1),
            relevance_score=0.87,
        ),
        SearchResult(
            commit_hash="ghi789jkl012",
            file_path="src/search.py",
            line_number=25,
            content="def search(self, text: str) -> List[str]:",
            author="Alice Developer",
            author_email="alice@example.com",
            message="Add advanced search functionality",
            date=datetime.now(),
            relevance_score=0.92,
        ),
    ]


@pytest.fixture
def mock_commit_info() -> list[CommitInfo]:
    """Provide mock commit information for testing."""
    return [
        CommitInfo(
            hash="abc123def456789",
            short_hash="abc123d",
            author_name="Alice Developer",
            author_email="alice@example.com",
            committer_name="Alice Developer",
            committer_email="alice@example.com",
            message="Add module 0 with core functionality",
            date=datetime.now() - timedelta(days=2),
            files_changed=1,
            insertions=45,
            deletions=0,
        ),
        CommitInfo(
            hash="def456ghi789abc",
            short_hash="def456g",
            author_name="Bob Developer",
            author_email="bob@example.com",
            committer_name="Bob Developer",
            committer_email="bob@example.com",
            message="Implement feature 1 for better performance",
            date=datetime.now() - timedelta(days=1),
            files_changed=2,
            insertions=32,
            deletions=5,
        ),
    ]


@pytest.fixture
def search_performance_data():
    """Provide data for search performance testing."""
    return {
        "large_file_count": 1000,
        "large_commit_count": 5000,
        "complex_patterns": [
            r"class\s+\w+\s*\([^)]*\):",
            r"def\s+\w+\s*\([^)]*\)\s*->.*:",
            r"import\s+[\w.]+",
            r"from\s+[\w.]+\s+import\s+.*",
        ],
        "stress_test_queries": [
            SearchQuery(content_pattern=pattern, case_sensitive=False)
            for pattern in [
                "function",
                "class",
                "import",
                "def",
                "return",
                "if",
                "for",
                "while",
                "try",
                "except",
            ]
        ],
    }
