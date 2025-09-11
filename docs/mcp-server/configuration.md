# MCP Server Configuration Reference

Complete reference for configuring the GitHound MCP server with MCP.json support, environment variables, and advanced options.

## Configuration Priority

GitHound uses the following configuration priority order:

1. **MCP.json files** (highest priority)
2. **Environment variables**
3. **Command-line arguments**
4. **Default values** (lowest priority)

## MCP.json Configuration

### Overview

GitHound supports the standard MCP.json configuration format used across the MCP ecosystem. This implementation follows the [FastMCP MCP.json specification](https://gofastmcp.com/integrations/mcp-json-configuration) and is compatible with various MCP clients.

### File Discovery

GitHound automatically searches for MCP.json files in these locations (priority order):

1. `./mcp.json` (current working directory)
2. `~/.mcp.json` (user home directory)
3. `~/.claude/mcp.json` (Claude Desktop config location)
4. `~/.cursor/mcp.json` (Cursor config location)
5. `./.vscode/mcp.json` (VS Code workspace config)
6. `~/.githound/mcp.json` (GitHound specific config)

### Configuration Structure

The MCP.json format follows this structure:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      },
      "description": "Server description"
    }
  }
}
```

### Configuration Models

#### MCPServerConfig

Represents a single MCP server configuration with:

- `command`: Executable command (required)
- `args`: Command-line arguments (optional)
- `env`: Environment variables (optional)
- `description`: Server description (optional)

#### MCPJsonConfig

Represents the complete MCP.json structure with:

- `mcpServers`: Dictionary of server configurations
- `get_githound_server()`: Method to find GitHound server configuration

### Example Configurations

#### Basic Configuration

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound MCP Server",
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      },
      "description": "GitHound MCP Server - Comprehensive Git repository analysis"
    }
  }
}
```

#### FastMCP-Compatible Configuration

```json
{
  "mcpServers": {
    "GitHound MCP Server": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "/absolute/path/to/githound/mcp_server.py"
      ],
      "env": {
        "FASTMCP_SERVER_NAME": "GitHound MCP Server",
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Advanced Configuration with Authentication

```json
{
  "mcpServers": {
    "githound-secure": {
      "command": "python",
      "args": ["-m", "githound.mcp_server", "--transport", "http"],
      "env": {
        "FASTMCP_SERVER_TRANSPORT": "http",
        "FASTMCP_SERVER_PORT": "3001",
        "FASTMCP_SERVER_ENABLE_AUTH": "true",
        "FASTMCP_SERVER_RATE_LIMIT_ENABLED": "true",
        "PERMIT_MCP_API_KEY": "your-api-key",
        "PERMIT_MCP_PROJECT_ID": "your-project-id"
      },
      "description": "GitHound MCP Server with authentication and rate limiting"
    }
  }
}
```

## Environment Variables

### Server Configuration

- `FASTMCP_SERVER_NAME` - Server display name (default: "GitHound MCP Server")
- `FASTMCP_SERVER_VERSION` - Server version (default: "2.0.0")
- `FASTMCP_SERVER_TRANSPORT` - Transport type: stdio, http, sse (default: "stdio")
- `FASTMCP_SERVER_HOST` - Host for HTTP/SSE transports (default: "localhost")
- `FASTMCP_SERVER_PORT` - Port for HTTP/SSE transports (default: "3000")
- `FASTMCP_SERVER_LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: "INFO")

### Authentication & Security

- `FASTMCP_SERVER_ENABLE_AUTH` - Enable authentication (default: "false")
- `FASTMCP_SERVER_RATE_LIMIT_ENABLED` - Enable rate limiting (default: "false")

### Authentication Providers

#### Permit.io Provider

- `PERMIT_MCP_API_KEY` - Your Permit.io API key
- `PERMIT_MCP_PROJECT_ID` - Project ID
- `PERMIT_MCP_ENVIRONMENT_ID` - Environment ID
- `PERMIT_MCP_PDP_URL` - PDP URL (default: "http://localhost:7766")

#### Eunomia Provider

- `EUNOMIA_POLICY_FILE` - Path to policy file (default: "mcp_policies.json")
- `EUNOMIA_SERVER_NAME` - Server name for policies (default: "githound-mcp")
- `EUNOMIA_ENABLE_AUDIT_LOGGING` - Enable audit logging (default: "true")

### Repository Settings

- `GITHOUND_DEFAULT_REPO` - Default repository path
- `GITHOUND_CACHE_DIR` - Cache directory path
- `GITHOUND_MAX_RESULTS` - Maximum search results (default: 1000)
- `GITHOUND_FUZZY_THRESHOLD` - Fuzzy search threshold (default: 0.8)

## Client-Specific Configurations

### Claude Desktop

Configuration file: `~/.claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Cursor

Configuration file: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound MCP Server for Cursor"
      }
    }
  }
}
```

### VS Code

Configuration file: `.vscode/mcp.json` (in workspace)

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Configuration Functions

### Core Functions

- `find_mcp_json_files() -> list[Path]` - Discovers MCP.json files in standard locations
- `load_mcp_json_config(config_path: Path) -> MCPJsonConfig | None` - Loads and validates MCP.json
- `get_server_config_from_mcp_json(mcp_config: MCPJsonConfig) -> ServerConfig | None` - Extracts GitHound config
- `get_server_config() -> ServerConfig` - Main configuration function with priority handling

### GitHound Server Detection

The system automatically detects GitHound servers in MCP.json by looking for:

1. **Exact name matches**: "githound", "GitHound", "git-hound", "git_hound"
2. **Partial name matches**: Any server name containing "githound"
3. **Module detection**: Servers using "githound.mcp_server" in args

## Error Handling

The configuration system includes robust error handling:

- **Invalid JSON files** are logged and skipped
- **Missing required fields** are validated with clear error messages
- **Circular import issues** are avoided with lazy loading
- **Graceful fallback** to environment variables and defaults

## Validation

Configuration validation includes:

- **Command validation**: Ensures command is not empty
- **Server validation**: At least one server must be configured
- **Environment variable parsing**: Proper type conversion and validation
- **Path validation**: File and directory existence checks

## Best Practices

1. **Use MCP.json for client compatibility** - Ensures your configuration works across different MCP clients
2. **Set appropriate log levels** - Use DEBUG for development, INFO for production
3. **Configure authentication for production** - Enable auth and rate limiting for public deployments
4. **Use absolute paths** - Ensures configuration works regardless of working directory
5. **Test configuration changes** - Verify server starts correctly after configuration changes

## Troubleshooting

### Configuration Not Loading

1. Check file locations and permissions
2. Validate JSON syntax
3. Verify required fields are present
4. Check log output for specific errors

### Server Detection Issues

1. Ensure server name contains "githound" or uses the module
2. Check command and args configuration
3. Verify environment variables are properly set

### Authentication Problems

1. Verify API keys and credentials
2. Check provider-specific environment variables
3. Ensure authentication providers are installed
