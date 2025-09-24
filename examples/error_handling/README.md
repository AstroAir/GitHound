# Error Handling Examples

This directory contains comprehensive examples for handling errors and edge cases in GitHound operations.

## Examples Overview

- `repository_errors.py` - Repository access and validation errors
- `git_operation_errors.py` - Git command and operation failures
- `network_errors.py` - Network and remote repository issues
- `permission_errors.py` - File system and access permission problems
- `validation_errors.py` - Input validation and data format errors
- `recovery_scenarios.py` - Error recovery and retry mechanisms
- `logging_examples.py` - Error logging and monitoring

## Error Categories

### Repository Errors
- Invalid repository paths
- Corrupted repositories
- Missing .git directories
- Bare repository handling
- Submodule issues

### Git Operation Errors
- Invalid commit hashes
- Missing branches or tags
- Merge conflicts
- Detached HEAD states
- Large file handling

### Network Errors
- Remote repository access
- Authentication failures
- Timeout issues
- Connection problems
- SSL/TLS errors

### Permission Errors
- File system permissions
- Read-only repositories
- Locked files
- Access denied scenarios
- Cross-platform issues

### Validation Errors
- Invalid input parameters
- Malformed data
- Type conversion errors
- Schema validation failures
- Range and boundary errors

## Running Examples

```bash
python examples/error_handling/repository_errors.py
python examples/error_handling/git_operation_errors.py
# etc.
```

## Error Handling Patterns

### Basic Error Handling
```python
from githound.git_handler import get_repository
from git import GitCommandError
import logging

def safe_repository_access(repo_path):
    try:
        repo = get_repository(Path(repo_path))
        return repo
    except GitCommandError as e:
        logging.error(f"Git operation failed: {e}")
        return None
    except FileNotFoundError:
        logging.error(f"Repository not found: {repo_path}")
        return None
    except PermissionError:
        logging.error(f"Permission denied: {repo_path}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None
```

### Retry Mechanism
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (GitCommandError, ConnectionError) as e:
                    if attempt == max_retries - 1:
                        raise e
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator
```

### Validation with Error Details
```python
from pydantic import BaseModel, ValidationError
from typing import Optional

def validate_search_request(data):
    try:
        request = SearchRequest(**data)
        return request, None
    except ValidationError as e:
        error_details = {
            "error": "Validation failed",
            "details": []
        }
        for error in e.errors():
            error_details["details"].append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        return None, error_details
```

## Common Error Scenarios

### Invalid Repository Path
```python
# Error: Repository not found
try:
    repo = get_repository(Path("/nonexistent/path"))
except FileNotFoundError as e:
    response = {
        "status": "error",
        "error_code": "REPO_NOT_FOUND",
        "message": "Repository not found",
        "details": {
            "path": "/nonexistent/path",
            "suggestion": "Verify the repository path exists"
        }
    }
```

### Invalid Commit Hash
```python
# Error: Invalid commit reference
try:
    commit = repo.commit("invalid-hash")
except GitCommandError as e:
    response = {
        "status": "error",
        "error_code": "INVALID_COMMIT",
        "message": "Invalid commit hash",
        "details": {
            "commit_hash": "invalid-hash",
            "suggestion": "Use a valid commit hash or reference"
        }
    }
```

### Permission Denied
```python
# Error: Access denied
try:
    repo = get_repository(Path("/restricted/repo"))
except PermissionError as e:
    response = {
        "status": "error",
        "error_code": "ACCESS_DENIED",
        "message": "Permission denied",
        "details": {
            "path": "/restricted/repo",
            "suggestion": "Check file permissions and user access"
        }
    }
```

### Network Timeout
```python
# Error: Network timeout
try:
    remote_data = fetch_remote_repository(url)
except TimeoutError as e:
    response = {
        "status": "error",
        "error_code": "NETWORK_TIMEOUT",
        "message": "Network operation timed out",
        "details": {
            "url": url,
            "timeout_seconds": 30,
            "suggestion": "Check network connectivity and try again"
        }
    }
```

## Error Response Format

### Standard Error Response
```json
{
  "status": "error",
  "error_code": "ERROR_TYPE",
  "message": "Human-readable error message",
  "details": {
    "field": "specific_field",
    "value": "problematic_value",
    "suggestion": "How to fix the issue"
  },
  "timestamp": "2023-11-15T14:30:00Z",
  "request_id": "uuid-here"
}
```

### Validation Error Response
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "details": [
    {
      "field": "repo_path",
      "message": "Field required",
      "type": "missing"
    },
    {
      "field": "date_from",
      "message": "Invalid date format",
      "type": "value_error"
    }
  ]
}
```

## Logging Configuration

### Error Logging Setup
```python
import logging
from pathlib import Path

def setup_error_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('githound_errors.log'),
            logging.StreamHandler()
        ]
    )

    # Set specific loggers
    logging.getLogger('githound.git_handler').setLevel(logging.DEBUG)
    logging.getLogger('githound.mcp_server').setLevel(logging.INFO)
```

## Recovery Strategies

### Graceful Degradation
```python
def analyze_repository_with_fallback(repo_path):
    try:
        # Try full analysis
        return full_repository_analysis(repo_path)
    except GitCommandError:
        try:
            # Fallback to basic analysis
            return basic_repository_analysis(repo_path)
        except Exception:
            # Return minimal information
            return minimal_repository_info(repo_path)
```

### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e
```
