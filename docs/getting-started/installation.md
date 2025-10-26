# Installation Guide

This guide will help you install GitHound and its dependencies on your system.

## Prerequisites

### System Requirements

- **Python 3.11 or higher**: GitHound requires modern Python with full type annotation support
- **Git**: Git must be installed and accessible from the command line
- **Operating System**: Windows, macOS, or Linux

### Python Version Check

```bash
python --version
# Should show Python 3.11.0 or higher
```

### Git Installation Check

```bash
git --version
# Should show git version 2.30 or higher
```

## Installation Methods

**Note**: GitHound is currently in development and not yet published to PyPI.

### Method 1: Install from Source (Current Method)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/AstroAir/GitHound.git
   cd GitHound
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install in development mode**:

   ```bash
   pip install -e .
   ```

### Method 2: Using UV (Fast Package Manager)

If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
# Clone repository first
git clone https://github.com/AstroAir/GitHound.git
cd GitHound

# Install with uv
uv pip install -e .
```

### Future: PyPI Installation

Once published, GitHound will be available via:

```bash
pip install githound
```

## Development Installation

For development work, install with additional dependencies:

```bash
# Clone the repository
git clone https://github.com/AstroAir/GitHound.git
cd GitHound

# Install with development dependencies (recommended modern syntax)
pip install -e . --dependency-groups dev,test

# Or install all dependency groups
pip install -e . --dependency-groups dev,test,docs,build

# Legacy syntax (still supported but not recommended)
pip install -e ".[dev,test,docs,build]"
```

This includes:

**Development Dependencies (`dev`):**

- **Type checking**: mypy, pandas-stubs, types-pyyaml, types-psutil, types-requests
- **Code quality**: ruff, black, isort, pre-commit

**Testing Dependencies (`test`):**

- **Testing framework**: pytest, pytest-asyncio, pytest-cov, pytest-mock
- **Performance testing**: pytest-benchmark, pytest-xdist
- **Web testing**: playwright, pytest-playwright, axe-playwright-python
- **HTTP testing**: httpx, respx

**Documentation Dependencies (`docs`):**

- **Documentation**: mkdocs, mkdocs-material, mkdocstrings
- **Documentation plugins**: mkdocs-gen-files, mkdocs-literate-nav

**Build Dependencies (`build`):**

- **Build tools**: build, twine, hatchling

## Verification

After installation, verify that GitHound is working correctly:

### 1. Check Installation

```bash
githound --version
```

### 2. Run Basic Command

```bash
githound --help
```

### 3. Test with a Repository

```bash
# Navigate to any git repository
cd /path/to/your/git/repo

# Run a simple search
githound search --repo-path . --content "function"
```

### 4. Verify Dependencies

```bash
# Check core dependencies
python -c "import githound; print('GitHound:', githound.__version__)"
python -c "import git; print('GitPython:', git.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"

# Check optional dependencies (if installed)
python -c "import redis; print('Redis:', redis.__version__)" 2>/dev/null || echo "Redis not available"
python -c "import pandas; print('Pandas:', pandas.__version__)" 2>/dev/null || echo "Pandas not available"
python -c "import rapidfuzz; print('RapidFuzz:', rapidfuzz.__version__)" 2>/dev/null || echo "RapidFuzz not available"
python -c "import slowapi; print('SlowAPI:', slowapi.__version__)" 2>/dev/null || echo "SlowAPI not available"
python -c "import openpyxl; print('OpenPyXL:', openpyxl.__version__)" 2>/dev/null || echo "OpenPyXL not available"
```

## Optional Dependencies

### For Web Interface

The web interface requires additional dependencies that are included by default:

- FastAPI
- Uvicorn
- WebSockets

### For MCP Server

The MCP server functionality requires:

- FastMCP (included by default)

### For Enhanced Export

For advanced export formats:

- pandas (included by default)
- openpyxl (for Excel export, included by default)

### For Caching and Performance

For enhanced caching and rate limiting:

- redis (for Redis backend)
- slowapi (for rate limiting, included by default)

Install Redis support:

```bash
pip install redis
```

### For Authentication

For advanced authentication providers:

- permit-sdk (for Permit.io RBAC)
- eunomia-client (for Eunomia ABAC)

Install authentication providers:

```bash
# For Permit.io
pip install permit-sdk

