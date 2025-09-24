#!/usr/bin/env python3
"""
FastMCP Transport Examples

This example demonstrates different FastMCP transport types and their usage patterns:
- STDIO Transport for local process communication
- HTTP Transport for remote server connections
- SSE Transport for server-sent events
- In-Memory Transport for testing

Usage:
    python examples/mcp_server/clients/transport_examples.py

This example covers:
- Transport configuration and initialization
- Connection patterns for different transport types
- Error handling specific to each transport
- Performance considerations and best practices
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Any
import json

from fastmcp import Client
from fastmcp.client.transports import (
    StdioTransport,
    StreamableHttpTransport,
    SSETransport,
    FastMCPTransport
)
from fastmcp.exceptions import McpError
import httpx

# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_stdio_transport() -> Dict[str, Any]:
    """
    Demonstrate STDIO transport for local process communication.

    STDIO transport is ideal for:
    - Local MCP servers running as separate processes
    - Development and testing scenarios
    - Servers that communicate via stdin/stdout

    Returns:
        Dict containing STDIO transport demonstration results
    """
    logger.info("Demonstrating STDIO Transport...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"

    try:
        # Create STDIO transport
        transport = StdioTransport("python", [str(server_script)])

        async with Client(transport) as client:
            logger.info("✓ STDIO transport connected successfully")

            # Test basic operations
            tools = await client.list_tools()
            logger.info(f"Tools available via STDIO: {len(tools)}")

            # Execute a simple tool
            result = await client.call_tool("echo", {"message": "Hello from STDIO!"})
            logger.info(f"STDIO tool result: {result.data}")

            # Access a resource
            resources = await client.list_resources()
            if resources:
                content = await client.read_resource(resources[0].uri)
                logger.info(f"STDIO resource content: {len(content)} blocks")

            return {
                "transport_type": "stdio",
                "status": "success",
                "tools_count": len(tools),
                "resources_count": len(resources),
                "connection_method": "process_communication"
            }

    except Exception as e:
        logger.error(f"STDIO transport failed: {e}")
        return {
            "transport_type": "stdio",
            "status": "failed",
            "error": str(e)
        }


async def demonstrate_http_transport() -> Dict[str, Any]:
    """
    Demonstrate HTTP transport for remote server connections.

    HTTP transport is ideal for:
    - Remote MCP servers accessible via HTTP
    - Production deployments
    - Servers behind load balancers or proxies

    Returns:
        Dict containing HTTP transport demonstration results
    """
    logger.info("Demonstrating HTTP Transport...")

    # Note: This example assumes an HTTP MCP server is running
    # In practice, you would start your HTTP MCP server first
    server_url = "http://localhost:8000/mcp"

    try:
        # Create HTTP transport
        transport = StreamableHttpTransport(server_url)

        # Test connection with timeout
        async with Client(transport) as client:
            logger.info("✓ HTTP transport connected successfully")

            # Test basic operations with HTTP-specific considerations
            tools = await client.list_tools()
            logger.info(f"Tools available via HTTP: {len(tools)}")

            # Execute tool with HTTP transport
            if tools:
                result = await client.call_tool(tools[0].name, {})
                logger.info(f"HTTP tool result type: {type(result.data)}")

            return {
                "transport_type": "http",
                "status": "success",
                "server_url": server_url,
                "tools_count": len(tools),
                "connection_method": "http_request"
            }

    except (McpError, httpx.ConnectError, Exception) as e:
        logger.warning(f"HTTP transport failed (expected if no HTTP server): {e}")
        return {
            "transport_type": "http",
            "status": "failed",
            "error": str(e),
            "note": "HTTP server may not be running"
        }


async def demonstrate_sse_transport() -> Dict[str, Any]:
    """
    Demonstrate SSE (Server-Sent Events) transport for real-time communication.

    SSE transport is ideal for:
    - Real-time updates from MCP servers
    - Streaming responses
    - Long-running operations with progress updates

    Returns:
        Dict containing SSE transport demonstration results
    """
    logger.info("Demonstrating SSE Transport...")

    # Note: This example assumes an SSE MCP server is running
    sse_url = "http://localhost:8001/mcp/sse"

    try:
        # Create SSE transport
        transport = SSETransport(sse_url)

        async with Client(transport) as client:
            logger.info("✓ SSE transport connected successfully")

            # Test SSE-specific operations
            tools = await client.list_tools()
            logger.info(f"Tools available via SSE: {len(tools)}")

            # SSE is particularly useful for streaming operations
            if tools:
                # Look for streaming or long-running tools
                streaming_tools = [t for t in tools if "stream" in t.name.lower()]
                if streaming_tools:
                    logger.info(f"Found streaming tool: {streaming_tools[0].name}")

            return {
                "transport_type": "sse",
                "status": "success",
                "server_url": sse_url,
                "tools_count": len(tools),
                "streaming_capable": len(streaming_tools) > 0 if 'streaming_tools' in locals() else False,
                "connection_method": "server_sent_events"
            }

    except Exception as e:
        logger.warning(f"SSE transport failed (expected if no SSE server): {e}")
        return {
            "transport_type": "sse",
            "status": "failed",
            "error": str(e),
            "note": "SSE server may not be running"
        }


async def demonstrate_inmemory_transport() -> Dict[str, Any]:
    """
    Demonstrate In-Memory transport for testing and development.

    In-Memory transport is ideal for:
    - Unit testing MCP clients
    - Development and debugging
    - Scenarios where server and client run in the same process

    Returns:
        Dict containing In-Memory transport demonstration results
    """
    logger.info("Demonstrating In-Memory Transport...")

    try:
        # For in-memory transport, we need to create a mock server
        # This is typically used in testing scenarios

        # Create a simple in-memory server implementation
        from fastmcp import FastMCP

        # Create mock server (simplified for demonstration)
        mock_server = FastMCP("Mock Server")

        # Create in-memory transport
        transport = FastMCPTransport(mock_server)

        async with Client(transport) as client:
            logger.info("✓ In-Memory transport connected successfully")

            # Test in-memory operations
            # Note: The mock server would need proper tool/resource implementations
            try:
                tools = await client.list_tools()
                logger.info(f"Tools available via In-Memory: {len(tools)}")

                resources = await client.list_resources()
                logger.info(f"Resources available via In-Memory: {len(resources)}")

            except Exception as e:
                logger.info(f"In-Memory operations (expected with mock): {e}")

            return {
                "transport_type": "inmemory",
                "status": "success",
                "server_type": "mock",
                "connection_method": "direct_memory"
            }

    except Exception as e:
        logger.error(f"In-Memory transport failed: {e}")
        return {
            "transport_type": "inmemory",
            "status": "failed",
            "error": str(e)
        }


async def demonstrate_transport_selection() -> Dict[str, Any]:
    """
    Demonstrate automatic transport selection based on input.

    FastMCP can automatically infer the appropriate transport based on:
    - URL schemes (http://, https://, ws://, wss://)
    - File paths (for STDIO transport)
    - Server objects (for in-memory transport)

    Returns:
        Dict containing transport selection examples
    """
    logger.info("Demonstrating automatic transport selection...")

    transport_examples = {
        "stdio_by_path": {
            "input": str(Path(__file__).parent.parent / "servers" / "simple_server.py"),
            "expected_transport": "StdioTransport",
            "description": "File path automatically selects STDIO transport"
        },
        "http_by_url": {
            "input": "http://localhost:8000/mcp",
            "expected_transport": "StreamableHttpTransport",
            "description": "HTTP URL automatically selects HTTP transport"
        },
        "https_by_url": {
            "input": "https://api.example.com/mcp",
            "expected_transport": "StreamableHttpTransport",
            "description": "HTTPS URL automatically selects HTTP transport"
        },
        "sse_by_url": {
            "input": "http://localhost:8001/mcp/sse",
            "expected_transport": "SSETransport",
            "description": "SSE endpoint automatically selects SSE transport"
        }
    }

    results: dict[str, Any] = {}

    for example_name, example_info in transport_examples.items():
        try:
            # This would be how automatic selection works in practice
            # Client can infer transport from the input
            logger.info(f"Example: {example_info['description']}")
            logger.info(f"Input: {example_info['input']}")
            logger.info(f"Expected: {example_info['expected_transport']}")

            results[example_name] = {
                "input": example_info["input"],
                "expected_transport": example_info["expected_transport"],
                "status": "documented"
            }

        except Exception as e:
            results[example_name] = {
                "input": example_info["input"],
                "status": "failed",
                "error": str(e)
            }

    return {
        "transport_selection": "automatic",
        "examples": results,
        "total_examples": len(transport_examples)
    }


async def demonstrate_transport_configuration() -> Dict[str, Any]:
    """
    Demonstrate advanced transport configuration options.

    Shows how to configure:
    - Timeouts and retry policies
    - Authentication headers
    - Custom connection parameters
    - Error handling strategies

    Returns:
        Dict containing transport configuration examples
    """
    logger.info("Demonstrating transport configuration...")  # [attr-defined]

    configurations: dict[str, Any] = {}

    # 1. STDIO with custom configuration
    try:
        server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"

        # STDIO transport with custom environment and working directory
        stdio_transport = StdioTransport(
            "python",
            str(server_script),
            env={"PYTHONPATH": str(Path(__file__).parent.parent)},
            cwd=str(Path(__file__).parent.parent)
        )

        configurations["stdio_custom"] = {
            "transport_type": "stdio",
            "custom_env": True,
            "custom_cwd": True,
            "status": "configured"
        }

    except Exception as e:
        configurations["stdio_custom"] = {"status": "failed", "error": str(e)}

    # 2. HTTP with authentication and timeouts
    try:
        # HTTP transport with custom headers and timeout
        http_transport = StreamableHttpTransport(
            "http://localhost:8000/mcp",
            headers={"Authorization": "Bearer token123"},
            sse_read_timeout=30.0
        )

        configurations["http_auth"] = {
            "transport_type": "http",
            "has_auth": True,
            "timeout": 30.0,
            "status": "configured"
        }

    except Exception as e:
        configurations["http_auth"] = {"status": "failed", "error": str(e)}

    return {
        "configuration_examples": configurations,
        "total_configurations": len(configurations)
    }


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating all FastMCP transport types and configurations.

    Returns:
        Dict containing all transport demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Transport Examples")
    print("=" * 60)

    results: dict[str, Any] = {}

    try:
        # 1. STDIO Transport
        logger.info("\n1. STDIO Transport")
        stdio_result = await demonstrate_stdio_transport()
        results["stdio"] = stdio_result

        # 2. HTTP Transport
        logger.info("\n2. HTTP Transport")
        http_result = await demonstrate_http_transport()
        results["http"] = http_result

        # 3. SSE Transport
        logger.info("\n3. SSE Transport")
        sse_result = await demonstrate_sse_transport()
        results["sse"] = sse_result

        # 4. In-Memory Transport
        logger.info("\n4. In-Memory Transport")
        inmemory_result = await demonstrate_inmemory_transport()
        results["inmemory"] = inmemory_result

        # 5. Transport Selection
        logger.info("\n5. Automatic Transport Selection")
        selection_result = await demonstrate_transport_selection()
        results["selection"] = selection_result

        # 6. Transport Configuration
        logger.info("\n6. Transport Configuration")  # [attr-defined]
        config_result = await demonstrate_transport_configuration()
        results["configuration"] = config_result

        print("\n" + "=" * 60)
        print("Transport examples completed!")
        print("=" * 60)

        return results

    except Exception as e:
        logger.error(f"Transport examples failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the transport examples
    result = asyncio.run(main())
    print(f"\nTransport Results Summary:")
    for transport_type, result_data in result.items():
        if isinstance(result_data, dict) and "status" in result_data:
            print(f"  {transport_type}: {result_data['status']}")
        else:
            print(f"  {transport_type}: completed")
