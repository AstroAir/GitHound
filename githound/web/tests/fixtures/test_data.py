"""
Test data management for GitHound web tests.
"""

import json
import random
import string
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class TestDataManager:
    """Manages test data for GitHound web tests."""

    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
        self.data_file = test_data_dir / "test_data.json"
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        """Ensure the test data file exists."""
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self.data_file.write_text(
                json.dumps(
                    {"users": [], "repositories": [], "search_results": [], "exports": []}, indent=2
                )
            )

    def create_test_user(self, role: str = "user") -> dict[str, Any]:
        """Create test user data."""
        user_id = str(uuid.uuid4())
        user_data = {
            "user_id": user_id,
            "username": f"testuser_{user_id[:8]}",
            "email": f"test_{user_id[:8]}@example.com",
            "password": "TestPassword123!",
            "roles": [role],
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
        }

        # Store in test data file
        data = self._load_data()
        data["users"].append(user_data)
        self._save_data(data)

        return user_data

    def create_test_admin(self) -> dict[str, Any]:
        """Create test admin user data."""
        return self.create_test_user(role="admin")

    def create_search_request_data(self) -> dict[str, Any]:
        """Create sample search request data."""
        return {
            "repo_path": "/test/repo",
            "query": "function",
            "search_type": "advanced",
            "filters": {
                "file_types": ["py", "js"],
                "authors": ["test@example.com"],
                "date_from": (datetime.now() - timedelta(days=30)).isoformat(),
                "date_to": datetime.now().isoformat(),
                "max_results": 100,
            },
            "fuzzy_search": False,
            "case_sensitive": False,
        }

    def create_fuzzy_search_data(self) -> dict[str, Any]:
        """Create fuzzy search request data."""
        return {
            "repo_path": "/test/repo",
            "query": "functon",  # Intentional typo for fuzzy search
            "search_type": "fuzzy",
            "fuzzy_threshold": 0.8,
            "max_results": 50,
        }

    def create_historical_search_data(self) -> dict[str, Any]:
        """Create historical search request data."""
        return {
            "repo_path": "/test/repo",
            "query": "class",
            "search_type": "historical",
            "commit_range": {"from": "HEAD~10", "to": "HEAD"},
            "max_results": 200,
        }

    def create_sample_search_results(self) -> list[dict[str, Any]]:
        """Create sample search results."""
        return [
            {
                "file_path": "src/main.py",
                "line_number": 15,
                "content": "def main() -> None:",
                "commit_hash": "abc123def456",
                "author": "test@example.com",
                "commit_date": "2023-01-01T12:00:00Z",
                "commit_message": "Add main function",
            },
            {
                "file_path": "src/utils.py",
                "line_number": 8,
                "content": "def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:",
                "commit_hash": "def456ghi789",
                "author": "another@example.com",
                "commit_date": "2023-01-02T14:30:00Z",
                "commit_message": "Add utility functions",
            },
            {
                "file_path": "src/feature.py",
                "line_number": 12,
                "content": "    def enable_feature(self, feature_name: str) -> None:",
                "commit_hash": "ghi789jkl012",
                "author": "test@example.com",
                "commit_date": "2023-01-03T09:15:00Z",
                "commit_message": "Implement feature management",
            },
        ]

    def create_export_request_data(self) -> dict[str, Any]:
        """Create export request data."""
        return {
            "search_id": str(uuid.uuid4()),
            "format": "json",
            "include_metadata": True,
            "filename": "search_results_export.json",
        }

    def create_webhook_data(self) -> dict[str, Any]:
        """Create webhook configuration data."""
        return {
            "url": "https://example.com/webhook",
            "secret": "webhook_secret_123",
            "events": ["search.completed", "analysis.completed"],
            "active": True,
        }

    def create_repository_data(self) -> dict[str, Any]:
        """Create repository configuration data."""
        return {
            "path": "/test/repo",
            "name": "Test Repository",
            "description": "A test repository for GitHound testing",
            "default_branch": "main",
            "is_active": True,
        }

    def create_blame_request_data(self) -> dict[str, Any]:
        """Create blame analysis request data."""
        return {"file_path": "src/main.py", "commit": "HEAD", "line_range": [1, 50]}

    def create_diff_request_data(self) -> dict[str, Any]:
        """Create diff analysis request data."""
        return {"from_commit": "HEAD~1", "to_commit": "HEAD", "file_patterns": ["*.py"]}

    def create_branch_diff_data(self) -> dict[str, Any]:
        """Create branch diff request data."""
        return {
            "from_branch": "main",
            "to_branch": "feature/new-feature",
            "file_patterns": ["*.py", "*.js"],
        }

    def get_test_credentials(self) -> dict[str, str]:
        """Get test user credentials."""
        return {"username": "testuser", "password": "TestPassword123!", "email": "test@example.com"}

    def get_admin_credentials(self) -> dict[str, str]:
        """Get test admin credentials."""
        return {"username": "admin", "password": "AdminPassword123!", "email": "admin@example.com"}

    def _load_data(self) -> dict[str, Any]:
        """Load data from the test data file."""
        try:
            return json.loads(self.data_file.read_text())  # type: ignore[no-any-return]
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": [], "repositories": [], "search_results": [], "exports": []}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save data to the test data file."""
        self.data_file.write_text(json.dumps(data, indent=2))

    def cleanup(self) -> None:
        """Clean up test data."""
        if self.data_file.exists():
            self.data_file.unlink()

    def reset(self) -> None:
        """Reset test data to initial state."""
        self.cleanup()
        self._ensure_data_file()

    # Enhanced test data generation methods

    def generate_random_string(self, length: int = 10) -> str:
        """Generate a random string for testing."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def generate_test_email(self) -> str:
        """Generate a unique test email."""
        return f"test_{self.generate_random_string(8)}@example.com"

    def generate_test_password(self, include_special: bool = True) -> str:
        """Generate a secure test password."""
        chars = string.ascii_letters + string.digits
        if include_special:
            chars += "!@#$%^&*"
        return "".join(random.choices(chars, k=12))

    def create_invalid_user_data(self) -> list[dict[str, Any]]:
        """Create various invalid user data for testing validation."""
        return [
            {
                "username": "",
                "email": "test@example.com",
                "password": "password123",
            },  # Empty username
            {
                "username": "test",
                "email": "invalid-email",
                "password": "password123",
            },  # Invalid email
            {"username": "test", "email": "test@example.com", "password": "123"},  # Weak password
            {
                "username": "a",
                "email": "test@example.com",
                "password": "password123",
            },  # Short username
            {"username": "test", "email": "", "password": "password123"},  # Empty email
            {"username": "test", "email": "test@example.com", "password": ""},  # Empty password
            {
                "username": "test" * 50,
                "email": "test@example.com",
                "password": "password123",
            },  # Long username
        ]

    def create_performance_test_data(self) -> dict[str, Any]:
        """Create data for performance testing."""
        return {
            "large_query": "function class method import export async await def return",
            "expected_min_results": 100,
            "max_response_time_ms": 5000,
            "concurrent_users": 5,
            "stress_test_duration_seconds": 30,
            "large_file_patterns": ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c"],
            "memory_limit_mb": 512,
        }

    def create_websocket_test_data(self) -> dict[str, Any]:
        """Create data for WebSocket testing."""
        return {
            "connection_timeout_ms": 5000,
            "message_timeout_ms": 1000,
            "max_reconnect_attempts": 3,
            "test_messages": [
                {"type": "search_progress", "data": {"progress": 25, "status": "searching"}},
                {"type": "search_progress", "data": {"progress": 50, "status": "processing"}},
                {"type": "search_progress", "data": {"progress": 75, "status": "formatting"}},
                {"type": "search_complete", "data": {"results_count": 42, "status": "completed"}},
            ],
        }

    def create_accessibility_test_data(self) -> dict[str, Any]:
        """Create data for accessibility testing."""
        return {
            "keyboard_navigation_elements": [
                "login-button",
                "username-input",
                "password-input",
                "submit-login",
                "search-query-input",
                "submit-search",
                "user-menu",
                "logout-button",
            ],
            "aria_labels": ["Search repository", "User menu", "Export results", "Filter options"],
            "color_contrast_elements": ["button", "input", "link", "text", "background"],
            "screen_reader_text": [
                "Search completed",
                "Results found",
                "Error occurred",
                "Loading",
            ],
        }

    def create_export_test_data(self) -> list[dict[str, Any]]:
        """Create various export format test data."""
        base_results = self.create_sample_search_results()
        return [
            {
                "format": "json",
                "filename": "test_export.json",
                "data": base_results,
                "expected_content_type": "application/json",
            },
            {
                "format": "csv",
                "filename": "test_export.csv",
                "data": base_results,
                "expected_content_type": "text/csv",
            },
            {
                "format": "yaml",
                "filename": "test_export.yaml",
                "data": base_results,
                "expected_content_type": "application/x-yaml",
            },
        ]

    def create_error_scenarios(self) -> list[dict[str, Any]]:
        """Create various error scenarios for testing."""
        return [
            {
                "name": "invalid_repository",
                "data": {"repo_path": "/nonexistent/repo", "query": "test"},
                "expected_error": "Repository not found",
            },
            {
                "name": "empty_query",
                "data": {"repo_path": "/test/repo", "query": ""},
                "expected_error": "Query cannot be empty",
            },
            {
                "name": "invalid_file_type",
                "data": {"repo_path": "/test/repo", "query": "test", "file_types": ["invalid"]},
                "expected_error": "Invalid file type",
            },
            {
                "name": "network_timeout",
                "data": {"simulate_timeout": True},
                "expected_error": "Request timeout",
            },
            {
                "name": "server_error",
                "data": {"simulate_server_error": True},
                "expected_error": "Internal server error",
            },
        ]
