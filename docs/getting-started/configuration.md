# Configuration Guide

GitHound provides flexible configuration options to customize its behavior for your specific needs. This guide covers all configuration methods and available options.

## Configuration Methods

GitHound supports multiple configuration methods with the following precedence (highest to lowest):

1. **Command-line arguments** - Immediate overrides
2. **Environment variables** - Runtime configuration
3. **Project configuration file** - Project-specific settings
4. **User configuration file** - User-specific settings
5. **System configuration file** - System-wide settings
6. **Default configuration** - Built-in defaults

## Configuration Files

### User Configuration

Create a user-specific configuration file at `~/.githound/config.yaml`:

```yaml
# ~/.githound/config.yaml

# Default repository path
default_repo: "/path/to/default/repo"

# Cache configuration
cache:
  directory: "~/.githound/cache"
  max_size: "1GB"
  ttl: 3600  # seconds

# Search defaults
search:
  max_results: 1000
  fuzzy_threshold: 0.8
  include_binary_files: false
  case_sensitive: false

# Export defaults
export:
  default_format: "json"
  include_metadata: true
  pretty_print: true

# Web server configuration
web:
  host: "localhost"
  port: 8000
  auto_open_browser: true
  cors_origins: ["*"]

# MCP server configuration
mcp:
  host: "localhost"
  port: 3000
  max_connections: 100
  auth_required: false

# Logging configuration
logging:
  level: "INFO"
  file: "~/.githound/logs/githound.log"
  max_file_size: "10MB"
  backup_count: 5

# Performance settings
performance:
  max_workers: 4
  chunk_size: 1000
  timeout: 300
```

### Project Configuration

Create a project-specific configuration file at `.githound.yaml` in your repository root:

```yaml
# .githound.yaml

# Project-specific search patterns
search_patterns:
  - "*.py"
  - "*.js"
  - "*.ts"
  - "*.md"

# Exclude patterns
exclude_patterns:
  - "node_modules/"
  - "__pycache__/"
  - "*.pyc"
  - ".git/"

# Custom search aliases
aliases:
  bugs: "--message 'bug|fix|error' --date-from '30 days ago'"
  features: "--message 'feat|feature|add' --date-from '30 days ago'"
  refactor: "--message 'refactor|cleanup|improve'"

# Export templates
export_templates:
  bug_report:
    format: "json"
    fields: ["commit_hash", "message", "author", "date", "files"]
    filters:
      message_pattern: "bug|fix|error"
  
  changelog:
    format: "markdown"
    template: |
      ## Changes
      {% for commit in commits %}
      - {{ commit.message }} ({{ commit.author }})
      {% endfor %}
```

## Environment Variables

Configure GitHound using environment variables:

```bash
# Repository settings
export GITHOUND_DEFAULT_REPO="/path/to/repo"
export GITHOUND_CACHE_DIR="/custom/cache/path"

# Search settings
export GITHOUND_MAX_RESULTS=500
export GITHOUND_FUZZY_THRESHOLD=0.9

# Web server settings
export GITHOUND_WEB_HOST="0.0.0.0"
export GITHOUND_WEB_PORT=9000

# MCP server settings
export GITHOUND_MCP_HOST="0.0.0.0"
export GITHOUND_MCP_PORT=4000

# Logging settings
export GITHOUND_LOG_LEVEL="DEBUG"
export GITHOUND_LOG_FILE="/var/log/githound.log"

# Performance settings
export GITHOUND_MAX_WORKERS=8
export GITHOUND_TIMEOUT=600
```

## Command-line Configuration

Override any setting using command-line arguments:

```bash
# Override search settings
githound search "pattern" . --max-results 2000 --fuzzy-threshold 0.7

# Override web server settings
githound web --host 0.0.0.0 --port 9000

# Override export settings
githound search "pattern" . --export results.yaml --format yaml --pretty
```

## Configuration Sections

### Search Configuration

```yaml
search:
  # Maximum number of results to return
  max_results: 1000
  
  # Fuzzy search similarity threshold (0.0 - 1.0)
  fuzzy_threshold: 0.8
  
  # Include binary files in search
  include_binary_files: false
  
  # Case-sensitive search
  case_sensitive: false
  
  # Default file patterns to search
  file_patterns:
    - "*.py"
    - "*.js"
    - "*.ts"
    - "*.md"
    - "*.txt"
  
  # Patterns to exclude from search
  exclude_patterns:
    - "node_modules/"
    - "__pycache__/"
    - "*.pyc"
    - ".git/"
    - "build/"
  
  # Search timeout in seconds
  timeout: 300
  
  # Enable parallel processing
  parallel: true
  
  # Number of worker threads
  max_workers: 4
```

### Cache Configuration

```yaml
cache:
  # Cache directory
  directory: "~/.githound/cache"
  
  # Maximum cache size
  max_size: "1GB"
  
  # Cache entry time-to-live in seconds
  ttl: 3600
  
  # Enable cache compression
  compress: true
  
  # Cache cleanup interval in seconds
  cleanup_interval: 300
  
  # Enable persistent cache
  persistent: true
```

### Export Configuration

```yaml
export:
  # Default export format
  default_format: "json"
  
  # Include metadata in exports
  include_metadata: true
  
  # Pretty-print output
  pretty_print: true
  
  # Default output directory
  output_directory: "./exports"
  
  # Timestamp format for filenames
  timestamp_format: "%Y%m%d_%H%M%S"
  
  # Compression for large exports
  compress_large_files: true
  
  # Size threshold for compression (in MB)
  compression_threshold: 10
```

### Web Server Configuration

