# GitHound Utility Scripts

This directory contains convenient utility scripts for GitHound development and operations
with full cross-platform support.

## 🚀 Quick Start

For new users, start here:

```bash
# Complete setup (recommended)
python scripts/quick-start.py setup

# Interactive demo
python scripts/quick-start.py demo

# Getting started guide
python scripts/quick-start.py guide
```

## 📋 Available Scripts

### Unified Script Runner

For convenience, use the unified script runner:

```bash
# List all available scripts
python scripts/run.py --list

# Run any script
python scripts/run.py dev-env check
python scripts/run.py services start web
python scripts/run.py quick-start setup

# Get help for all scripts
python scripts/run.py --help-all
```

### Core Development Scripts

| Script             | Description                          | Usage                                       |
| ------------------ | ------------------------------------ | ------------------------------------------- |
| `run.py`           | **Unified script runner**            | `python scripts/run.py [script] [args]`     |
| `dev-env.py`       | Development environment management   | `python scripts/dev-env.py [command]`       |
| `services.py`      | Service management (web, MCP server) | `python scripts/services.py [command]`      |
| `cache-manager.py` | Cache and data management            | `python scripts/cache-manager.py [command]` |
| `health-check.py`  | System health validation             | `python scripts/health-check.py [command]`  |
| `quick-start.py`   | One-command setup and demos          | `python scripts/quick-start.py [command]`   |
| `benchmark.py`     | Performance benchmarking             | `python scripts/benchmark.py [command]`     |
| `run_mcp_tests.py` | MCP server testing (existing)        | `python scripts/run_mcp_tests.py [suite]`   |

### Documentation Validation Scripts

| Script                        | Description                              | Usage                                           |
| ----------------------------- | ---------------------------------------- | ----------------------------------------------- |
| `validate_all_docs.py`        | **Comprehensive documentation validation** | `python scripts/validate_all_docs.py [options]` |
| `validate_documentation.py`   | Core validation engine                   | `python scripts/validate_documentation.py [options]` |
| `validate_links.py`           | Link validation (legacy)                 | `python scripts/validate_links.py`             |
| `validate_docs_examples.py`   | Code example validation (legacy)         | `python scripts/validate_docs_examples.py`     |
| `validate_config_examples.py` | Configuration validation (legacy)        | `python scripts/validate_config_examples.py`   |
| `setup_validation.py`         | Setup validation environment             | `python scripts/setup_validation.py`           |

#### Documentation Validation Quick Start

```bash
# Setup validation environment
python scripts/setup_validation.py

# Run comprehensive validation
python scripts/validate_all_docs.py

# Quick validation (skip external links)
python scripts/validate_all_docs.py --skip-external

# Validate specific files
python scripts/validate_documentation.py docs/user-guide/README.md

# Using Makefile targets
make docs-validate          # Full validation
make docs-validate-quick     # Quick validation
make docs-lint              # Markdown linting only
```

### Cross-Platform Wrappers

For convenience, cross-platform wrapper scripts are available in `wrappers/`:

**Unix/Linux/macOS:**

```bash
./scripts/wrappers/dev-env.sh check
./scripts/wrappers/services.sh start web
./scripts/wrappers/cache-manager.sh clean
```

**Windows:**

```cmd
scripts\wrappers\dev-env.bat check
scripts\wrappers\services.bat start web
scripts\wrappers\cache-manager.bat clean
```

## 🔧 Script Details

### Development Environment (`dev-env.py`)

Manages the development environment setup and validation.

```bash
# Check environment status
python scripts/dev-env.py check

# Set up development environment
python scripts/dev-env.py setup

# Show environment information
python scripts/dev-env.py info

# Clean development artifacts
python scripts/dev-env.py clean

# Validate complete environment
python scripts/dev-env.py validate
```

**Features:**

- ✅ Python version and virtual environment validation
- ✅ Dependency installation and verification
- ✅ Git configuration checks
- ✅ Pre-commit hooks setup
- ✅ Development directory creation

### Services Management (`services.py`)

Manages GitHound services with health monitoring.

```bash
# Start services
python scripts/services.py start web --port 8000
python scripts/services.py start mcp --port 3000
python scripts/services.py start all

# Check service status
python scripts/services.py status
python scripts/services.py status --watch

# Stop services
python scripts/services.py stop web
python scripts/services.py stop all --force

# View logs
python scripts/services.py logs web --follow
python scripts/services.py logs mcp --lines 100

# Health checks
python scripts/services.py health
```

**Features:**

- ✅ Background service management
- ✅ Port conflict detection and resolution
- ✅ Health monitoring with HTTP endpoints
- ✅ Log file management and viewing
- ✅ Cross-platform process management

### Cache Management (`cache-manager.py`)

Manages various caches and temporary data.

