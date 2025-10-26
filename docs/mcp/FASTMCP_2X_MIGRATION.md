# FastMCP 2.x Migration Guide for GitHound

This guide helps you understand and leverage the latest FastMCP 2.x features integrated into GitHound MCP Server.

## What's New in FastMCP 2.x

FastMCP 2.x brings significant improvements over previous versions:

### 1. Enhanced Context API

The `Context` object now provides rich capabilities:

```python
from fastmcp import Context

@mcp.tool
async def my_tool(repo_path: str, ctx: Context) -> dict:
    # Multiple logging levels
    await ctx.debug("Debug information")
    await ctx.info("General information")
    await ctx.warning("Warning message")
    await ctx.error("Error message")
    await ctx.critical("Critical issue")

    # Progress reporting
    await ctx.report_progress(
        progress=50,
        total=100,
        message="Halfway through processing"
    )

    # LLM sampling
    result = await ctx.sample(
        prompt="Analyze this code...",
        max_tokens=1000,
        temperature=0.7
    )

    # Resource reading
    resource = await ctx.read_resource("githound://repo/path/config")

    return {"status": "success"}
```

### 2. Progress Reporting

Long-running operations can now report progress to clients:

```python
from githound.mcp import ProgressTracker

@mcp.tool
async def analyze_large_repo(repo_path: str, ctx: Context) -> dict:
    async with ProgressTracker(ctx, "Analysis", total=1000) as tracker:
        for i in range(1000):
            # Process item
            await tracker.increment()

    return {"status": "success"}
```

### 3. LLM Sampling

Request LLM analysis directly from your tools:

```python
from githound.mcp import request_llm_analysis

@mcp.tool
async def intelligent_analysis(code: str, ctx: Context) -> dict:
    prompt = f"Analyze this code and suggest improvements:\n{code}"
    analysis = await request_llm_analysis(ctx, prompt)

    return {"status": "success", "analysis": analysis}
```

### 4. Resource Access

Tools can now read resources from the same or other MCP servers:

```python
from githound.mcp import read_mcp_resource

@mcp.tool
async def cross_reference(uri: str, ctx: Context) -> dict:
    content = await read_mcp_resource(ctx, uri)
    return {"status": "success", "content": content}
```

## GitHound's FastMCP 2.x Integration

### Available Helper Functions

GitHound provides several helper functions in `githound.mcp`:

```python
from githound.mcp import (
    ProgressTracker,              # Context manager for progress tracking
    report_operation_progress,    # Report progress for operations
    stream_results_with_progress, # Stream results with progress
    safe_execute_with_logging,    # Execute with error handling
    log_operation_metrics,        # Log performance metrics
    request_llm_analysis,         # Request LLM analysis
    read_mcp_resource,           # Read MCP resources
)
```

### Examples

#### Example 1: Advanced Search with Progress

```python
from githound.mcp import ProgressTracker

@mcp.tool
async def advanced_search_with_progress(
    repo_path: str,
    pattern: str,
    ctx: Context
) -> dict:
    results = []

    async with ProgressTracker(ctx, "Searching", total=100) as tracker:
        # Perform search
        async for result in search_iterator:
            results.append(result)
            await tracker.increment()

    return {"status": "success", "results": results}
```

#### Example 2: Intelligent Code Review

```python
from githound.mcp import request_llm_analysis

@mcp.tool
async def intelligent_code_review(
    repo_path: str,
    branch: str,
    ctx: Context
) -> dict:
    # Get diff
    diff = get_branch_diff(repo_path, branch)

    # Request LLM review
    prompt = f"Review this code change:\n{diff}"
    review = await request_llm_analysis(
        ctx,
        prompt,
        max_tokens=2000,
        temperature=0.3
    )

    return {
        "status": "success",
        "branch": branch,
        "review": review
    }
```

#### Example 3: Performance Metrics

