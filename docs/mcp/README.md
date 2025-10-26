# GitHound MCP Server - FastMCP 2.x Integration

GitHound provides a comprehensive Model Context Protocol (MCP) server implementation built on FastMCP 2.x, enabling AI assistants and applications to interact with Git repositories through a standardized, powerful interface.

## Overview

The GitHound MCP server exposes Git repository analysis capabilities through:

- **Tools**: Execute operations like searching, analyzing commits, comparing branches
- **Resources**: Access repository data like configurations, branches, contributors
- **Prompts**: Pre-built templates for common AI-assisted workflows

## Features

### 🚀 FastMCP 2.x Integration

- **Progress Reporting**: Real-time progress updates for long-running operations
- **Enhanced Logging**: Multiple log levels (debug, info, warning, error, critical)
- **LLM Sampling**: Request AI analysis directly from tools
- **Resource Access**: Cross-server resource reading capabilities
- **Performance Metrics**: Built-in operation timing and throughput tracking

### 🔍 Search Capabilities

- Advanced multi-modal search (content, commits, authors, dates)
- Fuzzy search with configurable thresholds
- Pattern detection and code quality analysis
- Full-text content search with regex support

### 📊 Analysis Tools

- Repository metadata and statistics
- Commit analysis and history tracking
- Branch comparison and diff analysis
- Author contributions and statistics
- File blame and history

### 🔐 Enterprise Features

- Authentication support (Permit.io, Eunomia, custom providers)
- Rate limiting and quota management
- Audit logging
- Multi-transport support (stdio, HTTP, SSE)

## Quick Start

### Installation

```bash
pip install githound[mcp]
# Or with specific FastMCP version
pip install "githound[mcp]" "fastmcp>=2.11.0"
```

### Basic Usage

#### Command Line

```bash
# Start MCP server with stdio transport
python -m githound.mcp

# Start with HTTP transport
python -m githound.mcp --transport http --port 3000
```

#### Programmatic Usage

```python
from githound.mcp import get_mcp_server, run_mcp_server

# Get configured server instance
mcp = get_mcp_server()

# Run the server
run_mcp_server(transport="stdio", log_level="INFO")
```

### Client Integration

#### Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp"],
      "env": {
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Cursor IDE

Create `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp"],
      "description": "GitHound - Advanced Git Repository Analysis"
    }
  }
}
```

## Available Tools

### Search Tools

- `advanced_search` - Multi-modal repository search
- `fuzzy_search` - Fuzzy string matching search
- `content_search` - Full-text content search
- `query_searcher_registry` - Query available searchers

### Analysis Tools

- `analyze_repository` - Comprehensive repository analysis
- `analyze_commit` - Detailed commit analysis
- `analyze_branches` - Branch analysis and comparison
- `analyze_diffs` - Diff analysis between references
- `detect_patterns` - Code pattern detection
- `analyze_statistics` - Statistical analysis

### Blame & History Tools

- `analyze_file_blame` - Line-by-line authorship
- `get_file_history_mcp` - File change history
- `get_commit_history` - Repository commit history
- `compare_commits_diff` - Compare commits
- `compare_branches_diff` - Compare branches
- `get_author_stats` - Author statistics

### Management Tools

- `list_branches` - List repository branches
- `list_tags` - List repository tags
- `list_remotes` - List remote repositories
- `validate_repository` - Check repository integrity

### Export Tools

- `export_repository_data` - Export data in multiple formats (JSON, YAML, CSV, Excel)

### Web Tools

- `start_web_server` - Launch web interface
- `generate_repository_report` - Generate comprehensive report

## Available Resources

Resources provide read-only access to repository data:

- `githound://repository/{repo_path}/config` - Repository configuration
- `githound://repository/{repo_path}/branches` - Branch information
- `githound://repository/{repo_path}/contributors` - Contributor data
- `githound://repository/{repo_path}/summary` - Repository summary
- `githound://repository/{repo_path}/files/{file_path}/history` - File history
- `githound://repository/{repo_path}/commits/{commit_hash}/details` - Commit details
- `githound://repository/{repo_path}/blame/{file_path}` - File blame

## Available Prompts

Pre-built prompt templates for common workflows:

- `investigate_bug_prompt` - Generate prompts for bug investigation
- `prepare_code_review_prompt` - Prepare comprehensive code reviews
- `analyze_performance_regression_prompt` - Analyze performance issues

## FastMCP 2.x Features

### Progress Reporting

```python
from githound.mcp import ProgressTracker

@mcp.tool
async def my_tool(repo_path: str, ctx: Context) -> dict:
    async with ProgressTracker(ctx, "Processing", total=100) as tracker:
        for item in items:
            await process(item)
            await tracker.increment()
    return {"status": "success"}
```

### LLM Sampling

```python
from githound.mcp import request_llm_analysis

@mcp.tool
async def analyze_code(code: str, ctx: Context) -> dict:
    prompt = f"Review this code:\n{code}"
    analysis = await request_llm_analysis(ctx, prompt)
    return {"status": "success", "analysis": analysis}
```

### Enhanced Logging

```python
@mcp.tool
async def my_tool(ctx: Context) -> dict:
    await ctx.debug("Detailed debug info")
    await ctx.info("General information")
    await ctx.warning("Warning message")
    await ctx.error("Error occurred")
    await ctx.critical("Critical failure")
    return {"status": "success"}
```

## Configuration

### Environment Variables

```bash
# Server settings
FASTMCP_SERVER_NAME="GitHound MCP Server"
FASTMCP_SERVER_VERSION="2.0.0"
FASTMCP_SERVER_TRANSPORT="stdio"  # stdio, http, sse
FASTMCP_SERVER_HOST="localhost"
FASTMCP_SERVER_PORT="3000"
FASTMCP_SERVER_LOG_LEVEL="INFO"

# Authentication
FASTMCP_SERVER_ENABLE_AUTH="false"
FASTMCP_SERVER_RATE_LIMIT_ENABLED="false"
```

### MCP.json Configuration

GitHound automatically searches for MCP.json files in:

1. `./mcp.json` (current directory)
2. `~/.mcp.json` (user home)
3. `~/.claude/mcp.json` (Claude Desktop)
4. `~/.cursor/mcp.json` (Cursor IDE)
5. `./.vscode/mcp.json` (VS Code)
6. `~/.githound/mcp.json` (GitHound specific)

## Examples

See the `examples/mcp/` directory for:

- `fastmcp_2x_features.py` - Demonstrates FastMCP 2.x capabilities
- `mcp.json` - Basic server configuration
- `claude_desktop_mcp.json` - Claude Desktop integration
- `cursor_mcp.json` - Cursor IDE integration
- `mcp_with_auth.json` - Authentication examples

## Documentation

- [FastMCP 2.x Migration Guide](./FASTMCP_2X_MIGRATION.md) - Upgrade guide and best practices
- [FastMCP Documentation](https://gofastmcp.com/) - Official FastMCP docs
- [MCP Protocol](https://modelcontextprotocol.io/) - Protocol specification

## Troubleshooting

### Server Won't Start

1. Check FastMCP installation: `pip show fastmcp`
2. Verify Python version >= 3.11
3. Check logs for specific errors

### Tools Not Available

1. Ensure server is running
2. Check client MCP configuration
3. Verify transport compatibility

### Performance Issues

1. Enable caching in search configuration
2. Adjust max_workers for parallel processing
3. Use appropriate max_results limits

## Support

- [GitHub Issues](https://github.com/AstroAir/GitHound/issues)
- [Documentation](https://github.com/AstroAir/GitHound/tree/main/docs)
- [Examples](https://github.com/AstroAir/GitHound/tree/main/examples/mcp)

## License

MIT License - See LICENSE file for details
