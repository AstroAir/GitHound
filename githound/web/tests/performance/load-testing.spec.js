/**
 * Load Testing Suite
 * Tests system performance under various load conditions and concurrent user scenarios
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');
const { PerformanceTestHelper } = require('../utils/performance-helper');

test.describe('Load Testing Suite', () => {
  test.describe('Concurrent User Load Tests @performance @load @concurrent', () => {
    test('should handle 10 concurrent users performing searches', async ({ browser }) => {
      const userCount = 10;
      const contexts = [];
      const userPromises = [];

      try {
        // Create concurrent user sessions
        for (let i = 0; i < userCount; i++) {
          const context = await browser.newContext();
          contexts.push(context);

          const userPromise = (async () => {
            const page = await context.newPage();
            const loginPage = new LoginPage(page);
            const searchPage = new SearchPage(page);
            const perfHelper = new PerformanceTestHelper(page);

            // Setup user
            const testUser = {
              username: `load_user_${Date.now()}_${i}`,
              email: `load_user_${Date.now()}_${i}@example.com`,
              password: 'LoadTest123!'
            };

            const startTime = Date.now();

            // User journey: Register -> Login -> Search -> Results
            await loginPage.register(testUser);
            await loginPage.login(testUser.username, testUser.password);

            await searchPage.navigateToSearch();

            // Perform multiple searches
            const searches = [
              { query: `function_${i}`, fileTypes: ['js'] },
              { query: `import_${i}`, fileTypes: ['py'] },
              { query: `class_${i}`, fileTypes: ['ts'] }
            ];

            const searchTimes = [];

            for (const search of searches) {
              const searchStartTime = Date.now();

              await searchPage.performAdvancedSearch({
                query: search.query,
                fileTypes: search.fileTypes,
                searchType: 'exact'
              });

              await searchPage.waitForResults();

              const searchTime = Date.now() - searchStartTime;
              searchTimes.push(searchTime);
            }

            const totalTime = Date.now() - startTime;
            const averageSearchTime = searchTimes.reduce((a, b) => a + b, 0) / searchTimes.length;

            // Measure final performance metrics
            const webVitals = await perfHelper.measureWebVitals();

            return {
              userId: i,
              totalTime,
              averageSearchTime,
              searchTimes,
              webVitals,
              success: true
            };
          })();

          userPromises.push(userPromise);
        }

        // Wait for all users to complete
        const results = await Promise.all(userPromises);

        // Analyze results
        const successfulUsers = results.filter(r => r.success);
        expect(successfulUsers.length).toBe(userCount);

        // Performance should remain reasonable under load
        const averageTotalTime = successfulUsers.reduce((sum, r) => sum + r.totalTime, 0) / successfulUsers.length;
        const averageSearchTime = successfulUsers.reduce((sum, r) => sum + r.averageSearchTime, 0) / successfulUsers.length;

        expect(averageTotalTime).toBeLessThan(60000); // Under 1 minute total
        expect(averageSearchTime).toBeLessThan(15000); // Under 15 seconds per search

        // Web Vitals should remain acceptable
        const averageLCP = successfulUsers.reduce((sum, r) => sum + r.webVitals.lcp, 0) / successfulUsers.length;
        expect(averageLCP).toBeLessThan(4000); // Under 4 seconds LCP under load

        console.log(`Load test results: ${userCount} users, avg total time: ${averageTotalTime.toFixed(0)}ms, avg search time: ${averageSearchTime.toFixed(0)}ms`);

      } finally {
        // Cleanup
        await Promise.all(contexts.map(context => context.close()));
      }
    });

    test('should handle burst traffic patterns', async ({ browser }) => {
      const burstSize = 5;
      const burstCount = 3;
      const burstInterval = 10000; // 10 seconds between bursts

      const allResults = [];

      for (let burst = 0; burst < burstCount; burst++) {
        console.log(`Starting burst ${burst + 1}/${burstCount}`);

        const contexts = [];
        const burstPromises = [];

        try {
          // Create burst of concurrent users
          for (let i = 0; i < burstSize; i++) {
            const context = await browser.newContext();
            contexts.push(context);

            const burstPromise = (async () => {
              const page = await context.newPage();
              const loginPage = new LoginPage(page);
              const searchPage = new SearchPage(page);

              const testUser = {
                username: `burst_${burst}_${i}_${Date.now()}`,
                email: `burst_${burst}_${i}_${Date.now()}@example.com`,
                password: 'BurstTest123!'
              };

              const startTime = Date.now();

              await loginPage.register(testUser);
              await loginPage.login(testUser.username, testUser.password);

              await searchPage.navigateToSearch();
              await searchPage.performAdvancedSearch({
                query: `burst_search_${burst}_${i}`,
                fileTypes: ['js'],
                searchType: 'exact'
              });

              await searchPage.waitForResults();

              const totalTime = Date.now() - startTime;

              return {
                burst,
                userId: i,
                totalTime,
                success: true
              };
            })();

            burstPromises.push(burstPromise);
          }

          const burstResults = await Promise.all(burstPromises);
          allResults.push(...burstResults);

          // All users in burst should succeed
          const successfulInBurst = burstResults.filter(r => r.success).length;
          expect(successfulInBurst).toBe(burstSize);

        } finally {
          await Promise.all(contexts.map(context => context.close()));
        }

        // Wait before next burst (except for last burst)
        if (burst < burstCount - 1) {
          await new Promise(resolve => setTimeout(resolve, burstInterval));
        }
      }

      // Analyze overall burst performance
      const averageTime = allResults.reduce((sum, r) => sum + r.totalTime, 0) / allResults.length;
      expect(averageTime).toBeLessThan(30000); // Under 30 seconds average

      console.log(`Burst test completed: ${allResults.length} total users, avg time: ${averageTime.toFixed(0)}ms`);
    });

    test('should maintain performance with sustained load', async ({ browser }) => {
      const duration = 60000; // 1 minute
      const userInterval = 2000; // New user every 2 seconds
      const maxConcurrentUsers = 15;

      const activeContexts = [];
      const results = [];
      let userCounter = 0;

      const startTime = Date.now();

      // Function to create a new user
      const createUser = async () => {
        if (activeContexts.length >= maxConcurrentUsers) {
          return; // Don't exceed max concurrent users
        }

        const context = await browser.newContext();
        activeContexts.push(context);

        const userPromise = (async () => {
          try {
            const page = await context.newPage();
            const loginPage = new LoginPage(page);
            const searchPage = new SearchPage(page);

            const testUser = {
              username: `sustained_${userCounter++}_${Date.now()}`,
              email: `sustained_${userCounter}_${Date.now()}@example.com`,
              password: 'SustainedTest123!'
            };

            const userStartTime = Date.now();

            await loginPage.register(testUser);
            await loginPage.login(testUser.username, testUser.password);

            await searchPage.navigateToSearch();
            await searchPage.performAdvancedSearch({
              query: `sustained_search_${userCounter}`,
              fileTypes: ['js'],
              searchType: 'exact'
            });

            await searchPage.waitForResults();

            const userTime = Date.now() - userStartTime;

            return {
              userId: userCounter,
              userTime,
              success: true
            };
          } catch (error) {
            return {
              userId: userCounter,
              error: error.message,
              success: false
            };
          } finally {
            // Remove context from active list
            const index = activeContexts.indexOf(context);
            if (index > -1) {
              activeContexts.splice(index, 1);
            }
            await context.close();
          }
        })();

        userPromise.then(result => results.push(result));
      };

      // Create users at intervals
      const userCreationInterval = setInterval(createUser, userInterval);

      // Stop creating users after duration
      setTimeout(() => {
        clearInterval(userCreationInterval);
      }, duration);

      // Wait for all users to complete (with additional buffer time)
      await new Promise(resolve => setTimeout(resolve, duration + 30000));

      // Cleanup any remaining contexts
      await Promise.all(activeContexts.map(context => context.close()));

      // Analyze sustained load results
      const successfulUsers = results.filter(r => r.success);
      const failedUsers = results.filter(r => !r.success);

      expect(successfulUsers.length).toBeGreaterThan(0);

      // Success rate should be high (at least 80%)
      const successRate = (successfulUsers.length / results.length) * 100;
      expect(successRate).toBeGreaterThan(80);

      // Average response time should be reasonable
      const averageTime = successfulUsers.reduce((sum, r) => sum + r.userTime, 0) / successfulUsers.length;
      expect(averageTime).toBeLessThan(45000); // Under 45 seconds under sustained load

      console.log(`Sustained load test: ${results.length} total users, ${successRate.toFixed(1)}% success rate, avg time: ${averageTime.toFixed(0)}ms`);
    });
  });

  test.describe('Resource Stress Tests @performance @stress @resources', () => {
    test('should handle high-frequency API requests', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const searchPage = new SearchPage(page);

      // Setup user
      const testUser = {
        username: `stress_api_${Date.now()}`,
        email: `stress_api_${Date.now()}@example.com`,
        password: 'StressApi123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Get auth token for direct API calls
      const authToken = await page.evaluate(() => localStorage.getItem('access_token'));

      // Make rapid API requests
      const requestCount = 50;
      const requestPromises = [];

      const startTime = Date.now();

      for (let i = 0; i < requestCount; i++) {
        const requestPromise = page.evaluate(async (token, index) => {
          const response = await fetch('/api/search/advanced', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              repo_path: '/test/repo',
              content_pattern: `stress_test_${index}`,
              file_extensions: ['js'],
              max_results: 10
            })
          });

          return {
            status: response.status,
            index,
            timestamp: Date.now()
          };
        }, authToken, i);

        requestPromises.push(requestPromise);
      }

      const results = await Promise.all(requestPromises);
      const endTime = Date.now();

      // Analyze API stress test results
      const successfulRequests = results.filter(r => r.status === 200);
      const totalTime = endTime - startTime;
      const requestsPerSecond = (requestCount / totalTime) * 1000;

      // Should handle most requests successfully
      expect(successfulRequests.length).toBeGreaterThan(requestCount * 0.8); // 80% success rate

      // Should maintain reasonable throughput
      expect(requestsPerSecond).toBeGreaterThan(5); // At least 5 requests per second

      console.log(`API stress test: ${successfulRequests.length}/${requestCount} successful, ${requestsPerSecond.toFixed(2)} req/sec`);
    });

    test('should handle memory-intensive operations', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const searchPage = new SearchPage(page);

      const testUser = {
        username: `memory_stress_${Date.now()}`,
        email: `memory_stress_${Date.now()}@example.com`,
        password: 'MemoryStress123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Monitor memory before stress test
      const memoryBefore = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      await searchPage.navigateToSearch();

      // Perform memory-intensive operations
      const operations = [
        { query: 'function', fileTypes: ['js', 'py', 'ts', 'jsx', 'tsx'] },
        { query: 'import', fileTypes: ['js', 'py', 'ts', 'jsx', 'tsx'] },
        { query: 'export', fileTypes: ['js', 'py', 'ts', 'jsx', 'tsx'] },
        { query: 'class', fileTypes: ['js', 'py', 'ts', 'jsx', 'tsx'] },
        { query: 'async', fileTypes: ['js', 'py', 'ts', 'jsx', 'tsx'] }
      ];

      for (const operation of operations) {
        await searchPage.performAdvancedSearch({
          query: operation.query,
          fileTypes: operation.fileTypes,
          searchType: 'fuzzy'
        });

        await searchPage.waitForResults();

        // Don't clear results to accumulate memory usage
      }

      // Monitor memory after stress test
      const memoryAfter = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      if (memoryBefore && memoryAfter) {
        const memoryIncrease = memoryAfter.used - memoryBefore.used;
        const memoryIncreasePercent = (memoryIncrease / memoryBefore.used) * 100;

        // Memory increase should be manageable
        expect(memoryIncreasePercent).toBeLessThan(300); // Less than 300% increase

        console.log(`Memory stress test: ${memoryIncreasePercent.toFixed(2)}% memory increase`);
      }

      // Application should still be responsive
      const isResponsive = await searchPage.isSearchFormVisible();
      expect(isResponsive).toBe(true);
    });

    test('should handle CPU-intensive operations', async ({ page }) => {
      const loginPage = new LoginPage(page);
      const searchPage = new SearchPage(page);

      const testUser = {
        username: `cpu_stress_${Date.now()}`,
        email: `cpu_stress_${Date.now()}@example.com`,
        password: 'CpuStress123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      await searchPage.navigateToSearch();

      // Create CPU stress in background
      await page.evaluate(() => {
        window.cpuStressTest = true;

        function cpuIntensiveTask() {
          if (!window.cpuStressTest) return;

          // CPU intensive calculation
          let result = 0;
          for (let i = 0; i < 100000; i++) {
            result += Math.random() * Math.random();
          }

          // Continue stress test
          setTimeout(cpuIntensiveTask, 10);
        }

        cpuIntensiveTask();
      });

      // Perform searches under CPU stress
      const searches = [
        'function async',
        'import export',
        'class extends'
      ];

      const searchTimes = [];

      for (const query of searches) {
        const startTime = Date.now();

        await searchPage.performAdvancedSearch({
          query: query,
          fileTypes: ['js'],
          searchType: 'fuzzy'
        });

        await searchPage.waitForResults();

        const searchTime = Date.now() - startTime;
        searchTimes.push(searchTime);
      }

      // Stop CPU stress test
      await page.evaluate(() => {
        window.cpuStressTest = false;
      });

      // Searches should still complete within reasonable time under CPU stress
      const averageSearchTime = searchTimes.reduce((a, b) => a + b, 0) / searchTimes.length;
      expect(averageSearchTime).toBeLessThan(30000); // Under 30 seconds under CPU stress

      console.log(`CPU stress test: avg search time ${averageSearchTime.toFixed(0)}ms under CPU load`);
    });
  });
});
