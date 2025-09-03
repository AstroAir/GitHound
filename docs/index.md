# GitHound Documentation

Welcome to GitHound, a comprehensive Git repository analysis tool that provides advanced search capabilities, detailed metadata extraction, blame analysis, diff comparison, and multiple integration options.

## 🚀 Key Features

### Advanced Git Analysis

- **Multi-modal Search**: Search by content, commit hash, author, message, date range, file path, and file type
- **Fuzzy Search**: Find approximate matches with configurable similarity thresholds
- **Git Blame Analysis**: Line-by-line authorship tracking with detailed history
- **Diff Analysis**: Compare commits, branches, and files with detailed change analysis
- **Repository Metadata**: Comprehensive repository statistics and contributor analysis

### Integration Options

- **MCP Server**: Full Model Context Protocol server implementation for AI integration
- **REST API**: Comprehensive API with OpenAPI documentation
- **WebSocket Support**: Real-time updates and streaming results
- **CLI Interface**: Powerful command-line interface with rich output formatting

### Data Export & Formats

- **Multiple Formats**: JSON, YAML, CSV, XML, Excel, and text formats
- **Structured Schemas**: Standardized data formats with comprehensive type information
- **Advanced Filtering**: Filter and sort results with flexible criteria
- **Progress Tracking**: Real-time progress reporting with cancellation support

## 🎯 Use Cases

### For Developers

- **Code Archaeology**: Understand how code evolved over time
- **Bug Investigation**: Track down when and why bugs were introduced
- **Refactoring Planning**: Identify code patterns and dependencies
- **Code Review**: Analyze changes and their impact

### For Project Managers

- **Team Analytics**: Understand team contributions and patterns
- **Release Planning**: Analyze changes between releases
- **Quality Metrics**: Track code quality and technical debt
- **Risk Assessment**: Identify high-risk areas and dependencies

### For AI/ML Applications

- **Training Data**: Extract structured git data for ML models
- **Code Understanding**: Provide context for AI code assistants
- **Automated Analysis**: Integrate with AI workflows via MCP server
- **Pattern Recognition**: Identify development patterns and anomalies

## 🏗️ Architecture Overview

GitHound is built with a modular architecture that separates concerns and enables flexible usage:

```mermaid
graph TB
    CLI[CLI Interface] --> Core[Core Engine]
    Web[Web Interface] --> Core
    MCP[MCP Server] --> Core
    API[REST API] --> Core

    Core --> SearchEngine[Search Engine]
    Core --> GitHandler[Git Handler]
    Core --> Models[Data Models]
    Core --> Utils[Utilities]

    SearchEngine --> Orchestrator[Search Orchestrator]
    SearchEngine --> Searchers[Individual Searchers]

    GitHandler --> Blame[Git Blame]
    GitHandler --> Diff[Git Diff]
    GitHandler --> Metadata[Metadata Extraction]

    Models --> Schemas[Pydantic Schemas]
    Models --> Types[Type Definitions]

    Utils --> Export[Export Manager]
    Utils --> Progress[Progress Tracking]
```

## 📚 Quick Navigation

### Getting Started

- [Installation Guide](getting-started/installation.md) - Install GitHound and dependencies
- [Quick Start](getting-started/quick-start.md) - Get up and running in minutes
- [Configuration](getting-started/configuration.md) - Configure GitHound for your needs

### User Guides

- [CLI Usage](user-guide/cli-usage.md) - Command-line interface reference
- [Search Capabilities](user-guide/search-capabilities.md) - Advanced search features
- [Web Interface](user-guide/web-interface.md) - Web-based analysis tools

### Integration

- [MCP Server](mcp-server/overview.md) - AI integration via Model Context Protocol
- [REST API](api-reference/rest-api.md) - HTTP API for external integrations
- [Python API](api-reference/python-api.md) - Direct Python integration

### Development

- [Architecture](architecture/overview.md) - System design and components
- [Contributing](development/contributing.md) - How to contribute to GitHound
- [Type Checking](development/type-checking.md) - MyPy configuration and best practices

## 🔧 Technology Stack

- **Python 3.11+**: Modern Python with full type annotation support
- **FastAPI**: High-performance web framework for APIs
- **Pydantic**: Data validation and serialization with type safety
- **GitPython**: Comprehensive Git repository interaction
- **FastMCP**: Model Context Protocol server implementation
- **Typer**: Modern CLI framework with rich formatting
- **MyPy**: Static type checking for code quality

## 📈 Performance & Scalability

GitHound is designed for performance and can handle large repositories efficiently:

- **Parallel Processing**: Multi-threaded search operations
- **Caching**: Intelligent caching of expensive operations
- **Streaming**: Memory-efficient processing of large datasets
- **Progress Tracking**: Real-time feedback for long-running operations

## 🤝 Community & Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Contributing**: Help improve GitHound
- **Documentation**: Comprehensive guides and API reference

## 📄 License

GitHound is released under the MIT License. See the [LICENSE](https://github.com/your-org/githound/blob/main/LICENSE) file for details.

---

Ready to get started? Check out our [Installation Guide](getting-started/installation.md) or jump into the [Quick Start](getting-started/quick-start.md) tutorial!
