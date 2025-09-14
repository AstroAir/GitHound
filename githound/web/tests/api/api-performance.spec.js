/**
 * API Performance Tests
 * Tests API response times, throughput, and performance under load
 */

const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages');

test.describe('API Performance Tests', () => {
  let loginPage;
  let authToken;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);

    // Setup authenticated user
    const testUser = {
      username: `perftest_${Date.now()}`,
      email: `perftest_${Date.now()}@example.com`,
      password: 'PerfTest123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
    
    // Get auth token for direct API calls
    authToken = await page.evaluate(() => localStorage.getItem('access_token'));
  });

  test.describe('API Response Time Tests @api @performance @timing', () => {
    test('should have fast authentication response times', async ({ page }) => {
      const userData = {
        username: `timing_${Date.now()}`,
        email: `timing_${Date.now()}@example.com`,
        password: 'Timing123!'
      };

      // Test registration timing
      const regStartTime = Date.now();
      const regResponse = await page.evaluate(async (userData) => {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData)
        });
        return { status: response.status, data: await response.json() };
      }, userData);
      const regEndTime = Date.now();

      expect(regResponse.status).toBe(200);
      expect(regEndTime - regStartTime).toBeLessThan(2000); // Under 2 seconds

      // Test login timing
      const loginStartTime = Date.now();
      const loginResponse = await page.evaluate(async (userData) => {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: userData.username,
            password: userData.password
          })
        });
        return { status: response.status, data: await response.json() };
      }, userData);
      const loginEndTime = Date.now();

      expect(loginResponse.status).toBe(200);
      expect(loginEndTime - loginStartTime).toBeLessThan(1000); // Under 1 second
    });

    test('should have reasonable search API response times', async ({ page }) => {
      const searchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'function',
        file_extensions: ['js'],
        max_results: 50
      };

      const startTime = Date.now();
      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return { status: response.status, data: await response.json() };
      }, searchRequest, authToken);
      const endTime = Date.now();

      expect(response.status).toBe(200);
      expect(endTime - startTime).toBeLessThan(5000); // Under 5 seconds for search initiation
    });

    test('should handle concurrent API requests efficiently', async ({ page }) => {
      const concurrentRequests = 10;
      const searchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'test',
        file_extensions: ['js']
      };

      const startTime = Date.now();
      
      // Make concurrent requests
      const promises = Array(concurrentRequests).fill().map(() =>
        page.evaluate(async (request, token) => {
          const response = await fetch('/api/search/advanced', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
          });
          return { status: response.status, data: await response.json() };
        }, searchRequest, authToken)
      );

      const results = await Promise.all(promises);
      const endTime = Date.now();

      // All requests should succeed
      results.forEach(result => {
        expect(result.status).toBe(200);
      });

      // Total time should be reasonable for concurrent requests
      const totalTime = endTime - startTime;
      const averageTime = totalTime / concurrentRequests;
      expect(averageTime).toBeLessThan(2000); // Average under 2 seconds per request
    });

    test('should maintain performance with large payloads', async ({ page }) => {
      const largeSearchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'function',
        file_extensions: Array(100).fill().map((_, i) => `ext${i}`), // Large array
        include_globs: Array(50).fill().map((_, i) => `pattern${i}/*`),
        exclude_globs: Array(50).fill().map((_, i) => `exclude${i}/*`),
        max_results: 1000
      };

      const startTime = Date.now();
      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return { status: response.status, data: await response.json() };
      }, largeSearchRequest, authToken);
      const endTime = Date.now();

      expect([200, 422]).toContain(response.status); // May reject if too large
      expect(endTime - startTime).toBeLessThan(10000); // Under 10 seconds even for large payloads
    });
  });

  test.describe('API Throughput Tests @api @performance @throughput', () => {
    test('should handle sustained API load', async ({ page }) => {
      const duration = 30000; // 30 seconds
      const requestInterval = 500; // Every 500ms
      const expectedRequests = duration / requestInterval;

      let requestCount = 0;
      let successCount = 0;
      let errorCount = 0;

      const startTime = Date.now();
      
      const intervalId = setInterval(async () => {
        if (Date.now() - startTime >= duration) {
          clearInterval(intervalId);
          return;
        }

        requestCount++;
        
        try {
          const response = await page.evaluate(async (token) => {
            const response = await fetch('/api/auth/profile', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });
            return response.status;
          }, authToken);

          if (response === 200) {
            successCount++;
          } else {
            errorCount++;
          }
        } catch (error) {
          errorCount++;
        }
      }, requestInterval);

      // Wait for test completion
      await new Promise(resolve => setTimeout(resolve, duration + 1000));

      // Verify throughput
      const successRate = (successCount / requestCount) * 100;
      expect(successRate).toBeGreaterThan(90); // 90% success rate
      expect(requestCount).toBeGreaterThan(expectedRequests * 0.8); // At least 80% of expected requests
    });

    test('should handle burst traffic patterns', async ({ page }) => {
      const burstSize = 20;
      const burstCount = 3;
      const burstInterval = 5000; // 5 seconds between bursts

      let totalRequests = 0;
      let totalSuccesses = 0;

      for (let burst = 0; burst < burstCount; burst++) {
        const burstStartTime = Date.now();
        
        // Create burst of requests
        const burstPromises = Array(burstSize).fill().map(() =>
          page.evaluate(async (token) => {
            const response = await fetch('/api/auth/profile', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });
            return response.status;
          }, authToken)
        );

        const burstResults = await Promise.all(burstPromises);
        const burstEndTime = Date.now();

        totalRequests += burstSize;
        totalSuccesses += burstResults.filter(status => status === 200).length;

        // Burst should complete within reasonable time
        expect(burstEndTime - burstStartTime).toBeLessThan(10000);

        // Wait before next burst
        if (burst < burstCount - 1) {
          await new Promise(resolve => setTimeout(resolve, burstInterval));
        }
      }

      // Overall success rate should be high
      const overallSuccessRate = (totalSuccesses / totalRequests) * 100;
      expect(overallSuccessRate).toBeGreaterThan(85);
    });

    test('should scale with increasing load', async ({ page }) => {
      const loadLevels = [5, 10, 20]; // Concurrent requests
      const results = [];

      for (const concurrency of loadLevels) {
        const startTime = Date.now();
        
        const promises = Array(concurrency).fill().map(() =>
          page.evaluate(async (token) => {
            const response = await fetch('/api/search/advanced', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                repo_path: '/test/repo',
                content_pattern: 'test',
                max_results: 10
              })
            });
            return response.status;
          }, authToken)
        );

        const responses = await Promise.all(promises);
        const endTime = Date.now();

        const successCount = responses.filter(status => status === 200).length;
        const successRate = (successCount / concurrency) * 100;
        const averageResponseTime = (endTime - startTime) / concurrency;

        results.push({
          concurrency,
          successRate,
          averageResponseTime,
          totalTime: endTime - startTime
        });

        expect(successRate).toBeGreaterThan(80); // At least 80% success rate
      }

      // Performance should not degrade significantly with increased load
      const firstResult = results[0];
      const lastResult = results[results.length - 1];
      
      // Response time should not increase more than 3x
      expect(lastResult.averageResponseTime).toBeLessThan(firstResult.averageResponseTime * 3);
    });
  });

  test.describe('API Resource Usage Tests @api @performance @resources', () => {
    test('should handle memory-intensive operations', async ({ page }) => {
      const largeSearchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'function',
        max_results: 10000, // Large result set
        include_context: true,
        context_lines: 10
      };

      // Monitor memory before request
      const memoryBefore = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      const startTime = Date.now();
      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return { status: response.status, data: await response.json() };
      }, largeSearchRequest, authToken);
      const endTime = Date.now();

      // Monitor memory after request
      const memoryAfter = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      expect(response.status).toBe(200);
      expect(endTime - startTime).toBeLessThan(30000); // Under 30 seconds

      // Memory usage should not increase dramatically
      if (memoryBefore && memoryAfter) {
        const memoryIncrease = memoryAfter.used - memoryBefore.used;
        expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024); // Less than 100MB increase
      }
    });

    test('should handle CPU-intensive search patterns', async ({ page }) => {
      const complexSearchRequest = {
        repo_path: '/test/repo',
        content_pattern: '.*function.*async.*await.*', // Complex regex
        fuzzy_search: true,
        fuzzy_threshold: 0.6,
        file_extensions: ['js', 'ts', 'jsx', 'tsx'],
        max_results: 1000
      };

      const startTime = Date.now();
      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return { status: response.status, data: await response.json() };
      }, complexSearchRequest, authToken);
      const endTime = Date.now();

      expect(response.status).toBe(200);
      expect(endTime - startTime).toBeLessThan(60000); // Under 1 minute for complex search
    });

    test('should handle network bandwidth efficiently', async ({ page }) => {
      // Test with throttled network
      const client = await page.context().newCDPSession(page);
      await client.send('Network.emulateNetworkConditions', {
        offline: false,
        downloadThroughput: 1024 * 1024, // 1 Mbps
        uploadThroughput: 512 * 1024,    // 512 Kbps
        latency: 100 // 100ms latency
      });

      const searchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'function',
        file_extensions: ['js'],
        max_results: 100
      };

      const startTime = Date.now();
      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return { status: response.status, data: await response.json() };
      }, searchRequest, authToken);
      const endTime = Date.now();

      expect(response.status).toBe(200);
      // Should still work reasonably well on slow network
      expect(endTime - startTime).toBeLessThan(15000); // Under 15 seconds on slow network

      // Restore normal network conditions
      await client.send('Network.emulateNetworkConditions', {
        offline: false,
        downloadThroughput: -1,
        uploadThroughput: -1,
        latency: 0
      });
    });
  });
});
