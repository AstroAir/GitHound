"""
Example demonstrating FastMCP 2.x advanced features in GitHound MCP Server.

This example shows how to use the latest FastMCP 2.x capabilities:
- Progress reporting for long-running operations
- LLM sampling for intelligent analysis
- Resource reading for cross-server communication
- Enhanced context logging methods
"""

import asyncio

try:
    from fastmcp import Context, FastMCP
except ImportError:
    print("FastMCP not available. Please install: pip install fastmcp>=2.11.0")
    exit(1)

from githound.mcp import ProgressTracker, request_llm_analysis

# Create a demo MCP server
mcp = FastMCP("GitHound Demo - FastMCP 2.x Features")


@mcp.tool
async def demo_progress_reporting(repo_path: str, ctx: Context) -> dict:
    """Demonstrate progress reporting during repository analysis."""
    # Use the ProgressTracker context manager
    async with ProgressTracker(ctx, "Repository Analysis", total=100) as tracker:
        for _ in range(100):
            # Simulate processing
            await asyncio.sleep(0.01)
            await tracker.increment()

    return {"status": "success", "message": "Analysis complete with progress tracking"}


@mcp.tool
async def demo_llm_analysis(repo_path: str, file_pattern: str, ctx: Context) -> dict:
    """Demonstrate using LLM sampling for intelligent code analysis."""
    await ctx.info(f"Analyzing files matching '{file_pattern}' in {repo_path}")

    # Prepare a prompt for LLM analysis
    prompt = f"""
    Analyze the code quality and suggest improvements for files matching:
    Pattern: {file_pattern}
    Repository: {repo_path}

    Provide a brief summary of:
    1. Common patterns found
    2. Potential issues
    3. Recommendations
    """

    # Request LLM analysis through FastMCP 2.x context
    analysis = await request_llm_analysis(ctx, prompt, max_tokens=500, temperature=0.7)

    if analysis:
        await ctx.info("LLM analysis completed successfully")
        return {"status": "success", "llm_analysis": analysis}
    else:
        return {"status": "warning", "message": "LLM sampling not available"}


@mcp.tool
async def demo_enhanced_logging(message: str, ctx: Context) -> dict:
    """Demonstrate FastMCP 2.x enhanced logging methods."""
    # FastMCP 2.x supports multiple log levels
    await ctx.debug(f"Debug message: {message}")
    await ctx.info(f"Info message: {message}")
    await ctx.warning(f"Warning message: {message}")
    await ctx.error(f"Error message: {message}")

    # Progress reporting
    for i in range(1, 6):
        await ctx.report_progress(progress=i, total=5, message=f"Step {i} of 5")
        await asyncio.sleep(0.1)

    return {"status": "success", "message": "All logging methods demonstrated"}


# Add a resource demonstrating dynamic templates
@mcp.resource("githound://demo/{repo_name}/status")
async def demo_resource_template(repo_name: str, ctx: Context) -> str:
    """Demonstrate dynamic resource templates with FastMCP 2.x."""
    await ctx.info(f"Accessing status for repository: {repo_name}")

    return f"""# Repository Status: {repo_name}

This is a demonstration of FastMCP 2.x dynamic resource templates.

Features demonstrated:
- URI path parameters ({repo_name})
- Context logging in resources
- Markdown formatted output

Status: Active
"""


if __name__ == "__main__":
    print("Starting GitHound FastMCP 2.x Demo Server...")
    print("This demonstrates the latest FastMCP features integrated with GitHound")
    mcp.run()
