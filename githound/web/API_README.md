# GitHound Enhanced API Documentation

## Overview

The GitHound Enhanced API provides comprehensive Git repository analysis and management capabilities through a modern REST API. This enhanced version includes complete coverage of Git operations, advanced analysis features, multi-modal search capabilities, and extensive integration options.

## 🚀 Quick Start

### Starting the API Server

```bash
# Using the enhanced main API
python -m uvicorn githound.web.enhanced_main_api:app --host 0.0.0.0 --port 8000 --reload

# Or using Docker
docker-compose up githound-web
```

### Authentication

1. **Login to get a JWT token:**
```bash
curl -X POST "http://localhost:8000/api/v3/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

2. **Use the token in subsequent requests:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/v3/repository/status?repo_path=/path/to/repo"
```

## 📚 API Documentation

- **Interactive Docs**: http://localhost:8000/api/v3/docs
- **ReDoc**: http://localhost:8000/api/v3/redoc
- **OpenAPI Spec**: http://localhost:8000/api/v3/openapi.json

## 🔧 Core Git Operations

### Repository Management

```bash
# Initialize a new repository
curl -X POST "http://localhost:8000/api/v3/repository/init" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/new/repo", "bare": false}'

# Clone a repository
curl -X POST "http://localhost:8000/api/v3/repository/clone" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo.git", "path": "/local/path"}'

# Get repository status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/repository/path%2Fto%2Frepo/status"
```

### Branch Operations

```bash
# List branches
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/repository/path%2Fto%2Frepo/branches"

# Create a new branch
curl -X POST "http://localhost:8000/api/v3/repository/path%2Fto%2Frepo/branches" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "branch_name": "feature-branch", "checkout": true}'

# Merge branches
curl -X POST "http://localhost:8000/api/v3/repository/path%2Fto%2Frepo/branches/merge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "source_branch": "feature", "target_branch": "main"}'
```

### Commit Operations

```bash
# Create a commit
curl -X POST "http://localhost:8000/api/v3/repository/path%2Fto%2Frepo/commits" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "message": "Add new feature", "all_files": true}'

# Revert a commit
curl -X POST "http://localhost:8000/api/v3/repository/path%2Fto%2Frepo/commits/abc123/revert" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "no_commit": false}'
```

## 📊 Advanced Analysis

### File Blame Analysis

```bash
curl -X POST "http://localhost:8000/api/v3/analysis/blame" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "src/main.py", "line_range": [1, 50]}' \
  -G -d "repo_path=/path/to/repo"
```

### Diff Analysis

```bash
# Compare commits
curl -X POST "http://localhost:8000/api/v3/analysis/diff/commits" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"from_commit": "abc123", "to_commit": "def456", "context_lines": 5}' \
  -G -d "repo_path=/path/to/repo"

# Compare branches
curl -X POST "http://localhost:8000/api/v3/analysis/diff/branches" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"from_branch": "main", "to_branch": "develop"}'
```

### Repository Statistics

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/analysis/repository-stats?repo_path=/path/to/repo&include_author_stats=true"
```

## 🔍 Search & Query

### Advanced Search

```bash
curl -X POST "http://localhost:8000/api/v3/search/advanced" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repo",
    "content_pattern": "function.*search",
    "author_pattern": "john@example.com",
    "file_extensions": ["py", "js"],
    "fuzzy_search": true,
    "fuzzy_threshold": 0.8,
    "max_results": 100
  }'
```

### Fuzzy Search

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/search/fuzzy?repo_path=/path/to/repo&pattern=searhc&threshold=0.7"
```

### Historical Search

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/search/historical?repo_path=/path/to/repo&pattern=deprecated&max_commits=1000"
```

### Real-time Search with WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v3/search/SEARCH_ID/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Search progress:', data.progress);
};
```

## 🔗 Integration Features

### Export Operations

```bash
# Start an export
curl -X POST "http://localhost:8000/api/v3/integration/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "export_type": "repository_metadata",
    "format": "JSON",
    "repo_path": "/path/to/repo",
    "include_metadata": true
  }'

# Check export status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/integration/export/EXPORT_ID/status"

# Download export
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/integration/export/EXPORT_ID/download" \
  -o export.json
```

### Webhook Management

```bash
# Create a webhook
curl -X POST "http://localhost:8000/api/v3/integration/webhooks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["repository.created", "branch.merged", "commit.created"],
    "secret": "your-webhook-secret"
  }'

# List webhooks
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/integration/webhooks"
```

### Batch Operations

```bash
# Start a batch operation
curl -X POST "http://localhost:8000/api/v3/integration/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "status_check",
    "repositories": ["/repo1", "/repo2", "/repo3"],
    "parallel": true,
    "max_concurrent": 3
  }'

# Check batch status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/integration/batch/BATCH_ID/status"
```

## 🔐 Authentication & Authorization

### User Roles

- **admin**: Full access to all operations and management features
- **user**: Standard access to repository operations and analysis
- **read_only**: Read-only access to repository information

### Rate Limits

- **Default**: 100 requests per minute per IP
- **Search**: 10 requests per minute
- **Export**: 5 requests per minute
- **Authentication**: 5 requests per minute
- **Batch Operations**: 3 requests per minute

## 📈 Monitoring & Health

### Health Check

```bash
curl "http://localhost:8000/api/v3/health"
```

### Operation Status

```bash
# Check active searches
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/search/active"

# Get search results
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v3/search/SEARCH_ID/results?page=1&page_size=50"
```

## 🐛 Error Handling

All API responses follow a consistent format:

```json
{
  "success": true|false,
  "message": "Human-readable message",
  "data": {...},
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-string"
}
```

### Common HTTP Status Codes

- **200**: Success
- **201**: Created
- **202**: Accepted (async operation started)
- **400**: Bad Request (validation error)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

## 🔧 Configuration

### Environment Variables

```bash
# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# Rate Limiting
REDIS_URL=redis://localhost:6379/0
API_RATE_LIMIT=100/minute
SEARCH_RATE_LIMIT=10/minute

# Server Configuration
GITHOUND_WEB_HOST=0.0.0.0
GITHOUND_WEB_PORT=8000
GITHOUND_LOG_LEVEL=info
```

## 📝 Examples

See the `/examples` directory for complete usage examples including:
- Python client library usage
- JavaScript/Node.js integration
- Webhook handling examples
- Batch processing scripts
- Search and analysis workflows

## 🤝 Support

- **Documentation**: http://localhost:8000/api/v3/docs
- **Issues**: GitHub Issues
- **API Support**: support@githound.dev
