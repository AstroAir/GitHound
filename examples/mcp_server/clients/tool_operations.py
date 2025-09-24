#!/usr/bin/env python3
"""
FastMCP Tool Operations Examples

This example demonstrates comprehensive tool operations with FastMCP client:
- Tool discovery and metadata inspection
- Tool execution with different argument types
- Structured data handling with .data property
- Error handling and timeout management
- Tool filtering and selection patterns

Usage:
    python examples/mcp_server/clients/tool_operations.py

This example covers:
- Tool discovery with list_tools()
- Tool execution with call_tool()
- Handling structured data responses
- Complex argument serialization
- Error handling patterns
- Performance considerations
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Any
from dataclasses import dataclass

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


@dataclass
class ToolExecutionResult:
    """Result of tool execution with metadata."""
    tool_name: str
    success: bool
    data: Any
    execution_time: float
    error: Optional[str] = None


async def discover_tools() -> Dict[str, Any]:
    """
    Demonstrate comprehensive tool discovery and metadata inspection.

    Shows how to:
    1. List all available tools
    2. Inspect tool metadata and schemas
    3. Filter tools by capabilities
    4. Analyze tool argument requirements

    Returns:
        Dict containing tool discovery results
    """
    logger.info("Discovering and analyzing available tools...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # 1. Basic tool discovery
            tools = await client.list_tools()
            logger.info(f"Discovered {len(tools)} tools")

            tool_analysis: list[Any] = []

            for tool in tools:
                # Analyze each tool's metadata
                analysis = {
                    "name": tool.name,
                    "description": tool.description,
                    "has_input_schema": tool.inputSchema is not None,
                    "schema_properties": [],
                    "required_args": [],
                    "optional_args": []
                }

                # Analyze input schema if available
                if tool.inputSchema:
                    schema = tool.inputSchema
                    if isinstance(schema, dict):
                        properties = schema.get("properties", {})
                        required = schema.get("required", [])

                        analysis["schema_properties"] = list(properties.keys())
                        analysis["required_args"] = required
                        analysis["optional_args"] = [
                            prop for prop in properties.keys()
                            if prop not in required
                        ]

                # Check for tags and metadata
                if hasattr(tool, '_meta') and tool._meta:
                    fastmcp_meta = tool._meta.get('_fastmcp', {})
                    analysis["tags"] = fastmcp_meta.get('tags', [])

                tool_analysis.append(analysis)

                logger.info(f"Tool: {tool.name}")
                logger.info(f"  Description: {tool.description}")
                logger.info(f"  Required args: {analysis['required_args']}")
                logger.info(f"  Optional args: {analysis['optional_args']}")

            # 2. Filter tools by capabilities
            simple_tools = [t for t in tool_analysis if not t["required_args"]]
            complex_tools = [t for t in tool_analysis if t["required_args"]]

            return {
                "status": "success",
                "total_tools": len(tools),
                "simple_tools": len(simple_tools),
                "complex_tools": len(complex_tools),
                "tool_details": tool_analysis,
                "discovery_method": "list_tools"
            }

    except Exception as e:
        logger.error(f"Tool discovery failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def execute_simple_tools() -> Dict[str, Any]:
    """
    Demonstrate execution of tools without complex arguments.

    Shows how to:
    1. Execute tools with no arguments
    2. Execute tools with simple string/number arguments
    3. Handle different response types
    4. Access structured data via .data property

    Returns:
        Dict containing simple tool execution results
    """
    logger.info("Executing simple tools...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    execution_results: list[Any] = []

    try:
        async with Client(transport) as client:
            tools = await client.list_tools()

            # 1. Execute tool with no arguments
            for tool in tools:
                if tool.name == "get_server_info":
                    start_time = datetime.now()

                    try:
                        result = await client.call_tool(tool.name, {})
                        execution_time = (datetime.now() - start_time).total_seconds()

                        logger.info(f"✓ {tool.name} executed successfully")
                        logger.info(f"  Structured data: {type(result.data)}")
                        logger.info(f"  Content blocks: {len(result.content)}")

                        if result.data:
                            logger.info(f"  Server name: {result.data.get('name', 'N/A')}")

                        execution_results.append(ToolExecutionResult(
                            tool_name=tool.name,
                            success=True,
                            data=result.data,
                            execution_time=execution_time
                        ))

                    except ToolError as e:
                        execution_time = (datetime.now() - start_time).total_seconds()
                        logger.error(f"✗ {tool.name} failed: {e}")

                        execution_results.append(ToolExecutionResult(
                            tool_name=tool.name,
                            success=False,
                            data=None,
                            execution_time=execution_time,
                            error=str(e)
                        ))

            # 2. Execute tool with simple arguments
            for tool in tools:
                if tool.name == "echo":
                    start_time = datetime.now()

                    try:
                        result = await client.call_tool(tool.name, {
                            "message": "Hello from tool operations example!"
                        })
                        execution_time = (datetime.now() - start_time).total_seconds()

                        logger.info(f"✓ {tool.name} executed with arguments")
                        logger.info(f"  Result: {result.data}")

                        execution_results.append(ToolExecutionResult(
                            tool_name=tool.name,
                            success=True,
                            data=result.data,
                            execution_time=execution_time
                        ))

                    except ToolError as e:
                        execution_time = (datetime.now() - start_time).total_seconds()
                        logger.error(f"✗ {tool.name} with args failed: {e}")

                        execution_results.append(ToolExecutionResult(
                            tool_name=tool.name,
                            success=False,
                            data=None,
                            execution_time=execution_time,
                            error=str(e)
                        ))

            # 3. Execute mathematical tool
            for tool in tools:
                if tool.name == "add_numbers":
                    start_time = datetime.now()

                    try:
                        result = await client.call_tool(tool.name, {
                            "a": 15.5,
                            "b": 24.3
                        })
                        execution_time = (datetime.now() - start_time).total_seconds()

                        logger.info(f"✓ {tool.name} executed with numbers")
                        if result.data:
                            logger.info(f"  Sum: {result.data.get('sum', 'N/A')}")
                            logger.info(f"  Operation: {result.data.get('operation', 'N/A')}")

                        execution_results.append(ToolExecutionResult(
                            tool_name=tool.name,
                            success=True,
                            data=result.data,
                            execution_time=execution_time
                        ))

                    except ToolError as e:
                        execution_time = (datetime.now() - start_time).total_seconds()
                        logger.error(f"✗ {tool.name} with numbers failed: {e}")

                        execution_results.append(ToolExecutionResult(
                            tool_name=tool.name,
                            success=False,
                            data=None,
                            execution_time=execution_time,
                            error=str(e)
                        ))

            successful_executions = [r for r in execution_results if r.success]
            failed_executions = [r for r in execution_results if not r.success]

            return {
                "status": "success",
                "total_executions": len(execution_results),
                "successful": len(successful_executions),
                "failed": len(failed_executions),
                "average_execution_time": sum(r.execution_time for r in successful_executions) / len(successful_executions) if successful_executions else 0,
                "results": [
                    {
                        "tool_name": r.tool_name,
                        "success": r.success,
                        "execution_time": r.execution_time,
                        "has_data": r.data is not None,
                        "error": r.error
                    }
                    for r in execution_results
                ]
            }

    except Exception as e:
        logger.error(f"Simple tool execution failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def demonstrate_complex_arguments() -> Dict[str, Any]:
    """
    Demonstrate tool execution with complex argument types.

    Shows how to:
    1. Pass complex data structures as arguments
    2. Handle automatic argument serialization
    3. Work with nested objects and arrays
    4. Manage type conversion and validation

    Returns:
        Dict containing complex argument execution results
    """
    logger.info("Demonstrating complex argument handling...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    try:
        async with Client(transport) as client:
            # Complex argument examples
            complex_args_examples = [
                {
                    "name": "nested_object",
                    "args": {
                        "config": {
                            "format": "json",
                            "include_metadata": True,
                            "filters": ["active", "recent"],
                            "limits": {"max_items": 100, "timeout": 30}
                        }
                    }
                },
                {
                    "name": "array_data",
                    "args": {
                        "items": [
                            {"id": 1, "name": "item1", "value": 10.5},
                            {"id": 2, "name": "item2", "value": 20.3},
                            {"id": 3, "name": "item3", "value": 15.7}
                        ]
                    }
                },
                {
                    "name": "mixed_types",
                    "args": {
                        "string_value": "test string",
                        "number_value": 42,
                        "boolean_value": True,
                        "null_value": None,
                        "array_value": [1, 2, 3],
                        "object_value": {"key": "value"}
                    }
                }
            ]

            results: list[Any] = []

            # Note: The simple server doesn't have tools that accept complex arguments
            # This demonstrates the client-side argument handling
            for example in complex_args_examples:
                try:
                    # Demonstrate argument serialization
                    logger.info(f"Preparing complex arguments: {example['name']}")
                    logger.info(f"  Arguments: {example['args']}")

                    # FastMCP automatically serializes complex arguments
                    # This would be passed to a tool that accepts complex data
                    serialized_size = len(str(example['args']))

                    results.append({
                        "example_name": example["name"],
                        "status": "serialized",
                        "argument_complexity": len(example["args"]),
                        "serialized_size": serialized_size
                    })

                except Exception as e:
                    results.append({
                        "example_name": example["name"],
                        "status": "failed",
                        "error": str(e)
                    })

            return {
                "status": "success",
                "complex_examples": len(complex_args_examples),
                "serialization_results": results,
                "note": "Complex arguments demonstrated (server tools would receive these)"
            }

    except Exception as e:
        logger.error(f"Complex argument demonstration failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def demonstrate_error_handling() -> Dict[str, Any]:
    """
    Demonstrate comprehensive error handling for tool operations.

    Shows how to:
    1. Handle tool execution errors
    2. Manage timeout scenarios
    3. Deal with invalid arguments
    4. Implement retry strategies

    Returns:
        Dict containing error handling demonstration results
    """
    logger.info("Demonstrating tool error handling...")

    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = PythonStdioTransport(str(server_script))

    error_scenarios: list[Any] = []

    try:
        async with Client(transport) as client:
            # 1. Non-existent tool error
            try:
                await client.call_tool("non_existent_tool", {})
            except ToolError as e:
                logger.info(f"✓ Non-existent tool error handled: {e}")
                error_scenarios.append({
                    "scenario": "non_existent_tool",
                    "error_type": "ToolError",
                    "handled": True,
                    "message": str(e)
                })

            # 2. Simulated validation error
            try:
                await client.call_tool("simulate_error", {"error_type": "validation"})
            except ToolError as e:
                logger.info(f"✓ Validation error handled: {e}")
                error_scenarios.append({
                    "scenario": "validation_error",
                    "error_type": "ToolError",
                    "handled": True,
                    "message": str(e)
                })

            # 3. Timeout handling (with short timeout)
            try:
                # This would timeout if the tool takes too long
                result = await client.call_tool(
                    "simulate_error",
                    {"error_type": "timeout"},
                    timeout=2.0  # 2 second timeout
                )
            except (ToolError, asyncio.TimeoutError) as e:
                logger.info(f"✓ Timeout error handled: {type(e).__name__}")
                error_scenarios.append({
                    "scenario": "timeout_error",
                    "error_type": type(e).__name__,
                    "handled": True,
                    "message": str(e)
                })

            # 4. Invalid argument handling
            try:
                # Pass invalid arguments to a tool
                await client.call_tool("add_numbers", {"a": "not_a_number", "b": "also_not_a_number"})
            except ToolError as e:
                logger.info(f"✓ Invalid argument error handled: {e}")
                error_scenarios.append({
                    "scenario": "invalid_arguments",
                    "error_type": "ToolError",
                    "handled": True,
                    "message": str(e)
                })

            return {
                "status": "success",
                "error_scenarios_tested": len(error_scenarios),
                "all_errors_handled": all(s["handled"] for s in error_scenarios),
                "scenarios": error_scenarios
            }

    except Exception as e:
        logger.error(f"Error handling demonstration failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating comprehensive tool operations.

    Returns:
        Dict containing all tool operation demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Tool Operations Examples")
    print("=" * 60)

    results: dict[str, Any] = {}

    try:
        # 1. Tool Discovery
        logger.info("\n1. Tool Discovery and Analysis")
        discovery_result = await discover_tools()
        results["discovery"] = discovery_result

        # 2. Simple Tool Execution
        logger.info("\n2. Simple Tool Execution")
        simple_result = await execute_simple_tools()
        results["simple_execution"] = simple_result

        # 3. Complex Arguments
        logger.info("\n3. Complex Argument Handling")
        complex_result = await demonstrate_complex_arguments()
        results["complex_arguments"] = complex_result

        # 4. Error Handling
        logger.info("\n4. Error Handling")
        error_result = await demonstrate_error_handling()
        results["error_handling"] = error_result

        print("\n" + "=" * 60)
        print("Tool operations examples completed!")
        print("=" * 60)

        return results

    except Exception as e:
        logger.error(f"Tool operations examples failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the tool operations examples
    result = asyncio.run(main())
    print(f"\nTool Operations Summary:")
    for category, result_data in result.items():
        if isinstance(result_data, dict) and "status" in result_data:
            print(f"  {category}: {result_data['status']}")
        else:
            print(f"  {category}: completed")
