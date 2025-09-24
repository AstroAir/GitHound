# GitHound Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with GitHound across all components and deployment scenarios.

## Quick Diagnosis

### Check System Status

```bash
# Verify GitHound installation
githound --version

# Check Python version
python --version  # Should be 3.11+

# Verify Git installation
git --version  # Should be 2.30+

# Test basic functionality
githound search --repo-path . --content "test" --max-results 5
```

### Health Checks

```bash
# Web API health check
curl http://localhost:8000/health

# MCP server health check (if running)
python -c "import socket; s=socket.socket(); s.connect(('localhost', 3000)); s.close(); print('MCP server is running')"

# Redis health check
redis-cli ping  # Should return "PONG"
```

## Installation Issues

### Python Version Errors

**Problem**: `GitHound requires Python 3.11 or higher`

**Solutions**:

1. **Upgrade Python**:

   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3.11 python3.11-venv

   # macOS
   brew install python@3.11

   # Windows
   # Download from python.org or use Microsoft Store
   ```

2. **Use pyenv for version management**:

   ```bash
   curl https://pyenv.run | bash
   pyenv install 3.11.7
   pyenv global 3.11.7
   ```

### Dependency Installation Failures

**Problem**: `pip install githound` fails with dependency conflicts

**Solutions**:

1. **Use virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   pip install --upgrade pip
   pip install githound
   ```

2. **Use UV for faster installation**:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv
   source .venv/bin/activate
   uv pip install githound
   ```

3. **Clear pip cache**:

   ```bash
   pip cache purge
   pip install --no-cache-dir githound
   ```

### Git Not Found

**Problem**: `Git command not found`

**Solutions**:

1. **Install Git**:

   ```bash
   # Ubuntu/Debian
   sudo apt install git

   # CentOS/RHEL
   sudo yum install git

   # macOS
   brew install git

   # Windows
   # Download from git-scm.com
   ```

2. **Add Git to PATH** (Windows):
   - Add `C:\Program Files\Git\bin` to system PATH
   - Restart terminal/IDE

## Runtime Issues

### Repository Access Errors

**Problem**: `Not a git repository` or `Permission denied`

**Solutions**:

1. **Verify repository path**:

   ```bash
   # Check if directory is a Git repository
   cd /path/to/repo
   git status

   # Initialize if needed
   git init
   ```

2. **Fix permissions**:

   ```bash
   # Linux/Mac
   chmod -R 755 /path/to/repo

   # Windows (run as administrator)
   icacls "C:\path\to\repo" /grant Users:F /T
   ```

3. **Check repository integrity**:

   ```bash
   git fsck --full
   git gc --aggressive
   ```

### Search Performance Issues

**Problem**: Searches are slow or timeout

**Solutions**:

1. **Optimize search parameters**:

   ```bash
   # Reduce scope
   githound search --repo-path . --content "query" --max-results 100

   # Use date filters
   githound search --repo-path . --content "query" --date-from "2024-01-01"

   # Search specific file types
   githound search --repo-path . --content "query" --file-type "py"
   ```

2. **Increase timeout**:

   ```bash
   # Set environment variable
   export GITHOUND_TIMEOUT=600  # 10 minutes

   # Or use CLI option
   githound search --timeout 600 --repo-path . --content "query"
   ```

3. **Enable caching**:

   ```bash
   export GITHOUND_CACHE_BACKEND=redis
   export REDIS_URL=redis://localhost:6379/0
   ```

### Memory Issues

**Problem**: `MemoryError` or high memory usage

**Solutions**:

1. **Reduce worker count**:

   ```bash
   export GITHOUND_MAX_WORKERS=2
   ```

2. **Process in batches**:

   ```python
   # Python API
   for batch in range(0, total_commits, 1000):
       results = gh.search_advanced_sync(query, offset=batch, limit=1000)
   ```

3. **Use streaming for large results**:

   ```python
   # Stream results instead of loading all at once
   async for result in gh.search_advanced(query):
       process_result(result)
   ```

## Web API Issues

### Server Won't Start

**Problem**: Web server fails to start

**Solutions**:

1. **Check port availability**:

   ```bash
   # Linux/Mac
   lsof -i :8000

   # Windows
   netstat -ano | findstr :8000
   ```

2. **Use different port**:

   ```bash
   export GITHOUND_WEB_PORT=8080
   githound web --port 8080
   ```

3. **Check Redis connection**:

   ```bash
   redis-cli ping
   # If Redis is not running:
   redis-server
   ```

### API Request Failures

**Problem**: API requests return 500 errors

**Solutions**:

1. **Check logs**:

   ```bash
   # Enable debug logging
   export GITHOUND_LOG_LEVEL=DEBUG
   githound web
   ```

2. **Verify request format**:

   ```bash
   # Test with curl
   curl -X POST http://localhost:8000/api/v1/search \
     -H "Content-Type: application/json" \
     -d '{"repo_path": ".", "content_pattern": "test"}'
   ```

3. **Check authentication** (if enabled):

   ```bash
   # Include JWT token
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/search
   ```

## MCP Server Issues

### MCP Server Connection Failures

**Problem**: Cannot connect to MCP server

**Solutions**:

1. **Verify server is running**:

   ```bash
   python -m githound.mcp_server --host localhost --port 3000
   ```

2. **Check transport configuration**:

   ```bash
   # For stdio transport
   export FASTMCP_SERVER_TRANSPORT=stdio

   # For HTTP transport
   export FASTMCP_SERVER_TRANSPORT=http
   export FASTMCP_SERVER_HOST=localhost
   export FASTMCP_SERVER_PORT=3000
   ```

3. **Test with MCP client**:

   ```python
   from mcp import ClientSession

   async with ClientSession() as session:
       result = await session.call_tool("search_repository", {
           "repo_path": ".",
           "content_pattern": "test"
       })
   ```

### Authentication Issues

**Problem**: MCP authentication failures

**Solutions**:

1. **Check authentication configuration**:

   ```bash
   export FASTMCP_SERVER_ENABLE_AUTH=true
   export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID=your_client_id
   export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET=your_secret
   ```

2. **Verify JWT configuration**:

   ```bash
   export FASTMCP_SERVER_AUTH_JWT_SECRET_KEY=your_secret
   export FASTMCP_SERVER_AUTH_JWT_ISSUER=your_issuer
   ```

3. **Test authentication**:

   ```bash
   curl -X POST http://localhost:3000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "test", "password": "test"}'
   ```

## Docker Issues

### Container Build Failures

**Problem**: Docker build fails

**Solutions**:

1. **Check Docker version**:

   ```bash
   docker --version  # Should be 20.10+
   docker-compose --version  # Should be 2.0+
   ```

2. **Clear Docker cache**:

   ```bash
   docker system prune -a
   docker-compose build --no-cache
   ```

3. **Check available disk space**:

   ```bash
   df -h  # Ensure sufficient space
   docker system df  # Check Docker space usage
   ```

### Container Runtime Issues

**Problem**: Containers fail to start or crash

**Solutions**:

1. **Check container logs**:

   ```bash
   docker-compose logs githound-web
   docker-compose logs githound-mcp
   docker-compose logs redis
   ```

2. **Verify environment variables**:

   ```bash
   # Check .env file
   cat .env

   # Verify container environment
   docker-compose exec githound-web env
   ```

3. **Check resource limits**:

   ```bash
   # Monitor resource usage
   docker stats

   # Increase memory limits in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