```yaml
web:
  # Server host
  host: "localhost"
  
  # Server port
  port: 8000
  
  # Auto-open browser on start
  auto_open_browser: true
  
  # CORS origins
  cors_origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
  
  # Enable authentication
  auth_enabled: false
  
  # JWT secret key
  jwt_secret: "your-secret-key"
  
  # Session timeout in seconds
  session_timeout: 3600
  
  # Rate limiting
  rate_limit:
    requests_per_minute: 100
    burst_size: 20
  
  # Static file serving
  static_files:
    enabled: true
    directory: "./static"
    cache_max_age: 3600
```

### MCP Server Configuration

```yaml
mcp:
  # Server host
  host: "localhost"
  
  # Server port
  port: 3000
  
  # Maximum concurrent connections
  max_connections: 100
  
  # Authentication required
  auth_required: false
  
  # API key for authentication
  api_key: "your-api-key"
  
  # Request timeout in seconds
  request_timeout: 60
  
  # Enable request logging
  log_requests: true
  
  # Allowed repositories
  allowed_repos:
    - "/path/to/repo1"
    - "/path/to/repo2"
  
  # Rate limiting per client
  rate_limit:
    requests_per_minute: 60
    burst_size: 10
```

### Logging Configuration

```yaml
logging:
  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: "INFO"
  
  # Log file path
  file: "~/.githound/logs/githound.log"
  
  # Maximum log file size
  max_file_size: "10MB"
  
  # Number of backup files to keep
  backup_count: 5
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Date format
  date_format: "%Y-%m-%d %H:%M:%S"
  
  # Enable console logging
  console: true
  
  # Console log level
  console_level: "WARNING"
  
  # Enable structured logging (JSON)
  structured: false
```

## Advanced Configuration

### Custom Search Aliases

Define custom search aliases for common patterns:

```yaml
aliases:
  # Bug-related commits
  bugs: "--message 'bug|fix|error|issue' --date-from '30 days ago'"
  
  # Feature commits
  features: "--message 'feat|feature|add|implement' --date-from '30 days ago'"
  
  # Refactoring commits
  refactor: "--message 'refactor|cleanup|improve|optimize'"
  
  # Security-related commits
  security: "--message 'security|vulnerability|cve|exploit'"
  
  # Documentation commits
  docs: "--message 'doc|documentation|readme' --file-type 'md'"
  
  # Recent changes by specific author
  my_changes: "--author '$(git config user.email)' --date-from '7 days ago'"
```

Use aliases in commands:

```bash
githound search bugs .
githound search features . --export features.json
```

### Export Templates

Define reusable export templates:

```yaml
export_templates:
  # Bug report template
  bug_report:
    format: "json"
    fields: ["commit_hash", "message", "author", "date", "files_changed"]
    filters:
      message_pattern: "bug|fix|error"
      date_from: "30 days ago"
    sort_by: "date"
    sort_order: "desc"
  
  # Changelog template
  changelog:
    format: "markdown"
    template: |
      # Changelog
      
      {% for commit in commits %}
      ## {{ commit.date.strftime('%Y-%m-%d') }} - {{ commit.author }}
      
      **{{ commit.message }}**
      
      Files changed:
      {% for file in commit.files_changed %}
      - {{ file }}
      {% endfor %}
      
      ---
      {% endfor %}
  
  # CSV export for analysis
  analysis:
    format: "csv"
    fields: ["date", "author", "message", "files_count", "lines_added", "lines_removed"]
    include_headers: true
```

### Performance Tuning

```yaml
performance:
  # Number of worker threads
  max_workers: 4
  
  # Chunk size for processing
  chunk_size: 1000
  
  # Memory limit for operations
  memory_limit: "2GB"
  
  # Enable result streaming
  stream_results: true
  
  # Batch size for database operations
  batch_size: 100
  
  # Connection pool size
  connection_pool_size: 10
  
  # Query timeout
  query_timeout: 300
  
  # Enable query optimization
  optimize_queries: true
```

## Configuration Validation

GitHound validates configuration on startup:

```bash
# Validate configuration
githound config validate

# Show current configuration
githound config show

# Show configuration sources
githound config sources
```

## Configuration Examples

### Development Environment

```yaml
# Development configuration
search:
  max_results: 100
  fuzzy_threshold: 0.7

logging:
  level: "DEBUG"
  console: true

web:
  auto_open_browser: true
  cors_origins: ["*"]

cache:
  ttl: 60  # Short TTL for development
```

### Production Environment

```yaml
# Production configuration
search:
  max_results: 10000
  parallel: true
  max_workers: 8

logging:
  level: "WARNING"
  file: "/var/log/githound/githound.log"
  console: false

web:
  host: "0.0.0.0"
  auth_enabled: true
  rate_limit:
    requests_per_minute: 1000

cache:
  max_size: "10GB"
  persistent: true
  compress: true

performance:
  memory_limit: "8GB"
  connection_pool_size: 20
```

### CI/CD Environment

```yaml
# CI/CD configuration
search:
  max_results: 1000
  timeout: 60

logging:
  level: "ERROR"
  console: true
  structured: true

cache:
  directory: "/tmp/githound-cache"
  ttl: 300

export:
  output_directory: "./artifacts"
  compress_large_files: true
```

## Troubleshooting Configuration

### Common Issues

1. **Configuration file not found**
   - Check file path and permissions
   - Verify YAML syntax

2. **Invalid configuration values**
   - Run `githound config validate`
   - Check data types and ranges

3. **Environment variable conflicts**
   - Use `githound config sources` to see precedence
   - Unset conflicting variables

4. **Permission errors**
   - Check file and directory permissions
   - Ensure cache directory is writable

### Debug Configuration

```bash
# Show effective configuration
githound config show --effective

# Validate configuration with details
githound config validate --verbose

# Test configuration with dry run
githound search "test" . --dry-run
```
