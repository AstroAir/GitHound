# GitHound MCP Server Setup

Comprehensive guide to install, configure, and run the GitHound MCP server.

## Installation

### Basic Installation

```bash
# Install GitHound with MCP support
pip install githound[mcp]

# Or upgrade FastMCP to 2.0+
pip install "fastmcp>=2.11.0"
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/AstroAir/GitHound.git
cd GitHound

# Install in development mode
pip install -e . --dependency-groups mcp
```

## Quick Start

### Basic Server Startup

```bash
# Start with stdio transport (default)
python -m githound.mcp_server

# Or using the CLI
githound mcp-server
```

### Advanced Server Options

```bash
# Start with HTTP transport
python -m githound.mcp_server --http --port 3000

# Start with SSE transport
python -m githound.mcp_server --sse --host 0.0.0.0 --port 3001

# With custom log level
python -m githound.mcp_server --log-level DEBUG
```

## Configuration

GitHound MCP server supports multiple configuration methods with the following priority:

1. **MCP.json files** (highest priority)
2. **Environment variables**
3. **Command-line arguments**
4. **Default values** (lowest priority)

### MCP.json Configuration

GitHound supports the standard MCP.json configuration format used across the MCP ecosystem. This makes it compatible with Claude Desktop, Cursor, VS Code, and other MCP clients.

#### File Locations

GitHound automatically searches for MCP.json files in these locations:

1. `./mcp.json` (current working directory)
2. `~/.mcp.json` (user home directory)
3. `~/.claude/mcp.json` (Claude Desktop config)
4. `~/.cursor/mcp.json` (Cursor config)
5. `./.vscode/mcp.json` (VS Code workspace config)
6. `~/.githound/mcp.json` (GitHound specific config)

#### Basic MCP.json Example

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

### Environment Variables

Configure the server using environment variables:

```bash
# Server settings
export FASTMCP_SERVER_NAME="GitHound MCP Server"
export FASTMCP_SERVER_VERSION="2.0.0"
export FASTMCP_SERVER_TRANSPORT="stdio"
export FASTMCP_SERVER_HOST="localhost"
export FASTMCP_SERVER_PORT="3000"
export FASTMCP_SERVER_LOG_LEVEL="INFO"

# Authentication settings
export FASTMCP_SERVER_ENABLE_AUTH="false"
export FASTMCP_SERVER_RATE_LIMIT_ENABLED="false"

# Repository settings
export GITHOUND_DEFAULT_REPO="/path/to/repo"
export GITHOUND_CACHE_DIR="/custom/cache/path"
```

### Authentication Configuration

For production deployments, you can enable authentication:

```json
{
  "mcpServers": {
    "githound-secure": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "FASTMCP_SERVER_ENABLE_AUTH": "true",
        "FASTMCP_SERVER_RATE_LIMIT_ENABLED": "true",
        "PERMIT_MCP_API_KEY": "your-permit-api-key",
        "PERMIT_MCP_PROJECT_ID": "your-project-id"
      },
      "description": "GitHound MCP Server with authentication"
    }
  }
}
```

## Client Integration

### Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound"
      }
    }
  }
}
```

### Cursor

Save as `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound"
      }
    }
  }
}
```

### VS Code

Save as `.vscode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound"
      }
    }
  }
}
```

## Verification

Test your setup:

```bash
# Check if the server starts correctly
python -m githound.mcp_server --help

# Test configuration loading
python -c "from githound.mcp.config import get_server_config; print(get_server_config())"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure FastMCP 2.0+ is installed
2. **Configuration Not Found**: Check MCP.json file locations and syntax
3. **Permission Errors**: Verify file permissions and paths
4. **Port Conflicts**: Use different ports for multiple servers

### Debug Mode

Run with debug logging for troubleshooting:

```bash
python -m githound.mcp_server --log-level DEBUG
```

## Next Steps

- Read the [Tools Reference](tools-reference.md) for available MCP tools
- Try the [Integration Examples](integration-examples.md) for practical usage
- See [Configuration Reference](configuration.md) for advanced options
