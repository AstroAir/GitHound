# REST API Reference

GitHound provides a comprehensive REST API for programmatic access to all Git analysis capabilities. The API is built with FastAPI and includes OpenAPI documentation.

## Base URL

```
http://localhost:8000/api
```

## Authentication

The API supports optional JWT-based authentication:

```http
Authorization: Bearer <jwt_token>
```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

## Core Endpoints

### Health Check

Check API health and status.

<span class="api-method get">GET</span> `/health`

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "timestamp": "2023-12-01T10:00:00Z"
}
```

### Repository Analysis

#### Analyze Repository

<span class="api-method post">POST</span> `/repositories/analyze`

Analyze a Git repository and return comprehensive metadata.

**Request Body:**

```json
{
  "repo_path": "/path/to/repository",
  "include_branches": true,
  "include_tags": true,
  "detailed": false
}
```

**Response:**

```json
{
  "repository": {
    "path": "/path/to/repository",
    "name": "my-repo",
    "total_commits": 1250,
    "total_branches": 15,
    "total_tags": 8,
    "contributors": [
      {
        "name": "John Doe",
        "email": "john@example.com",
        "commits": 245,
        "first_commit": "2023-01-15T09:30:00Z",
        "last_commit": "2023-11-30T16:45:00Z"
      }
    ],
    "file_types": {
      "py": 45,
      "js": 32,
      "md": 12
    },
    "created_date": "2023-01-15T09:30:00Z",
    "last_activity": "2023-11-30T16:45:00Z"
  }
}
```

### Search Operations

#### Advanced Search

<span class="api-method post">POST</span> `/search/advanced`

Perform advanced search across repository history.

**Request Body:**

```json
{
  "repo_path": "/path/to/repository",
  "query": {
    "content_pattern": "function",
    "author_pattern": "john.doe",
    "message_pattern": "bug fix",
    "file_patterns": ["*.py", "*.js"],
    "date_from": "2023-01-01",
    "date_to": "2023-12-31",
    "fuzzy_search": true,
    "fuzzy_threshold": 0.8,
    "case_sensitive": false
  },
  "options": {
    "max_results": 100,
    "include_content": true,
    "include_metadata": true
  }
}
```

**Response:**

```json
{
  "results": [
    {
      "commit_hash": "abc123def456",
      "file_path": "src/main.py",
      "line_number": 42,
      "content": "def my_function():",
      "relevance_score": 0.95,
      "commit_info": {
        "author": "John Doe <john@example.com>",
        "date": "2023-11-15T14:30:00Z",
        "message": "Add new function for authentication"
      }
    }
  ],
  "total_results": 1,
  "search_duration_ms": 150,
  "query_id": "search_123456"
}
```

#### Search Status

<span class="api-method get">GET</span> `/search/status/{query_id}`

Get the status of a long-running search operation.

**Response:**

```json
{
  "query_id": "search_123456",
  "status": "completed",
  "progress": 100,
  "results_count": 42,
  "started_at": "2023-12-01T10:00:00Z",
  "completed_at": "2023-12-01T10:00:05Z"
}
```

### File Operations

#### File Blame

<span class="api-method post">POST</span> `/files/blame`

Get line-by-line authorship information for a file.

**Request Body:**

```json
{
  "repo_path": "/path/to/repository",
  "file_path": "src/main.py",
  "line_range": {
    "start": 1,
    "end": 100
  },
  "include_stats": true
}
```

**Response:**

```json
{
  "file_path": "src/main.py",
  "total_lines": 150,
  "lines": [
    {
      "line_number": 1,
      "content": "#!/usr/bin/env python3",
      "commit_hash": "abc123",
      "author": "John Doe <john@example.com>",
      "date": "2023-01-15T09:30:00Z",
      "commit_message": "Initial commit"
    }
  ],
  "contributors": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "lines": 120,
      "percentage": 80.0
    }
  ]
}
```

#### File History

<span class="api-method post">POST</span> `/files/history`

Get the complete history of changes to a specific file.

**Request Body:**

```json
{
  "repo_path": "/path/to/repository",
  "file_path": "src/main.py",
  "max_commits": 50,
  "include_content": false
}
```

### Diff Operations

#### Compare Commits

<span class="api-method post">POST</span> `/diff/commits`

Compare two commits and get detailed diff information.

**Request Body:**

```json
{
  "repo_path": "/path/to/repository",
  "commit1": "abc123",
  "commit2": "def456",
  "file_path": "src/main.py",
  "context_lines": 3
}
```

**Response:**

```json
{
  "commit1": "abc123",
  "commit2": "def456",
  "files_changed": [
    {
      "file_path": "src/main.py",
      "change_type": "modified",
      "lines_added": 15,
      "lines_removed": 8,
      "diff_lines": [
        {
          "line_number": 42,
          "type": "removed",
          "content": "old_function()"
        },
        {
          "line_number": 42,
          "type": "added",
          "content": "new_function()"
        }
      ]
    }
  ],
  "summary": {
    "files_changed": 1,
    "total_lines_added": 15,
    "total_lines_removed": 8
  }
}
```

### Export Operations

#### Export Results

<span class="api-method post">POST</span> `/export`

Export search or analysis results in various formats.

**Request Body:**

```json
{
  "data": {
    "results": [...],
    "metadata": {...}
  },
  "format": "json",
  "options": {
    "pretty_print": true,
    "include_metadata": true,
    "filename": "results.json"
  }
}
```

**Response:**

```json
{
  "export_id": "export_123456",
  "download_url": "/api/exports/download/export_123456",
  "format": "json",
  "size_bytes": 1024,
  "created_at": "2023-12-01T10:00:00Z"
}
```

#### Download Export

<span class="api-method get">GET</span> `/exports/download/{export_id}`

Download an exported file.

**Response:** File download with appropriate content type.

## WebSocket API

Real-time updates and streaming results via WebSocket.

### Connection

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
```

