#!/usr/bin/env python3
"""
Basic FastMCP Client Example

This example demonstrates fundamental FastMCP client operations including:
- Client initialization and connection management
- Basic transport configuration
- Tool discovery and execution
- Resource access patterns
- Error handling and cleanup

Usage:
    python examples/mcp_server/clients/basic_client.py

This example covers:
- FastMCP client setup with different transports
- Connection lifecycle management
- Basic tool and resource operations
- Proper error handling patterns
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Any

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from fastmcp.exceptions import ToolError
import mcp.types as mcp_types

# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_client_setup() -> Dict[str, Any]:
    """
    Demonstrate basic FastMCP client setup and initialization.

    Shows how to:
    1. Create a FastMCP client with STDIO transport
    2. Establish connection to an MCP server
    3. Verify client capabilities
    4. Handle connection lifecycle

    Returns:
        Dict containing setup results and client information
    """
    logger.info("Starting basic FastMCP client setup...")

    # For this example, we'll use a simple echo server script
    # In practice, this would be your actual MCP server
    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"

    try:
        # Create FastMCP client with STDIO transport
        transport = PythonStdioTransport(str(server_script))

        async with Client(transport) as client:
            logger.info("✓ FastMCP client connected successfully")

            # Get server information using tool call
            server_info_result = await client.call_tool("get_server_info", {})
            server_info = server_info_result.content[0].text if server_info_result.content else "Unknown"
            logger.info(f"Connected to server: {server_info}")
            logger.info(f"Server response type: {type(server_info_result.content[0].text) if server_info_result.content else 'None'}")

            # Test basic connectivity
            tools = await client.list_tools()
            logger.info(f"Available tools: {len(tools)}")

            resources = await client.list_resources()
            logger.info(f"Available resources: {len(resources)}")

            return {
                "status": "success",
                "server_info": str(server_info)[:100] + "..." if len(str(server_info)) > 100 else str(server_info),
                "tools_count": len(tools),
                "resources_count": len(resources),
                "transport_type": "stdio"
            }

    except Exception as e:
        logger.error(f"Client setup failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "transport_type": "stdio"
        }


async def demonstrate_tool_operations() -> Dict[str, Any]:
    """
    Demonstrate basic tool discovery and execution patterns.

    Shows how to:
    1. Discover available tools
    2. Execute tools with arguments
    3. Handle tool results and structured data
    4. Manage tool execution errors

    Returns:
        Dict containing tool operation results
    """
    logger.info("Demonstrating tool operations...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # 1. Tool Discovery
            tools = await client.list_tools()
            logger.info(f"Discovered {len(tools)} tools:")

            tool_info: list[Any] = []
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                tool_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "has_schema": tool.inputSchema is not None
                })

            # 2. Tool Execution - Simple tool without arguments
            if tools:
                simple_tool = tools[0]
                logger.info(f"Executing tool: {simple_tool.name}")

                try:
                    result = await client.call_tool(simple_tool.name, {})
                    logger.info(f"Tool result: {result.data}")

                    # Access structured data if available
                    if result.data is not None:
                        logger.info(f"Structured data type: {type(result.data)}")

                    # Access traditional content blocks
                    for i, content in enumerate(result.content):
                        if hasattr(content, 'text'):
                            logger.info(f"Content {i}: {content.text[:100]}...")

                except ToolError as e:
                    logger.warning(f"Tool execution failed: {e}")

            return {
                "status": "success",
                "tools_discovered": len(tools),
                "tool_info": tool_info,
                "execution_attempted": len(tools) > 0
            }

    except Exception as e:
        logger.error(f"Tool operations failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def demonstrate_resource_access() -> Dict[str, Any]:
    """
    Demonstrate basic resource discovery and access patterns.

    Shows how to:
    1. Discover available resources
    2. Read static resources
    3. Handle different content types
    4. Manage resource access errors

    Returns:
        Dict containing resource access results
    """
    logger.info("Demonstrating resource access...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # 1. Resource Discovery
            resources = await client.list_resources()
            logger.info(f"Discovered {len(resources)} resources:")

            resource_info: list[Any] = []
            for resource in resources:
                logger.info(f"  - {resource.uri}: {resource.description}")
                resource_info.append({
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mime_type": getattr(resource, 'mimeType', None)
                })

            # 2. Resource Access
            if resources:
                resource = resources[0]
                logger.info(f"Reading resource: {resource.uri}")

                try:
                    content = await client.read_resource(resource.uri)
                    logger.info(f"Resource content blocks: {len(content)}")

                    for i, block in enumerate(content):
                        if hasattr(block, 'text'):
                            logger.info(f"Text content {i}: {block.text[:100]}...")
                        elif hasattr(block, 'blob'):
                            logger.info(f"Binary content {i}: {len(block.blob)} bytes")

                except Exception as e:
                    logger.warning(f"Resource access failed: {e}")

            return {
                "status": "success",
                "resources_discovered": len(resources),
                "resource_info": resource_info,
                "access_attempted": len(resources) > 0
            }

    except Exception as e:
        logger.error(f"Resource access failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def demonstrate_error_handling() -> Dict[str, Any]:
    """
    Demonstrate comprehensive error handling patterns.

    Shows how to:
    1. Handle connection failures
    2. Manage tool execution errors
    3. Deal with resource access failures
    4. Implement proper cleanup

    Returns:
        Dict containing error handling results
    """
    logger.info("Demonstrating error handling patterns...")

    results = {
        "connection_error_handled": False,
        "tool_error_handled": False,
        "resource_error_handled": False,
        "cleanup_successful": False
    }

    # 1. Connection Error Handling
    try:
        # Try to connect to non-existent server
        transport = PythonStdioTransport("non_existent_server.py")
        async with Client(transport) as client:
            await client.list_tools()
    except (FileNotFoundError, Exception) as e:
        logger.info(f"✓ Connection error handled: {type(e).__name__}")
        results["connection_error_handled"] = True

    # 2. Tool Error Handling
    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # Try to call non-existent tool
            try:
                await client.call_tool("non_existent_tool", {})
            except ToolError as e:
                logger.info(f"✓ Tool error handled: {e}")
                results["tool_error_handled"] = True

            # 3. Resource Error Handling
            try:
                await client.read_resource("non://existent/resource")
            except Exception as e:
                logger.info(f"✓ Resource error handled: {type(e).__name__}")
                results["resource_error_handled"] = True

            results["cleanup_successful"] = True

    except Exception as e:
        logger.error(f"Error handling demonstration failed: {e}")

    return results


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating comprehensive basic FastMCP client usage.

    Returns:
        Dict containing all demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Basic Usage Examples")
    print("=" * 60)

    results: dict[str, Any] = {}

    try:
        # 1. Basic client setup
        logger.info("\n1. Basic Client Setup")
        setup_result = await basic_client_setup()
        results["setup"] = setup_result

        # 2. Tool operations
        logger.info("\n2. Tool Operations")
        tool_result = await demonstrate_tool_operations()
        results["tools"] = tool_result

        # 3. Resource access
        logger.info("\n3. Resource Access")
        resource_result = await demonstrate_resource_access()
        results["resources"] = resource_result

        # 4. Error handling
        logger.info("\n4. Error Handling")
        error_result = await demonstrate_error_handling()
        results["error_handling"] = error_result

        print("\n" + "=" * 60)
        print("Basic client examples completed!")
        print("=" * 60)

        return results

    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the basic client examples
    result = asyncio.run(main())
    print(f"\nFinal Results: {result}")
