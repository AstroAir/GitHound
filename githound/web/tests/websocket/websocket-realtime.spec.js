/**
 * WebSocket Real-time Testing Suite
 * Tests WebSocket connections, real-time updates, and live search progress
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');
const { WebSocketTestHelper } = require('../utils/websocket-helper');

test.describe('WebSocket Real-time Tests', () => {
  let searchPage;
  let loginPage;
  let wsHelper;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    wsHelper = new WebSocketTestHelper(page);

    // Login first
    const testUser = {
      username: `wstest_${Date.now()}`,
      email: `wstest_${Date.now()}@example.com`,
      password: 'WebSocketTest123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
    await searchPage.navigateToSearch();
  });

  test.describe('WebSocket Connection Management @websocket @connection', () => {
    test('should establish WebSocket connection successfully', async () => {
      const connection = await wsHelper.connect();
      
      expect(connection.isConnected).toBe(true);
      expect(connection.connectionId).toBeTruthy();
      
      await wsHelper.disconnect();
    });

    test('should handle connection failures gracefully', async ({ page }) => {
      // Mock WebSocket connection failure
      await page.addInitScript(() => {
        const originalWebSocket = window.WebSocket;
        window.WebSocket = function(url) {
          throw new Error('Connection failed');
        };
      });

      const result = await wsHelper.connect();
      
      expect(result.isConnected).toBe(false);
      expect(result.error).toContain('Connection failed');
    });

    test('should reconnect automatically after disconnection', async ({ page }) => {
      const connection = await wsHelper.connect();
      expect(connection.isConnected).toBe(true);

      // Simulate connection loss
      await wsHelper.simulateConnectionLoss();
      
      // Wait for automatic reconnection
      const reconnected = await wsHelper.waitForReconnection(10000);
      expect(reconnected).toBe(true);
    });

    test('should handle multiple concurrent connections', async ({ browser }) => {
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const connections = await Promise.all(
        contexts.map(async (context) => {
          const page = await context.newPage();
          const helper = new WebSocketTestHelper(page);
          return helper.connect();
        })
      );

      // All connections should be successful
      connections.forEach(conn => {
        expect(conn.isConnected).toBe(true);
      });

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should maintain connection during page navigation', async ({ page }) => {
      const connection = await wsHelper.connect();
      expect(connection.isConnected).toBe(true);

      // Navigate to different page
      await page.goto('/profile');
      
      // Connection should still be active
      const isStillConnected = await wsHelper.isConnected();
      expect(isStillConnected).toBe(true);

      await wsHelper.disconnect();
    });
  });

  test.describe('Real-time Search Progress @websocket @search @realtime', () => {
    test('should receive progress updates during search', async () => {
      const connection = await wsHelper.connect();
      const searchId = `search_${Date.now()}`;
      
      // Subscribe to search updates
      await wsHelper.subscribeToSearch(searchId);
      
      // Start a search
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js', 'py'],
        searchType: 'fuzzy'
      });

      // Wait for progress updates
      const progressUpdates = await wsHelper.waitForProgressUpdates(30000);
      
      expect(progressUpdates.length).toBeGreaterThan(0);
      
      // Verify progress update structure
      const firstUpdate = progressUpdates[0];
      expect(firstUpdate.type).toBe('progress');
      expect(firstUpdate.data.search_id).toBeTruthy();
      expect(firstUpdate.data.progress).toBeGreaterThanOrEqual(0);
      expect(firstUpdate.data.progress).toBeLessThanOrEqual(100);
      expect(firstUpdate.data.message).toBeTruthy();
      expect(firstUpdate.data.timestamp).toBeTruthy();

      await wsHelper.disconnect();
    });

    test('should receive real-time search results', async () => {
      const connection = await wsHelper.connect();
      const searchId = `search_${Date.now()}`;
      
      await wsHelper.subscribeToSearch(searchId);
      
      // Start search
      await searchPage.performAdvancedSearch({
        query: 'test',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Wait for result updates
      const resultUpdates = await wsHelper.waitForResultUpdates(30000);
      
      expect(resultUpdates.length).toBeGreaterThan(0);
      
      // Verify result structure
      const firstResult = resultUpdates[0];
      expect(firstResult.type).toBe('result');
      expect(firstResult.data.search_id).toBeTruthy();
      expect(firstResult.data.result).toBeTruthy();
      expect(firstResult.data.result.file_path).toBeTruthy();
      expect(firstResult.data.result.line_number).toBeGreaterThan(0);
      expect(firstResult.data.timestamp).toBeTruthy();

      await wsHelper.disconnect();
    });

    test('should receive search completion notification', async () => {
      const connection = await wsHelper.connect();
      const searchId = `search_${Date.now()}`;
      
      await wsHelper.subscribeToSearch(searchId);
      
      // Start search
      await searchPage.performAdvancedSearch({
        query: 'import',
        fileTypes: ['py'],
        searchType: 'exact'
      });

      // Wait for completion
      const completion = await wsHelper.waitForSearchCompletion(60000);
      
      expect(completion).toBeTruthy();
      expect(completion.type).toBe('completed');
      expect(completion.data.search_id).toBeTruthy();
      expect(completion.data.status).toBe('completed');
      expect(completion.data.total_results).toBeGreaterThanOrEqual(0);
      expect(completion.data.timestamp).toBeTruthy();

      await wsHelper.disconnect();
    });

    test('should handle search errors via WebSocket', async () => {
      const connection = await wsHelper.connect();
      const searchId = `search_${Date.now()}`;
      
      await wsHelper.subscribeToSearch(searchId);
      
      // Trigger a search that will cause an error
      await searchPage.performAdvancedSearch({
        query: '',  // Empty query should cause error
        fileTypes: [],
        searchType: 'exact'
      });

      // Wait for error notification
      const errorUpdate = await wsHelper.waitForErrorUpdate(10000);
      
      expect(errorUpdate).toBeTruthy();
      expect(errorUpdate.type).toBe('error');
      expect(errorUpdate.data.search_id).toBeTruthy();
      expect(errorUpdate.data.error).toBeTruthy();
      expect(errorUpdate.data.timestamp).toBeTruthy();

      await wsHelper.disconnect();
    });
  });

  test.describe('WebSocket Message Handling @websocket @messages', () => {
    test('should handle ping/pong messages correctly', async () => {
      const connection = await wsHelper.connect();
      
      // Send ping
      const pingResult = await wsHelper.sendPing();
      
      expect(pingResult.success).toBe(true);
      expect(pingResult.pongReceived).toBe(true);
      expect(pingResult.roundTripTime).toBeGreaterThan(0);
      expect(pingResult.roundTripTime).toBeLessThan(5000); // Should be under 5 seconds

      await wsHelper.disconnect();
    });

    test('should handle subscription/unsubscription correctly', async () => {
      const connection = await wsHelper.connect();
      const searchId = `search_${Date.now()}`;
      
      // Subscribe to search
      const subscribeResult = await wsHelper.subscribeToSearch(searchId);
      expect(subscribeResult.success).toBe(true);
      
      // Verify subscription is active
      const isSubscribed = await wsHelper.isSubscribedToSearch(searchId);
      expect(isSubscribed).toBe(true);
      
      // Unsubscribe from search
      const unsubscribeResult = await wsHelper.unsubscribeFromSearch(searchId);
      expect(unsubscribeResult.success).toBe(true);
      
      // Verify subscription is removed
      const isStillSubscribed = await wsHelper.isSubscribedToSearch(searchId);
      expect(isStillSubscribed).toBe(false);

      await wsHelper.disconnect();
    });

    test('should handle malformed messages gracefully', async () => {
      const connection = await wsHelper.connect();
      
      // Send malformed JSON
      const malformedResult = await wsHelper.sendRawMessage('invalid json');
      expect(malformedResult.error).toBeTruthy();
      
      // Connection should still be active
      const isConnected = await wsHelper.isConnected();
      expect(isConnected).toBe(true);
      
      // Send message with unknown type
      const unknownTypeResult = await wsHelper.sendMessage({
        type: 'unknown_type',
        data: { test: 'data' }
      });
      
      // Should handle gracefully without disconnecting
      const isStillConnected = await wsHelper.isConnected();
      expect(isStillConnected).toBe(true);

      await wsHelper.disconnect();
    });

    test('should handle large message payloads', async () => {
      const connection = await wsHelper.connect();
      
      // Create a large message
      const largeData = {
        type: 'test',
        data: {
          large_field: 'x'.repeat(100000) // 100KB of data
        }
      };
      
      const result = await wsHelper.sendMessage(largeData);
      
      // Should handle large messages appropriately
      expect(result.success || result.error).toBeTruthy();
      
      // Connection should remain stable
      const isConnected = await wsHelper.isConnected();
      expect(isConnected).toBe(true);

      await wsHelper.disconnect();
    });
  });

  test.describe('WebSocket Performance @websocket @performance', () => {
    test('should handle high-frequency updates efficiently', async () => {
      const connection = await wsHelper.connect();
      const searchId = `perf_search_${Date.now()}`;
      
      await wsHelper.subscribeToSearch(searchId);
      
      // Simulate high-frequency updates
      const updateCount = 100;
      const startTime = Date.now();
      
      for (let i = 0; i < updateCount; i++) {
        await wsHelper.simulateProgressUpdate(searchId, {
          progress: (i / updateCount) * 100,
          message: `Processing item ${i + 1}`,
          results_count: i
        });
      }
      
      const endTime = Date.now();
      const totalTime = endTime - startTime;
      
      // Should handle updates efficiently (under 10 seconds for 100 updates)
      expect(totalTime).toBeLessThan(10000);
      
      // Verify all updates were received
      const receivedUpdates = await wsHelper.getReceivedUpdates();
      expect(receivedUpdates.length).toBe(updateCount);

      await wsHelper.disconnect();
    });

    test('should maintain connection stability under load', async () => {
      const connection = await wsHelper.connect();
      
      // Send multiple concurrent messages
      const messagePromises = [];
      for (let i = 0; i < 50; i++) {
        messagePromises.push(wsHelper.sendPing());
      }
      
      const results = await Promise.all(messagePromises);
      
      // All pings should succeed
      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.pongReceived).toBe(true);
      });
      
      // Connection should remain stable
      const isConnected = await wsHelper.isConnected();
      expect(isConnected).toBe(true);

      await wsHelper.disconnect();
    });

    test('should handle connection timeouts appropriately', async ({ page }) => {
      // Set a very short timeout for testing
      await page.addInitScript(() => {
        window.WEBSOCKET_TIMEOUT = 1000; // 1 second
      });

      const connection = await wsHelper.connect();
      
      // Wait longer than timeout
      await page.waitForTimeout(2000);
      
      // Should handle timeout gracefully
      const connectionStatus = await wsHelper.getConnectionStatus();
      expect(connectionStatus.hasTimeout || connectionStatus.isReconnecting).toBe(true);
    });
  });

  test.describe('WebSocket Error Scenarios @websocket @error', () => {
    test('should handle server-side WebSocket errors', async ({ page }) => {
      // Mock server error
      await page.route('**/ws/**', route => {
        route.fulfill({
          status: 500,
          body: 'Internal Server Error'
        });
      });

      const connection = await wsHelper.connect();

      expect(connection.isConnected).toBe(false);
      expect(connection.error).toContain('500');
    });

    test('should handle network interruptions', async () => {
      const connection = await wsHelper.connect();
      expect(connection.isConnected).toBe(true);

      // Simulate network interruption
      await wsHelper.simulateNetworkInterruption(5000); // 5 second interruption

      // Should attempt to reconnect
      const reconnected = await wsHelper.waitForReconnection(15000);
      expect(reconnected).toBe(true);
    });

    test('should handle WebSocket protocol errors', async ({ page }) => {
      // Mock protocol error
      await page.addInitScript(() => {
        const originalWebSocket = window.WebSocket;
        window.WebSocket = function(url) {
          const ws = new originalWebSocket(url);
          setTimeout(() => {
            ws.dispatchEvent(new Event('error'));
          }, 1000);
          return ws;
        };
      });

      const connection = await wsHelper.connect();

      // Should handle protocol error
      const errorHandled = await wsHelper.waitForError(5000);
      expect(errorHandled).toBe(true);
    });

    test('should handle browser tab visibility changes', async ({ page }) => {
      const connection = await wsHelper.connect();
      expect(connection.isConnected).toBe(true);

      // Simulate tab becoming hidden
      await page.evaluate(() => {
        Object.defineProperty(document, 'hidden', { value: true, writable: true });
        document.dispatchEvent(new Event('visibilitychange'));
      });

      // Connection should be paused or handled appropriately
      await page.waitForTimeout(1000);

      // Simulate tab becoming visible again
      await page.evaluate(() => {
        Object.defineProperty(document, 'hidden', { value: false, writable: true });
        document.dispatchEvent(new Event('visibilitychange'));
      });

      // Connection should resume
      const isConnected = await wsHelper.isConnected();
      expect(isConnected).toBe(true);

      await wsHelper.disconnect();
    });

    test('should handle memory pressure scenarios', async ({ page }) => {
      const connection = await wsHelper.connect();

      // Simulate memory pressure by creating large objects
      await page.evaluate(() => {
        window.memoryPressureTest = [];
        for (let i = 0; i < 1000; i++) {
          window.memoryPressureTest.push(new Array(10000).fill('memory pressure test'));
        }
      });

      // Connection should remain stable under memory pressure
      const isConnected = await wsHelper.isConnected();
      expect(isConnected).toBe(true);

      // Cleanup
      await page.evaluate(() => {
        window.memoryPressureTest = null;
      });

      await wsHelper.disconnect();
    });
  });

  test.describe('WebSocket Integration Tests @websocket @integration', () => {
    test('should integrate with search UI updates', async () => {
      const connection = await wsHelper.connect();
      const searchId = `ui_integration_${Date.now()}`;

      await wsHelper.subscribeToSearch(searchId);

      // Start search and monitor both WebSocket and UI
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Wait for WebSocket progress updates
      const wsUpdates = await wsHelper.waitForProgressUpdates(30000);

      // Verify UI is updated accordingly
      const uiProgress = await searchPage.getSearchProgress();
      const hasResults = await searchPage.hasResults();

      expect(wsUpdates.length).toBeGreaterThan(0);
      expect(uiProgress).toBeGreaterThan(0);
      expect(hasResults).toBe(true);

      await wsHelper.disconnect();
    });

    test('should handle multiple search sessions simultaneously', async ({ browser }) => {
      // Create multiple browser contexts for concurrent searches
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const searchPromises = contexts.map(async (context, index) => {
        const page = await context.newPage();
        const helper = new WebSocketTestHelper(page);
        const searchPageInstance = new SearchPage(page);

        // Login and setup
        const testUser = {
          username: `concurrent_${Date.now()}_${index}`,
          email: `concurrent_${Date.now()}_${index}@example.com`,
          password: 'Concurrent123!'
        };

        const loginPageInstance = new LoginPage(page);
        await loginPageInstance.register(testUser);
        await loginPageInstance.login(testUser.username, testUser.password);

        // Connect WebSocket and start search
        const connection = await helper.connect();
        const searchId = `concurrent_search_${Date.now()}_${index}`;
        await helper.subscribeToSearch(searchId);

        await searchPageInstance.navigateToSearch();
        await searchPageInstance.performAdvancedSearch({
          query: `test${index}`,
          fileTypes: ['js'],
          searchType: 'exact'
        });

        // Wait for completion
        const completion = await helper.waitForSearchCompletion(60000);
        await helper.disconnect();

        return {
          searchId,
          completion,
          success: completion !== null
        };
      });

      const results = await Promise.all(searchPromises);

      // All searches should complete successfully
      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.completion.type).toBe('completed');
      });

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should maintain WebSocket connection during page transitions', async ({ page }) => {
      const connection = await wsHelper.connect();
      expect(connection.isConnected).toBe(true);

      // Navigate through different pages
      const pages = ['/search', '/profile', '/settings', '/search'];

      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForTimeout(1000);

        // Connection should remain active
        const isConnected = await wsHelper.isConnected();
        expect(isConnected).toBe(true);
      }

      await wsHelper.disconnect();
    });

    test('should handle authentication state changes', async ({ page }) => {
      const connection = await wsHelper.connect();
      expect(connection.isConnected).toBe(true);

      // Logout user
      await loginPage.logout();

      // WebSocket should handle auth state change appropriately
      const connectionAfterLogout = await wsHelper.getConnectionStatus();
      expect(connectionAfterLogout.isAuthenticated).toBe(false);

      // Login again
      const testUser = {
        username: `auth_change_${Date.now()}`,
        email: `auth_change_${Date.now()}@example.com`,
        password: 'AuthChange123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // WebSocket should re-authenticate
      const connectionAfterLogin = await wsHelper.getConnectionStatus();
      expect(connectionAfterLogin.isAuthenticated).toBe(true);

      await wsHelper.disconnect();
    });

    test('should synchronize with export functionality', async () => {
      const connection = await wsHelper.connect();
      const searchId = `export_sync_${Date.now()}`;

      await wsHelper.subscribeToSearch(searchId);

      // Perform search first
      await searchPage.performAdvancedSearch({
        query: 'export',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Wait for search completion
      await wsHelper.waitForSearchCompletion(30000);

      // Start export and monitor via WebSocket
      const exportUpdates = await wsHelper.waitForExportUpdates(searchId, 30000);

      expect(exportUpdates.length).toBeGreaterThan(0);
      expect(exportUpdates[0].type).toBe('export_progress');

      await wsHelper.disconnect();
    });
  });

  test.describe('WebSocket Security Tests @websocket @security', () => {
    test('should require authentication for WebSocket connection', async ({ page }) => {
      // Logout first
      await loginPage.logout();

      // Try to connect without authentication
      const connection = await wsHelper.connect();

      expect(connection.isConnected).toBe(false);
      expect(connection.error).toMatch(/authentication|unauthorized/i);
    });

    test('should validate WebSocket message authorization', async () => {
      const connection = await wsHelper.connect();

      // Try to subscribe to another user's search
      const unauthorizedSearchId = 'unauthorized_search_123';
      const result = await wsHelper.subscribeToSearch(unauthorizedSearchId);

      expect(result.success).toBe(false);
      expect(result.error).toMatch(/unauthorized|forbidden/i);

      await wsHelper.disconnect();
    });

    test('should prevent WebSocket message injection', async () => {
      const connection = await wsHelper.connect();

      // Try to send malicious messages
      const maliciousMessages = [
        { type: 'admin_command', data: { action: 'delete_all' } },
        { type: 'system_override', data: { privilege: 'admin' } },
        { type: 'inject_result', data: { fake_result: 'malicious' } }
      ];

      for (const message of maliciousMessages) {
        const result = await wsHelper.sendMessage(message);
        expect(result.success).toBe(false);
      }

      // Connection should remain stable
      const isConnected = await wsHelper.isConnected();
      expect(isConnected).toBe(true);

      await wsHelper.disconnect();
    });

    test('should handle WebSocket rate limiting', async () => {
      const connection = await wsHelper.connect();

      // Send many messages rapidly
      const rapidMessages = [];
      for (let i = 0; i < 100; i++) {
        rapidMessages.push(wsHelper.sendPing());
      }

      const results = await Promise.all(rapidMessages);

      // Some messages should be rate limited
      const rateLimitedCount = results.filter(r => r.error && r.error.includes('rate limit')).length;
      expect(rateLimitedCount).toBeGreaterThan(0);

      await wsHelper.disconnect();
    });
  });
});