### Search Streaming

```javascript
// Start streaming search
ws.send(
  JSON.stringify({
    type: "search",
    data: {
      repo_path: "/path/to/repo",
      query: {
        content_pattern: "function",
      },
    },
  })
);

// Receive results
ws.onmessage = function (event) {
  const message = JSON.parse(event.data);
  if (message.type === "search_result") {
    console.log("New result:", message.data);
  }
};
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "REPOSITORY_NOT_FOUND",
    "message": "Repository not found at specified path",
    "details": {
      "path": "/invalid/path",
      "suggestion": "Verify the repository path exists"
    }
  },
  "timestamp": "2023-12-01T10:00:00Z",
  "request_id": "req_123456"
}
```

### Common Error Codes

| Code                      | Description                     | HTTP Status |
| ------------------------- | ------------------------------- | ----------- |
| `REPOSITORY_NOT_FOUND`    | Repository path not found       | 404         |
| `INVALID_QUERY`           | Invalid search query parameters | 400         |
| `AUTHENTICATION_REQUIRED` | Authentication token required   | 401         |
| `PERMISSION_DENIED`       | Insufficient permissions        | 403         |
| `RATE_LIMIT_EXCEEDED`     | Too many requests               | 429         |
| `INTERNAL_ERROR`          | Internal server error           | 500         |

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default Limit**: 100 requests per minute per IP
- **Burst Limit**: 20 requests in 10 seconds
- **Headers**: Rate limit information in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701432000
```

## Pagination

Large result sets are paginated:

**Request Parameters:**

```json
{
  "pagination": {
    "page": 1,
    "per_page": 50,
    "max_per_page": 1000
  }
}
```

**Response:**

```json
{
  "results": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 10,
    "total_results": 500,
    "has_next": true,
    "has_prev": false
  }
}
```

## Client Libraries

### Python Client

```python
import requests

class GitHoundClient:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.session = requests.Session()

    def search(self, repo_path, query):
        response = self.session.post(
            f"{self.base_url}/search/advanced",
            json={
                "repo_path": repo_path,
                "query": query
            }
        )
        return response.json()

# Usage
client = GitHoundClient()
results = client.search("/path/to/repo", {
    "content_pattern": "function"
})
```

### JavaScript Client

```javascript
class GitHoundClient {
  constructor(baseUrl = "http://localhost:8000/api") {
    this.baseUrl = baseUrl;
  }

  async search(repoPath, query) {
    const response = await fetch(`${this.baseUrl}/search/advanced`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        repo_path: repoPath,
        query: query,
      }),
    });
    return response.json();
  }
}

// Usage
const client = new GitHoundClient();
const results = await client.search("/path/to/repo", {
  content_pattern: "function",
});
```

## OpenAPI Specification

The complete OpenAPI specification is available at:

- **JSON**: `http://localhost:8000/api/openapi.json`
- **YAML**: `http://localhost:8000/api/openapi.yaml`

## Configuration

### API Server Configuration

```yaml
# config.yaml
web:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["*"]
  auth_enabled: true
  rate_limit:
    requests_per_minute: 100
    burst_size: 20
```

### Environment Variables

```bash
export GITHOUND_WEB_HOST="0.0.0.0"
export GITHOUND_WEB_PORT=8000
export GITHOUND_API_AUTH_ENABLED=true
export GITHOUND_JWT_SECRET="your-secret-key"
```

## Examples

### Complete Search Workflow

```python
import requests
import json

# Initialize client
base_url = "http://localhost:8000/api"

# Analyze repository
analysis = requests.post(f"{base_url}/repositories/analyze", json={
    "repo_path": "/path/to/repo",
    "detailed": True
}).json()

print(f"Repository has {analysis['repository']['total_commits']} commits")

# Perform search
search_results = requests.post(f"{base_url}/search/advanced", json={
    "repo_path": "/path/to/repo",
    "query": {
        "content_pattern": "TODO",
        "file_patterns": ["*.py"]
    },
    "options": {
        "max_results": 50
    }
}).json()

print(f"Found {len(search_results['results'])} TODO items")

# Export results
export_response = requests.post(f"{base_url}/export", json={
    "data": search_results,
    "format": "csv",
    "options": {
        "filename": "todos.csv"
    }
}).json()

# Download export
export_file = requests.get(
    f"{base_url}/exports/download/{export_response['export_id']}"
)

with open("todos.csv", "wb") as f:
    f.write(export_file.content)
```
