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
# Should show git version 2.0 or higher
```

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install githound
```

### Method 2: Install from Source

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-org/githound.git
   cd githound
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

### Method 3: Using UV (Fast Package Manager)

If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
uv pip install githound
```

## Development Installation

For development work, install with additional dependencies:

```bash
# Clone the repository
git clone https://github.com/your-org/githound.git
cd githound

# Install with development dependencies
pip install -e ".[dev,test]"
```

This includes:

- **Testing tools**: pytest, pytest-asyncio, pytest-cov, pytest-mock
- **Type checking**: mypy, pandas-stubs, types-pyyaml
- **Development tools**: Additional linting and formatting tools

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
githound search "function" .
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
- openpyxl (for Excel export)

Install additional export dependencies:

```bash
pip install openpyxl
```

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

```
Error: GitHound requires Python 3.11 or higher
```

**Solution**: Upgrade Python or use a virtual environment with Python 3.11+

#### 2. Git Not Found

```
Error: Git command not found
```

**Solution**: Install Git and ensure it's in your PATH

#### 3. Permission Errors

```
Error: Permission denied when installing
```

**Solution**: Use a virtual environment or install with `--user` flag:

```bash
pip install --user githound
```

#### 4. Import Errors

```
ImportError: No module named 'githound'
```

**Solution**: Ensure you're in the correct virtual environment and GitHound is installed

### Getting Help

If you encounter issues:

1. **Check the logs**: Run with `--verbose` flag for detailed output
2. **Search existing issues**: Check [GitHub Issues](https://github.com/your-org/githound/issues)
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
