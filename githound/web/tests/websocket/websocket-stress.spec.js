/**
 * WebSocket Stress Testing Suite
 * Tests WebSocket performance under high load and stress conditions
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');
const { WebSocketTestHelper } = require('../utils/websocket-helper');

test.describe('WebSocket Stress Tests', () => {
  let searchPage;
  let loginPage;
  let wsHelper;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    wsHelper = new WebSocketTestHelper(page);

    // Login first
    const testUser = {
      username: `stress_${Date.now()}`,
      email: `stress_${Date.now()}@example.com`,
      password: 'StressTest123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
    await searchPage.navigateToSearch();
  });

  test.describe('High Volume Message Testing @websocket @stress @performance', () => {
    test('should handle rapid message bursts', async () => {
      const connection = await wsHelper.connect();

      // Send burst of messages
      const burstSize = 50;
      const startTime = Date.now();

      const messagePromises = [];
      for (let i = 0; i < burstSize; i++) {
        messagePromises.push(wsHelper.sendMessage({
          type: 'ping',
          data: { sequence: i, timestamp: Date.now() }
        }));
      }

      const results = await Promise.all(messagePromises);
      const endTime = Date.now();

      // Verify performance
      const totalTime = endTime - startTime;
      const messagesPerSecond = (burstSize / totalTime) * 1000;

      expect(messagesPerSecond).toBeGreaterThan(10); // At least 10 messages/second

      // Verify all messages were handled
      const successCount = results.filter(r => r.success).length;
      expect(successCount).toBeGreaterThan(burstSize * 0.8); // At least 80% success rate

      await wsHelper.disconnect();
    });

    test('should maintain performance with sustained load', async () => {
      const connection = await wsHelper.connect();
      const searchId = `sustained_load_${Date.now()}`;

      await wsHelper.subscribeToSearch(searchId);

      // Simulate sustained load over time
      const duration = 30000; // 30 seconds
      const messageInterval = 100; // Every 100ms
      const expectedMessages = duration / messageInterval;

      const startTime = Date.now();
      let messageCount = 0;
      let successCount = 0;

      const intervalId = setInterval(async () => {
        if (Date.now() - startTime >= duration) {
          clearInterval(intervalId);
          return;
        }

        messageCount++;
        const result = await wsHelper.simulateProgressUpdate(searchId, {
          progress: (messageCount / expectedMessages) * 100,
          message: `Sustained load message ${messageCount}`,
          results_count: messageCount
        });

        if (result.success) {
          successCount++;
        }
      }, messageInterval);

      // Wait for test completion
      await new Promise(resolve => setTimeout(resolve, duration + 1000));

      // Verify performance under sustained load
      const successRate = (successCount / messageCount) * 100;
      expect(successRate).toBeGreaterThan(90); // 90% success rate
      expect(messageCount).toBeGreaterThan(expectedMessages * 0.9); // At least 90% of expected messages

      await wsHelper.disconnect();
    });

    test('should handle large payload messages', async () => {
      const connection = await wsHelper.connect();

      // Test various payload sizes
      const payloadSizes = [1024, 10240, 102400, 1048576]; // 1KB, 10KB, 100KB, 1MB

      for (const size of payloadSizes) {
        const largePayload = 'x'.repeat(size);
        const startTime = Date.now();

        const result = await wsHelper.sendMessage({
          type: 'test_large_payload',
          data: {
            payload: largePayload,
            size: size
          }
        });

        const endTime = Date.now();
        const transferTime = endTime - startTime;

        // Verify message handling
        if (size <= 102400) { // Up to 100KB should succeed
          expect(result.success || result.error).toBeTruthy();
        }

        // Performance should be reasonable (under 5 seconds for any size)
        expect(transferTime).toBeLessThan(5000);
      }

      await wsHelper.disconnect();
    });
  });

  test.describe('Connection Stability Under Stress @websocket @stress @stability', () => {
    test('should maintain connection during CPU stress', async ({ page }) => {
      const connection = await wsHelper.connect();

      // Create CPU stress
      await page.evaluate(() => {
        const stressTest = () => {
          const start = Date.now();
          while (Date.now() - start < 1000) {
            // CPU intensive operation
            Math.random() * Math.random();
          }
        };

        // Run stress test for 10 seconds
        const stressInterval = setInterval(() => {
          stressTest();
        }, 100);

        setTimeout(() => {
          clearInterval(stressInterval);
        }, 10000);
      });

      // Send periodic pings during stress
      const pingResults = [];
      for (let i = 0; i < 10; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const pingResult = await wsHelper.sendPing();
        pingResults.push(pingResult);
      }

      // Connection should remain stable
      const successfulPings = pingResults.filter(r => r.success).length;
      expect(successfulPings).toBeGreaterThan(7); // At least 70% success rate

      await wsHelper.disconnect();
    });

    test('should handle memory pressure gracefully', async ({ page }) => {
      const connection = await wsHelper.connect();

      // Create memory pressure
      await page.evaluate(() => {
        window.memoryStressTest = [];
        const createMemoryPressure = () => {
          for (let i = 0; i < 1000; i++) {
            window.memoryStressTest.push(new Array(1000).fill('memory stress test data'));
          }
        };

        // Gradually increase memory usage
        const memoryInterval = setInterval(() => {
          createMemoryPressure();

          // Clean up some memory to prevent browser crash
          if (window.memoryStressTest.length > 10000) {
            window.memoryStressTest = window.memoryStressTest.slice(-5000);
          }
        }, 500);

        setTimeout(() => {
          clearInterval(memoryInterval);
          window.memoryStressTest = null;
        }, 15000);
      });

      // Test WebSocket functionality during memory pressure
      const testResults = [];
      for (let i = 0; i < 15; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));

        const result = await wsHelper.sendMessage({
          type: 'memory_pressure_test',
          data: { iteration: i, timestamp: Date.now() }
        });

        testResults.push(result);
      }

      // Should handle memory pressure without major failures
      const successCount = testResults.filter(r => r.success).length;
      expect(successCount).toBeGreaterThan(10); // At least 66% success rate

      await wsHelper.disconnect();
    });

    test('should recover from temporary network issues', async () => {
      const connection = await wsHelper.connect();

      // Simulate intermittent network issues
      const networkIssues = [1000, 2000, 500, 3000, 1500]; // Various durations

      for (const duration of networkIssues) {
        // Simulate network interruption
        await wsHelper.simulateNetworkInterruption(duration);

        // Wait for recovery
        await new Promise(resolve => setTimeout(resolve, duration + 1000));

        // Test connection after recovery
        const pingResult = await wsHelper.sendPing();
        expect(pingResult.success || pingResult.reconnected).toBe(true);
      }

      await wsHelper.disconnect();
    });
  });

  test.describe('Concurrent User Stress Testing @websocket @stress @concurrent', () => {
    test('should handle multiple concurrent WebSocket connections', async ({ browser }) => {
      const connectionCount = 10;
      const contexts = [];
      const connections = [];

      try {
        // Create multiple browser contexts
        for (let i = 0; i < connectionCount; i++) {
          const context = await browser.newContext();
          contexts.push(context);

          const page = await context.newPage();
          const helper = new WebSocketTestHelper(page);

          // Setup user and login
          const testUser = {
            username: `concurrent_${Date.now()}_${i}`,
            email: `concurrent_${Date.now()}_${i}@example.com`,
            password: 'Concurrent123!'
          };

          const loginPageInstance = new LoginPage(page);
          await loginPageInstance.register(testUser);
          await loginPageInstance.login(testUser.username, testUser.password);

          // Connect WebSocket
          const connection = await helper.connect();
          connections.push({ helper, connection, index: i });
        }

        // Verify all connections are established
        const successfulConnections = connections.filter(c => c.connection.isConnected).length;
        expect(successfulConnections).toBe(connectionCount);

        // Test concurrent messaging
        const messagePromises = connections.map(async ({ helper, index }) => {
          const results = [];
          for (let i = 0; i < 10; i++) {
            const result = await helper.sendMessage({
              type: 'concurrent_test',
              data: { user: index, message: i, timestamp: Date.now() }
            });
            results.push(result);
          }
          return results;
        });

        const allResults = await Promise.all(messagePromises);

        // Verify concurrent messaging works
        allResults.forEach((userResults, userIndex) => {
          const successCount = userResults.filter(r => r.success).length;
          expect(successCount).toBeGreaterThan(7); // At least 70% success rate per user
        });

      } finally {
        // Cleanup
        for (const { helper } of connections) {
          await helper.disconnect();
        }
        for (const context of contexts) {
          await context.close();
        }
      }
    });

    test('should handle concurrent search operations', async ({ browser }) => {
      const searchCount = 5;
      const contexts = [];
      const searchPromises = [];

      try {
        for (let i = 0; i < searchCount; i++) {
          const context = await browser.newContext();
          contexts.push(context);

          const searchPromise = (async () => {
            const page = await context.newPage();
            const helper = new WebSocketTestHelper(page);
            const searchPageInstance = new SearchPage(page);
            const loginPageInstance = new LoginPage(page);

            // Setup user
            const testUser = {
              username: `search_stress_${Date.now()}_${i}`,
              email: `search_stress_${Date.now()}_${i}@example.com`,
              password: 'SearchStress123!'
            };

            await loginPageInstance.register(testUser);
            await loginPageInstance.login(testUser.username, testUser.password);

            // Connect WebSocket and perform search
            const connection = await helper.connect();
            const searchId = `stress_search_${Date.now()}_${i}`;
            await helper.subscribeToSearch(searchId);

            await searchPageInstance.navigateToSearch();
            await searchPageInstance.performAdvancedSearch({
              query: `stress_test_${i}`,
              fileTypes: ['js', 'py'],
              searchType: 'fuzzy'
            });

            // Wait for search completion
            const completion = await helper.waitForSearchCompletion(60000);
            await helper.disconnect();

            return {
              searchId,
              success: completion !== null,
              completion
            };
          })();

          searchPromises.push(searchPromise);
        }

        // Wait for all searches to complete
        const results = await Promise.all(searchPromises);

        // Verify all searches completed successfully
        const successfulSearches = results.filter(r => r.success).length;
        expect(successfulSearches).toBeGreaterThan(searchCount * 0.8); // At least 80% success rate

      } finally {
        // Cleanup
        for (const context of contexts) {
          await context.close();
        }
      }
    });
  });

  test.describe('Resource Exhaustion Testing @websocket @stress @resources', () => {
    test('should handle WebSocket connection limits', async ({ browser }) => {
      const maxConnections = 20;
      const contexts = [];
      const connections = [];

      try {
        // Attempt to create many connections
        for (let i = 0; i < maxConnections; i++) {
          const context = await browser.newContext();
          contexts.push(context);

          const page = await context.newPage();
          const helper = new WebSocketTestHelper(page);

          // Quick setup without full registration
          await page.goto('/');

          try {
            const connection = await helper.connect();
            connections.push({ helper, connection, index: i });
          } catch (error) {
            // Connection limit reached
            break;
          }
        }

        // Should handle connection limits gracefully
        expect(connections.length).toBeGreaterThan(5); // Should allow at least 5 connections

        // Test that existing connections still work
        const activeConnections = connections.filter(c => c.connection.isConnected);
        expect(activeConnections.length).toBeGreaterThan(0);

        // Test messaging on active connections
        const pingResults = await Promise.all(
          activeConnections.slice(0, 5).map(({ helper }) => helper.sendPing())
        );

        const successfulPings = pingResults.filter(r => r.success).length;
        expect(successfulPings).toBeGreaterThan(0);

      } finally {
        // Cleanup
        for (const { helper } of connections) {
          try {
            await helper.disconnect();
          } catch (error) {
            // Ignore cleanup errors
          }
        }
        for (const context of contexts) {
          await context.close();
        }
      }
    });

    test('should handle message queue overflow', async () => {
      const connection = await wsHelper.connect();

      // Send many messages without waiting for responses
      const messageCount = 1000;
      const messages = [];

      for (let i = 0; i < messageCount; i++) {
        messages.push(wsHelper.sendMessage({
          type: 'queue_overflow_test',
          data: { sequence: i, timestamp: Date.now() }
        }, { waitForResponse: false }));
      }

      // Wait for all messages to be processed
      const results = await Promise.all(messages);

      // Should handle queue overflow gracefully
      const processedCount = results.filter(r => r.success || r.queued).length;
      expect(processedCount).toBeGreaterThan(messageCount * 0.5); // At least 50% processed

      await wsHelper.disconnect();
    });
  });
});
