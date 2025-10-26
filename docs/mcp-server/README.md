# GitHound MCP Server Documentation

Complete documentation for GitHound's Model Context Protocol (MCP) server implementation.

## Quick Navigation

### Getting Started

- **[Setup](setup.md)** - Installation, configuration, and client integration guide
- **[Configuration](configuration.md)** - Complete configuration reference with MCP.json support

### Reference Documentation

- **[Tools Reference](tools-reference.md)** - Comprehensive guide to all 29 MCP tools
- **[Integration Examples](integration-examples.md)** - Practical examples and usage patterns

## What is GitHound MCP Server

GitHound MCP Server is a comprehensive Model Context Protocol implementation that exposes all of GitHound's Git repository analysis capabilities through a standardized interface. Built with FastMCP 2.0, it provides:

- **29 MCP Tools** for repository analysis, search, and management
- **7 MCP Resources** for dynamic data access
- **3 MCP Prompts** for common workflows
- **Universal Client Support** through MCP.json configuration
- **Robust Authentication** with multiple provider options

### 🔐 **Advanced Authentication**

- **Permit.io Integration** for Role-Based Access Control (RBAC)
- **Eunomia Authorization** for Attribute-Based Access Control (ABAC)
- **Fine-grained Permissions** for tool and resource access
- **Multi-tenant Support** with organization-level isolation

## Key Features

### 🔍 **Advanced Search & Analysis**

- Multi-modal search across repository content
- Fuzzy string matching and pattern analysis
- Comprehensive commit and file history tracking
- Author statistics and contribution analysis

### 🛠️ **Repository Management**

- Complete repository metadata and health checks
- Branch and tag management with detailed information
- Remote repository configuration and validation
- Export capabilities in multiple formats

### 🔗 **Universal Client Compatibility**

- **Claude Desktop** integration
- **Cursor** editor support
- **VS Code** workspace integration
- **Custom MCP clients** through standard protocol

### ⚙️ **Flexible Configuration**

- **MCP.json** standard configuration format
- **Environment variables** for programmatic setup
- **Command-line arguments** for development
- **Priority-based** configuration system

### 🔐 **Enterprise-Ready Security**

- **Permit.io** integration for authorization
- **Eunomia** policy engine support
- **Rate limiting** and request throttling
- **Audit logging** for compliance

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  GitHound MCP    │    │  Git Repository │
│  (Claude/Cursor)│◄──►│     Server       │◄──►│   (Local/Remote)│
│                 │    │   (FastMCP 2.0)  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  GitHound Core   │
                       │   Analysis       │
                       │    Engine        │
                       └──────────────────┘
```

## What is MCP

The Model Context Protocol (MCP) is a standardized protocol that enables AI applications to access external data sources and tools in a secure, structured way. GitHound's MCP server exposes all of its Git analysis capabilities through this protocol.

## Key Benefits

### For AI Applications

- **Structured Data Access**: Get Git data in standardized, type-safe formats
- **Context-Aware Analysis**: Understand code evolution and repository patterns
- **Real-time Information**: Access up-to-date repository information
- **Comprehensive Coverage**: Full access to GitHound's analysis capabilities

### For Developers

- **Easy Integration**: Simple setup with any MCP-compatible AI tool
- **Rich Metadata**: Detailed information about commits, authors, and changes
- **Flexible Queries**: Support for complex search and analysis operations
- **Performance Optimized**: Efficient data retrieval with caching

## Quick Start

For detailed installation and setup instructions, see the **[Setup Guide](setup.md)**.

## Documentation Structure

### Core Documentation

1. **[Setup](setup.md)**
   - Installation instructions
   - Configuration methods
   - Client integration guides
   - Troubleshooting tips

2. **[Configuration](configuration.md)**
   - MCP.json format specification
   - Environment variables reference
   - Authentication setup
   - Client-specific configurations

### Reference Materials

3. **[Tools Reference](tools-reference.md)**
   - Complete tool documentation
   - Parameter specifications
   - Return value formats
   - Usage examples

4. **[Integration Examples](integration-examples.md)**
   - Client setup examples
   - Common usage patterns
   - AI assistant integration
   - Performance optimization

## Supported Clients

### AI Development Tools

- **Claude Desktop** - Anthropic's desktop application
- **Cursor** - AI-powered code editor
- **VS Code** - With MCP extensions
- **Custom Applications** - Any MCP-compatible tool

### Configuration Locations

- `~/.claude/claude_desktop_config.json` (Claude Desktop)
- `~/.cursor/mcp.json` (Cursor)
- `.vscode/mcp.json` (VS Code workspace)
- `./mcp.json` (Project-specific)

## Common Use Cases

### 🔍 **Code Investigation**

- Search for specific patterns or functions
- Analyze file change history
- Track bug introduction and fixes
- Understand code evolution

### 📊 **Repository Analysis**

- Generate comprehensive repository reports
- Analyze contributor activity and patterns
- Assess repository health and maintenance
- Compare branches and releases

### 🤖 **AI-Assisted Development**

- Repository onboarding for new team members
- Automated code review assistance
- Bug investigation and root cause analysis
- Documentation generation from code analysis

### 📈 **Project Management**

- Track development velocity and trends
- Identify bottlenecks and areas for improvement
- Generate reports for stakeholders
- Monitor security and compliance

## Advanced Features

### Authentication & Authorization

- **Permit.io** integration for fine-grained access control
- **Eunomia** policy engine for custom authorization rules
- **Rate limiting** to prevent abuse
- **Audit logging** for security compliance

### Performance Optimization

- **Intelligent caching** for repeated queries
- **Pagination** for large result sets
- **Lazy loading** for resource-intensive operations
- **Configurable timeouts** and limits

### Extensibility

- **Plugin architecture** for custom tools
- **Resource providers** for dynamic data
- **Custom prompts** for specialized workflows
- **Event hooks** for integration with external systems

## Community & Support

### Getting Help

- **Documentation** - Comprehensive guides and references
- **Examples** - Practical integration patterns
- **Issues** - GitHub issue tracker for bugs and features
- **Discussions** - Community forum for questions and ideas

### Contributing

- **Code contributions** - Tools, features, and improvements
- **Documentation** - Guides, examples, and tutorials
- **Testing** - Integration testing and validation
- **Feedback** - Usage patterns and feature requests

## Version Compatibility

- **FastMCP 2.0+** - Required for full feature support
- **Python 3.8+** - Minimum Python version
- **Git 2.0+** - Minimum Git version for repository analysis
- **MCP Protocol** - Compatible with MCP specification v1.0

## License & Legal

GitHound MCP Server is released under the same license as GitHound core. See the main repository for license details and terms of use.

---

**Next Steps:**

1. Follow the [Setup](setup.md) guide to get started
2. Explore [Integration Examples](integration-examples.md) for practical usage
3. Reference the [Tools Documentation](tools-reference.md) for detailed API information
4. Check the [Configuration Guide](configuration.md) for advanced setup options
