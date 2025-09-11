"""
Test repository management for GitHound web tests.
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class TestRepositoryManager:
    """Manages test Git repositories for testing."""
    
    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
        self.repositories: Dict[str, Path] = {}
        
    def create_test_repository(self, name: str = "test_repo") -> Path:
        """Create a test repository with sample data."""
        repo_path = self.test_data_dir / name
        
        if repo_path.exists():
            return repo_path
            
        # Initialize repository
        repo_path.mkdir(parents=True, exist_ok=True)
        self._run_git_command(repo_path, ["init"])
        
        # Configure git user
        self._run_git_command(repo_path, ["config", "user.name", "Test User"])
        self._run_git_command(repo_path, ["config", "user.email", "test@example.com"])
        
        # Create sample files and commits
        self._create_sample_content(repo_path)
        
        self.repositories[name] = repo_path
        return repo_path
        
    def create_large_repository(self, name: str = "large_repo") -> Path:
        """Create a larger test repository for performance testing."""
        repo_path = self.test_data_dir / name
        
        if repo_path.exists():
            return repo_path
            
        # Initialize repository
        repo_path.mkdir(parents=True, exist_ok=True)
        self._run_git_command(repo_path, ["init"])
        
        # Configure git user
        self._run_git_command(repo_path, ["config", "user.name", "Test User"])
        self._run_git_command(repo_path, ["config", "user.email", "test@example.com"])
        
        # Create many files and commits
        self._create_large_content(repo_path)
        
        self.repositories[name] = repo_path
        return repo_path
        
    def _create_sample_content(self, repo_path: Path) -> None:
        """Create sample content in the repository."""
        # Create initial file
        readme_file = repo_path / "README.md"
        readme_file.write_text("""# Test Repository

This is a test repository for GitHound testing.

## Features

- Sample Python code
- Configuration files
- Documentation
- Multiple branches and commits
""")
        
        self._run_git_command(repo_path, ["add", "README.md"])
        self._run_git_command(repo_path, ["commit", "-m", "Initial commit: Add README"])
        
        # Create Python files
        src_dir = repo_path / "src"
        src_dir.mkdir()
        
        main_py = src_dir / "main.py"
        main_py.write_text("""#!/usr/bin/env python3
\"\"\"
Main application module.
\"\"\"

import os
import sys
from typing import List, Dict, Any


def main() -> None:
    \"\"\"Main function.\"\"\"
    print("Hello, GitHound!")
    
    # Sample function calls
    config = load_config()
    process_data(config)


def load_config() -> Dict[str, Any]:
    \"\"\"Load configuration from environment.\"\"\"
    return {
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "port": int(os.getenv("PORT", "8000")),
        "host": os.getenv("HOST", "localhost"),
    }


def process_data(config: Dict[str, Any]) -> List[str]:
    \"\"\"Process data with given configuration.\"\"\"
    results = []
    
    if config.get("debug"):
        results.append("Debug mode enabled")
        
    results.append(f"Server: {config['host']}:{config['port']}")
    return results


if __name__ == "__main__":
    main()
""")
        
        utils_py = src_dir / "utils.py"
        utils_py.write_text("""\"\"\"
Utility functions for the application.
\"\"\"

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    \"\"\"Read and parse a JSON file.\"\"\"
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return None


def write_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    \"\"\"Write data to a JSON file.\"\"\"
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON file {file_path}: {e}")
        return False


def format_size(size_bytes: int) -> str:
    \"\"\"Format file size in human-readable format.\"\"\"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
