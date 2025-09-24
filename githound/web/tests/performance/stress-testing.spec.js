/**
 * Stress Testing Suite
 * Tests system behavior under extreme load conditions and stress scenarios
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('Stress Testing Suite', () => {
  test.describe('High Concurrency Stress Tests @performance @stress @high-load', () => {
    test('should handle 25 concurrent users with sustained load', async ({ browser }) => {
      const userCount = 25;
      const testDuration = 60000; // 1 minute
      const contexts = [];
      const userPromises = [];
      const results = [];

      try {
        // Create concurrent user sessions
        for (let i = 0; i < userCount; i++) {
          const context = await browser.newContext();
          contexts.push(context);

          const userPromise = (async () => {
            const page = await context.newPage();
            const loginPage = new LoginPage(page);
            const searchPage = new SearchPage(page);

            const userResults = {
              userId: i,
              operations: 0,
              errors: 0,
              totalTime: 0,
              averageResponseTime: 0
            };

            try {
              // Setup user
              const testUser = {
                username: `stress_user_${Date.now()}_${i}`,
                email: `stress_user_${Date.now()}_${i}@example.com`,
                password: 'StressTest123!'
              };

              await loginPage.register(testUser);
              await loginPage.login(testUser.username, testUser.password);

              const startTime = Date.now();

              // Sustained load for test duration
              while (Date.now() - startTime < testDuration) {
                try {
                  const operationStart = Date.now();

                  // Perform various operations
                  await searchPage.navigateToSearch();

                  await page.fill('[data-testid="repo-path-input"]', `/stress/repo/${i}`);
                  await page.fill('[data-testid="search-query-input"]', `stress_query_${userResults.operations}`);
                  await page.click('[data-testid="submit-search"]');

                  // Wait for search to start
                  await page.waitForSelector('[data-testid="progress-message"]', {
                    state: 'visible',
                    timeout: 5000
                  });

                  const operationTime = Date.now() - operationStart;
                  userResults.operations++;
                  userResults.totalTime += operationTime;

                  // Brief pause between operations
                  await page.waitForTimeout(100);

                } catch (error) {
                  userResults.errors++;
                }
              }

              userResults.averageResponseTime = userResults.totalTime / userResults.operations;

            } catch (error) {
              userResults.errors++;
            }

            return userResults;
          })();

          userPromises.push(userPromise);
        }

        // Wait for all users to complete
        const allResults = await Promise.all(userPromises);

        // Analyze results
        const totalOperations = allResults.reduce((sum, result) => sum + result.operations, 0);
        const totalErrors = allResults.reduce((sum, result) => sum + result.errors, 0);
        const averageResponseTime = allResults.reduce((sum, result) => sum + result.averageResponseTime, 0) / userCount;

        // Assertions
        expect(totalOperations).toBeGreaterThan(userCount * 5); // Each user should complete at least 5 operations
        expect(totalErrors / totalOperations).toBeLessThan(0.05); // Error rate should be less than 5%
        expect(averageResponseTime).toBeLessThan(3000); // Average response time should be reasonable

      } finally {
        // Cleanup contexts
        for (const context of contexts) {
          await context.close();
        }
      }
    });

    test('should handle rapid authentication requests', async ({ browser }) => {
      const concurrentLogins = 20;
      const contexts = [];
      const loginPromises = [];

      try {
        for (let i = 0; i < concurrentLogins; i++) {
          const context = await browser.newContext();
          contexts.push(context);

          const loginPromise = (async () => {
            const page = await context.newPage();
            const loginPage = new LoginPage(page);

            const testUser = {
              username: `rapid_auth_${Date.now()}_${i}`,
              email: `rapid_auth_${Date.now()}_${i}@example.com`,
              password: 'RapidAuth123!'
            };

            const startTime = Date.now();

            // Register and login rapidly
            await loginPage.register(testUser);
            await loginPage.login(testUser.username, testUser.password);

            const authTime = Date.now() - startTime;

            // Verify authentication succeeded
            await page.waitForSelector('[data-testid="user-menu"]', { state: 'visible' });

            return { userId: i, authTime };
          })();

          loginPromises.push(loginPromise);
        }

        const authResults = await Promise.all(loginPromises);

        // All authentications should succeed
        expect(authResults.length).toBe(concurrentLogins);

        // Average auth time should be reasonable
        const averageAuthTime = authResults.reduce((sum, result) => sum + result.authTime, 0) / concurrentLogins;
        expect(averageAuthTime).toBeLessThan(5000);

      } finally {
        for (const context of contexts) {
          await context.close();
        }
      }
    });
  });

  test.describe('Memory Stress Tests @performance @stress @memory', () => {
    test('should handle memory-intensive operations', async ({ page }) => {
      const testUser = {
        username: `memory_stress_${Date.now()}`,
        email: `memory_stress_${Date.now()}@example.com`,
        password: 'MemoryStress123!'
      };

      const loginPage = new LoginPage(page);
      const searchPage = new SearchPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Get initial memory
      const initialMemory = await page.evaluate(() => {
        return performance.memory ? performance.memory.usedJSHeapSize : 0;
      });

      // Perform memory-intensive operations
      for (let i = 0; i < 50; i++) {
        await searchPage.navigateToSearch();

        // Create large DOM elements
        await page.evaluate((iteration) => {
          const container = document.querySelector('[data-testid="results-container"]');
          if (container) {
            for (let j = 0; j < 100; j++) {
              const div = document.createElement('div');
              div.innerHTML = `<p>Large content block ${iteration}-${j} with lots of text content that takes up memory space</p>`;
              container.appendChild(div);
            }
          }
        }, i);

        // Navigate away to test cleanup
        await page.goto('/');

        // Force garbage collection if available
        await page.evaluate(() => {
          if (window.gc) {
            window.gc();
          }
        });
      }

      // Check final memory
      const finalMemory = await page.evaluate(() => {
        return performance.memory ? performance.memory.usedJSHeapSize : 0;
      });

      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = ((finalMemory - initialMemory) / initialMemory) * 100;
        expect(memoryIncrease).toBeLessThan(200); // Memory should not increase by more than 200%
      }
    });
  });

  test.describe('Network Stress Tests @performance @stress @network', () => {
    test('should handle rapid API requests', async ({ page }) => {
      const testUser = {
        username: `api_stress_${Date.now()}`,
        email: `api_stress_${Date.now()}@example.com`,
        password: 'ApiStress123!'
      };

      const loginPage = new LoginPage(page);
      const searchPage = new SearchPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      await searchPage.navigateToSearch();

      // Track API requests
      const apiRequests = [];
      page.on('request', request => {
        if (request.url().includes('/api/')) {
          apiRequests.push({
            url: request.url(),
            timestamp: Date.now()
          });
        }
      });

      // Make rapid API requests
      const rapidRequests = [];
      for (let i = 0; i < 20; i++) {
        const requestPromise = (async () => {
          try {
            await page.fill('[data-testid="search-query-input"]', `rapid_query_${i}`);
            await page.click('[data-testid="submit-search"]');
            await page.waitForTimeout(100); // Brief pause
            return { success: true, iteration: i };
          } catch (error) {
            return { success: false, iteration: i, error: error.message };
          }
        })();

        rapidRequests.push(requestPromise);
      }

      const requestResults = await Promise.all(rapidRequests);

      // Most requests should succeed
      const successfulRequests = requestResults.filter(result => result.success);
      expect(successfulRequests.length).toBeGreaterThan(15); // At least 75% success rate

      // Should have made API requests
      expect(apiRequests.length).toBeGreaterThan(10);
    });
  });

  test.describe('UI Stress Tests @performance @stress @ui', () => {
    test('should handle rapid UI interactions', async ({ page }) => {
      const testUser = {
        username: `ui_stress_${Date.now()}`,
        email: `ui_stress_${Date.now()}@example.com`,
        password: 'UiStress123!'
      };

      const loginPage = new LoginPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Rapid UI interactions
      for (let i = 0; i < 50; i++) {
        try {
          // Rapid navigation
          await page.goto('/search');
          await page.goto('/');

          // Rapid modal opening/closing
          await page.click('[data-testid="login-button"]');
          await page.keyboard.press('Escape');

          // Rapid form interactions
          await page.fill('[data-testid="search-query-input"]', `stress_${i}`);
          await page.keyboard.press('Backspace');

        } catch (error) {
          // Some interactions may fail under stress, but most should work
        }
      }

      // UI should still be responsive
      await page.click('[data-testid="user-menu"]');
      await expect(page.locator('[data-testid="profile-link"]')).toBeVisible();
    });
  });
});
