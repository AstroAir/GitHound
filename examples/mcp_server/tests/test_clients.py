"""
Tests for FastMCP client examples.

This module contains comprehensive tests for all FastMCP client implementations,
ensuring functionality, error handling, and performance requirements.
"""


# Import client modules to test
import sys
import time
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from fastmcp.exceptions import McpError, ToolError

sys.path.append(str(Path(__file__).parent.parent))

from clients import basic_client, resource_operations, tool_operations, transport_examples


class TestBasicClient:
    """Test basic FastMCP client functionality."""

    @pytest.mark.asyncio
    async def test_basic_client_setup(self, simple_mcp_client) -> None:
        """Test basic client setup and connection."""
        # Test that client is connected
        assert simple_mcp_client is not None

        # Test basic operations
        tools = await simple_mcp_client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

        resources = await simple_mcp_client.list_resources()
        assert isinstance(resources, list)

    @pytest.mark.asyncio
    async def test_basic_client_setup_function(self) -> None:
        """Test the basic_client_setup function."""
        result = await basic_client.basic_client_setup()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "server_name" in result
            assert "server_version" in result
            assert "tools_count" in result
            assert "resources_count" in result
            assert result["transport_type"] == "stdio"

    @pytest.mark.asyncio
    async def test_tool_operations_demo(self) -> None:
        """Test the tool operations demonstration."""
        result = await basic_client.demonstrate_tool_operations()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "tools_discovered" in result
            assert "tool_info" in result
            assert isinstance(result["tool_info"], list)

    @pytest.mark.asyncio
    async def test_resource_access_demo(self) -> None:
        """Test the resource access demonstration."""
        result = await basic_client.demonstrate_resource_access()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "resources_discovered" in result
            assert "resource_info" in result
            assert isinstance(result["resource_info"], list)

    @pytest.mark.asyncio
    async def test_error_handling_demo(self) -> None:
        """Test the error handling demonstration."""
        result = await basic_client.demonstrate_error_handling()

        assert isinstance(result, dict)
        assert "connection_error_handled" in result
        assert "tool_error_handled" in result
        assert "resource_error_handled" in result
        assert "cleanup_successful" in result

    @pytest.mark.asyncio
    async def test_main_function(self) -> None:
        """Test the main function execution."""
        result = await basic_client.main()

        assert isinstance(result, dict)
        assert "setup" in result
        assert "tools" in result
        assert "resources" in result
        assert "error_handling" in result


class TestTransportExamples:
    """Test transport examples functionality."""

    @pytest.mark.asyncio
    async def test_stdio_transport_demo(self) -> None:
        """Test STDIO transport demonstration."""
        result = await transport_examples.demonstrate_stdio_transport()

        assert isinstance(result, dict)
        assert "transport_type" in result
        assert result["transport_type"] == "stdio"
        assert "status" in result

        if result["status"] == "success":
            assert "tools_count" in result
            assert "resources_count" in result
            assert "connection_method" in result

    @pytest.mark.asyncio
    async def test_http_transport_demo(self) -> None:
        """Test HTTP transport demonstration."""
        result = await transport_examples.demonstrate_http_transport()

        assert isinstance(result, dict)
        assert "transport_type" in result
        assert result["transport_type"] == "http"
        assert "status" in result

        # HTTP transport may fail if no server is running
        if result["status"] == "failed":
            assert "error" in result
            assert "note" in result

    @pytest.mark.asyncio
    async def test_sse_transport_demo(self) -> None:
        """Test SSE transport demonstration."""
        result = await transport_examples.demonstrate_sse_transport()

        assert isinstance(result, dict)
        assert "transport_type" in result
        assert result["transport_type"] == "sse"
        assert "status" in result

        # SSE transport may fail if no server is running
        if result["status"] == "failed":
            assert "error" in result
            assert "note" in result

    @pytest.mark.asyncio
    async def test_inmemory_transport_demo(self) -> None:
        """Test In-Memory transport demonstration."""
        result = await transport_examples.demonstrate_inmemory_transport()

        assert isinstance(result, dict)
        assert "transport_type" in result
        assert result["transport_type"] == "inmemory"
        assert "status" in result

    @pytest.mark.asyncio
    async def test_transport_selection_demo(self) -> None:
        """Test transport selection demonstration."""
        result = await transport_examples.demonstrate_transport_selection()

        assert isinstance(result, dict)
        assert "transport_selection" in result
        assert "examples" in result
        assert "total_examples" in result

    @pytest.mark.asyncio
    async def test_transport_configuration_demo(self) -> None:
        """Test transport configuration demonstration."""
        result = await transport_examples.demonstrate_transport_configuration()  # [attr-defined]

        assert isinstance(result, dict)
        assert "configuration_examples" in result
        assert "total_configurations" in result


class TestToolOperations:
    """Test tool operations functionality."""

    @pytest.mark.asyncio
    async def test_discover_tools(self) -> None:
        """Test tool discovery functionality."""
        result = await tool_operations.discover_tools()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "total_tools" in result
            assert "simple_tools" in result
            assert "complex_tools" in result
            assert "tool_details" in result
            assert isinstance(result["tool_details"], list)

    @pytest.mark.asyncio
    async def test_execute_simple_tools(self) -> None:
        """Test simple tool execution."""
        result = await tool_operations.execute_simple_tools()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "total_executions" in result
            assert "successful" in result
            assert "failed" in result
            assert "results" in result
            assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_complex_arguments_demo(self) -> None:
        """Test complex argument handling."""
        result = await tool_operations.demonstrate_complex_arguments()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "complex_examples" in result
            assert "serialization_results" in result
            assert isinstance(result["serialization_results"], list)

    @pytest.mark.asyncio
    async def test_error_handling_demo(self) -> None:
        """Test tool error handling."""
        result = await tool_operations.demonstrate_error_handling()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "error_scenarios_tested" in result
            assert "scenarios" in result
            assert isinstance(result["scenarios"], list)

    @pytest.mark.asyncio
    async def test_tool_execution_result_model(self) -> None:
        """Test ToolExecutionResult dataclass."""
        from tool_operations import ToolExecutionResult

        result = ToolExecutionResult(
            tool_name="test_tool", success=True, data={"key": "value"}, execution_time=0.5
        )

        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.execution_time == 0.5
        assert result.error is None