# For Eunomia
pip install eunomia-client
```

### For Search Enhancement

For enhanced search capabilities:

- rapidfuzz (for fuzzy search, included by default)
- diskcache (for disk-based caching, included by default)

## Configuration

### Environment Variables

GitHound supports several environment variables for configuration:

```bash
# Set default repository path
export GITHOUND_DEFAULT_REPO="/path/to/default/repo"

# Set cache directory
export GITHOUND_CACHE_DIR="/path/to/cache"

# Set log level
export GITHOUND_LOG_LEVEL="INFO"
```

### Configuration File

Create a configuration file at `~/.githound/config.yaml`:

```yaml
# Default configuration
default_repo: "/path/to/default/repo"
cache_dir: "~/.githound/cache"
log_level: "INFO"

# Search defaults
search:
  max_results: 1000
  fuzzy_threshold: 0.8

# Export defaults
export:
  default_format: "json"
  include_metadata: true

# Web server defaults
web:
  host: "localhost"
  port: 8000

# MCP server defaults
mcp:
  port: 3000
```

## Troubleshooting

### Common Issues

#### 1. Python Version Error

```text
Error: GitHound requires Python 3.11 or higher
```

**Solution**: Upgrade Python or use a virtual environment with Python 3.11+

#### 2. Git Not Found

```text
Error: Git command not found
```

**Solution**: Install Git and ensure it's in your PATH

#### 3. Permission Errors

```text
Error: Permission denied when installing
```

**Solution**: Use a virtual environment or install with `--user` flag:

```bash
pip install --user githound
```

#### 4. Import Errors

```text
ImportError: No module named 'githound'
```

**Solution**: Ensure you're in the correct virtual environment and GitHound is installed

### Getting Help

If you encounter issues:

1. **Check the logs**: Run with `--verbose` flag for detailed output
2. **Search existing issues**: Check [GitHub Issues](https://github.com/AstroAir/GitHound/issues)
3. **Create a new issue**: Provide system info, error messages, and steps to reproduce

### System Information

To help with troubleshooting, gather system information:

```bash
# Python version
python --version

# Git version
git --version

# GitHound version
githound --version

# Installed packages
pip list | grep -E "(githound|git|fastapi|pydantic)"
```

## Next Steps

Once GitHound is installed:

1. **Quick Start**: Follow the [Quick Start Guide](quick-start.md)
2. **Configuration**: Set up [Configuration](configuration.md)
3. **CLI Usage**: Learn about [CLI Usage](../user-guide/cli-usage.md)
4. **Web Interface**: Explore the [Web Interface](../user-guide/web-interface.md)

## Uninstallation

To remove GitHound:

```bash
pip uninstall githound
```

To remove all configuration and cache files:

```bash
# Remove configuration directory
rm -rf ~/.githound

# Remove cache files (if using default location)
rm -rf ~/.cache/githound
```

## 🚀 Next Steps

Now that GitHound is installed, here's what to do next:

### Quick Start

- **[Quick Start Guide](quick-start.md)** - Get up and running in 5 minutes
- **[Configuration Guide](configuration.md)** - Set up GitHound for your environment

### Learn GitHound

- **[CLI Usage](../user-guide/cli-usage.md)** - Master the command-line interface
- **[Search Capabilities](../user-guide/search-capabilities.md)** - Explore advanced search features
- **[Web Interface](../user-guide/web-interface.md)** - Use the web-based interface

### Integration Options

- **[MCP Server Setup](../mcp-server/setup.md)** - Set up AI integration
- **[Python API](../api-reference/python-api.md)** - Use GitHound in your Python projects
- **[REST API](../api-reference/rest-api.md)** - Integrate with other applications

### Need Help

- **[Troubleshooting Guide](../troubleshooting/README.md)** - Solve common issues
- **[FAQ](../troubleshooting/faq.md)** - Frequently asked questions

---

**📚 [Back to Documentation Home](../index.md)** | **➡️ [Continue to Quick Start](quick-start.md)**
