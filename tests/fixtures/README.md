# Test Fixtures

This directory contains reusable test fixtures, mock data generators, and testing utilities for consistent test data across all GitHound test suites.

## Directory Structure

```
tests/fixtures/
├── repositories/           # Test repository fixtures
│   ├── simple_repo/       # Basic repository for unit tests
│   ├── complex_repo/      # Complex repository for integration tests
│   └── large_repo/        # Large repository for performance tests
├── data/                  # Test data files
│   ├── sample_commits.json
│   ├── sample_authors.json
│   └── sample_diffs.json
├── mocks/                 # Mock objects and services
│   ├── git_mocks.py
│   ├── api_mocks.py
│   └── mcp_mocks.py
├── builders/              # Test data builders
│   ├── repository_builder.py
│   ├── commit_builder.py
│   └── search_builder.py
└── utilities/             # Test utilities
    ├── assertions.py
    ├── helpers.py
    └── cleanup.py
```

## Repository Fixtures

### Simple Repository Fixture

```python
@pytest.fixture(scope="session")
def simple_test_repo():
    """
    Create a simple test repository with basic structure:
    - 5 commits
    - 3 files
    - 2 branches
    - 1 tag
    """
    repo_path = create_simple_repository()
    yield repo_path
    cleanup_repository(repo_path)

def create_simple_repository():
    """Create a simple repository for basic testing."""
    import tempfile
    import shutil
    from git import Repo

    temp_dir = tempfile.mkdtemp(prefix="githound_test_")
    repo = Repo.init(temp_dir)

    # Configure test user
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    readme_path = Path(temp_dir) / "README.md"
    readme_path.write_text("# Test Repository\n\nThis is a test repository.")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create additional files and commits
    for i in range(2, 6):
        file_path = Path(temp_dir) / f"file_{i}.txt"
        file_path.write_text(f"Content of file {i}\nLine 2\nLine 3")
        repo.index.add([f"file_{i}.txt"])
        repo.index.commit(f"Add file_{i}.txt")

    # Create a branch
    feature_branch = repo.create_head("feature-branch")
    feature_branch.checkout()

    feature_file = Path(temp_dir) / "feature.py"
    feature_file.write_text("def feature_function():\n    return 'feature'")
    repo.index.add(["feature.py"])
    repo.index.commit("Add feature implementation")

    # Switch back to main and create tag
    repo.heads.master.checkout()
    repo.create_tag("v1.0.0", message="Version 1.0.0")

    return temp_dir
```

### Complex Repository Fixture

```python
@pytest.fixture(scope="session")
def complex_test_repo():
    """
    Create a complex test repository with:
    - 50+ commits
    - Multiple branches with merges
    - Various file types
    - Complex history patterns
    """
    repo_path = create_complex_repository()
    yield repo_path
    cleanup_repository(repo_path)

def create_complex_repository():
    """Create a complex repository for integration testing."""
    import tempfile
    from datetime import datetime, timedelta

    temp_dir = tempfile.mkdtemp(prefix="githound_complex_")
    repo = Repo.init(temp_dir)

    # Configure test user
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create project structure
    create_project_structure(temp_dir)

    # Create commit history with multiple authors
    authors = [
        ("Alice Developer", "alice@example.com"),
        ("Bob Contributor", "bob@example.com"),
        ("Charlie Maintainer", "charlie@example.com")
    ]

    base_date = datetime.now() - timedelta(days=365)

    for i in range(50):
        author_name, author_email = authors[i % len(authors)]
        commit_date = base_date + timedelta(days=i * 7)

        # Modify random files
        modify_random_files(temp_dir, i)

        # Stage changes
        repo.index.add_all()

        # Create commit with specific author and date
        commit_message = generate_commit_message(i)

        with repo.config_writer() as config:
            config.set_value("user", "name", author_name)
            config.set_value("user", "email", author_email)

        repo.index.commit(
            commit_message,
            author_date=commit_date,
            commit_date=commit_date
        )

    # Create branches and merges
    create_branches_and_merges(repo)

    return temp_dir

def create_project_structure(base_path):
    """Create a realistic project structure."""
    base = Path(base_path)

    # Source code
    src_dir = base / "src"
    src_dir.mkdir()

    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text("""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")

    (src_dir / "utils.py").write_text("""
def helper_function(x):
    return x * 2

class UtilityClass:
    def __init__(self, value):
        self.value = value

    def process(self):
        return helper_function(self.value)
""")

    # Tests
    tests_dir = base / "tests"
    tests_dir.mkdir()

    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_main.py").write_text("""
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # Test implementation
        pass
""")

    # Documentation
    docs_dir = base / "docs"
    docs_dir.mkdir()

    (docs_dir / "README.md").write_text("# Project Documentation")
    (docs_dir / "api.md").write_text("# API Documentation")

    # Configuration files
    (base / "requirements.txt").write_text("requests>=2.25.0\npytest>=6.0.0")
    (base / "setup.py").write_text("""
from setuptools import setup, find_packages

setup(
    name="test-project",
    version="1.0.0",
    packages=find_packages(),
)
""")
```

