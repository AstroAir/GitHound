#!/usr/bin/env python3
"""
Multi-Server FastMCP Client Example

This example demonstrates how to connect to and manage multiple MCP servers
simultaneously using FastMCP 2.x client capabilities.

Usage:
    python examples/mcp_server/clients/multi_server_client.py

This example covers:
- Connecting to multiple servers with different transports
- Server composition and unified client interface
- Cross-server tool and resource access
- Load balancing and failover patterns
- Configuration management for multiple servers
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport, FastMCPTransport
from fastmcp.exceptions import ToolError, McpError
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""
    name: str
    transport_type: str
    connection_string: str
    description: str
    priority: int = 1
    enabled: bool = True


async def create_mock_servers() -> Dict[str, FastMCP]:
    """
    Create mock MCP servers for demonstration.
    
    Returns:
        Dict mapping server names to FastMCP instances
    """
    servers = {}
    
    # Math server
    math_server = FastMCP("Math Server")
    
    @math_server.tool
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    @math_server.tool
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    @math_server.resource("math://constants/pi")
    def get_pi() -> str:
        """Get the value of pi."""
        return "3.14159265359"
    
    servers["math"] = math_server
    
    # Text server
    text_server = FastMCP("Text Server")
    
    @text_server.tool
    def uppercase(text: str) -> str:
        """Convert text to uppercase."""
        return text.upper()
    
    @text_server.tool
    def word_count(text: str) -> Dict[str, int]:
        """Count words in text."""
        words = text.split()
        return {"word_count": len(words), "character_count": len(text)}
    
    @text_server.resource("text://samples/lorem")
    def get_lorem() -> str:
        """Get lorem ipsum text."""
        return "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    
    servers["text"] = text_server
    
    return servers


async def demonstrate_multi_server_setup() -> Dict[str, Any]:
    """
    Demonstrate setting up connections to multiple MCP servers.
    
    Returns:
        Dict containing setup results
    """
    logger.info("Setting up connections to multiple MCP servers...")
    
    # Create mock servers
    mock_servers = await create_mock_servers()
    
    # Server configurations
    server_configs = [
        ServerConfig(
            name="simple",
            transport_type="stdio",
            connection_string=str(Path(__file__).parent.parent / "servers" / "simple_server.py"),
            description="Simple demonstration server"
        ),
        ServerConfig(
            name="math",
            transport_type="inmemory",
            connection_string="math_server",
            description="Mathematical operations server"
        ),
        ServerConfig(
            name="text",
            transport_type="inmemory", 
            connection_string="text_server",
            description="Text processing server"
        )
    ]
    
    # Connect to servers
    connected_servers = {}
    
    for config in server_configs:
        if not config.enabled:
            continue
            
        try:
            logger.info(f"Connecting to {config.name} server...")
            
            if config.transport_type == "stdio":
                transport = PythonStdioTransport(config.connection_string)
                client = Client(transport)
            elif config.transport_type == "inmemory":
                server_instance = mock_servers.get(config.name)
                if server_instance:
                    transport = FastMCPTransport(server_instance)
                    client = Client(transport)
                else:
                    logger.warning(f"Mock server {config.name} not found")
                    continue
            else:
                logger.warning(f"Unsupported transport type: {config.transport_type}")
                continue
            
            # Test connection
            async with client:
                tools = await client.list_tools()
                resources = await client.list_resources()
                
                connected_servers[config.name] = {
                    "config": config,
                    "client": client,
                    "tools": len(tools),
                    "resources": len(resources),
                    "status": "connected"
                }
                
                logger.info(f"✓ Connected to {config.name}: {len(tools)} tools, {len(resources)} resources")
                
        except Exception as e:
            logger.error(f"Failed to connect to {config.name}: {e}")
            connected_servers[config.name] = {
                "config": config,
                "client": None,
                "status": "failed",
                "error": str(e)
            }
    
    return {
        "status": "success",
        "servers_configured": len(server_configs),
        "servers_connected": len([s for s in connected_servers.values() if s["status"] == "connected"]),
        "server_details": connected_servers
    }


async def demonstrate_cross_server_operations() -> Dict[str, Any]:
    """
    Demonstrate operations across multiple servers.
    
    Returns:
        Dict containing cross-server operation results
    """
    logger.info("Demonstrating cross-server operations...")
    
    # Create mock servers for this demo
    mock_servers = await create_mock_servers()
    
    results = {
        "math_operations": [],
        "text_operations": [],
        "combined_operations": []
    }
    
    try:
        # Connect to math server
        math_transport = FastMCPTransport(mock_servers["math"])
        async with Client(math_transport) as math_client:
            
            # Connect to text server
            text_transport = FastMCPTransport(mock_servers["text"])
            async with Client(text_transport) as text_client:
                
                # Math operations
                add_result = await math_client.call_tool("add", {"a": 10, "b": 5})
                multiply_result = await math_client.call_tool("multiply", {"a": 3, "b": 4})
                
                results["math_operations"] = [
                    {"operation": "add", "result": add_result.data},
                    {"operation": "multiply", "result": multiply_result.data}
                ]
                
                # Text operations
                text_input = "Hello FastMCP World"
                upper_result = await text_client.call_tool("uppercase", {"text": text_input})
                count_result = await text_client.call_tool("word_count", {"text": text_input})
                
                results["text_operations"] = [
                    {"operation": "uppercase", "result": upper_result.data},
                    {"operation": "word_count", "result": count_result.data}
                ]
                
                # Combined operation: process math result with text server
                math_result_text = f"The result is {add_result.data}"
                combined_result = await text_client.call_tool("word_count", {"text": math_result_text})
                
                results["combined_operations"] = [
                    {
                        "description": "Math result processed by text server",
                        "input": math_result_text,
                        "result": combined_result.data
                    }
                ]
                
                logger.info("✓ Cross-server operations completed successfully")
                
    except Exception as e:
        logger.error(f"Cross-server operations failed: {e}")
        return {"status": "failed", "error": str(e)}
    
    return {
        "status": "success",
        "operations": results
    }


async def demonstrate_server_failover() -> Dict[str, Any]:
    """
    Demonstrate failover patterns when servers are unavailable.
    
    Returns:
        Dict containing failover demonstration results
    """
    logger.info("Demonstrating server failover patterns...")
    
    # Simulate server priority list
    server_priorities = [
        {"name": "primary", "available": False},
        {"name": "secondary", "available": True},
        {"name": "tertiary", "available": True}
    ]
    
    failover_results = []
    
    for server in server_priorities:
        try:
            if server["available"]:
                # Simulate successful connection
                logger.info(f"✓ Connected to {server['name']} server")
                failover_results.append({
                    "server": server["name"],
                    "status": "connected",
                    "selected": True
                })
                break
            else:
                # Simulate failed connection
                logger.warning(f"✗ {server['name']} server unavailable")
                failover_results.append({
                    "server": server["name"],
                    "status": "unavailable",
                    "selected": False
                })
                
        except Exception as e:
            logger.error(f"Connection to {server['name']} failed: {e}")
            failover_results.append({
                "server": server["name"],
                "status": "failed",
                "error": str(e),
                "selected": False
            })
    
    return {
        "status": "success",
        "failover_sequence": failover_results,
        "final_server": next((r["server"] for r in failover_results if r.get("selected")), None)
    }


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating multi-server FastMCP client usage.
    
    Returns:
        Dict containing all demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Multi-Server Examples")
    print("=" * 60)
    
    results = {}
    
    try:
        # 1. Multi-server setup
        logger.info("\n1. Multi-Server Setup")
        setup_result = await demonstrate_multi_server_setup()
        results["setup"] = setup_result
        
        # 2. Cross-server operations
        logger.info("\n2. Cross-Server Operations")
        cross_server_result = await demonstrate_cross_server_operations()
        results["cross_server"] = cross_server_result
        
        # 3. Server failover
        logger.info("\n3. Server Failover")
        failover_result = await demonstrate_server_failover()
        results["failover"] = failover_result
        
        print("\n" + "=" * 60)
        print("Multi-server client examples completed!")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the multi-server client examples
    result = asyncio.run(main())
    print(f"\nFinal Results: {json.dumps(result, indent=2, default=str)}")
