# OpenAPI/Swagger Documentation

GitHound provides comprehensive OpenAPI 3.0 specification for all REST API endpoints, enabling automatic client generation and interactive documentation.

## Interactive Documentation

### Swagger UI

Access the interactive Swagger UI documentation at:

```text
http://localhost:8000/docs
```

Features:

- **Interactive Testing**: Test API endpoints directly from the browser
- **Request/Response Examples**: See example requests and responses
- **Authentication**: Test authenticated endpoints with JWT tokens
- **Schema Validation**: Automatic request/response validation
- **Download Specification**: Download OpenAPI JSON/YAML files

### ReDoc

Access the ReDoc documentation at:

```text
http://localhost:8000/redoc
```

Features:

- **Clean Interface**: Professional documentation layout
- **Code Samples**: Multiple language code examples
- **Schema Explorer**: Interactive schema browsing
- **Search Functionality**: Search across all endpoints
- **Print-Friendly**: Optimized for printing and PDF export

## OpenAPI Specification

### Download Formats

The OpenAPI specification is available in multiple formats:

- **JSON**: `http://localhost:8000/openapi.json`
- **YAML**: `http://localhost:8000/openapi.yaml`

### Specification Details

```yaml
openapi: 3.0.0
info:
  title: GitHound API
  version: 1.0.0
  description: Comprehensive Git repository analysis and search API
  contact:
    name: GitHound Team
    url: https://github.com/AstroAir/GitHound
    email: support@githound.dev
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
```

## API Tags

The API is organized into logical groups using OpenAPI tags:

### Core Operations

- **root**: Root endpoints and basic information
- **health**: Health check and system status endpoints
- **information**: API information and metadata endpoints

### Authentication & Security

- **authentication**: User authentication and authorization endpoints

### Git Operations

- **search**: Advanced search capabilities across Git repositories
- **analysis**: Git analysis, blame, diff, and repository statistics
- **repository**: Repository management and Git operations

### Integration & Real-time

- **integration**: Export, webhook, and integration endpoints
- **websocket**: Real-time WebSocket connections and streaming

## Client Generation

### Supported Languages

The OpenAPI specification can be used to generate clients in multiple languages:

#### Python

```bash
# Using openapi-generator
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./githound-python-client

# Using swagger-codegen
swagger-codegen generate \
  -i http://localhost:8000/openapi.json \
  -l python \
  -o ./githound-python-client
```

#### JavaScript/TypeScript

```bash
# Using openapi-generator
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./githound-ts-client

# Using swagger-codegen
swagger-codegen generate \
  -i http://localhost:8000/openapi.json \
  -l typescript-axios \
  -o ./githound-ts-client
```

#### Java

```bash
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g java \
  -o ./githound-java-client \
  --additional-properties=library=okhttp-gson
```

#### Go

```bash
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g go \
  -o ./githound-go-client
```

### Client Configuration

Generated clients typically support configuration for:

- **Base URL**: API server endpoint
- **Authentication**: JWT token configuration
- **Timeouts**: Request timeout settings
- **Retry Logic**: Automatic retry configuration
- **Rate Limiting**: Client-side rate limiting

## Schema Validation

### Request Validation

All API endpoints include comprehensive request validation:

```json
{
  "type": "object",
  "required": ["repo_path", "query"],
  "properties": {
    "repo_path": {
      "type": "string",
      "description": "Path to Git repository",
      "example": "/path/to/repo"
    },
    "query": {
      "type": "object",
      "properties": {
        "content_pattern": {
          "type": "string",
          "description": "Content search pattern"
        }
      }
    }
  }
}
```

### Response Validation

All responses follow standardized schemas:

```json
{
  "type": "object",
  "required": ["success", "message"],
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Operation success status"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message"
    },
    "data": {
      "type": "object",
      "description": "Response data"
    }
  }
}
```

## Authentication in OpenAPI

### Security Schemes

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token for API authentication
```

### Protected Endpoints

Most endpoints require authentication:

```yaml
paths:
  /api/v1/search/advanced:
    post:
      security:
        - BearerAuth: []
      summary: Advanced search
      description: Perform advanced search with filters
```

## Testing with OpenAPI

### Swagger UI Testing

1. Navigate to `http://localhost:8000/docs`
2. Click "Authorize" button
3. Enter JWT token: `Bearer your-jwt-token`
4. Test endpoints directly in the browser

### Postman Integration

Import the OpenAPI specification into Postman:

1. Open Postman
2. Click "Import"
3. Enter URL: `http://localhost:8000/openapi.json`
4. Configure authentication in collection settings

### Insomnia Integration

Import into Insomnia REST client:

1. Open Insomnia
2. Click "Create" → "Import From"
3. Enter URL: `http://localhost:8000/openapi.json`
4. Set up environment variables for authentication

## Customization

### Adding Custom Fields

To add custom fields to the OpenAPI specification:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="GitHound API",
        version="1.0.0",
        description="Custom description",
        routes=app.routes,
    )

    # Add custom fields
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Custom Response Examples

Add custom examples to endpoints:

```python
@app.post("/api/v1/search/advanced")
async def advanced_search(request: SearchRequest):
    """
    Advanced search endpoint.

    Examples:
        Content search:
            {
                "repo_path": "/path/to/repo",
                "query": {
                    "content_pattern": "function"
                }
            }
    """
    pass
```

## Validation and Testing

### Schema Validation Tools

- **OpenAPI Validator**: Validate specification compliance
- **Spectral**: Lint OpenAPI specifications
- **Swagger Parser**: Parse and validate OpenAPI documents

### Automated Testing

```bash
# Validate OpenAPI specification
swagger-codegen validate -i http://localhost:8000/openapi.json

# Generate and test client
openapi-generator generate -i http://localhost:8000/openapi.json -g python
cd python-client && python -m pytest tests/
```
