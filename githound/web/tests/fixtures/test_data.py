"""
Test data management for GitHound web tests.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


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
            self.data_file.write_text(json.dumps({
                "users": [],
                "repositories": [],
                "search_results": [],
                "exports": []
            }, indent=2))
            
    def create_test_user(self, role: str = "user") -> Dict[str, Any]:
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
            "last_login": None
        }
        
        # Store in test data file
        data = self._load_data()
        data["users"].append(user_data)
        self._save_data(data)
        
        return user_data
        
    def create_test_admin(self) -> Dict[str, Any]:
        """Create test admin user data."""
        return self.create_test_user(role="admin")
        
    def create_search_request_data(self) -> Dict[str, Any]:
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
                "max_results": 100
            },
            "fuzzy_search": False,
            "case_sensitive": False
        }
        
    def create_fuzzy_search_data(self) -> Dict[str, Any]:
        """Create fuzzy search request data."""
        return {
            "repo_path": "/test/repo",
            "query": "functon",  # Intentional typo for fuzzy search
            "search_type": "fuzzy",
            "fuzzy_threshold": 0.8,
            "max_results": 50
        }
        
    def create_historical_search_data(self) -> Dict[str, Any]:
        """Create historical search request data."""
        return {
            "repo_path": "/test/repo",
            "query": "class",
            "search_type": "historical",
            "commit_range": {
                "from": "HEAD~10",
                "to": "HEAD"
            },
            "max_results": 200
        }
        
    def create_sample_search_results(self) -> List[Dict[str, Any]]:
        """Create sample search results."""
        return [
            {
                "file_path": "src/main.py",
                "line_number": 15,
                "content": "def main() -> None:",
                "commit_hash": "abc123def456",
                "author": "test@example.com",
                "commit_date": "2023-01-01T12:00:00Z",
                "commit_message": "Add main function"
            },
            {
                "file_path": "src/utils.py",
                "line_number": 8,
                "content": "def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:",
                "commit_hash": "def456ghi789",
                "author": "another@example.com",
                "commit_date": "2023-01-02T14:30:00Z",
                "commit_message": "Add utility functions"
            },
            {
                "file_path": "src/feature.py",
                "line_number": 12,
                "content": "    def enable_feature(self, feature_name: str) -> None:",
                "commit_hash": "ghi789jkl012",
                "author": "test@example.com",
                "commit_date": "2023-01-03T09:15:00Z",
                "commit_message": "Implement feature management"
            }
        ]
        
    def create_export_request_data(self) -> Dict[str, Any]:
        """Create export request data."""
        return {
            "search_id": str(uuid.uuid4()),
            "format": "json",
            "include_metadata": True,
            "filename": "search_results_export.json"
        }
        
    def create_webhook_data(self) -> Dict[str, Any]:
        """Create webhook configuration data."""
        return {
            "url": "https://example.com/webhook",
            "secret": "webhook_secret_123",
            "events": ["search.completed", "analysis.completed"],
            "active": True
        }
        
    def create_repository_data(self) -> Dict[str, Any]:
        """Create repository configuration data."""
        return {
            "path": "/test/repo",
            "name": "Test Repository",
            "description": "A test repository for GitHound testing",
            "default_branch": "main",
            "is_active": True
        }
        
    def create_blame_request_data(self) -> Dict[str, Any]:
        """Create blame analysis request data."""
        return {
            "file_path": "src/main.py",
            "commit": "HEAD",
            "line_range": [1, 50]
        }
        
    def create_diff_request_data(self) -> Dict[str, Any]:
        """Create diff analysis request data."""
        return {
            "from_commit": "HEAD~1",
            "to_commit": "HEAD",
            "file_patterns": ["*.py"]
        }
        
    def create_branch_diff_data(self) -> Dict[str, Any]:
        """Create branch diff request data."""
        return {
            "from_branch": "main",
            "to_branch": "feature/new-feature",
            "file_patterns": ["*.py", "*.js"]
        }
        
    def get_test_credentials(self) -> Dict[str, str]:
        """Get test user credentials."""
        return {
            "username": "testuser",
            "password": "TestPassword123!",
            "email": "test@example.com"
        }
        
    def get_admin_credentials(self) -> Dict[str, str]:
        """Get test admin credentials."""
        return {
            "username": "admin",
            "password": "AdminPassword123!",
            "email": "admin@example.com"
        }
        
    def _load_data(self) -> Dict[str, Any]:
        """Load data from the test data file."""
        try:
            return json.loads(self.data_file.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "users": [],
                "repositories": [],
                "search_results": [],
                "exports": []
            }
            
    def _save_data(self, data: Dict[str, Any]) -> None:
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