## Performance Optimization

### Slow Search Performance

**Solutions**:

1. **Enable Redis caching**:

   ```bash
   export GITHOUND_CACHE_BACKEND=redis
   export GITHOUND_CACHE_TTL=3600
   ```

2. **Optimize worker configuration**:

   ```bash
   # Set based on CPU cores
   export GITHOUND_MAX_WORKERS=4
   ```

3. **Use search filters**:

   ```bash
   # Limit search scope
   githound search --file-type py --date-from "2024-01-01"
   ```

### High Memory Usage

**Solutions**:

1. **Reduce batch sizes**:

   ```bash
   export GITHOUND_BATCH_SIZE=100
   ```

2. **Enable streaming**:

   ```python
   # Use async generators for large datasets
   async for result in gh.search_advanced(query):
       yield result
   ```

3. **Configure garbage collection**:

   ```python
   import gc
   gc.set_threshold(700, 10, 10)
   ```

## Getting Help

### Debug Information

When reporting issues, include:

```bash
# System information
githound --version
python --version
git --version
uname -a  # Linux/Mac
systeminfo  # Windows

# Configuration
env | grep GITHOUND
env | grep FASTMCP
env | grep REDIS

# Error logs
tail -n 50 ~/.githound/logs/githound.log
```

### Support Channels

1. **Documentation**: Check this guide and [API documentation](../api-reference/)
2. **GitHub Issues**: Report bugs and feature requests
3. **GitHub Discussions**: Ask questions and get community help
4. **Examples**: Check [examples directory](../../examples/) for common patterns

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `GH001` | Repository not found | Check path and permissions |
| `GH002` | Git command failed | Verify Git installation |
| `GH003` | Search timeout | Increase timeout or reduce scope |
| `GH004` | Authentication failed | Check credentials and configuration |
| `GH005` | Rate limit exceeded | Wait or increase limits |
| `GH006` | Invalid configuration | Check environment variables |

### Emergency Recovery

If GitHound is completely broken:

```bash
# Reset to clean state
pip uninstall githound
rm -rf ~/.githound
pip install --no-cache-dir githound

# Or use Docker
docker-compose down -v
docker-compose up --build
```

For more specific issues, check the component-specific troubleshooting guides:

- [Frequently Asked Questions](faq.md)
- [Configuration Guide](../getting-started/configuration.md) - Environment variables and setup
- [MCP Server Documentation](../mcp-server/README.md) - MCP server troubleshooting
