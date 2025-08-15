# FastMCP Server Examples

This directory contains comprehensive examples demonstrating how to build and use MCP (Model Context Protocol) servers with FastMCP 2.x framework. These examples showcase real-world usage patterns, best practices, and advanced features for both server and client implementations.

**Updated for FastMCP 2.11.3** - All examples have been updated to use the latest FastMCP 2.x API with modern features like authentication, server composition, middleware, and enhanced transports.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FastMCP framework installed
- Git (for GitHound examples)

### Installation

```bash
# From GitHound root directory
cd examples/mcp_server

# Install dependencies (if not already installed)
pip install fastmcp pytest pytest-asyncio
```

### Running Examples

```bash
# Basic client example (start here)
python examples/mcp_server/clients/basic_client.py

# Transport layer examples (FastMCP 2.x transports)
python examples/mcp_server/clients/transport_examples.py

# Tool operations (discovery, execution, error handling)
python examples/mcp_server/clients/tool_operations.py

# Resource operations (static and templated resources)
python examples/mcp_server/clients/resource_operations.py

# Prompt operations (template usage and arguments)
python examples/mcp_server/clients/prompt_operations.py

# Authentication examples (Bearer token & OAuth 2.1)
python examples/mcp_server/clients/authentication_examples.py

# Multi-server client (composition and failover)
python examples/mcp_server/clients/multi_server_client.py

# Advanced features (progress monitoring, logging)
python examples/mcp_server/clients/advanced_features.py

# GitHound-specific client example
python examples/mcp_server/clients/githound_client.py /path/to/repo
```

## 📁 Directory Structure

```
examples/mcp_server/
├── README.md                     # This file
├── requirements.txt              # Dependencies
├── servers/                      # MCP Server implementations
│   ├── __init__.py
│   ├── githound_server.py       # GitHound MCP server
│   └── simple_server.py         # Basic example server
├── clients/                     # FastMCP Client examples
│   ├── __init__.py
│   ├── basic_client.py          # Basic client setup
│   ├── transport_examples.py    # Transport layer examples
│   ├── tool_operations.py       # Tool discovery and execution
│   ├── resource_operations.py   # Resource access patterns
│   ├── prompt_operations.py     # Prompt template usage
│   ├── advanced_features.py     # Auth, progress, logging
│   ├── authentication_examples.py # Bearer token & OAuth 2.1
│   ├── githound_client.py       # GitHound-specific client
│   └── multi_server_client.py   # Multi-server configuration
├── tests/                       # Comprehensive test suite
│   ├── __init__.py
│   ├── test_servers.py
│   ├── test_clients.py
│   ├── test_integration.py
│   └── conftest.py
└── utils/                       # Shared utilities
    ├── __init__.py
    ├── git_operations.py        # Git metadata helpers
    └── test_helpers.py          # Testing utilities
```

## 🔧 FastMCP 2.x Features Demonstrated

### Core Operations
- **Client Setup**: Modern `Client` class with automatic transport detection
- **Tool Operations**: Discovery, execution, structured data handling
- **Resource Operations**: Static and templated resource access with proper URI handling
- **Prompt Operations**: Template usage with type conversion and argument serialization

### FastMCP 2.x Advanced Features
- **Authentication**: Bearer token and OAuth 2.1 support (FastMCP 2.6+)
- **Server Composition**: Multi-server client configuration and failover patterns
- **Modern Transports**: StreamableHttpTransport, FastMCPTransport for testing
- **Progress Monitoring**: Long-running operation tracking with callbacks
- **Error Handling**: Comprehensive error management with proper exception types
- **In-Memory Testing**: FastMCPTransport for deterministic testing patterns

### Transport Examples
- **PythonStdioTransport**: Local Python process communication
- **StreamableHttpTransport**: Modern HTTP transport (FastMCP 2.3+)
- **SSETransport**: Server-sent events for real-time updates
- **FastMCPTransport**: In-memory transport for testing and development

## 📚 Example Categories

### 1. Basic Client Examples
- `basic_client.py` - FastMCP client initialization and basic operations
- `transport_examples.py` - Different transport layer configurations

