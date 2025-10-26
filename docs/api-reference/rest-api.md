# REST API Reference

GitHound provides a comprehensive REST API for programmatic access to all Git analysis capabilities. The API is built with FastAPI and includes OpenAPI documentation with versioned endpoints.

## Base URL

```text
http://localhost:8000/api/v1
```

## Authentication

The API supports multiple authentication mechanisms with fine-grained access control:

### JWT Authentication

Standard JWT-based authentication with role-based access control:

```http
Authorization: Bearer <jwt_token>
```

### Advanced Authentication Providers

GitHound supports enterprise-grade authentication providers:

- **Permit.io**: Role-Based Access Control (RBAC) with policy management
- **Eunomia**: Attribute-Based Access Control (ABAC) with fine-grained permissions

### Authentication Endpoints

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/change-password` - Password change
- `GET /api/v1/auth/profile` - User profile
- `PUT /api/v1/auth/profile` - Update user profile
- `GET /api/v1/auth/users` - List all users (admin only)

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **API Info**: `http://localhost:8000/api/info`

## Core Endpoints

## Search API

### Advanced Search

Perform advanced search with multiple criteria and filters.

**POST** `/api/v1/search/advanced`

**Request Body:**

```json
{
  "repo_path": "/path/to/repo",
  "content_pattern": "function",
  "author_pattern": "john",
  "message_pattern": "fix",
  "date_from": "2023-01-01T00:00:00Z",
  "date_to": "2023-12-31T23:59:59Z",
  "file_extensions": ["py", "js"],
  "fuzzy_search": true,
  "fuzzy_threshold": 0.8,
  "max_results": 100
}
```

**Response:**

```json
{
  "results": [...],
  "total_count": 42,
  "search_id": "uuid-string",
  "status": "completed",
  "commits_searched": 1000,
  "files_searched": 500,
  "search_duration_ms": 1500.0
}
```

### Fuzzy Search

Perform fuzzy search with similarity thresholds.

**GET** `/api/v1/search/fuzzy`

**Query Parameters:**

- `repo_path` (required): Repository path
- `pattern` (required): Search pattern
- `threshold` (optional): Similarity threshold (0.0-1.0, default: 0.8)
- `max_distance` (optional): Maximum edit distance (default: 2)
- `file_types` (optional): File types to search

### Historical Search

Search across entire repository history timeline.

**GET** `/api/v1/search/historical`

**Query Parameters:**

- `repo_path` (required): Repository path
- `pattern` (required): Search pattern
- `max_commits` (optional): Maximum commits to search (default: 1000)
- `date_from` (optional): Start date
- `date_to` (optional): End date

### Search Status

Get the status of a running search operation.

**GET** `/api/v1/search/status/{search_id}`

**Response:**

```json
{
  "search_id": "uuid-string",
  "status": "running",
  "progress": 0.75,
  "message": "Searching commits...",
  "commits_searched": 750,
  "files_searched": 300,
  "results_found": 42,
  "started_at": "2023-11-15T14:30:00Z",
  "estimated_completion": "2023-11-15T14:32:00Z"
}
```

## Analysis API

### File Blame Analysis

Analyze line-by-line authorship for files.

**POST** `/api/v1/analysis/blame`

**Request Body:**

```json
{
  "repo_path": "/path/to/repo",
  "file_path": "src/main.py",
  "commit": "abc123",
  "line_range": [1, 100]
}
```

### Commit Comparison

Compare two commits with detailed diff information.

**POST** `/api/v1/analysis/diff/commits`

**Request Body:**

```json
{
  "repo_path": "/path/to/repo",
  "from_commit": "abc123",
  "to_commit": "def456",
  "file_path": "src/main.py"
}
```

### Branch Comparison

Compare two branches with detailed analysis.

**POST** `/api/v1/analysis/diff/branches`

**Request Body:**

```json
{
  "repo_path": "/path/to/repo",
  "from_branch": "main",
  "to_branch": "feature-branch"
}
```

## Repository API

### Repository Status

Get repository status and metadata.

**GET** `/api/v1/repository/status`

**Query Parameters:**

- `repo_path` (required): Repository path

### Branch Management

Create and manage repository branches.

**POST** `/api/v1/repository/branches`

**Request Body:**

```json
{
  "repo_path": "/path/to/repo",
  "branch_name": "feature-branch",
  "base_branch": "main"
}
```

## Integration API

### Export Data

Export search results and analysis data.

**POST** `/api/v1/integration/export`

**Request Body:**

```json
{
  "repo_path": "/path/to/repo",
  "search_id": "uuid-string",
  "format": "json",
  "include_metadata": true,
  "filters": {
    "file_types": ["py"],
    "date_range": ["2023-01-01", "2023-12-31"]
  }
}
```

### Repository Analysis

#### Analyze Repository

**POST** `/api/v1/analysis/repository`

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

## Rate Limiting

The API implements Redis-backed rate limiting with slowapi to ensure fair usage:

- **Search endpoints**: 15 requests per minute
- **Analysis endpoints**: 10 requests per minute
- **Export endpoints**: 3 requests per minute
- **Authentication endpoints**: 5 requests per minute
- **Global limit**: 1000 requests per hour for authenticated users

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 15
X-RateLimit-Remaining: 14
X-RateLimit-Reset: 1640995200
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "success": false,
  "message": "Validation error",
  "data": null,
  "request_id": "uuid-string",
  "timestamp": "2023-12-01T10:00:00Z",
  "errors": [
    {
      "field": "repo_path",
      "message": "Repository path is required"
    }
  ]
}
```

### Common Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## WebSocket API

Real-time updates are available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{connection_id}');

// Subscribe to search updates
ws.send(JSON.stringify({
    type: 'subscribe',
    data: { search_id: 'your-search-id' }
}));

// Handle real-time updates
ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log('Search progress:', update.progress);
};
```

