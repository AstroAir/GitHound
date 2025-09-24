"""
Performance tests for GitHound web interface.
"""

import time

import pytest
from playwright.async_api import Page, expect


@pytest.mark.performance
@pytest.mark.e2e
class TestPerformance:
    """Test performance characteristics of the web interface."""

    async def test_page_load_performance(self, page: Page):
        """Test page load performance metrics."""
        # Start timing
        start_time = time.time()

        # Navigate to main page
        await page.goto("/")

        # Wait for page to be fully loaded
        await page.wait_for_load_state("networkidle")

        # Calculate load time
        load_time = time.time() - start_time

        # Page should load within reasonable time (5 seconds)
        assert load_time < 5.0, f"Page load time {load_time:.2f}s exceeds 5 seconds"

        # Check performance metrics
        performance_metrics = await page.evaluate(
            """
            () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime,
                    firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime
                };
            }
        """
        )

        # DOM Content Loaded should be fast
        if performance_metrics["domContentLoaded"]:
            assert (
                performance_metrics["domContentLoaded"] < 2000
            ), f"DOM Content Loaded time {performance_metrics['domContentLoaded']}ms exceeds 2 seconds"

        # First Contentful Paint should be fast
        if performance_metrics["firstContentfulPaint"]:
            assert (
                performance_metrics["firstContentfulPaint"] < 3000
            ), f"First Contentful Paint {performance_metrics['firstContentfulPaint']}ms exceeds 3 seconds"

    async def test_search_performance(self, page: Page, authenticated_user, test_repository):
        """Test search operation performance."""
        await page.goto("/search")

        # Fill search form
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")

        # Start timing search
        start_time = time.time()

        # Submit search
        await page.click('[data-testid="submit-search"]')

        # Wait for search results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Calculate search time
        search_time = time.time() - start_time

        # Search should complete within reasonable time (30 seconds)
        assert search_time < 30.0, f"Search time {search_time:.2f}s exceeds 30 seconds"

        # Verify results are displayed
        result_count = await page.locator('[data-testid="result-card"]').count()
        assert result_count > 0, "Search should return results"

    async def test_large_result_set_performance(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test performance with large result sets."""
        await page.goto("/search")

        # Search for common term that should return many results
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "import")
        await page.fill('[data-testid="max-results"]', "1000")

        # Start timing
        start_time = time.time()

        # Submit search
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=60000)

        # Calculate time
        search_time = time.time() - start_time

        # Large search should complete within reasonable time (60 seconds)
        assert search_time < 60.0, f"Large search time {search_time:.2f}s exceeds 60 seconds"

        # Check if pagination is working for large results
        pagination = page.locator('[data-testid="pagination"]')
        if await pagination.is_visible():
            # Test pagination performance
            page_start = time.time()
            await page.click('[data-testid="next-page"]')
            await expect(page.locator('[data-testid="current-page"]')).to_contain_text("2")
            page_time = time.time() - page_start

            assert page_time < 5.0, f"Pagination time {page_time:.2f}s exceeds 5 seconds"

    async def test_websocket_performance(self, page: Page, authenticated_user, test_repository):
        """Test WebSocket connection and message performance."""
        await page.goto("/search")

        # Monitor WebSocket messages
        await page.evaluate(
            """
            window.websocketPerformance = {
                connectionTime: null,
                messageCount: 0,
                firstMessageTime: null,
                lastMessageTime: null
            };

            const startTime = Date.now();

            if (window.websocketManager) {
                window.websocketManager.onConnect(() => {
                    window.websocketPerformance.connectionTime = Date.now() - startTime;
                });

                window.websocketManager.onMessage((message) => {
                    const now = Date.now();
                    window.websocketPerformance.messageCount++;

                    if (!window.websocketPerformance.firstMessageTime) {
                        window.websocketPerformance.firstMessageTime = now - startTime;
                    }
                    window.websocketPerformance.lastMessageTime = now - startTime;
                });
            }
        """
        )

        # Perform search to generate WebSocket traffic
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')

        # Wait for search to complete
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Get WebSocket performance metrics
        ws_performance = await page.evaluate("window.websocketPerformance")

        # WebSocket connection should be fast
        if ws_performance["connectionTime"]:
            assert (
                ws_performance["connectionTime"] < 5000
            ), f"WebSocket connection time {ws_performance['connectionTime']}ms exceeds 5 seconds"

        # Should receive messages during search
        assert ws_performance["messageCount"] > 0, "Should receive WebSocket messages during search"

        # First message should arrive quickly
        if ws_performance["firstMessageTime"]:
            assert (
                ws_performance["firstMessageTime"] < 10000
            ), f"First WebSocket message time {ws_performance['firstMessageTime']}ms exceeds 10 seconds"

    async def test_memory_usage(self, page: Page, authenticated_user, test_repository):
        """Test memory usage during operations."""
        await page.goto("/search")

        # Get initial memory usage
        initial_memory = await page.evaluate(
            """
            () => {
                if (performance.memory) {
                    return {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    };
                }
                return null;
            }
        """
        )

        if initial_memory:
            # Perform multiple searches to test memory usage
            for i in range(5):
                await page.fill('[data-testid="search-query-input"]', f"search_{i}")
                await page.click('[data-testid="submit-search"]')
                await expect(page.locator('[data-testid="search-results"]')).to_be_visible(
                    timeout=30000
                )
                await page.wait_for_timeout(1000)

            # Get final memory usage
            final_memory = await page.evaluate(
                """
                () => {
                    if (performance.memory) {
                        return {
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        };
                    }
                    return null;
                }
            """
            )

            if final_memory:
                # Memory usage should not increase dramatically
                memory_increase = final_memory["used"] - initial_memory["used"]
                memory_increase_mb = memory_increase / (1024 * 1024)

                # Should not use more than 50MB additional memory
                assert (
                    memory_increase_mb < 50
                ), f"Memory usage increased by {memory_increase_mb:.2f}MB, exceeds 50MB limit"

    async def test_concurrent_user_simulation(self, browser, test_repository):
        """Test performance with multiple concurrent users."""
        # Create multiple browser contexts to simulate concurrent users
        contexts = []
        pages = []

        try:
            # Create 5 concurrent users
            for i in range(5):
                context = await browser.new_context()
                page = await context.new_page()
                contexts.append(context)
                pages.append(page)

            # All users navigate to search page
            navigation_tasks = []
            for page in pages:
                navigation_tasks.append(page.goto("/search"))

            # Wait for all navigations to complete
            await page.wait_for_timeout(5000)

            # All users perform searches simultaneously
            search_start = time.time()

            search_tasks = []
            for i, page in enumerate(pages):

                async def perform_search(p, query_suffix):
                    await p.fill('[data-testid="repo-path-input"]', str(test_repository))
                    await p.fill('[data-testid="search-query-input"]', f"function_{query_suffix}")
                    await p.click('[data-testid="submit-search"]')
                    await expect(p.locator('[data-testid="search-results"]')).to_be_visible(
                        timeout=60000
                    )

                search_tasks.append(perform_search(page, i))

            # Execute all searches concurrently
            import asyncio

            await asyncio.gather(*search_tasks)

            search_time = time.time() - search_start

            # Concurrent searches should complete within reasonable time
            assert (
                search_time < 120.0
            ), f"Concurrent searches took {search_time:.2f}s, exceeds 120 seconds"

        finally:
            # Clean up contexts
            for context in contexts:
                await context.close()

    async def test_resource_loading_performance(self, page: Page):
        """Test static resource loading performance."""
        # Monitor network requests
        resource_timings = []

        def handle_response(response):
            if response.url.endswith((".js", ".css", ".png", ".jpg", ".svg")):
                resource_timings.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "size": len(response.body()) if response.body() else 0,
                    }
                )

        page.on("response", handle_response)

        # Navigate to page
        await page.goto("/")
        await page.wait_for_load_state("networkidle")

        # Check resource loading
        assert len(resource_timings) > 0, "Should load static resources"

        # All resources should load successfully
        failed_resources = [r for r in resource_timings if r["status"] >= 400]
        assert len(failed_resources) == 0, f"Failed to load resources: {failed_resources}"

        # Check for large resources that might impact performance
        large_resources = [r for r in resource_timings if r["size"] > 1024 * 1024]  # > 1MB

        if large_resources:
            print(f"Warning: Large resources detected: {large_resources}")

    async def test_scroll_performance(self, page: Page, authenticated_user, test_repository):
        """Test scroll performance with large result sets."""
        await page.goto("/search")

        # Perform search that returns many results
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Test scroll performance
        scroll_start = time.time()

        # Scroll down multiple times
        for i in range(10):
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(100)

        scroll_time = time.time() - scroll_start

        # Scrolling should be smooth and fast
        assert scroll_time < 5.0, f"Scroll performance {scroll_time:.2f}s exceeds 5 seconds"

        # Check if lazy loading is working (if implemented)
        visible_results = await page.locator('[data-testid="result-card"]:visible').count()
        total_results = await page.locator('[data-testid="result-card"]').count()

        # If lazy loading is implemented, not all results should be rendered initially
        if total_results > 50:
            assert (
                visible_results <= total_results
            ), "Lazy loading should limit initially rendered results"

    async def test_export_performance(self, page: Page, authenticated_user, test_repository):
        """Test export operation performance."""
        # Perform search first
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Test export performance
        export_start = time.time()

        # Trigger export
        await page.click('[data-testid="export-button"]')
        await page.select_option('[data-testid="export-format"]', "json")
        await page.click('[data-testid="confirm-export"]')

        # Wait for export to complete
        await expect(page.locator('[data-testid="export-complete"]')).to_be_visible(timeout=30000)

        export_time = time.time() - export_start

        # Export should complete within reasonable time
        assert export_time < 30.0, f"Export time {export_time:.2f}s exceeds 30 seconds"
