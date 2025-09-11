# GitHound Web Interface

A modern, responsive web interface for GitHound that provides comprehensive Git repository analysis and search capabilities through an intuitive browser-based interface.

## Features

- **Advanced Search**: Powerful search capabilities with multiple filters and real-time results
- **Repository Analysis**: Comprehensive Git analysis including blame, diff, and statistics
- **Real-time Updates**: WebSocket-powered live progress updates during operations
- **Export Functionality**: Export results in multiple formats (JSON, CSV, YAML)
- **Authentication**: JWT-based authentication with role-based access control
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Responsive Design**: Mobile-friendly interface that works on all devices

## Quick Start

### Development Server

```bash
# Start the development server
python -m githound.web.main

# Or use the test interface script
python githound/web/scripts/test_interface.py
```

The web interface will be available at `http://localhost:8000`.

### Production Deployment

```bash
# Install production dependencies
pip install uvicorn[standard] gunicorn

# Run with Gunicorn
gunicorn githound.web.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## New Architecture

The web interface has been completely refactored with a clean, modular architecture:

### Directory Structure

```text
githound/web/
├── main.py                    # Main FastAPI application entry point
├── apis/                      # API route modules
│   ├── auth_api.py           # Authentication endpoints
│   ├── search_api.py         # Search functionality
│   ├── analysis_api.py       # Git analysis endpoints
│   ├── repository_api.py     # Repository management
│   └── integration_api.py    # Export, webhooks, batch operations
├── core/                      # Core business logic
│   ├── search_orchestrator.py # Unified search orchestrator
│   └── git_operations.py     # Git operations manager
├── services/                  # Service layer
│   ├── auth_service.py       # Authentication service
│   ├── webhook_service.py    # Webhook management
│   └── websocket_service.py  # WebSocket connections
├── middleware/                # FastAPI middleware
│   └── rate_limiting.py      # Rate limiting configuration
├── models/                    # Data models
│   ├── api_models.py         # API request/response models
│   └── auth_models.py        # Authentication models
├── utils/                     # Utility functions
│   └── validation.py         # Input validation helpers
├── scripts/                   # Helper scripts
│   ├── server.py             # Server management
│   └── test_interface.py     # Development testing
└── static/                    # Frontend assets
    ├── index.html
    ├── style.css
    └── app.js
```

### Key Improvements

1. **Modular API Design**: APIs are organized by functionality (search, analysis, auth, etc.)
2. **Service Layer**: Business logic separated into dedicated service classes
3. **Consolidated Models**: All Pydantic models organized by purpose
4. **Unified Search**: Single search orchestrator eliminates duplication
5. **Clean Dependencies**: Proper import structure and dependency injection
6. **Standardized Naming**: Consistent PascalCase for classes, snake_case for files

## API Documentation

Once the server is running, visit:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# Rate Limiting (Redis)
REDIS_URL=redis://localhost:6379/0

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Server Settings
HOST=0.0.0.0
PORT=8000
```

### Authentication

The web interface supports JWT-based authentication with role-based access control:

- **Admin**: Full access to all features including user management
- **User**: Standard access to search and analysis features
- **Read-only**: Limited access to view-only operations

## API Endpoints

### Authentication API (`/api/v1/auth/`)

- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /profile` - User profile
- `POST /change-password` - Password change
- `POST /refresh` - Token refresh

### Search API (`/api/v1/search/`)

- `POST /advanced` - Advanced search with filters
- `POST /fuzzy` - Fuzzy search capabilities
- `POST /historical` - Historical search across commits
- `GET /status/{search_id}` - Get search status

### Analysis API (`/api/v1/analysis/`)

- `POST /blame` - File blame analysis
- `POST /diff/commits` - Commit comparison
- `POST /diff/branches` - Branch comparison
- `POST /commits/filter` - Filtered commit history
- `GET /file-history` - File change history

### Repository API (`/api/v1/repository/`)

- `POST /init` - Initialize repository
- `POST /clone` - Clone repository
- `GET /status` - Repository status
- `POST /branches` - Create branch
- `POST /commits` - Create commit
- `POST /tags` - Create tag

### Integration API (`/api/v1/integration/`)

- `POST /export` - Export search results
- `POST /export/batch` - Batch export
- `POST /webhooks` - Create webhook
- `GET /webhooks` - List webhooks

## WebSocket Support

Real-time updates are provided via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{connection_id}');

// Subscribe to search updates
ws.send(JSON.stringify({
    type: 'subscribe',
    data: { search_id: 'your-search-id' }
}));

// Handle progress updates
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'progress') {
        console.log('Progress:', message.data.progress);
    }
};
```

## Development

### Adding New Features

1. **API Endpoints**: Add new routes to appropriate API module in `apis/`
2. **Models**: Define Pydantic models in `models/`
3. **Services**: Add business logic to `services/`
4. **Authentication**: Use decorators from `services/auth_service.py`
5. **Frontend**: Update `static/` files for UI changes

### Testing

```bash
# Run the test interface
python githound/web/scripts/test_interface.py

# Test API endpoints
curl -X POST http://localhost:8000/api/v1/search/advanced \
  -H "Content-Type: application/json" \
  -d '{"query": "function", "repo_path": "/path/to/repo"}'
```

## Migration from Old Structure

The refactoring consolidated several duplicate API files:

- `api.py`, `enhanced_api.py`, `comprehensive_api.py`, `enhanced_main_api.py` → Consolidated into modular APIs
- Moved authentication logic to `services/auth_service.py`
- Centralized search orchestration in `core/search_orchestrator.py`
- Organized models by purpose in `models/`

All functionality has been preserved while eliminating duplication and improving maintainability.

## Security

- **JWT Tokens**: Secure authentication with configurable expiration
- **Rate Limiting**: Prevents API abuse with Redis-backed limiting
- **CORS**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation with Pydantic
- **Error Handling**: Secure error responses without information leakage

## Performance

- **Async Operations**: Non-blocking I/O for better concurrency
- **Background Tasks**: Long-running operations handled asynchronously
- **Caching**: Redis-based caching for improved response times
- **Connection Pooling**: Efficient database and Redis connections

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find and kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Redis Connection Error**
   ```bash
   # Start Redis server
   redis-server
   ```

3. **CORS Issues**
   ```bash
   # Add your frontend URL to ALLOWED_ORIGINS
   export ALLOWED_ORIGINS=http://localhost:3000
   ```

### Logs

Check application logs for detailed error information:
```bash
# View logs with timestamps
python -m githound.web.main 2>&1 | tee web.log
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure all endpoints have proper authentication
5. Test with different user roles and permissions
6. Maintain the modular architecture when adding features

## License

This web interface is part of the GitHound project and follows the same license terms.
