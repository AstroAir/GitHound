"""
Repository builder for creating test repositories with specific characteristics.

This module provides utilities for building test repositories with controlled
structure, history, and content for comprehensive testing scenarios.
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from git import Repo


class RepositoryBuilder:
    """Builder for creating test repositories with specific characteristics."""

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize repository builder."""
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(tempfile.mkdtemp(prefix="githound_test_"))

        self.repo: Repo | None = None
        self.commits: list[Any] = []
        self.branches: list[str] = []
        self.tags: list[str] = []
        self.authors: list[tuple[str, str]] = [
            ("Test User", "test@example.com")]
        self.current_author_index = 0

    def initialize_repository(self) -> "RepositoryBuilder":
        """Initialize a new Git repository."""
        self.repo = Repo.init(str(self.base_path))

        # Configure initial user
        with self.repo.config_writer() as config:  # [attr-defined]
            # [attr-defined]
            config.set_value("user", "name", self.authors[0][0])
            # [attr-defined]
            config.set_value("user", "email", self.authors[0][1])

        return self

    def add_authors(self, authors: list[tuple[str, str]]) -> "RepositoryBuilder":
        """Add authors for commits."""
        self.authors.extend(authors)
        return self

    def create_file(self, file_path: str, content: str) -> "RepositoryBuilder":
        """Create a file with specified content."""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return self

    def create_directory_structure(self, structure: dict[str, Any]) -> "RepositoryBuilder":
        """Create directory structure from nested dictionary."""
        self._create_structure_recursive(self.base_path, structure)
        return self

    def _create_structure_recursive(self, base: Path, structure: dict[str, Any]) -> None:
        """Recursively create directory structure."""
        for name, content in structure.items():
            path = base / name

            if isinstance(content, dict):
                # It's a directory
                path.mkdir(exist_ok=True)
                self._create_structure_recursive(path, content)
            else:
                # It's a file
                path.write_text(str(content))

    def commit_changes(
        self, message: str, author_index: int | None = None
    ) -> "RepositoryBuilder":
        """Commit current changes."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        # Set author if specified
        if author_index is not None:
            self.current_author_index = author_index % len(self.authors)

        author_name, author_email = self.authors[self.current_author_index]

        with self.repo.config_writer() as config:  # [attr-defined]
            config.set_value("user", "name", author_name)  # [attr-defined]
            config.set_value("user", "email", author_email)  # [attr-defined]

        # Stage all changes
        self.repo.index.add_all()

        # Create commit
        commit = self.repo.index.commit(message)
        self.commits.append(commit)

        # Rotate to next author for subsequent commits
        self.current_author_index = (
            self.current_author_index + 1) % len(self.authors)

        return self

    def create_branch(self, branch_name: str, checkout: bool = True) -> "RepositoryBuilder":
        """Create a new branch."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        branch = self.repo.create_head(branch_name)
        self.branches.append(branch_name)

        if checkout:
            branch.checkout()

        return self

    def checkout_branch(self, branch_name: str) -> "RepositoryBuilder":
        """Checkout an existing branch."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        if branch_name in [b.name for b in self.repo.branches]:
            self.repo.heads[branch_name].checkout()
        else:
            raise ValueError(f"Branch {branch_name} does not exist")

        return self

    def merge_branch(self, branch_name: str, message: str | None = None) -> "RepositoryBuilder":
        """Merge a branch into current branch."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        if not message:
            message = f"Merge branch '{branch_name}'"

        self.repo.git.merge(branch_name, m=message)
        return self

    def create_tag(self, tag_name: str, message: str | None = None) -> "RepositoryBuilder":
        """Create a tag."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        if message:
            self.repo.create_tag(tag_name, message=message)
        else:
            self.repo.create_tag(tag_name)

        self.tags.append(tag_name)
        return self

    def add_commits_with_pattern(self, count: int, pattern: str = "commit") -> "RepositoryBuilder":
        """Add multiple commits following a pattern."""
        for i in range(count):
            file_name = f"{pattern}_{i}.txt"
            content = f"Content for {pattern} {i}\nLine 2\nLine 3"

            self.create_file(file_name, content)
            self.commit_changes(f"Add {pattern} {i}")

        return self

    def add_realistic_project_structure(self) -> "RepositoryBuilder":
        """Add a realistic project structure."""
        structure = {
            "src": {
                "__init__.py": "",
                "main.py": """
def main() -> None:
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""",
                "utils.py": """
def helper_function(x) -> None:
    return x * 2

class UtilityClass:
    def __init__(self, value) -> None:
        self.value = value
    
    def process(self) -> None:
        return helper_function(self.value)
""",
                "models": {
                    "__init__.py": "",
                    "user.py": """
class User:
    def __init__(self, name, email) -> None:
        self.name = name
        self.email = email
    
    def __str__(self) -> None:
        return f"User({self.name}, {self.email})"
""",
                    "project.py": """
from datetime import datetime

class Project:
    def __init__(self, name, description) -> None:
        self.name = name
        self.description = description
        self.created_at = datetime.now()
    
    def get_info(self) -> None:
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
""",
                },
            },
            "tests": {
                "__init__.py": "",
                "test_main.py": """
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main_returns_zero(self) -> None:
        result = main()
        self.assertEqual(result, 0)
""",
                "test_utils.py": """
import unittest
from src.utils import helper_function, UtilityClass

class TestUtils(unittest.TestCase):
    def test_helper_function(self) -> None:
        self.assertEqual(helper_function(5), 10)
    
    def test_utility_class(self) -> None:
        util = UtilityClass(3)
        self.assertEqual(util.process if util is not None else None(), 6)
""",
            },
            "docs": {
                "README.md": """
# Test Project

This is a test project for GitHound testing.