## Mock Objects

### Git Repository Mock

```python
class MockGitRepository:
    """Mock Git repository for unit testing."""

    def __init__(self, commits=None, branches=None, tags=None):
        self.commits = commits or []
        self.branches = branches or ["main"]
        self.tags = tags or []
        self.head = MockHead(self.commits[0] if self.commits else None)

    def iter_commits(self, max_count=None, since=None, until=None):
        """Mock commit iteration."""
        filtered_commits = self.commits

        if since:
            filtered_commits = [c for c in filtered_commits if c.committed_datetime >= since]
        if until:
            filtered_commits = [c for c in filtered_commits if c.committed_datetime <= until]
        if max_count:
            filtered_commits = filtered_commits[:max_count]

        return iter(filtered_commits)

    def commit(self, commit_hash):
        """Get commit by hash."""
        for commit in self.commits:
            if commit.hexsha.startswith(commit_hash):
                return commit
        raise ValueError(f"Commit {commit_hash} not found")

class MockCommit:
    """Mock Git commit for testing."""

    def __init__(self, hexsha, author_name, author_email, message,
                 committed_datetime, files_changed=None):
        self.hexsha = hexsha
        self.author = MockAuthor(author_name, author_email)
        self.message = message
        self.committed_datetime = committed_datetime
        self.stats = MockStats(files_changed or {})

    @property
    def short_hash(self):
        return self.hexsha[:7]

class MockAuthor:
    """Mock Git author for testing."""

    def __init__(self, name, email):
        self.name = name
        self.email = email

class MockStats:
    """Mock Git commit stats for testing."""

    def __init__(self, files):
        self.files = files
        self.total = {
            'insertions': sum(f.get('insertions', 0) for f in files.values()),
            'deletions': sum(f.get('deletions', 0) for f in files.values()),
            'lines': sum(f.get('lines', 0) for f in files.values()),
            'files': len(files)
        }
```

## Data Builders

### Commit Builder

```python
class CommitBuilder:
    """Builder for creating test commit data."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._hexsha = "abc123def456"
        self._author_name = "Test User"
        self._author_email = "test@example.com"
        self._message = "Test commit"
        self._datetime = datetime.now()
        self._files = {}
        return self

    def with_hash(self, hexsha):
        self._hexsha = hexsha
        return self

    def with_author(self, name, email):
        self._author_name = name
        self._author_email = email
        return self

    def with_message(self, message):
        self._message = message
        return self

    def with_datetime(self, dt):
        self._datetime = dt
        return self

    def with_file_changes(self, filename, insertions=0, deletions=0):
        self._files[filename] = {
            'insertions': insertions,
            'deletions': deletions,
            'lines': insertions + deletions
        }
        return self

    def build(self):
        return MockCommit(
            hexsha=self._hexsha,
            author_name=self._author_name,
            author_email=self._author_email,
            message=self._message,
            committed_datetime=self._datetime,
            files_changed=self._files
        )

# Usage example:
def test_commit_analysis():
    commit = (CommitBuilder()
              .with_hash("abc123")
              .with_author("Alice", "alice@example.com")
              .with_message("Fix bug in authentication")
              .with_file_changes("auth.py", insertions=10, deletions=5)
              .build())

    # Test with the built commit
    assert commit.hexsha == "abc123"
    assert commit.author.name == "Alice"
```

## Test Utilities

### Assertion Helpers

```python
def assert_commit_metadata(commit_info, expected_hash=None, expected_author=None):
    """Assert commit metadata matches expectations."""
    if expected_hash:
        assert commit_info.hash.startswith(expected_hash)
    if expected_author:
        assert commit_info.author_name == expected_author

def assert_repository_structure(repo_metadata, min_commits=0, min_contributors=0):
    """Assert repository structure meets minimum requirements."""
    assert repo_metadata['total_commits'] >= min_commits
    assert len(repo_metadata['contributors']) >= min_contributors

def assert_search_results(results, expected_count=None, contains_terms=None):
    """Assert search results meet expectations."""
    if expected_count is not None:
        assert len(results) == expected_count
    if contains_terms:
        for term in contains_terms:
            assert any(term.lower() in str(result).lower() for result in results)
```

### Cleanup Utilities

```python
def cleanup_repository(repo_path):
    """Clean up test repository."""
    if Path(repo_path).exists():
        shutil.rmtree(repo_path, ignore_errors=True)

def cleanup_test_files(file_patterns):
    """Clean up test files matching patterns."""
    for pattern in file_patterns:
        for file_path in Path.cwd().glob(pattern):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path, ignore_errors=True)

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically clean up after each test."""
    yield
    # Cleanup logic runs after each test
    cleanup_test_files(["test_output_*", "temp_*", "*.tmp"])
```
