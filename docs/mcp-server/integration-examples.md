# GitHound MCP Integration Examples

Practical examples showing how to integrate and use GitHound MCP Server with various AI tools and applications.

## Client Setup Examples

### Claude Desktop Integration

Add to your `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Cursor Integration

Create `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound for Cursor"
      }
    }
  }
}
```

### VS Code Integration

Create `.vscode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### GitHub Copilot Integration

For GitHub Copilot Chat extensions that support MCP:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound for GitHub Copilot",
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      },
      "description": "Git repository analysis and search capabilities"
    }
  }
}
```

### OpenAI GPT Integration

For custom GPT applications using MCP protocol:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server", "--transport", "http", "--port", "3000"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound for OpenAI GPT",
        "FASTMCP_SERVER_HOST": "0.0.0.0",
        "FASTMCP_SERVER_PORT": "3000",
        "FASTMCP_SERVER_TRANSPORT": "http"
      },
      "description": "HTTP-based GitHound MCP server for OpenAI integration"
    }
  }
}
```

### Anthropic Claude API Integration

For applications using Claude API with MCP support:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server", "--transport", "sse"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound for Claude API",
        "FASTMCP_SERVER_TRANSPORT": "sse",
        "FASTMCP_SERVER_ENABLE_AUTH": "true",
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.JWTVerifier"
      },
      "description": "Server-Sent Events GitHound MCP server with authentication"
    }
  }
}
```

### Custom AI Application Integration

For custom AI applications with specific requirements:

```json
{
  "mcpServers": {
    "githound-custom": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_NAME": "GitHound Custom Integration",
        "FASTMCP_SERVER_LOG_LEVEL": "DEBUG",
        "FASTMCP_SERVER_RATE_LIMIT_ENABLED": "true",
        "FASTMCP_SERVER_ENABLE_AUTH": "true",
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.github.GitHubProvider",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID": "your-github-client-id",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET": "your-github-client-secret"
      },
      "description": "Custom GitHound integration with GitHub authentication"
    }
  }
}
```

## Common Usage Patterns

### Repository Analysis Workflow

```python
# 1. Start with repository overview
analyze_repository(repo_path="/path/to/project")

# 2. Get branch information
list_branches(repo_path="/path/to/project", include_remote=True)

# 3. Analyze recent activity
get_commit_history(
    repo_path="/path/to/project",
    max_commits=50,
    since="2024-01-01"
)

# 4. Get contributor statistics
get_author_stats(
    repo_path="/path/to/project",
    since="2024-01-01"
)
```

### Code Investigation Workflow

```python
# 1. Search for specific functionality
advanced_search(
    repo_path="/path/to/project",
    query="authentication",
    search_type="content",
    include_patterns=["*.py", "*.js", "*.ts"]
)

# 2. Analyze specific files
analyze_file_blame(
    repo_path="/path/to/project",
    file_path="src/auth/login.py"
)

# 3. Track file changes
get_file_history_mcp(
    repo_path="/path/to/project",
    file_path="src/auth/login.py",
    max_commits=20
)

# 4. Compare implementations
compare_commits_diff(
    repo_path="/path/to/project",
    commit1="abc123",
    commit2="def456"
)
```

### Security Analysis Workflow

```python
# 1. Search for security-related patterns
content_search(
    repo_path="/path/to/project",
    pattern="(password|secret|key|token)",
    file_types=[".py", ".js", ".env", ".config"]
)

# 2. Analyze recent security changes
get_filtered_commits(
    repo_path="/path/to/project",
    message_pattern="(security|fix|vulnerability)",
    date_from="2024-01-01"
)

# 3. Check for sensitive files
advanced_search(
    repo_path="/path/to/project",
    query="config",
    search_type="file",
    include_patterns=["*.env", "*.key", "*.pem"]
)
```

## AI Assistant Integration Examples

### Repository Onboarding Assistant

```markdown
You are a repository onboarding assistant. When a user provides a repository path, help them understand the codebase by:

1. **Repository Overview**: Use `analyze_repository` to get basic information
2. **Structure Analysis**: Use `list_branches` and `list_tags` to understand the development workflow
3. **Recent Activity**: Use `get_commit_history` to show recent changes
4. **Key Contributors**: Use `get_author_stats` to identify main contributors
5. **Documentation**: Use `content_search` to find README, docs, and setup files

Example conversation:
User: "Help me understand this repository: /path/to/new-project"
Assistant: [Uses MCP tools to analyze and provide comprehensive overview]
```

### Code Review Assistant

```markdown
You are a code review assistant. When reviewing changes, use GitHound MCP tools to:

1. **Change Analysis**: Use `compare_commits_diff` to understand what changed
2. **Historical Context**: Use `get_file_history_mcp` to see how files evolved
3. **Author Context**: Use `analyze_file_blame` to understand authorship
4. **Related Changes**: Use `advanced_search` to find related code patterns
5. **Impact Assessment**: Use `compare_branches_diff` to understand branch differences