```python
from githound.mcp import log_operation_metrics
import time

@mcp.tool
async def analyze_with_metrics(repo_path: str, ctx: Context) -> dict:
    start = time.time()

    # Perform analysis
    results = await perform_analysis(repo_path)

    duration_ms = (time.time() - start) * 1000
    await log_operation_metrics(
        ctx,
        "Repository Analysis",
        duration_ms,
        items_processed=len(results)
    )

    return {"status": "success", "results": results}
```

## Migration Checklist

### For Existing GitHound Users

- [x] FastMCP 2.x is already integrated - no action needed
- [x] All existing tools continue to work
- [ ] Optional: Add progress reporting to long-running operations
- [ ] Optional: Use LLM sampling for intelligent analysis
- [ ] Optional: Add performance metrics logging

### For New Implementations

1. **Install FastMCP 2.x**

   ```bash
   pip install fastmcp>=2.11.0
   ```

2. **Use Enhanced Context**

   ```python
   from fastmcp import Context

   @mcp.tool
   async def my_tool(ctx: Context) -> dict:
       await ctx.info("Starting operation")
       # Your code here
       return {"status": "success"}
   ```

3. **Add Progress Reporting** (Optional)

   ```python
   from githound.mcp import ProgressTracker

   async with ProgressTracker(ctx, "Operation") as tracker:
       # Your code with tracker.increment()
   ```

4. **Enable LLM Features** (Optional)

   ```python
   from githound.mcp import request_llm_analysis

   analysis = await request_llm_analysis(ctx, prompt)
   ```

## Configuration

### Environment Variables

FastMCP 2.x settings can be configured via environment variables:

```bash
# Server configuration
export FASTMCP_SERVER_NAME="GitHound MCP Server"
export FASTMCP_SERVER_VERSION="2.0.0"
export FASTMCP_SERVER_TRANSPORT="stdio"  # or "http", "sse"
export FASTMCP_SERVER_HOST="localhost"
export FASTMCP_SERVER_PORT="3000"
export FASTMCP_SERVER_LOG_LEVEL="INFO"

# Authentication (if enabled)
export FASTMCP_SERVER_ENABLE_AUTH="true"
```

### MCP.json Configuration

Use MCP.json for client integration:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp"],
      "env": {
        "FASTMCP_SERVER_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Best Practices

### 1. Use Progress Reporting for Long Operations

Operations taking >5 seconds should report progress:

```python
async with ProgressTracker(ctx, "Operation", total=items) as tracker:
    for item in items:
        await process(item)
        await tracker.increment()
```

### 2. Log at Appropriate Levels

```python
await ctx.debug("Detailed debugging info")
await ctx.info("General progress updates")
await ctx.warning("Non-critical issues")
await ctx.error("Errors that don't stop execution")
await ctx.critical("Critical failures")
```

### 3. Use LLM Sampling Wisely

- Keep prompts focused and specific
- Use appropriate temperature (0.3-0.7)
- Limit max_tokens to avoid excessive costs
- Handle cases where LLM is unavailable

### 4. Implement Graceful Degradation

```python
from githound.mcp import request_llm_analysis

analysis = await request_llm_analysis(ctx, prompt)
if analysis:
    # Use LLM insights
    pass
else:
    # Fall back to rule-based analysis
    pass
```

## Troubleshooting

### Context Methods Not Available

If you get `AttributeError` for context methods:

1. Verify FastMCP version: `pip show fastmcp`
2. Ensure version >= 2.11.0
3. Check imports: `from fastmcp import Context`

### Progress Not Showing

Some clients may not support progress reporting. The tool will still work, but progress won't be visible.

### LLM Sampling Failures

LLM sampling requires:

- Client support for sampling
- Proper authentication (if required)
- Network connectivity (for remote LLMs)

Use try-except or helper functions that handle failures gracefully.

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [GitHound Examples](../examples/mcp/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## Support

For issues or questions:

- GitHound Issues: https://github.com/AstroAir/GitHound/issues
- FastMCP Discord: https://discord.gg/fastmcp
- MCP Community: https://github.com/modelcontextprotocol