```bash
# Show cache information
python scripts/cache-manager.py info
python scripts/cache-manager.py info pytest_cache

# Clean caches
python scripts/cache-manager.py clean all
python scripts/cache-manager.py clean __pycache__ --force
python scripts/cache-manager.py clean --dry-run

# Analyze cache usage
python scripts/cache-manager.py analyze

# Optimize caches
python scripts/cache-manager.py optimize
```

**Managed Cache Types:**

- 🐍 Python caches (`__pycache__`, `.mypy_cache`, `.ruff_cache`)
- 🧪 Test caches (`.pytest_cache`, coverage data)
- 🏗️ Build artifacts (`build/`, `dist/`, `*.egg-info`)
- 📚 Documentation builds
- 🗂️ Application caches and logs

### Health Checks (`health-check.py`)

Comprehensive system health validation and monitoring.

```bash
# Run health checks
python scripts/health-check.py check
python scripts/health-check.py check --verbose --save

# Generate detailed report
python scripts/health-check.py report --output health.json
python scripts/health-check.py report --format yaml

# Continuous monitoring
python scripts/health-check.py monitor --interval 30

# Performance benchmarks
python scripts/health-check.py benchmark
```

**Health Check Categories:**

- 🖥️ System requirements (Python, commands, environment)
- 📦 Dependencies (core and development packages)
- ⚙️ Configuration files and Git setup
- 🌐 Service health and connectivity
- ⚡ Performance benchmarks

### Quick Start (`quick-start.py`)

One-command setup and interactive demos.

```bash
# Complete setup
python scripts/quick-start.py setup
python scripts/quick-start.py setup --force

# Interactive demo
python scripts/quick-start.py demo

# Getting started guide
python scripts/quick-start.py guide

# Example workflows
python scripts/quick-start.py examples
```

**Features:**

- 🎯 One-command complete setup
- 🎮 Interactive demos with real examples
- 📖 Comprehensive getting started guide
- 🔄 Example workflow demonstrations

## 🔗 Integration with Existing Build Tools

These scripts complement the existing build infrastructure:

### With build.sh/build.ps1

```bash
# Use existing build scripts for compilation tasks
./build.sh install-dev
./build.sh test

# Use new scripts for environment and services
python scripts/dev-env.py check
python scripts/services.py start web
```

### With Makefile

```bash
# Use Makefile for traditional build tasks
make install-dev
make test

# Use new scripts for advanced operations
python scripts/health-check.py check
python scripts/cache-manager.py optimize
```

## 🛠️ Development

### Adding New Scripts

1. Create the Python script in `scripts/`
2. Use the utility modules in `scripts/utils/`
3. Follow the established patterns (typer CLI, rich output)
4. Create cross-platform wrappers in `scripts/wrappers/`
5. Update this README

### Utility Modules

The `scripts/utils/` package provides shared functionality:

- `common.py` - Common utilities (commands, file operations, Git info)
- `colors.py` - Console output with rich formatting
- `platform.py` - Cross-platform compatibility helpers

### Testing Scripts

```bash
# Test individual scripts
python scripts/dev-env.py check
python scripts/health-check.py check

# Test with existing test suite
python scripts/run_mcp_tests.py unit
```

## 🌍 Cross-Platform Support

All scripts are designed for cross-platform compatibility:

- **Python-based core** for maximum compatibility
- **Shell/Batch wrappers** for convenience
- **Path handling** with pathlib
- **Process management** with subprocess
- **Platform detection** and adaptation

### Platform-Specific Notes

**Windows:**

- Use `.bat` wrappers or call Python directly
- PowerShell and Command Prompt supported
- Automatic path separator handling

**macOS/Linux:**

- Use `.sh` wrappers or call Python directly
- Bash and other shells supported
- POSIX-compliant operations

## 📊 Examples

### Complete Development Setup

```bash
# 1. Quick setup
python scripts/quick-start.py setup

# 2. Verify environment
python scripts/dev-env.py check

# 3. Start services
python scripts/services.py start all

# 4. Run health check
python scripts/health-check.py check

# 5. Clean up when done
python scripts/cache-manager.py clean
```

### Daily Development Workflow

```bash
# Morning: Check system health
python scripts/health-check.py check

# Start development services
python scripts/services.py start web --port 8080

# Work on code...

# Evening: Clean up and optimize
python scripts/cache-manager.py optimize
python scripts/services.py stop all
```

### CI/CD Integration

```bash
# In CI pipeline
python scripts/dev-env.py setup
python scripts/health-check.py check --save
python scripts/cache-manager.py clean all

# Run tests with existing tools
./build.sh ci
```

## 🤝 Contributing

When contributing to the utility scripts:

1. Follow existing patterns and conventions
2. Use the shared utility modules
3. Ensure cross-platform compatibility
4. Add comprehensive help text and examples
5. Update this README with new functionality

## 📝 License

These utility scripts are part of GitHound and follow the same MIT license.