Example workflow:
User: "Review the changes in commit abc123"
Assistant: [Uses MCP tools to provide detailed code review with context]
```

### Bug Investigation Assistant

```markdown
You are a bug investigation assistant. When investigating issues, use GitHound MCP tools to:

1. **Search for Error Patterns**: Use `content_search` with error messages
2. **Find Related Changes**: Use `get_filtered_commits` with bug-related keywords
3. **Analyze File History**: Use `get_file_history_mcp` for problematic files
4. **Compare Working Versions**: Use `compare_commits_diff` to find when bugs were introduced
5. **Check Author Context**: Use `analyze_file_blame` to understand code ownership

Example workflow:
User: "Investigate authentication failures in the login system"
Assistant: [Uses MCP tools to systematically investigate the issue]
```

## Advanced Integration Patterns

### Multi-Repository Analysis

```python
# Analyze multiple repositories
repositories = [
    "/path/to/frontend",
    "/path/to/backend",
    "/path/to/shared-lib"
]

for repo in repositories:
    # Get overview of each repository
    analysis = analyze_repository(repo_path=repo)

    # Find cross-repository patterns
    search_results = advanced_search(
        repo_path=repo,
        query="shared_function",
        search_type="content"
    )

    # Compare activity levels
    stats = get_author_stats(repo_path=repo, since="2024-01-01")
```

### Automated Reporting

```python
# Generate comprehensive repository report
def generate_weekly_report(repo_path):
    # Repository health check
    validation = validate_repository(repo_path=repo_path)

    # Recent activity analysis
    recent_commits = get_commit_history(
        repo_path=repo_path,
        since="7 days ago",
        max_commits=100
    )

    # Contributor activity
    author_stats = get_author_stats(
        repo_path=repo_path,
        since="7 days ago"
    )

    # Export detailed data
    export_repository_data(
        repo_path=repo_path,
        format="json",
        output_path="weekly_report.json",
        date_range="7 days"
    )

    return {
        "validation": validation,
        "activity": recent_commits,
        "contributors": author_stats
    }
```

### Real-time Monitoring

```python
# Monitor repository changes
def monitor_repository_changes(repo_path):
    # Get current state
    current_state = analyze_repository(repo_path=repo_path)

    # Check for new commits
    recent_commits = get_commit_history(
        repo_path=repo_path,
        since="1 hour ago"
    )

    # Alert on specific patterns
    security_changes = get_filtered_commits(
        repo_path=repo_path,
        message_pattern="(security|fix|vulnerability)",
        date_from="1 hour ago"
    )

    return {
        "new_commits": len(recent_commits),
        "security_changes": len(security_changes),
        "current_state": current_state
    }
```

## Resource Usage Examples

### Dynamic Data Access

```python
# Access repository resources directly
config_resource = "githound://repository/path/to/repo/config"
branches_resource = "githound://repository/path/to/repo/branches"
contributors_resource = "githound://repository/path/to/repo/contributors"

# These resources provide real-time data without explicit tool calls
```

### Prompt-Driven Workflows

```python
# Use specialized prompts for common tasks
analyze_codebase_prompt = "analyze_codebase"
investigate_changes_prompt = "investigate_changes"
generate_insights_prompt = "generate_insights"

# These prompts guide AI assistants through structured workflows
```

## Error Handling Examples

### Robust Integration

```python
def safe_repository_analysis(repo_path):
    try:
        # Validate repository first
        validation = validate_repository(repo_path=repo_path)
        if not validation.get("is_valid"):
            return {"error": "Invalid repository", "details": validation}

        # Perform analysis with error handling
        analysis = analyze_repository(repo_path=repo_path)
        return {"success": True, "data": analysis}

    except Exception as e:
        return {"error": "Analysis failed", "message": str(e)}
```

### Graceful Degradation

```python
def comprehensive_search(repo_path, query):
    results = {}

    # Try advanced search first
    try:
        results["advanced"] = advanced_search(
            repo_path=repo_path,
            query=query
        )
    except Exception:
        # Fall back to content search
        try:
            results["content"] = content_search(
                repo_path=repo_path,
                pattern=query
            )
        except Exception:
            # Final fallback to fuzzy search
            results["fuzzy"] = fuzzy_search(
                repo_path=repo_path,
                query=query,
                threshold=0.6
            )

    return results
```

## Performance Optimization

### Efficient Data Retrieval

```python
# Use pagination for large datasets
def get_all_commits_efficiently(repo_path):
    all_commits = []
    skip = 0
    batch_size = 100

    while True:
        batch = get_commit_history(
            repo_path=repo_path,
            max_commits=batch_size,
            skip_commits=skip
        )

        if not batch:
            break

        all_commits.extend(batch)
        skip += batch_size

    return all_commits
