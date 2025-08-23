# GitHound Web Interface

This directory contains the web interface and API for GitHound, providing a modern web-based interface for advanced Git history searching.

## Architecture

The web interface consists of three main components:

### 1. FastAPI Backend (`api.py`)

- **RESTful API**: Complete REST API for all search functionality
- **Async Operations**: Non-blocking search operations with background tasks
- **Real-time Updates**: WebSocket support for live progress updates
- **Export Functionality**: Multiple export formats (JSON, CSV, text)
- **Error Handling**: Comprehensive error handling and validation
- **Auto Documentation**: Automatic OpenAPI/Swagger documentation

### 2. WebSocket Support (`websocket.py`)

- **Real-time Progress**: Live progress updates during search operations
- **Connection Management**: Robust connection handling with automatic cleanup
- **Broadcasting**: Efficient message broadcasting to multiple clients
- **Heartbeat**: Connection health monitoring with ping/pong
- **Error Recovery**: Graceful handling of connection failures

### 3. Web Frontend (`static/`)

- **Modern Interface**: Responsive Bootstrap-based UI
- **Multi-tab Search**: Organized search options across multiple tabs
- **Real-time Updates**: Live progress bars and result streaming
- **Export Options**: Direct download of results in multiple formats
- **Responsive Design**: Mobile-friendly interface

## API Endpoints

### Core Search Endpoints

- `POST /api/search` - Start a new search operation
- `GET /api/search/{search_id}/status` - Get search status
- `GET /api/search/{search_id}/results` - Get search results
- `DELETE /api/search/{search_id}` - Cancel a search
- `POST /api/search/{search_id}/export` - Export results

### Management Endpoints

- `GET /health` - Health check
- `GET /api/searches` - List all searches
- `DELETE /api/searches/cleanup` - Clean up old searches

### WebSocket Endpoint

- `WS /ws/{search_id}` - Real-time progress updates

### Documentation

- `GET /api/docs` - Swagger UI documentation
- `GET /api/redoc` - ReDoc documentation

## Features

### Search Capabilities

- **Multi-Modal Search**: Content, commit hash, author, message, date range, file path, file type
- **Fuzzy Search**: Configurable fuzzy matching with threshold control
- **Advanced Filtering**: Include/exclude patterns, file size limits, result limits
- **Real-time Results**: Live streaming of search results as they're found

### User Experience

- **Intuitive Interface**: Clean, organized search form with tabbed sections
- **Progress Tracking**: Real-time progress bars with detailed status messages
- **Result Display**: Rich result cards with syntax highlighting and metadata
- **Export Options**: One-click export to JSON, CSV, or text formats
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### Performance

- **Async Operations**: Non-blocking search operations
- **Background Processing**: Search runs in background with real-time updates
- **Connection Pooling**: Efficient WebSocket connection management
- **Caching**: Intelligent caching of search results and metadata

## Usage

### Starting the Server

```python
# Using uvicorn directly
uvicorn githound.web.api:app --host 0.0.0.0 --port 8000 --reload

# Using the provided server script
python -m githound.web.server
```

### API Usage Examples

```python
import requests

# Start a search
response = requests.post('http://localhost:8000/api/search', json={
    'repo_path': '/path/to/repo',
    'content_pattern': 'password',
    'fuzzy_search': True,
    'max_results': 100
})
search_id = response.json()['search_id']

# Check status
status = requests.get(f'http://localhost:8000/api/search/{search_id}/status')
print(status.json())

# Get results
results = requests.get(f'http://localhost:8000/api/search/{search_id}/results')
print(results.json())
```

### WebSocket Usage

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket(`ws://localhost:8000/ws/${searchId}`);

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        case 'progress':
            updateProgress(message.data.progress, message.data.message);
            break;
        case 'result':
            addNewResult(message.data.result);
            break;
        case 'completed':
            handleCompletion(message.data);
            break;
    }
};
```

## Configuration

### Environment Variables

- `GITHOUND_HOST`: Server host (default: 0.0.0.0)
- `GITHOUND_PORT`: Server port (default: 8000)
- `GITHOUND_RELOAD`: Enable auto-reload (default: False)
- `GITHOUND_LOG_LEVEL`: Log level (default: info)

### CORS Configuration

The API is configured to allow all origins by default. For production, update the CORS settings in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## Security Considerations

### Production Deployment

- **CORS**: Restrict allowed origins to your domain
- **Authentication**: Add authentication middleware if needed
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Input Validation**: All inputs are validated using Pydantic models
- **Path Traversal**: Repository paths are validated to prevent directory traversal

### File System Access

- The API requires read access to Git repositories
- Repository paths are validated before access
- No write operations are performed on repositories

## Development

### Adding New Features

1. **API Endpoints**: Add new endpoints in `api.py`
2. **WebSocket Messages**: Extend message types in `websocket.py`
3. **Frontend**: Update the JavaScript application in `static/app.js`
4. **Models**: Add new Pydantic models in `models.py`

### Testing

```bash
# Run the development server
uvicorn githound.web.api:app --reload

# Test API endpoints
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"repo_path": ".", "content_pattern": "test"}'
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**: Check firewall settings and proxy configuration
2. **Search Timeout**: Increase timeout_seconds in search request
3. **Large Repository Performance**: Use max_results and file filters to limit scope
4. **Export Failures**: Check disk space and file permissions

### Logging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Authentication**: User authentication and authorization
- **Search History**: Persistent search history and bookmarks
- **Collaborative Features**: Share searches and results with team members
- **Advanced Visualizations**: Commit timeline and file change visualizations
- **Plugin System**: Extensible plugin architecture for custom search types