## Examples

### Complete Search Workflow

```bash
# 1. Authenticate
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# 2. Start search
curl -X POST http://localhost:8000/api/v1/search/advanced \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "content_pattern": "function"}'

# 3. Export results
curl -X POST http://localhost:8000/api/v1/integration/export \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"search_id": "uuid", "format": "json"}'
```

## Response Schemas

All API responses follow standardized schemas for consistency and validation.

### Standard API Response

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    "key": "value"
  },
  "request_id": "req_123456",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

### Search Result Schema

```json
{
  "commit_hash": "abc123def456",
  "file_path": "src/main.py",
  "line_number": 42,
  "matching_line": "def my_function():",
  "search_type": "content",
  "relevance_score": 0.95,
  "match_context": [
    "# Previous line",
    "def my_function():",
    "# Next line"
  ],
  "commit_info": {
    "author": "John Doe <john@example.com>",
    "date": "2023-11-15T14:30:00Z",
    "message": "Add new function for authentication",
    "hash": "abc123def456"
  },
  "match_metadata": {
    "fuzzy_score": 0.85,
    "pattern_matched": "function"
  }
}
```

### Search Response Schema

```json
{
  "results": [
    {
      "commit_hash": "abc123",
      "file_path": "src/main.py",
      "line_number": 42,
      "matching_line": "def function():",
      "search_type": "content",
      "relevance_score": 0.95,
      "match_context": ["line1", "line2", "line3"],
      "commit_info": {
        "author": "John Doe <john@example.com>",
        "date": "2023-11-15T14:30:00Z",
        "message": "Add function",
        "hash": "abc123"
      }
    }
  ],
  "total_count": 42,
  "search_id": "search_123456",
  "status": "completed",
  "commits_searched": 1000,
  "files_searched": 500,
  "search_duration_ms": 1500.0,
  "error_message": null
}
```

### Repository Analysis Schema

```json
{
  "path": "/path/to/repo",
  "name": "my-repository",
  "is_bare": false,
  "current_branch": "main",
  "head_commit": "abc123def456",
  "total_commits": 1500,
  "total_branches": 12,
  "total_tags": 8,
  "contributors": [
    "John Doe <john@example.com>",
    "Jane Smith <jane@example.com>"
  ],
  "last_commit_date": "2023-11-30T16:45:00Z",
  "repository_size_mb": 45.2,
  "file_types": {
    "py": 45,
    "js": 32,
    "md": 12,
    "json": 8
  },
  "branches": [
    {
      "name": "main",
      "commit": "abc123",
      "is_current": true,
      "last_commit_date": "2023-11-30T16:45:00Z"
    }
  ],
  "tags": [
    {
      "name": "v1.0.0",
      "commit": "def456",
      "date": "2023-10-15T10:30:00Z"
    }
  ]
}
```

### File Blame Schema

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
      "percentage": 80.0,
      "first_commit": "2023-01-15T09:30:00Z",
      "last_commit": "2023-11-30T16:45:00Z"
    }
  ],
  "file_stats": {
    "total_lines": 150,
    "blank_lines": 15,
    "comment_lines": 25,
    "code_lines": 110
  }
}
```

### Diff Comparison Schema

```json
{
  "from_commit": "abc123",
  "to_commit": "def456",
  "files_changed": 3,
  "total_additions": 25,
  "total_deletions": 12,
  "file_diffs": [
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
    "files_changed": 3,
    "total_lines_added": 25,
    "total_lines_removed": 12,
    "net_change": 13
  }
}
```

## WebSocket API

GitHound provides real-time WebSocket endpoints for streaming search results and live updates.

### WebSocket Endpoints

#### Real-time Search

**WebSocket** `/ws/search`

Stream search results in real-time as they are discovered.

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search');
```

**Message Format:**

```json
{
  "type": "search_request",
  "data": {
    "repo_path": "/path/to/repo",
    "content_pattern": "function",
    "max_results": 100
  }
}
```

**Response Stream:**

```json
{
  "type": "search_result",
  "data": {
    "match": {
      "file_path": "src/main.py",
      "line_number": 42,
      "content": "def function_name():",
      "commit_hash": "abc123"
    },
    "progress": {
      "files_processed": 150,
      "total_files": 500,
      "percentage": 30
    }
  }
}
```

#### Repository Monitoring

**WebSocket** `/ws/monitor/{repo_id}`

Monitor repository changes and receive real-time notifications.

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/monitor/repo123');
```

**Event Types:**

- `commit_added` - New commit detected
- `branch_created` - New branch created
- `tag_created` - New tag created
- `file_changed` - File modification detected

### WebSocket Authentication

WebSocket connections support the same authentication mechanisms as REST endpoints:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search', [], {
  headers: {
    'Authorization': 'Bearer <jwt_token>'
  }
});
```

### Rate Limiting

WebSocket connections are subject to rate limiting:

- **Connection limit**: 10 concurrent connections per user
- **Message rate**: 100 messages per minute
- **Data transfer**: 10MB per minute

### Export Response Schema

```json
{
  "export_id": "export_123456",
  "status": "completed",
  "download_url": "/api/integration/export/export_123456/download",
  "filename": "search_results.json",
  "file_size": 2048,
  "format": "json",
  "created_at": "2023-12-01T10:00:00Z",
  "expires_at": "2023-12-08T10:00:00Z"
}
```

### Pagination Schema

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 10,
    "total_items": 500,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  },
  "total_count": 500,
  "request_id": "req_123456",
  "timestamp": "2023-12-01T10:00:00Z"
}
```
