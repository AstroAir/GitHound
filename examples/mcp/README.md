# GitHound MCP.json Configuration Examples

This directory contains example MCP.json configuration files for GitHound MCP Server, following the standard MCP JSON configuration format used across the MCP ecosystem.

## Overview

GitHound now supports MCP.json configuration files, which provide a standardized way to configure MCP servers that works with various MCP clients including Claude Desktop, Cursor, VS Code, and other MCP-compatible applications.

## Configuration Priority

GitHound uses the following configuration priority order:

1. **MCP.json files** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

## MCP.json File Locations

GitHound automatically searches for MCP.json files in these locations (in order of priority):

1. `./mcp.json` (current working directory)
2. `~/.mcp.json` (user home directory)
3. `~/.claude/mcp.json` (Claude Desktop config location)
4. `~/.cursor/mcp.json` (Cursor config location)
5. `./.vscode/mcp.json` (VS Code workspace config)
6. `~/.githound/mcp.json` (GitHound specific config)

## Example Files

### Basic Configuration
- `mcp.json` - Basic GitHound MCP server configuration
- `claude_desktop_mcp.json` - Configuration for Claude Desktop
- `cursor_mcp.json` - Configuration for Cursor IDE

### Advanced Configuration
- `mcp_with_auth.json` - Multiple server configurations with authentication
- `fastmcp_compatible.json` - FastMCP-compatible configuration using `uv`

## Configuration Structure

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

## GitHound-Specific Environment Variables

You can configure GitHound through environment variables in the `env` section:

- `FASTMCP_SERVER_NAME` - Server display name
- `FASTMCP_SERVER_VERSION` - Server version
- `FASTMCP_SERVER_TRANSPORT` - Transport type (stdio, http, sse)
- `FASTMCP_SERVER_HOST` - Host for HTTP/SSE transports
- `FASTMCP_SERVER_PORT` - Port for HTTP/SSE transports
- `FASTMCP_SERVER_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `FASTMCP_SERVER_ENABLE_AUTH` - Enable authentication (true/false)
- `FASTMCP_SERVER_RATE_LIMIT_ENABLED` - Enable rate limiting (true/false)

## Authentication Configuration

For authentication-enabled configurations, you can include provider-specific environment variables:

### Permit.io Provider
- `PERMIT_MCP_API_KEY` - Your Permit.io API key
- `PERMIT_MCP_PROJECT_ID` - Project ID
- `PERMIT_MCP_ENVIRONMENT_ID` - Environment ID

### Eunomia Provider
- `EUNOMIA_POLICY_FILE` - Path to policy file
- `EUNOMIA_SERVER_NAME` - Server name for policies
- `EUNOMIA_ENABLE_AUDIT_LOGGING` - Enable audit logging

## Usage with Different Clients

### Claude Desktop
Copy the `mcpServers` object from any example into your `~/.claude/claude_desktop_config.json` file.

### Cursor
Save the configuration as `~/.cursor/mcp.json`.

### VS Code
Save the configuration as `.vscode/mcp.json` in your workspace.

### Custom Applications
Use the JSON configuration with any application that supports the MCP protocol.

## Testing Configuration

You can test your MCP.json configuration by running:

```bash
python -m githound.mcp_server
```

GitHound will automatically detect and use your MCP.json configuration, logging which configuration file it found and loaded.