""")
        
        self._run_git_command(repo_path, ["add", "src/"])
        self._run_git_command(repo_path, ["commit", "-m", "Add Python source files"])
        
        # Create configuration files
        config_dir = repo_path / "config"
        config_dir.mkdir()
        
        config_json = config_dir / "config.json"
        config_json.write_text("""{
  "application": {
    "name": "GitHound Test App",
    "version": "1.0.0",
    "debug": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4
  },
  "database": {
    "url": "sqlite:///app.db",
    "echo": false
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}""")
        
        requirements_txt = repo_path / "requirements.txt"
        requirements_txt.write_text("""fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
redis==5.0.1
pytest==7.4.3
playwright==1.40.0
""")
        
        self._run_git_command(repo_path, ["add", "config/", "requirements.txt"])
        self._run_git_command(repo_path, ["commit", "-m", "Add configuration files"])
        
        # Create a feature branch
        self._run_git_command(repo_path, ["checkout", "-b", "feature/new-feature"])
        
        feature_py = src_dir / "feature.py"
        feature_py.write_text("""\"\"\"
New feature implementation.
\"\"\"

from typing import List


class FeatureManager:
    \"\"\"Manages application features.\"\"\"
    
    def __init__(self):
        self.enabled_features: List[str] = []
        
    def enable_feature(self, feature_name: str) -> None:
        \"\"\"Enable a feature.\"\"\"
        if feature_name not in self.enabled_features:
            self.enabled_features.append(feature_name)
            
    def disable_feature(self, feature_name: str) -> None:
        \"\"\"Disable a feature.\"\"\"
        if feature_name in self.enabled_features:
            self.enabled_features.remove(feature_name)
            
    def is_feature_enabled(self, feature_name: str) -> bool:
        \"\"\"Check if a feature is enabled.\"\"\"
        return feature_name in self.enabled_features
        
    def list_features(self) -> List[str]:
        \"\"\"List all enabled features.\"\"\"
        return self.enabled_features.copy()
""")
        
        self._run_git_command(repo_path, ["add", "src/feature.py"])
        self._run_git_command(repo_path, ["commit", "-m", "Add new feature implementation"])
        
        # Switch back to main and merge
        self._run_git_command(repo_path, ["checkout", "main"])
        self._run_git_command(repo_path, ["merge", "feature/new-feature", "--no-ff", "-m", "Merge feature branch"])
        
        # Add some more commits with different authors
        self._run_git_command(repo_path, ["config", "user.name", "Another User"])
        self._run_git_command(repo_path, ["config", "user.email", "another@example.com"])
        
        docs_dir = repo_path / "docs"
        docs_dir.mkdir()
        
        api_md = docs_dir / "api.md"
        api_md.write_text("""# API Documentation

## Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### POST /search
Search functionality.

**Request:**
```json
{
  "query": "search term",
  "filters": {
    "file_type": "py",
    "author": "user@example.com"
  }
}
```

**Response:**
```json
{
  "results": [...],
  "total": 42,
  "page": 1
}
```
""")
        
        self._run_git_command(repo_path, ["add", "docs/"])
        self._run_git_command(repo_path, ["commit", "-m", "Add API documentation"])
        
    def _create_large_content(self, repo_path: Path) -> None:
        """Create a large amount of content for performance testing."""
        # Create many files and commits
        for i in range(50):
            file_path = repo_path / f"file_{i:03d}.py"
            file_path.write_text(f"""# File {i}

def function_{i}():
    \"\"\"Function {i} implementation.\"\"\"
    result = []
    for j in range(100):
        result.append(f"item_{{j}}")
    return result

class Class{i}:
    \"\"\"Class {i} implementation.\"\"\"
    
    def __init__(self):
        self.value = {i}
        
    def method_{i}(self):
        return self.value * 2
""")
            
            if i % 10 == 0:
                self._run_git_command(repo_path, ["add", "."])
                self._run_git_command(repo_path, ["commit", "-m", f"Add files {i-9} to {i}"])
                
        # Final commit for remaining files
        self._run_git_command(repo_path, ["add", "."])
        self._run_git_command(repo_path, ["commit", "-m", "Add remaining files"])
        
    def _run_git_command(self, repo_path: Path, command: List[str]) -> None:
        """Run a git command in the repository."""
        full_command = ["git"] + command
        result = subprocess.run(
            full_command,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Git command failed: {' '.join(full_command)}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )
            
    def cleanup(self) -> None:
        """Clean up all test repositories."""
        for repo_path in self.repositories.values():
            if repo_path.exists():
                # Remove the repository directory
                import shutil
                shutil.rmtree(repo_path)
        self.repositories.clear()
