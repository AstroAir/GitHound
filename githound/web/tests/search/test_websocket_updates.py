"""
WebSocket real-time updates tests for GitHound web interface.
"""

import asyncio
import json
import pytest
from playwright.async_api import Page, expect


@pytest.mark.search
@pytest.mark.e2e
class TestWebSocketUpdates:
    """Test WebSocket real-time updates during search operations."""
    
    async def test_websocket_connection_establishment(self, page: Page, authenticated_user):
        """Test WebSocket connection is established properly."""
        # Navigate to search page
        await page.goto("/search")
        
        # Check WebSocket connection status
        connection_status = await page.evaluate("""
            () => {
                return window.websocketManager ? window.websocketManager.isConnected() : false;
            }
        """)
        
        assert connection_status, "WebSocket connection should be established"
        
    async def test_search_progress_updates(self, page: Page, authenticated_user, test_repository):
        """Test real-time search progress updates via WebSocket."""
        # Set up WebSocket message listener
        messages = []
        
        await page.evaluate("""
            window.websocketMessages = [];
            if (window.websocketManager) {
                window.websocketManager.onMessage((message) => {
                    window.websocketMessages.push(message);
                });
            }
        """)
        
        # Start a search
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')
        
        # Wait for progress updates
        await page.wait_for_function("""
            () => window.websocketMessages && window.websocketMessages.length > 0
        """, timeout=10000)
        
        # Verify progress updates are received
        messages = await page.evaluate("() => window.websocketMessages")
        assert len(messages) > 0, "Should receive WebSocket progress updates"
        
        # Check message structure
        progress_messages = [msg for msg in messages if msg.get('type') == 'search_progress']
        assert len(progress_messages) > 0, "Should receive search progress messages"
        
    async def test_search_completion_notification(self, page: Page, authenticated_user, test_repository):
        """Test search completion notification via WebSocket."""
        # Set up WebSocket message listener
        await page.evaluate("""
            window.searchCompleted = false;
            window.websocketMessages = [];
            if (window.websocketManager) {
                window.websocketManager.onMessage((message) => {
                    window.websocketMessages.push(message);
                    if (message.type === 'search_completed') {
                        window.searchCompleted = true;
                    }
                });
            }
        """)
        
        # Start a search
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')
        
        # Wait for search completion
        await page.wait_for_function("""
            () => window.searchCompleted === true
        """, timeout=30000)
        
        # Verify completion message
        messages = await page.evaluate("() => window.websocketMessages")
        completion_messages = [msg for msg in messages if msg.get('type') == 'search_completed']
        assert len(completion_messages) > 0, "Should receive search completion message"
        
        # Verify results are displayed
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible()
        
    async def test_search_error_notification(self, page: Page, authenticated_user):
        """Test search error notification via WebSocket."""
        # Set up WebSocket message listener
        await page.evaluate("""
            window.searchError = false;
            window.websocketMessages = [];
            if (window.websocketManager) {
                window.websocketManager.onMessage((message) => {
                    window.websocketMessages.push(message);
                    if (message.type === 'search_error') {
                        window.searchError = true;
                    }
                });
            }
        """)
        
        # Start a search with invalid repository
        await page.fill('[data-testid="repo-path-input"]', "/nonexistent/repo")
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')
        
        # Wait for error notification
        await page.wait_for_function("""
            () => window.searchError === true
        """, timeout=10000)
        
        # Verify error message
        messages = await page.evaluate("() => window.websocketMessages")
        error_messages = [msg for msg in messages if msg.get('type') == 'search_error']
        assert len(error_messages) > 0, "Should receive search error message"
        
        # Verify error is displayed in UI
        await expect(page.locator('[data-testid="search-error"]')).to_be_visible()
        
    async def test_multiple_concurrent_searches(self, page: Page, authenticated_user, test_repository):
        """Test WebSocket updates for multiple concurrent searches."""
        # Open multiple tabs/contexts for concurrent searches
        context = page.context
        page2 = await context.new_page()
        
        # Set up WebSocket listeners on both pages
        for p in [page, page2]:
            await p.goto("/search")
            await p.evaluate("""
                window.websocketMessages = [];
                if (window.websocketManager) {
                    window.websocketManager.onMessage((message) => {
                        window.websocketMessages.push(message);
                    });
                }
            """)
        
        # Start searches on both pages
        search_queries = ["function", "class"]
        pages = [page, page2]
        
        for i, (p, query) in enumerate(zip(pages, search_queries)):
            await p.fill('[data-testid="repo-path-input"]', str(test_repository))
            await p.fill('[data-testid="search-query-input"]', query)
            await p.click('[data-testid="submit-search"]')
        
        # Wait for both searches to complete
        for p in pages:
            await p.wait_for_function("""
                () => window.websocketMessages.some(msg => msg.type === 'search_completed')
            """, timeout=30000)
        
        # Verify each page received its own updates
        for p in pages:
            messages = await p.evaluate("() => window.websocketMessages")
            assert len(messages) > 0, "Each page should receive WebSocket updates"
            
        await page2.close()
        
    async def test_websocket_reconnection(self, page: Page, authenticated_user):
        """Test WebSocket reconnection after connection loss."""
        # Navigate to search page
        await page.goto("/search")
        
        # Verify initial connection
        initial_status = await page.evaluate("""
            () => window.websocketManager ? window.websocketManager.isConnected() : false
        """)
        assert initial_status, "Initial WebSocket connection should be established"
        
        # Simulate connection loss
        await page.evaluate("""
            () => {
                if (window.websocketManager && window.websocketManager.websocket) {
                    window.websocketManager.websocket.close();
                }
            }
        """)
        
        # Wait for reconnection
        await page.wait_for_function("""
            () => window.websocketManager && window.websocketManager.isConnected()
        """, timeout=10000)
        
        # Verify reconnection
        reconnected_status = await page.evaluate("""
            () => window.websocketManager ? window.websocketManager.isConnected() : false
        """)
        assert reconnected_status, "WebSocket should reconnect after connection loss"
        
    async def test_websocket_message_ordering(self, page: Page, authenticated_user, test_repository):
        """Test that WebSocket messages are received in correct order."""
        # Set up message tracking
        await page.evaluate("""
            window.messageOrder = [];
            window.websocketMessages = [];
            if (window.websocketManager) {
                window.websocketManager.onMessage((message) => {
                    window.websocketMessages.push(message);
                    if (message.sequence_number) {
                        window.messageOrder.push(message.sequence_number);
                    }
                });
            }
        """)
        
        # Start a search
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')
        
        # Wait for multiple messages
        await page.wait_for_function("""
            () => window.websocketMessages && window.websocketMessages.length >= 3
        """, timeout=30000)
        
        # Verify message ordering
        message_order = await page.evaluate("() => window.messageOrder")
        if len(message_order) > 1:
            # Check that sequence numbers are in ascending order
            for i in range(1, len(message_order)):
                assert message_order[i] > message_order[i-1], "Messages should be received in order"
                
    async def test_websocket_heartbeat(self, page: Page, authenticated_user):
        """Test WebSocket heartbeat/ping-pong mechanism."""
        # Navigate to search page
        await page.goto("/search")
        
        # Set up heartbeat tracking
        await page.evaluate("""
            window.heartbeatReceived = false;
            window.websocketMessages = [];
            if (window.websocketManager) {
                window.websocketManager.onMessage((message) => {
                    window.websocketMessages.push(message);
                    if (message.type === 'heartbeat' || message.type === 'ping') {
                        window.heartbeatReceived = true;
                    }
                });
            }
        """)
        
        # Wait for heartbeat message
        await page.wait_for_function("""
            () => window.heartbeatReceived === true
        """, timeout=15000)
        
        # Verify heartbeat was received
        heartbeat_received = await page.evaluate("() => window.heartbeatReceived")
        assert heartbeat_received, "Should receive WebSocket heartbeat messages"
        
    async def test_websocket_authentication(self, page: Page, authenticated_user):
        """Test WebSocket authentication with JWT token."""
        # Navigate to search page
        await page.goto("/search")
        
        # Check that WebSocket is authenticated
        auth_status = await page.evaluate("""
            () => {
                if (window.websocketManager) {
                    return window.websocketManager.isAuthenticated();
                }
                return false;
            }
        """)
        
        assert auth_status, "WebSocket should be authenticated with user token"
        
    async def test_websocket_cleanup_on_logout(self, page: Page, authenticated_user):
        """Test WebSocket connection cleanup when user logs out."""
        # Navigate to search page
        await page.goto("/search")
        
        # Verify WebSocket is connected
        initial_status = await page.evaluate("""
            () => window.websocketManager ? window.websocketManager.isConnected() : false
        """)
        assert initial_status, "WebSocket should be connected"
        
        # Logout
        await page.click('[data-testid="user-menu"]')
        await page.click('[data-testid="logout-button"]')
        
        # Verify WebSocket is disconnected
        final_status = await page.evaluate("""
            () => window.websocketManager ? window.websocketManager.isConnected() : false
        """)
        assert not final_status, "WebSocket should be disconnected after logout"
