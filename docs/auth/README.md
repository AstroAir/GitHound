# GitHound MCP Server Authentication

This module provides comprehensive OAuth 2.0 and JWT authentication support for the GitHound MCP server, following the FastMCP authentication patterns.

## Features

- **Multiple Authentication Providers**: Support for JWT verification, OAuth proxy, and full OAuth server
- **Popular OAuth Providers**: Built-in support for GitHub, Google, and Google Workspace
- **Dynamic Client Registration**: Support for MCP's DCR requirements
- **Environment Configuration**: Easy deployment with environment variables
- **Extensible Architecture**: Easy to add custom authentication providers

## Authentication Providers

### 1. JWT Verifier (`JWTVerifier`)

Validates JWT tokens issued by external systems.

**Use Case**: When you already have an authentication system that issues JWTs.

**Configuration**:
```bash
export FASTMCP_SERVER_AUTH="githound.mcp.auth.providers.jwt.JWTVerifier"
export FASTMCP_SERVER_AUTH_JWT_JWKS_URI="https://your-auth-system.com/.well-known/jwks.json"
export FASTMCP_SERVER_AUTH_JWT_ISSUER="https://your-auth-system.com"
export FASTMCP_SERVER_AUTH_JWT_AUDIENCE="mcp-server"
```

### 2. OAuth Proxy (`OAuthProxy`)

Bridges non-DCR OAuth providers with MCP's DCR expectations.

**Use Case**: When using OAuth providers like GitHub or Google that don't support Dynamic Client Registration.

### 3. GitHub Provider (`GitHubProvider`)

OAuth proxy specifically configured for GitHub.

**Configuration**:
```bash
export FASTMCP_SERVER_AUTH="githound.mcp.auth.providers.github.GitHubProvider"
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID="Ov23li..."
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET="github_pat_..."
export FASTMCP_SERVER_BASE_URL="http://localhost:8000"
```

### 4. Google Provider (`GoogleProvider`)

OAuth proxy specifically configured for Google OAuth.

**Configuration**:
```bash
export FASTMCP_SERVER_AUTH="githound.mcp.auth.providers.google.GoogleProvider"
export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID="123456.apps.googleusercontent.com"
export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET="GOCSPX-..."
export FASTMCP_SERVER_BASE_URL="http://localhost:8000"
```

### 5. Full OAuth Server (`OAuthProvider`)

Complete OAuth 2.0 authorization server implementation.

**Use Case**: When you need complete control over the authentication process or operate in air-gapped environments.

## Quick Start

### 1. Environment Configuration

Set the authentication provider and its configuration:

```bash
# Choose your provider
export FASTMCP_SERVER_AUTH="githound.mcp.auth.providers.github.GitHubProvider"

# Configure the provider
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID="your-client-id"
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET="your-client-secret"
export FASTMCP_SERVER_BASE_URL="http://localhost:8000"

# Enable authentication
export FASTMCP_SERVER_ENABLE_AUTH="true"
```

### 2. Start the Server

The server will automatically detect and configure authentication:

```python
from githound.mcp.server import get_mcp_server

# Server automatically uses environment configuration
mcp = get_mcp_server()
```

### 3. Programmatic Configuration

For more control, configure authentication programmatically:

```python
from githound.mcp.auth.providers.github import GitHubProvider
from githound.mcp.auth import set_auth_provider
from githound.mcp.server import get_mcp_server

# Create authentication provider
auth = GitHubProvider(
    client_id="your-github-client-id",
    client_secret="your-github-client-secret",
    base_url="http://localhost:8000"
)

# Set the provider
set_auth_provider(auth)

# Create server
mcp = get_mcp_server()
```

## OAuth Provider Setup

### GitHub OAuth App

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Set Authorization callback URL to: `http://your-server.com/oauth/callback`
4. Copy Client ID and Client Secret
5. Configure environment variables

### Google OAuth

1. Go to Google Cloud Console
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials > Create Credentials > OAuth 2.0 Client IDs
5. Add authorized redirect URI: `http://your-server.com/oauth/callback`
6. Copy Client ID and Client Secret
7. Configure environment variables

## Custom Providers

Create custom authentication providers by extending the base classes:

```python
from githound.mcp.auth.providers.base import AuthProvider, TokenInfo

class CustomProvider(AuthProvider):
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        # Implement your token validation logic
        pass
    
    def get_oauth_metadata(self) -> Optional[Dict[str, Any]]:
        # Return OAuth metadata if applicable
        pass
```

## Security Considerations

1. **Environment Variables**: Store sensitive credentials in environment variables, not in code
2. **HTTPS**: Always use HTTPS in production
3. **Token Validation**: Properly validate all tokens and check expiration
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Logging**: Log authentication events for security monitoring

## Testing

Use the static JWT verifier for development and testing:

```bash
export FASTMCP_SERVER_AUTH="githound.mcp.auth.providers.jwt.StaticJWTVerifier"
export FASTMCP_SERVER_AUTH_JWT_SECRET_KEY="development-secret-key"
export FASTMCP_SERVER_AUTH_JWT_ISSUER="githound-mcp-server"
export FASTMCP_SERVER_AUTH_JWT_AUDIENCE="mcp-client"
```

## Examples

See `examples.py` for complete configuration examples and usage patterns.

## Architecture

The authentication system follows FastMCP's patterns:

- **Token Verification**: For existing JWT infrastructure
- **OAuth Proxy**: For non-DCR OAuth providers
- **Remote Auth Provider**: For DCR-capable providers
- **Full OAuth Server**: For complete control

This architecture allows migration between approaches as requirements evolve.
