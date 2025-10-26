"""Tests for FastMCP 2.x integration in GitHound MCP server."""

import asyncio

import pytest

from githound.mcp.context_helpers import (
    ProgressTracker,
    log_operation_metrics,
    read_mcp_resource,
    report_operation_progress,
    request_llm_analysis,
    safe_execute_with_logging,
    stream_results_with_progress,
)
from githound.mcp.direct_wrappers import MockContext


class TestMockContext:
    """Test MockContext for FastMCP 2.x compatibility."""

    @pytest.mark.asyncio
    async def test_info_logging(self):
        """Test info logging method."""
        ctx = MockContext()
        await ctx.info("Test info message")
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test error logging method."""
        ctx = MockContext()
        await ctx.error("Test error message")
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_warning_logging(self):
        """Test warning logging method."""
        ctx = MockContext()
        await ctx.warning("Test warning message")
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_debug_logging(self):
        """Test debug logging method."""
        ctx = MockContext()
        await ctx.debug("Test debug message")
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_critical_logging(self):
        """Test critical logging method."""
        ctx = MockContext()
        await ctx.critical("Test critical message")
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_report_progress(self):
        """Test progress reporting."""
        ctx = MockContext()
        await ctx.report_progress(progress=50, total=100, message="Halfway done")
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_sample(self):
        """Test LLM sampling mock."""
        ctx = MockContext()
        result = await ctx.sample(prompt="Test prompt", max_tokens=100)
        assert hasattr(result, "text")
        assert result.text == "Mock LLM response"

    @pytest.mark.asyncio
    async def test_read_resource(self):
        """Test resource reading mock."""
        ctx = MockContext()
        result = await ctx.read_resource(uri="test://resource")
        assert hasattr(result, "content")
        assert "test://resource" in result.content


class TestProgressReporting:
    """Test progress reporting functionality."""

    @pytest.mark.asyncio
    async def test_report_operation_progress(self):
        """Test basic progress reporting."""
        ctx = MockContext()
        await report_operation_progress(ctx, current=50, total=100, operation="Test")
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_report_operation_progress_with_interval(self):
        """Test progress reporting with custom interval."""
        ctx = MockContext()
        # Should only report on intervals
        await report_operation_progress(
            ctx, current=5, total=100, operation="Test", log_interval=10
        )
        await report_operation_progress(
            ctx, current=10, total=100, operation="Test", log_interval=10
        )


class TestProgressTracker:
    """Test ProgressTracker context manager."""

    @pytest.mark.asyncio
    async def test_progress_tracker_basic(self):
        """Test basic progress tracker usage."""
        ctx = MockContext()

        async with ProgressTracker(ctx, "Test Operation", total=10) as tracker:
            for _ in range(10):
                await tracker.increment()

        # Should complete successfully

    @pytest.mark.asyncio
    async def test_progress_tracker_with_error(self):
        """Test progress tracker handles errors."""
        ctx = MockContext()

        with pytest.raises(ValueError):
            async with ProgressTracker(ctx, "Test Operation", total=10) as tracker:
                await tracker.increment()
                raise ValueError("Test error")

    @pytest.mark.asyncio
    async def test_progress_tracker_set_total(self):
        """Test updating total during operation."""
        ctx = MockContext()

        async with ProgressTracker(ctx, "Test Operation") as tracker:
            await tracker.set_total(20)
            for _ in range(20):
                await tracker.increment()


class TestLLMIntegration:
    """Test LLM sampling integration."""

    @pytest.mark.asyncio
    async def test_request_llm_analysis(self):
        """Test requesting LLM analysis."""
        ctx = MockContext()
        result = await request_llm_analysis(ctx, "Test prompt")
        assert result == "Mock LLM response"

    @pytest.mark.asyncio
    async def test_request_llm_analysis_with_params(self):
        """Test LLM analysis with parameters."""
        ctx = MockContext()
        result = await request_llm_analysis(ctx, "Test prompt", max_tokens=500, temperature=0.8)
        assert result is not None

    @pytest.mark.asyncio
    async def test_request_llm_analysis_no_sample_method(self):
        """Test graceful handling when sample method unavailable."""

        class NoSampleContext(MockContext):
            def __getattribute__(self, name):
                if name == "sample":
                    raise AttributeError("sample not available")
                return super().__getattribute__(name)

        ctx = NoSampleContext()
        # Remove sample method
        delattr(ctx.__class__, "sample")
        result = await request_llm_analysis(ctx, "Test prompt")
        assert result is None


class TestResourceAccess:
    """Test resource access functionality."""

    @pytest.mark.asyncio
    async def test_read_mcp_resource(self):
        """Test reading MCP resource."""
        ctx = MockContext()
        result = await read_mcp_resource(ctx, "test://resource/path")
        assert result is not None
        assert "test://resource/path" in result

    @pytest.mark.asyncio
    async def test_read_mcp_resource_no_method(self):
        """Test graceful handling when read_resource unavailable."""

        class NoResourceContext(MockContext):
            pass

        ctx = NoResourceContext()
        delattr(ctx.__class__, "read_resource")
        result = await read_mcp_resource(ctx, "test://resource")
        assert result is None


class TestSafeExecution:
    """Test safe execution with error handling."""

    @pytest.mark.asyncio
    async def test_safe_execute_success(self):
        """Test successful execution."""
        ctx = MockContext()

        async def test_func():
            return {"data": "success"}

        result = await safe_execute_with_logging(ctx, "Test Operation", test_func)
        assert result["status"] == "success"
        assert result["result"]["data"] == "success"

    @pytest.mark.asyncio
    async def test_safe_execute_error(self):
        """Test error handling."""
        ctx = MockContext()

        async def failing_func():
            raise ValueError("Test error")

        result = await safe_execute_with_logging(ctx, "Test Operation", failing_func)
        assert result["status"] == "error"
        assert "Test error" in result["error"]


class TestOperationMetrics:
    """Test operation metrics logging."""

    @pytest.mark.asyncio
    async def test_log_operation_metrics_basic(self):
        """Test basic metrics logging."""
        ctx = MockContext()
        await log_operation_metrics(ctx, "Test Operation", duration_ms=100.5)
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_log_operation_metrics_with_items(self):
        """Test metrics logging with items processed."""
        ctx = MockContext()
        await log_operation_metrics(ctx, "Test Operation", duration_ms=1000.0, items_processed=100)
        # Should include items_per_second calculation


class TestStreamResults:
    """Test streaming results with progress."""

    @pytest.mark.asyncio
    async def test_stream_results_with_progress(self):
        """Test streaming results with progress reporting."""
        ctx = MockContext()

        async def mock_iterator():
            for i in range(50):
                yield {"item": i}

        results = await stream_results_with_progress(
            ctx, mock_iterator(), operation="Test Search", max_results=50
        )

        assert len(results) == 50
        assert results[0]["item"] == 0
        assert results[49]["item"] == 49

    @pytest.mark.asyncio
    async def test_stream_results_without_max(self):
        """Test streaming without known maximum."""
        ctx = MockContext()

        async def mock_iterator():
            for i in range(25):
                yield {"item": i}

        results = await stream_results_with_progress(ctx, mock_iterator(), operation="Test")

        assert len(results) == 25


@pytest.mark.integration
class TestFastMCP2xIntegration:
    """Integration tests for FastMCP 2.x features."""

    @pytest.mark.asyncio
    async def test_combined_features(self):
        """Test combining multiple FastMCP 2.x features."""
        ctx = MockContext()

        # Use progress tracker
        async with ProgressTracker(ctx, "Integration Test", total=3) as tracker:
            # Step 1: Log messages
            await ctx.info("Step 1: Starting integration test")
            await tracker.increment()

            # Step 2: Request LLM analysis
            await ctx.info("Step 2: Requesting LLM analysis")
            analysis = await request_llm_analysis(ctx, "Test prompt")
            assert analysis is not None
            await tracker.increment()

            # Step 3: Read resource
            await ctx.info("Step 3: Reading resource")
            resource = await read_mcp_resource(ctx, "test://resource")
            assert resource is not None
            await tracker.increment()

        await ctx.info("Integration test complete")

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery in complex operations."""
        ctx = MockContext()

        async def risky_operation():
            # Simulate partial success
            await ctx.info("Starting risky operation")
            await asyncio.sleep(0.01)
            raise ValueError("Simulated error")

        result = await safe_execute_with_logging(ctx, "Risky Operation", risky_operation)

        assert result["status"] == "error"
        assert "Simulated error" in result["error"]
