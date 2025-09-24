#!/usr/bin/env python3
"""
FastMCP Advanced Features Examples

This example demonstrates advanced FastMCP client features including:
- Authentication (Bearer token, OAuth 2.1)
- Progress monitoring for long-running operations
- Logging and debugging capabilities
- Advanced error handling and retry strategies
- Performance monitoring and optimization

Usage:
    python examples/mcp_server/clients/advanced_features.py

This example covers:
- Authentication configuration and management
- Progress tracking for long-running operations
- Comprehensive logging setup
- Advanced error handling patterns
- Performance monitoring and metrics
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, List, Dict
from dataclasses import dataclass
import json

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from fastmcp.exceptions import ToolError

# Configure advanced logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_client.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProgressInfo:
    """Progress information for long-running operations."""
    operation: str
    current: int
    total: int
    start_time: float
    message: Optional[str] = None

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100.0

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def estimated_remaining(self) -> float:
        """Estimate remaining time in seconds."""
        if self.current == 0:
            return 0.0

        rate = self.current / self.elapsed_time
        remaining_items = self.total - self.current
        return remaining_items / rate if rate > 0 else 0.0


class ProgressMonitor:
    """Monitor progress of long-running operations."""

    def __init__(self, operation: str, total: int) -> None:
        """
        Initialize progress monitor.

        Args:
            operation: Name of the operation
            total: Total number of items to process
        """
        self.operation = operation
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.callbacks: List[Callable[[ProgressInfo], None]] = []

    def add_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """Add a progress callback."""
        self.callbacks.append(callback)

    def update(self, increment: int = 1, message: Optional[str] = None) -> None:
        """
        Update progress.

        Args:
            increment: Number of items completed
            message: Optional progress message
        """
        self.current += increment

        progress = ProgressInfo(
            operation=self.operation,
            current=self.current,
            total=self.total,
            start_time=self.start_time,
            message=message
        )

        # Call all callbacks
        for callback in self.callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def complete(self, message: Optional[str] = None) -> None:
        """Mark operation as complete."""
        self.current = self.total
        self.update(0, message or f"{self.operation} completed")


def default_progress_callback(progress: ProgressInfo) -> None:
    """Default progress callback that logs progress."""
    logger.info(
        f"{progress.operation}: {progress.current}/{progress.total} "
        f"({progress.percentage:.1f}%) - "
        f"Elapsed: {progress.elapsed_time:.1f}s, "
        f"ETA: {progress.estimated_remaining:.1f}s"
    )

    if progress.message:
        logger.info(f"  {progress.message}")


class AuthenticationManager:
    """Manage authentication for MCP clients."""

    def __init__(self) -> None:
        """Initialize authentication manager."""
        self.tokens: Dict[str, str] = {}
        self.refresh_tokens: Dict[str, str] = {}
        self.token_expiry: Dict[str, datetime] = {}

    def set_bearer_token(self, server_id: str, token: str, expires_at: Optional[datetime] = None) -> None:
        """
        Set bearer token for a server.

        Args:
            server_id: Server identifier
            token: Bearer token
            expires_at: Optional token expiry time
        """
        self.tokens[server_id] = token
        if expires_at:
            self.token_expiry[server_id] = expires_at

        logger.info(f"Bearer token set for server: {server_id}")

    def set_oauth_tokens(self, server_id: str, access_token: str, refresh_token: str, expires_at: datetime) -> None:
        """
        Set OAuth 2.1 tokens for a server.

        Args:
            server_id: Server identifier
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiry time
        """
        self.tokens[server_id] = access_token
        self.refresh_tokens[server_id] = refresh_token
        self.token_expiry[server_id] = expires_at

        logger.info(f"OAuth tokens set for server: {server_id}")

    def get_auth_headers(self, server_id: str) -> Dict[str, str]:
        """
        Get authentication headers for a server.

        Args:
            server_id: Server identifier

        Returns:
            Dictionary of authentication headers
        """
        if server_id not in self.tokens:
            return {}

        # Check if token is expired
        if server_id in self.token_expiry:
            if datetime.now() >= self.token_expiry[server_id]:
                logger.warning(f"Token expired for server: {server_id}")
                # In a real implementation, you would refresh the token here
                return {}

        return {"Authorization": f"Bearer {self.tokens[server_id]}"}

    def is_token_valid(self, server_id: str) -> bool:
        """
        Check if token is valid for a server.

        Args:
            server_id: Server identifier

        Returns:
            True if token is valid, False otherwise
        """
        if server_id not in self.tokens:
            return False

        if server_id in self.token_expiry:
            return datetime.now() < self.token_expiry[server_id]

        return True


async def demonstrate_authentication() -> Dict[str, Any]:
    """
    Demonstrate authentication features.

    Shows how to:
    1. Configure bearer token authentication
    2. Handle OAuth 2.1 authentication
    3. Manage token expiry and refresh
    4. Handle authentication errors

    Returns:
        Dict containing authentication demonstration results
    """
    logger.info("Demonstrating authentication features...")

    auth_manager = AuthenticationManager()

    # 1. Bearer Token Authentication
    logger.info("1. Bearer Token Authentication")
    auth_manager.set_bearer_token("test-server", "test_bearer_token_123")

    headers = auth_manager.get_auth_headers("test-server")
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer test_bearer_token_123"
    logger.info("✓ Bearer token authentication configured")  # [attr-defined]

    # 2. OAuth 2.1 Authentication
    logger.info("2. OAuth 2.1 Authentication")
    expires_at = datetime.now().replace(hour=23, minute=59, second=59)
    auth_manager.set_oauth_tokens(
        "oauth-server",
        "oauth_access_token_456",
        "oauth_refresh_token_789",
        expires_at
    )

    oauth_headers = auth_manager.get_auth_headers("oauth-server")
    assert "Authorization" in oauth_headers
    assert oauth_headers["Authorization"] == "Bearer oauth_access_token_456"
    logger.info("✓ OAuth 2.1 authentication configured")  # [attr-defined]

    # 3. Token Validation
    logger.info("3. Token Validation")
    assert auth_manager.is_token_valid("test-server") is True
    assert auth_manager.is_token_valid("oauth-server") is True
    assert auth_manager.is_token_valid("non-existent") is False
    logger.info("✓ Token validation working")

    # 4. HTTP Transport with Authentication
    logger.info("4. HTTP Transport with Authentication")
    try:
        # This would be used with a real HTTP MCP server
        auth_headers = auth_manager.get_auth_headers("test-server")

        # Example of creating HTTP transport with authentication
        # transport = HttpTransport("http://localhost:8000/mcp", headers=auth_headers)
        logger.info("✓ HTTP transport with authentication configured")  # [attr-defined]

        auth_demo_result = {
            "bearer_token_configured": True,
            "oauth_configured": True,
            "token_validation": True,
            "http_auth_ready": True
        }

    except Exception as e:
        logger.warning(f"HTTP authentication demo failed: {e}")
        auth_demo_result = {
            "bearer_token_configured": True,
            "oauth_configured": True,
            "token_validation": True,
            "http_auth_ready": False,
            "error": str(e)
        }

    return {
        "status": "success",
        "authentication_features": auth_demo_result,
        "servers_configured": len(auth_manager.tokens)  # [attr-defined]
    }


async def demonstrate_progress_monitoring() -> Dict[str, Any]:
    """
    Demonstrate progress monitoring for long-running operations.

    Shows how to:
    1. Set up progress monitoring
    2. Track operation progress
    3. Estimate completion time
    4. Handle progress callbacks

    Returns:
        Dict containing progress monitoring demonstration results
    """
    logger.info("Demonstrating progress monitoring...")

    # 1. Basic Progress Monitoring
    logger.info("1. Basic Progress Monitoring")

    progress_monitor = ProgressMonitor("Repository Analysis", 100)
    progress_monitor.add_callback(default_progress_callback)

    # Simulate long-running operation
    for i in range(10):
        await asyncio.sleep(0.1)  # Simulate work
        progress_monitor.update(10, f"Processing batch {i+1}")

    progress_monitor.complete("Repository analysis finished")

    # 2. Multiple Operations Progress
    logger.info("2. Multiple Operations Progress")

    operations = [
        ("Analyzing commits", 50),
        ("Processing files", 30),
        ("Generating statistics", 20)
    ]

    operation_results: list[Any] = []

    for operation_name, total_items in operations:
        monitor = ProgressMonitor(operation_name, total_items)
        monitor.add_callback(default_progress_callback)

        start_time = time.time()

        # Simulate operation
        for i in range(total_items):
            await asyncio.sleep(0.01)  # Simulate work
            if i % 10 == 0:  # Update every 10 items
                monitor.update(10, f"Processed {i+10} items")

        monitor.complete()

        operation_results.append({
            "operation": operation_name,
            "total_items": total_items,
            "duration": time.time if time is not None else None() - start_time
        })

    # 3. Progress with Error Handling
    logger.info("3. Progress with Error Handling")

    error_monitor = ProgressMonitor("Error-prone Operation", 20)
    error_monitor.add_callback(default_progress_callback)

    try:
        for i in range(20):
            await asyncio.sleep(0.05)

            # Simulate error in the middle
            if i == 10:
                raise RuntimeError("Simulated operation error")

            error_monitor.update(1, f"Processing item {i+1}")

        error_monitor.complete()

    except Exception as e:
        logger.error(f"Operation failed at {error_monitor.current}/{error_monitor.total}: {e}")
        error_handled = True
    else:
        error_handled = False

    return {
        "status": "success",
        "basic_progress": True,
        "multiple_operations": len(operation_results),
        "operation_results": operation_results,
        "error_handling": error_handled,
        "total_operations_monitored": 1 + len(operations) + 1
    }


async def demonstrate_advanced_logging() -> Dict[str, Any]:
    """
    Demonstrate advanced logging and debugging capabilities.

    Shows how to:
    1. Configure structured logging
    2. Log MCP operations
    3. Debug connection issues
    4. Performance logging

    Returns:
        Dict containing logging demonstration results
    """
    logger.info("Demonstrating advanced logging...")

    # 1. Structured Logging
    logger.info("1. Structured Logging")

    # Create a structured log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": "mcp_client_demo",
        "client_version": "1.0.0",
        "server_type": "simple",
        "metrics": {
            "connection_time": 0.5,
            "tool_count": 4,
            "resource_count": 3
        }
    }

    logger.info(f"Structured log: {json.dumps(log_entry, indent=2)}")

    # 2. Operation Logging
    logger.info("2. Operation Logging")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    operation_logs: list[Any] = []

    try:
        async with Client(transport) as client:
            # Log connection
            connection_log = {
                "event": "connection_established",
                "transport": "stdio",
                "timestamp": datetime.now().isoformat()
            }
            operation_logs.append(connection_log)
            logger.info(f"Connection log: {json.dumps(connection_log)}")

            # Log tool discovery
            start_time = time.time()
            tools = await client.list_tools()
            discovery_time = time.time() - start_time

            discovery_log = {
                "event": "tool_discovery",
                "tools_found": len(tools),
                "discovery_time": discovery_time,
                "timestamp": datetime.now().isoformat()
            }
            operation_logs.append(discovery_log)
            logger.info(f"Discovery log: {json.dumps(discovery_log)}")

            # Log tool execution
            start_time = time.time()
            result = await client.call_tool("echo", {"message": "logging test"})
            execution_time = time.time() - start_time

            execution_log = {
                "event": "tool_execution",
                "tool_name": "echo",
                "execution_time": execution_time,
                "success": result is not None,
                "timestamp": datetime.now().isoformat()
            }
            operation_logs.append(execution_log)
            logger.info(f"Execution log: {json.dumps(execution_log)}")

    except Exception as e:
        error_log = {
            "event": "operation_error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        operation_logs.append(error_log)
        logger.error(f"Error log: {json.dumps(error_log)}")

    # 3. Performance Logging
    logger.info("3. Performance Logging")

    performance_metrics = {
        "total_operations": len(operation_logs),
        "successful_operations": len([log for log in operation_logs if log.get("success", True)]),
        "average_execution_time": sum(log.get("execution_time", 0) for log in operation_logs) / len(operation_logs) if operation_logs else 0,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Performance metrics: {json.dumps(performance_metrics, indent=2)}")

    return {
        "status": "success",
        "structured_logging": True,
        "operation_logs": len(operation_logs),
        "performance_metrics": performance_metrics,
        "log_file_created": True
    }


async def demonstrate_retry_strategies() -> Dict[str, Any]:
    """
    Demonstrate advanced retry strategies and error handling.

    Shows how to:
    1. Implement exponential backoff
    2. Handle different error types
    3. Circuit breaker pattern
    4. Graceful degradation

    Returns:
        Dict containing retry strategy demonstration results
    """
    logger.info("Demonstrating retry strategies...")

    retry_results: list[Any] = []

    # 1. Exponential Backoff
    logger.info("1. Exponential Backoff Retry")

    async def retry_with_backoff(operation, max_retries=3, base_delay=1.0) -> None:
        """Retry operation with exponential backoff."""
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries:
                    raise e

                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)

    # Simulate failing operation
    attempt_count = 0

    async def failing_operation() -> None:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"Simulated failure {attempt_count}")
        return "Success after retries"

    try:
        result = await retry_with_backoff(failing_operation)
        retry_results.append({
            "strategy": "exponential_backoff",
            "attempts": attempt_count,
            "success": True,
            "result": result
        })
        logger.info(f"✓ Exponential backoff succeeded after {attempt_count} attempts")
    except Exception as e:
        retry_results.append({
            "strategy": "exponential_backoff",
            "attempts": attempt_count,
            "success": False,
            "error": str(e)
        })

    # 2. Circuit Breaker Pattern
    logger.info("2. Circuit Breaker Pattern")

    class CircuitBreaker:
        def __init__(self, failure_threshold=3, recovery_timeout=5.0) -> None:
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "closed"  # closed, open, half-open

        async def call(self, operation) -> None:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise RuntimeError("Circuit breaker is open")

            try:
                result = await operation()
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"

                raise e

    circuit_breaker = CircuitBreaker()

    # Test circuit breaker
    async def unreliable_operation() -> None:
        if circuit_breaker.failure_count < 2:
            raise RuntimeError("Simulated service failure")
        return "Service recovered"

    circuit_results: list[Any] = []
    for i in range(5):
        try:
            result = await circuit_breaker.call(unreliable_operation)
            circuit_results.append({"attempt": i + 1, "success": True, "result": result})
        except Exception as e:
            circuit_results.append({"attempt": i + 1, "success": False, "error": str(e)})

        await asyncio.sleep(0.1)

    retry_results.append({
        "strategy": "circuit_breaker",
        "attempts": len(circuit_results),
        "successful_attempts": len([r for r in circuit_results if r["success"]]),
        "circuit_state": circuit_breaker.state
    })

    return {
        "status": "success",
        "retry_strategies": len(retry_results),
        "strategy_results": retry_results,
        "total_attempts": sum(r.get("attempts", 0) for r in retry_results)
    }


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating all advanced FastMCP client features.

    Returns:
        Dict containing all advanced feature demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Advanced Features Examples")
    print("=" * 60)

    results: dict[str, Any] = {}

    try:
        # 1. Authentication
        logger.info("\n1. Authentication Features")
        auth_result = await demonstrate_authentication()
        results["authentication"] = auth_result

        # 2. Progress Monitoring
        logger.info("\n2. Progress Monitoring")
        progress_result = await demonstrate_progress_monitoring()
        results["progress_monitoring"] = progress_result

        # 3. Advanced Logging
        logger.info("\n3. Advanced Logging")
        logging_result = await demonstrate_advanced_logging()
        results["advanced_logging"] = logging_result

        # 4. Retry Strategies
        logger.info("\n4. Retry Strategies")
        retry_result = await demonstrate_retry_strategies()
        results["retry_strategies"] = retry_result

        print("\n" + "=" * 60)
        print("Advanced features examples completed!")
        print("=" * 60)

        return results

    except Exception as e:
        logger.error(f"Advanced features examples failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the advanced features examples
    result = asyncio.run(main())
    print(f"\nAdvanced Features Summary:")
    for category, result_data in result.items():
        if isinstance(result_data, dict) and "status" in result_data:
            print(f"  {category}: {result_data['status']}")
        else:
            print(f"  {category}: completed")