```

### Caching Strategies

```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_repository_analysis(repo_path):
    return analyze_repository(repo_path=repo_path)

# Use cached results for repeated queries
analysis = cached_repository_analysis("/path/to/repo")
```

## Testing Integration

### Unit Testing MCP Tools

```python
import pytest
from githound.mcp.tools import analyze_repository

def test_repository_analysis():
    # Test with valid repository
    result = analyze_repository(repo_path="/path/to/test/repo")
    assert result is not None
    assert "name" in result
    assert "branches" in result

    # Test with invalid repository
    with pytest.raises(Exception):
        analyze_repository(repo_path="/invalid/path")
```

### Integration Testing

```python
def test_full_workflow():
    repo_path = "/path/to/test/repo"

    # Test complete analysis workflow
    analysis = analyze_repository(repo_path=repo_path)
    branches = list_branches(repo_path=repo_path)
    commits = get_commit_history(repo_path=repo_path, max_commits=10)

    assert analysis is not None
    assert len(branches) > 0
    assert len(commits) > 0
```

## Best Practices

### 1. Repository Validation

Always validate repositories before performing operations:

```python
validation = validate_repository(repo_path=repo_path)
if not validation.get("is_valid"):
    handle_invalid_repository(validation)
```

### 2. Error Handling

Implement comprehensive error handling:

```python
try:
    result = mcp_tool_call(parameters)
except ValidationError as e:
    handle_validation_error(e)
except RepositoryError as e:
    handle_repository_error(e)
except Exception as e:
    handle_general_error(e)
```

### 3. Resource Management

Use appropriate limits and timeouts:

```python
# Limit result sizes
results = advanced_search(
    repo_path=repo_path,
    query=query,
    max_results=100  # Reasonable limit
)

# Use pagination for large datasets
commits = get_commit_history(
    repo_path=repo_path,
    max_commits=50,  # Manageable batch size
    skip_commits=0
)
```

### 4. Performance Monitoring

Monitor tool performance and usage:

```python
import time

start_time = time.time()
result = analyze_repository(repo_path=repo_path)
execution_time = time.time() - start_time

if execution_time > 10:  # 10 seconds threshold
    log_slow_operation("analyze_repository", execution_time)
```

## Platform-Specific Workflows

### Claude Desktop Workflows

#### Pull Request Review Workflow

```markdown
# Claude Desktop Prompt Example

I'm reviewing a pull request. Can you help me analyze the changes?

1. First, analyze the repository structure:
   - Use `analyze_repository` to understand the codebase
   - Use `list_branches` to see all branches

2. Compare the feature branch with main:
   - Use `compare_branches_diff` to see all changes
   - Use `get_commit_history` to understand the development timeline

3. For each changed file:
   - Use `analyze_file_blame` to understand authorship
   - Use `get_file_history_mcp` to see change patterns

4. Look for potential issues:
   - Use `advanced_search` to find similar patterns
   - Use `detect_patterns` to identify anti-patterns
```

### Cursor Workflows

#### Feature Development

```markdown
# Cursor Integration Example

When developing a new feature in Cursor:

1. **Context Gathering**:

   @githound analyze_repository repo_path="/current/project"
   @githound list_branches include_remote=true

2. **Pattern Research**:

   @githound advanced_search repo_path="/current/project" content_pattern="similar_feature" file_extensions=["py", "js"]

3. **Impact Analysis**:

   @githound compare_branches_diff repo_path="/current/project" branch1="main" branch2="feature/new-auth"
```

### GitHub Copilot Workflows

#### Code Documentation

```markdown
# GitHub Copilot Chat Example

/githound analyze_repository repo_path="." include_stats=true

Based on the repository analysis, help me:
1. Generate comprehensive README documentation
2. Identify undocumented functions and classes
3. Suggest code organization improvements
4. Create API documentation templates
```

## Best Practices by Platform

### Claude Desktop

- Use descriptive prompts that leverage GitHound's analysis capabilities
- Combine multiple tools for comprehensive analysis
- Use the built-in prompts for common workflows

### Cursor

- Integrate GitHound commands into your development workflow
- Use context-aware queries based on current file/project
- Leverage real-time analysis during coding

### VS Code

- Create custom tasks and commands for frequent operations
- Use workspace-specific configurations
- Integrate with debugging and testing workflows

### GitHub Copilot

- Use GitHound for context gathering before code generation
- Combine repository analysis with code suggestions
- Leverage historical patterns for better recommendations

### Custom Applications

- Implement proper error handling and retry logic
- Use authentication for production deployments
- Monitor performance and implement caching strategies

These examples demonstrate how to effectively integrate GitHound MCP server with various AI tools
and applications, providing comprehensive Git repository analysis capabilities through the
standardized MCP protocol.
