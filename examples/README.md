# GitHound Examples

This directory contains comprehensive examples demonstrating all GitHound functionality including MCP server operations, REST API usage, git operations, and various output formats.

## Directory Structure

- `mcp/` - MCP client configuration examples and basic usage patterns
- `mcp_server/` - MCP server usage examples and client interactions
- `rest_api/` - REST API endpoint examples with sample requests/responses
- `git_operations/` - Git repository analysis and metadata extraction examples
- `output_formats/` - JSON/YAML output format examples and export options
- `error_handling/` - Error handling scenarios and edge cases
- `workflows/` - End-to-end workflow examples
- `auth/` - Authentication and configuration examples
- `authorization/` - Authorization provider examples (Permit.io, Eunomia)

## Running Examples

Each subdirectory contains executable examples with detailed documentation. Examples are designed to be:

- **Self-contained**: Can be run independently
- **Well-documented**: Include detailed explanations and comments
- **Realistic**: Use real-world scenarios and data
- **Educational**: Demonstrate best practices and common patterns

## Prerequisites

Ensure you have GitHound installed and configured:

```bash
pip install -e .
```

For MCP server examples, you'll also need the MCP client tools.

## Example Categories

### 1. MCP Client Examples (`mcp/`)

- Basic MCP client configuration
- Claude Desktop integration
- Cursor editor integration
- FastMCP-compatible configurations
- Authentication setup

### 2. MCP Server Examples (`mcp_server/`)

- MCP server setup and configuration
- Tool usage and resource access
- Client-server communication patterns
- Advanced MCP features and integrations

### 3. REST API Examples (`rest_api/`)

- Authentication and authorization
- All endpoint demonstrations
- Error handling and validation
- Batch operations and pagination

### 4. Git Operations Examples (`git_operations/`)

- Repository analysis and metadata extraction
- Commit history and filtering
- Blame analysis and author statistics
- Diff analysis and branch comparisons
- File history tracking

### 5. Output Format Examples (`output_formats/`)

- JSON structured output
- YAML configuration and export
- CSV data export
- Custom format implementations

### 6. Authentication Examples (`auth/`)

- Authentication configuration
- Provider setup and integration
- Security best practices

### 7. Authorization Examples (`authorization/`)

- Permit.io RBAC integration
- Eunomia ABAC configuration
- Fine-grained access control

### 8. Error Handling Examples (`error_handling/`)

- Invalid repository handling
- Network error scenarios
- Permission and access issues
- Recovery and retry mechanisms

### 9. Workflow Examples (`workflows/`)

- Complete analysis workflows
- Integration with CI/CD pipelines
- Automated reporting scenarios
- Performance optimization patterns

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Include comprehensive documentation
3. Add corresponding tests in `tests/examples/`
4. Update this README with new example descriptions
5. Ensure examples are self-contained and executable