## Features
- Main application functionality
- Utility functions and classes
- Comprehensive test suite

## Usage
```python
from src.main import main
main()
```
""",
                "api.md": """
# API Documentation

## Main Module
- `main()`: Entry point function

## Utils Module
- `helper_function(x)`: Doubles the input value
- `UtilityClass`: Utility class for processing values
""",
            },
            "requirements.txt": "pytest>=6.0.0\nmypy>=0.900\nrequests>=2.25.0",
            "setup.py": """
from setuptools import setup, find_packages

setup(
    name="test-project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "mypy>=0.900",
        ]
    }
)
""",
            ".gitignore": """
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
""",
        }

        self.create_directory_structure(structure)
        return self

    def simulate_development_history(self, days: int = 30) -> "RepositoryBuilder":
        """Simulate realistic development history over specified days."""
        base_date = datetime.now() - timedelta(days=days)

        # Initial project setup
        self.add_realistic_project_structure()
        self.commit_changes("Initial project setup")

        # Simulate daily development
        for day in range(1, days):
            commit_date = base_date + timedelta(days=day)

            # Randomly choose what to do this day
            import random

            action = random.choice(
                ["feature", "bugfix", "docs", "tests", "refactor"])

            if action == "feature":
                self._add_feature_commit(day)
            elif action == "bugfix":
                self._add_bugfix_commit(day)
            elif action == "docs":
                self._add_docs_commit(day)
            elif action == "tests":
                self._add_test_commit(day)
            elif action == "refactor":
                self._add_refactor_commit(day)

        return self

    def _add_feature_commit(self, day: int) -> None:
        """Add a feature commit."""
        feature_file = f"src/feature_{day}.py"
        content = f"""
def feature_{day}():
    '''Feature added on day {day}'''
    return "Feature {day} result"

class Feature{day}Handler:
    def handle(self) -> None:
        return feature_{day}()
"""
        self.create_file(feature_file, content)
        self.commit_changes(f"Add feature {day}")

    def _add_bugfix_commit(self, day: int) -> None:
        """Add a bugfix commit."""
        # Modify existing file
        utils_path = self.base_path / "src" / "utils.py"
        if utils_path.exists():
            content = utils_path.read_text()
            content += f"\n# Bugfix applied on day {day}\n"
            utils_path.write_text(content)
            self.commit_changes(f"Fix bug discovered on day {day}")

    def _add_docs_commit(self, day: int) -> None:
        """Add a documentation commit."""
        doc_file = f"docs/day_{day}.md"
        content = f"""
# Documentation Update - Day {day}

Updated documentation with new information.

## Changes
- Added new section
- Updated examples
- Fixed typos
"""
        self.create_file(doc_file, content)
        self.commit_changes(f"Update documentation - day {day}")

    def _add_test_commit(self, day: int) -> None:
        """Add a test commit."""
        test_file = f"tests/test_day_{day}.py"
        content = f"""
import unittest

class TestDay{day}(unittest.TestCase):
    def test_day_{day}_functionality(self):
        # Test added on day {day}
        self.assertTrue(True)
"""
        self.create_file(test_file, content)
        self.commit_changes(f"Add tests for day {day}")

    def _add_refactor_commit(self, day: int) -> None:
        """Add a refactoring commit."""
        # Modify main.py
        main_path = self.base_path / "src" / "main.py"
        if main_path.exists():
            content = main_path.read_text()
            content += f"\n# Refactored on day {day}\n"
            main_path.write_text(content)
            self.commit_changes(f"Refactor code - day {day}")

    def build(self) -> tuple[Repo, str]:
        """Build and return the repository."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        return self.repo, str(self.base_path)

    def cleanup(self) -> None:
        """Clean up the repository."""
        if self.base_path.exists():
            shutil.rmtree(self.base_path, ignore_errors=True)


def create_simple_repository() -> tuple[Repo, str]:
    """Create a simple repository for basic testing."""
    builder = RepositoryBuilder()

    repo, path = (
        builder.initialize_repository()
        .create_file("README.md", "# Simple Test Repository")
        .commit_changes("Initial commit")
        .create_file("main.py", "print('Hello, World!')")
        .commit_changes("Add main.py")
        .create_tag("v1.0.0")
        .build()
    )

    return repo, path


def create_complex_repository() -> tuple[Repo, str]:
    """Create a complex repository for integration testing."""
    authors = [
        ("Alice Developer", "alice@example.com"),
        ("Bob Contributor", "bob@example.com"),
        ("Charlie Maintainer", "charlie@example.com"),
    ]

    builder = RepositoryBuilder()

    repo, path = (
        builder.initialize_repository()
        .add_authors(authors)
        .add_realistic_project_structure()
        .commit_changes("Initial project setup")
        .create_branch("feature/authentication")
        .create_file("src/auth.py", "# Authentication module")
        .commit_changes("Add authentication module")
        .checkout_branch("master")
        .merge_branch("feature/authentication")
        .create_tag("v1.0.0", "First release")
        .add_commits_with_pattern(10, "enhancement")
        .create_tag("v1.1.0", "Enhancement release")
        .build()
    )

    return repo, path


def create_performance_repository(commit_count: int = 100) -> tuple[Repo, str]:
    """Create a repository optimized for performance testing."""
    authors = [
        ("Perf Tester 1", "perf1@example.com"),
        ("Perf Tester 2", "perf2@example.com"),
        ("Perf Tester 3", "perf3@example.com"),
    ]

    builder = RepositoryBuilder()

    repo, path = (
        builder.initialize_repository()
        .add_authors(authors)
        .add_realistic_project_structure()
        .commit_changes("Initial setup")
        .add_commits_with_pattern(commit_count, "perf_test")
        .build()
    )

    return repo, path