### 2. Core Operations
- `tool_operations.py` - Tool discovery, execution, and data handling
- `resource_operations.py` - Static and templated resource access
- `prompt_operations.py` - Prompt templates and argument serialization

### 3. GitHound Integration
- `githound_server.py` - Complete MCP server using GitHound functionality
- `githound_client.py` - Client for GitHound-specific git operations

### 4. Advanced Features
- `advanced_features.py` - Progress monitoring, logging, retry strategies
- `authentication_examples.py` - Bearer token & OAuth 2.1 authentication
- `multi_server_client.py` - Multi-server client configuration and failover

## 🛠️ GitHound MCP Tools

The GitHound MCP server provides comprehensive git metadata analysis tools:

### Repository Analysis
- `analyze_repository` - Complete repository metadata and statistics
- `get_repository_summary` - High-level repository overview
- `get_author_stats` - Contributor statistics and analysis

### Commit Operations
- `analyze_commit` - Detailed commit analysis with metadata
- `get_commit_history` - Filtered commit history retrieval
- `compare_commits` - Diff analysis between commits

### File Analysis
- `get_file_history` - Complete file change history
- `get_file_blame` - Line-by-line authorship information
- `get_line_history` - Individual line change tracking

### Branch Operations
- `compare_branches` - Branch comparison and analysis
- `get_branch_stats` - Branch statistics and metadata

## 📦 MCP Resources

GitHound exposes structured data through MCP resources:

- `githound://repository/{path}/config` - Repository configuration
- `githound://repository/{path}/contributors` - Contributor information
- `githound://repository/{path}/summary` - Repository summary
- `githound://file/{path}/history` - File change history
- `githound://commit/{hash}/metadata` - Commit metadata

## 🎯 Usage Examples

### Basic Tool Execution
```python
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

async with Client(PythonStdioTransport("servers/githound_server.py")) as client:
    # Analyze repository
    result = await client.call_tool("analyze_repository", {
        "repo_path": "/path/to/repo"
    })

    # Access structured data
    repo_data = result.data
    print(f"Repository: {repo_data.name}")
    print(f"Commits: {repo_data.total_commits}")
```

### Resource Access
```python
async with Client(transport) as client:
    # Read repository summary
    content = await client.read_resource("githound://repository/./summary")
    summary = getattr(content[0], 'text', str(content[0]))

    # Access file history
    history = await client.read_resource("githound://file/src/main.py/history")
```

### Error Handling
```python
from fastmcp.exceptions import ToolError, McpError

try:
    result = await client.call_tool("analyze_commit", {"commit_hash": "invalid"})
except (ToolError, McpError) as e:
    logger.error(f"Tool execution failed: {e}")
    # Handle error appropriately
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest examples/mcp_server/tests/

# Run with coverage
pytest examples/mcp_server/tests/ --cov=examples/mcp_server

# Run mypy type checking
mypy examples/mcp_server/

# Run specific test categories
pytest examples/mcp_server/tests/test_clients.py
pytest examples/mcp_server/tests/test_integration.py
```

## 🔍 Type Safety

All examples include comprehensive type annotations and pass mypy strict checking:

```bash
mypy examples/mcp_server/ --strict
```

## 📋 Prerequisites

- Python 3.11+
- GitHound installed and configured
- FastMCP client library
- Access to a Git repository for testing

## 🚦 Getting Started

1. **Choose an Example**: Start with `basic_client.py` for FastMCP fundamentals
2. **Run GitHound Server**: Use `githound_server.py` for real git operations
3. **Explore Transports**: Try different connection methods in `transport_examples.py`
4. **Advanced Features**: Experiment with authentication and monitoring

## 📖 Documentation References

- [FastMCP Client Documentation](https://gofastmcp.com/clients/client)
- [FastMCP Transports](https://gofastmcp.com/clients/transports)
- [FastMCP Tools](https://gofastmcp.com/clients/tools)
- [FastMCP Resources](https://gofastmcp.com/clients/resources)
- [FastMCP Prompts](https://gofastmcp.com/clients/prompts)
