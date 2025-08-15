# REST API Examples

This directory contains comprehensive examples for using GitHound's REST API endpoints.

## Examples Overview

- `basic_usage.py` - Basic API usage and authentication
- `search_operations.py` - Search functionality examples
- `repository_analysis.py` - Repository analysis endpoints
- `export_operations.py` - Data export and formatting
- `websocket_examples.py` - Real-time WebSocket communication
- `error_handling.py` - Error handling and validation
- `batch_operations.py` - Batch processing examples

## API Endpoints

### Health and Status
- `GET /health` - API health check
- `GET /api/searches` - List active searches

### Search Operations
- `POST /api/search` - Start new search
- `GET /api/search/{search_id}` - Get search results
- `GET /api/search/{search_id}/status` - Get search status
- `DELETE /api/search/{search_id}` - Cancel search

### Export Operations
- `POST /api/export` - Export search results
- `GET /api/export/{export_id}` - Download exported data

### WebSocket Endpoints
- `WS /ws/{search_id}` - Real-time search progress

## Running Examples

Start the GitHound API server:

```bash
uvicorn githound.web.api:app --reload
```

Then run examples:

```bash
python examples/rest_api/basic_usage.py
python examples/rest_api/search_operations.py
# etc.
```

## Authentication

The API supports various authentication methods:

```python
# API Key authentication
headers = {"X-API-Key": "your-api-key"}

# Bearer token authentication  
headers = {"Authorization": "Bearer your-token"}
```

## Example Request/Response Patterns

### Search Request
```json
{
  "query": "bug fix",
  "repository_path": "/path/to/repo",
  "search_type": "message",
  "filters": {
    "author": "john.doe",
    "date_from": "2023-01-01",
    "date_to": "2023-12-31"
  }
}
```

### Search Response
```json
{
  "results": [...],
  "total_count": 42,
  "search_id": "uuid-here",
  "status": "completed",
  "commits_searched": 1000,
  "files_searched": 500,
  "search_duration_ms": 1250.5
}
```

### Error Response
```json
{
  "error": "Invalid repository path",
  "error_code": "INVALID_REPO",
  "details": {
    "path": "/invalid/path",
    "reason": "Directory does not exist"
  }
}
```

## WebSocket Communication

Real-time progress updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search-id');
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  console.log(`Progress: ${progress.percentage}%`);
};
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (invalid data)
- `500` - Internal Server Error

## Rate Limiting

API includes rate limiting:

- 100 requests per minute per IP
- 10 concurrent searches per user
- WebSocket connections limited to 5 per user
