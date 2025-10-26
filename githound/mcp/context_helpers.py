"""Helper utilities for working with FastMCP 2.x Context in GitHound MCP server.

This module provides convenient wrappers and utilities for leveraging
FastMCP 2.x's enhanced Context capabilities, including progress reporting,
LLM sampling, and resource access.
"""

from collections.abc import AsyncIterator
from typing import Any

try:
    from fastmcp import Context

    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    Context = Any


async def report_operation_progress(
    ctx: Context,
    current: int,
    total: int,
    operation: str = "Processing",
    log_interval: int = 10,
) -> None:
    """
    Report progress for long-running operations with smart logging.

    Args:
        ctx: FastMCP context object
        current: Current progress value
        total: Total expected items/operations
        operation: Name of the operation being performed
        log_interval: Report progress every N items
    """
    if current % log_interval == 0 or current == total:
        percentage = (current / total * 100) if total > 0 else 0
        message = f"{operation}: {current}/{total} ({percentage:.1f}%)"

        # Use FastMCP 2.x progress reporting
        if hasattr(ctx, "report_progress"):
            await ctx.report_progress(progress=current, total=total, message=message)

        # Also log for compatibility
        if hasattr(ctx, "info"):
            await ctx.info(message)


async def stream_results_with_progress(
    ctx: Context,
    results_iterator: AsyncIterator[Any],
    operation: str = "Search",
    max_results: int | None = None,
) -> list[Any]:
    """
    Stream results from an async iterator with progress reporting.

    Args:
        ctx: FastMCP context object
        results_iterator: Async iterator yielding results
        operation: Name of the operation
        max_results: Maximum expected results (if known)

    Returns:
        List of all results
    """
    results = []
    count = 0

    async for result in results_iterator:
        results.append(result)
        count += 1

        # Report progress
        if max_results:
            await report_operation_progress(ctx, count, max_results, operation)
        elif count % 10 == 0:
            await ctx.info(f"{operation}: {count} items processed")

    await ctx.info(f"{operation} complete: {count} items total")
    return results


async def safe_execute_with_logging(
    ctx: Context, operation: str, func: Any, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """
    Execute a function with comprehensive error handling and logging.

    Args:
        ctx: FastMCP context object
        operation: Name of the operation for logging
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Dictionary with status and result or error
    """
    try:
        await ctx.info(f"Starting {operation}")
        result = await func(*args, **kwargs) if callable(func) else func
        await ctx.info(f"{operation} completed successfully")

        return {"status": "success", "result": result}

    except Exception as e:
        error_msg = f"{operation} failed: {str(e)}"
        await ctx.error(error_msg)

        return {"status": "error", "error": str(e), "operation": operation}


async def log_operation_metrics(
    ctx: Context, operation: str, duration_ms: float, items_processed: int = 0
) -> None:
    """
    Log operation metrics for performance monitoring.

    Args:
        ctx: FastMCP context object
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        items_processed: Number of items processed
    """
    metrics = {
        "operation": operation,
        "duration_ms": duration_ms,
        "items_processed": items_processed,
    }

    if items_processed > 0:
        items_per_second = items_processed / (duration_ms / 1000)
        metrics["items_per_second"] = round(items_per_second, 2)

    message = f"Metrics for {operation}: {duration_ms:.2f}ms"
    if items_processed > 0:
        message += f", {items_processed} items ({metrics.get('items_per_second', 0):.2f} items/s)"

    await ctx.info(message)


async def request_llm_analysis(
    ctx: Context, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
) -> str | None:
    """
    Request LLM analysis through FastMCP 2.x context sampling.

    Args:
        ctx: FastMCP context object
        prompt: Prompt for the LLM
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature

    Returns:
        LLM response text or None if sampling unavailable
    """
    if not hasattr(ctx, "sample"):
        await ctx.warning("LLM sampling not available in this context")
        return None

    try:
        result = await ctx.sample(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        return result.text if hasattr(result, "text") else str(result)
    except Exception as e:
        await ctx.error(f"LLM sampling failed: {str(e)}")
        return None


async def read_mcp_resource(ctx: Context, resource_uri: str) -> str | None:
    """
    Read a resource through FastMCP 2.x context.

    Args:
        ctx: FastMCP context object
        resource_uri: URI of the resource to read

    Returns:
        Resource content or None if unavailable
    """
    if not hasattr(ctx, "read_resource"):
        await ctx.warning("Resource reading not available in this context")
        return None

    try:
        resource = await ctx.read_resource(resource_uri)
        return resource.content if hasattr(resource, "content") else str(resource)
    except Exception as e:
        await ctx.error(f"Resource read failed for {resource_uri}: {str(e)}")
        return None


class ProgressTracker:
    """Context manager for tracking operation progress with FastMCP 2.x."""

    def __init__(
        self, ctx: Context, operation: str, total: int | None = None, log_interval: int = 10
    ):
        self.ctx = ctx
        self.operation = operation
        self.total = total
        self.log_interval = log_interval
        self.current = 0

    async def __aenter__(self) -> "ProgressTracker":
        await self.ctx.info(f"Starting {self.operation}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            await self.ctx.info(f"{self.operation} completed: {self.current} items processed")
        else:
            await self.ctx.error(f"{self.operation} failed: {exc_val}")

    async def increment(self, count: int = 1) -> None:
        """Increment progress counter and report if needed."""
        self.current += count

        if self.total:
            await report_operation_progress(
                self.ctx, self.current, self.total, self.operation, self.log_interval
            )
        elif self.current % self.log_interval == 0:
            await self.ctx.info(f"{self.operation}: {self.current} items processed")

    async def set_total(self, total: int) -> None:
        """Set or update the total expected items."""
        self.total = total