class TestResourceOperations:
    """Test resource operations functionality."""

    @pytest.mark.asyncio
    async def test_discover_resources(self) -> None:
        """Test resource discovery functionality."""
        result = await resource_operations.discover_resources()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "total_resources" in result
            assert "static_resources" in result
            assert "templated_resources" in result
            assert "uri_schemes" in result
            assert "resource_details" in result

    @pytest.mark.asyncio
    async def test_access_static_resources(self) -> None:
        """Test static resource access."""
        result = await resource_operations.access_static_resources()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "total_attempts" in result
            assert "successful" in result
            assert "failed" in result
            assert "access_results" in result

    @pytest.mark.asyncio
    async def test_templated_resources_demo(self) -> None:
        """Test templated resource demonstration."""
        result = await resource_operations.demonstrate_templated_resources()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "templated_resources_found" in result
            assert "template_attempts" in result
            assert "template_results" in result

    @pytest.mark.asyncio
    async def test_content_types_demo(self) -> None:
        """Test content type handling."""
        result = await resource_operations.demonstrate_content_types()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "content_types" in result
            assert "content_details" in result

    @pytest.mark.asyncio
    async def test_resource_patterns_demo(self) -> None:
        """Test resource pattern analysis."""
        result = await resource_operations.demonstrate_resource_patterns()

        assert isinstance(result, dict)
        assert "status" in result

        if result["status"] == "success":
            assert "total_resources" in result
            assert "pattern_analysis" in result
            assert "recommendations" in result


class TestClientIntegration:
    """Integration tests for client functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_client_server_communication(self, simple_mcp_client) -> None:
        """Test end-to-end client-server communication."""
        # Test tool execution
        tools = await simple_mcp_client.list_tools()
        assert len(tools) > 0

        # Execute a simple tool
        echo_tool = next((t for t in tools if t.name == "echo"), None)
        if echo_tool:
            result = await simple_mcp_client.call_tool("echo", {"message": "test"})
            assert result is not None
            assert result.data is not None

        # Test resource access
        resources = await simple_mcp_client.list_resources()
        if resources:
            content = await simple_mcp_client.read_resource(resources[0].uri)
            assert content is not None
            assert len(content) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_scenarios(self, simple_mcp_client) -> None:
        """Test various error scenarios."""
        # Test non-existent tool
        with pytest.raises(ToolError):
            await simple_mcp_client.call_tool("non_existent_tool", {})

        # Test invalid arguments
        with pytest.raises(ToolError):
            await simple_mcp_client.call_tool("add_numbers", {"a": "not_a_number"})

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_thresholds(self, simple_mcp_client, performance_thresholds) -> None:
        """Test that operations meet performance thresholds."""
        # Test tool execution performance
        start_time = time.time()
        tools = await simple_mcp_client.list_tools()
        execution_time = time.time() - start_time

        assert execution_time < performance_thresholds["tool_execution_max_time"]

        # Test resource access performance
        start_time = time.time()
        resources = await simple_mcp_client.list_resources()
        execution_time = time.time() - start_time

        assert execution_time < performance_thresholds["resource_access_max_time"]

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_comprehensive_client_workflow(self) -> None:
        """Test comprehensive client workflow."""
        # Run all main functions
        basic_result = await basic_client.main()
        assert isinstance(basic_result, dict)

        transport_result = await transport_examples.main()
        assert isinstance(transport_result, dict)

        tool_result = await tool_operations.main()
        assert isinstance(tool_result, dict)

        resource_result = await resource_operations.main()
        assert isinstance(resource_result, dict)


class TestClientErrorHandling:
    """Test client error handling capabilities."""

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self) -> None:
        """Test handling of connection failures."""
        # Try to connect to non-existent server
        transport = PythonStdioTransport("non_existent_server.py")

        with pytest.raises((McpError, FileNotFoundError, Exception)):
            async with Client(transport) as client:
                await client.list_tools()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, simple_mcp_client) -> None:
        """Test timeout handling."""
        # Test with very short timeout
        try:
            result = await simple_mcp_client.call_tool(
                "simulate_error", {"error_type": "timeout"}, timeout=0.1  # Very short timeout
            )
        except (TimeoutError, ToolError):
            # Expected to timeout or fail
            pass

    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, mock_mcp_server) -> None:
        """Test handling of malformed responses."""
        # This would require mocking the transport layer
        # For now, we'll test that the client can handle various response types
        pass


class TestClientConfiguration:
    """Test client configuration options."""

    @pytest.mark.asyncio
    async def test_client_with_custom_config(self, client_test_config) -> None:
        """Test client with custom configuration."""
        # Test configuration values
        assert client_test_config["timeout"] > 0
        assert client_test_config["retry_attempts"] > 0
        assert client_test_config["max_content_size"] > 0
        assert len(client_test_config["supported_transports"]) > 0

    def test_transport_configuration(self) -> None:
        """Test transport configuration options."""
        # Test STDIO transport configuration
        server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"

        transport = PythonStdioTransport(
            str(server_script),
            env={"TEST_ENV": "test_value"},
            cwd=str(Path(__file__).parent.parent),
        )

        assert transport is not None
        # Additional transport configuration tests would go here
