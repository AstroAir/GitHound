/**
 * Network Error Handling Tests
 * Tests application behavior during network failures, timeouts, and connectivity issues
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('Network Error Handling Tests', () => {
  let searchPage;
  let loginPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);

    // Setup authenticated user
    const testUser = {
      username: `network_error_${Date.now()}`,
      email: `network_error_${Date.now()}@example.com`,
      password: 'NetworkError123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
  });

  test.describe('Connection Failures @error @network @connection', () => {
    test('should handle complete network failure gracefully', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Simulate complete network failure
      await page.route('**/*', route => {
        route.abort('failed');
      });

      // Attempt to perform search
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show appropriate error message
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/network|connection|offline|failed/i);

      // Should provide retry option
      const retryButton = page.locator('[data-testid="retry-button"]');
      if (await retryButton.count() > 0) {
        await expect(retryButton).toBeVisible();
      }

      // Application should remain functional for offline features
      const searchForm = page.locator('[data-testid="search-form"]');
      await expect(searchForm).toBeVisible();
    });

    test('should handle intermittent connection issues', async ({ page }) => {
      await searchPage.navigateToSearch();

      let requestCount = 0;

      // Simulate intermittent failures (fail every other request)
      await page.route('**/api/**', route => {
        requestCount++;
        if (requestCount % 2 === 0) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      // Attempt multiple searches
      const searches = ['function', 'import', 'class'];
      
      for (const query of searches) {
        await page.fill('[data-testid="search-input"]', query);
        await page.click('[data-testid="search-button"]');

        // Wait for either success or error
        await Promise.race([
          page.waitForSelector('[data-testid="search-results"]', { timeout: 5000 }).catch(() => null),
          page.waitForSelector('[data-testid="error-message"]', { timeout: 5000 }).catch(() => null)
        ]);

        // If error occurred, should have retry mechanism
        const errorMessage = page.locator('[data-testid="error-message"]');
        if (await errorMessage.isVisible()) {
          const retryButton = page.locator('[data-testid="retry-button"]');
          if (await retryButton.count() > 0) {
            await retryButton.click();
            
            // Retry should eventually succeed
            await page.waitForSelector('[data-testid="search-results"], [data-testid="error-message"]', { timeout: 10000 });
          }
        }
      }
    });

    test('should handle slow network conditions', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Simulate very slow network
      await page.route('**/api/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second delay
        route.continue();
      });

      const startTime = Date.now();

      // Perform search
      await page.fill('[data-testid="search-input"]', 'function');
      await page.click('[data-testid="search-button"]');

      // Should show loading indicator
      const loadingIndicator = page.locator('[data-testid="loading-spinner"], [data-testid="loading-message"]');
      await expect(loadingIndicator).toBeVisible();

      // Should eventually complete or timeout gracefully
      await Promise.race([
        page.waitForSelector('[data-testid="search-results"]', { timeout: 15000 }),
        page.waitForSelector('[data-testid="timeout-error"]', { timeout: 15000 })
      ]);

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Should handle the delay appropriately
      expect(duration).toBeGreaterThan(4000); // Should wait for slow response
      expect(duration).toBeLessThan(20000); // But should timeout eventually
    });

    test('should handle DNS resolution failures', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Simulate DNS failure
      await page.route('**/api/**', route => {
        route.abort('namenotresolved');
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show DNS-specific error message
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/connection|server|network|resolve/i);
    });
  });

  test.describe('HTTP Error Responses @error @network @http', () => {
    test('should handle 500 Internal Server Error', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock 500 error
      await page.route('**/api/search/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Internal Server Error',
            message: 'Something went wrong on our end'
          })
        });
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show server error message
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible();

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/server|error|try again/i);

      // Should provide retry option
      const retryButton = page.locator('[data-testid="retry-button"]');
      if (await retryButton.count() > 0) {
        await expect(retryButton).toBeVisible();
      }
    });

    test('should handle 404 Not Found errors', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock 404 error
      await page.route('**/api/search/**', route => {
        route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Not Found',
            message: 'The requested resource was not found'
          })
        });
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show not found error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible();

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/not found|unavailable/i);
    });

    test('should handle 401 Unauthorized errors', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock 401 error
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Unauthorized',
            message: 'Authentication required'
          })
        });
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should handle authentication error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible();

      // Should redirect to login or show login prompt
      await Promise.race([
        page.waitForURL('**/login', { timeout: 5000 }),
        page.waitForSelector('[data-testid="login-prompt"]', { timeout: 5000 })
      ]);
    });

    test('should handle 403 Forbidden errors', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock 403 error
      await page.route('**/api/search/**', route => {
        route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Forbidden',
            message: 'You do not have permission to access this resource'
          })
        });
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show permission error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible();

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/permission|forbidden|access/i);
    });

    test('should handle 429 Rate Limit errors', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock 429 error
      await page.route('**/api/search/**', route => {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          headers: {
            'Retry-After': '60'
          },
          body: JSON.stringify({
            error: 'Too Many Requests',
            message: 'Rate limit exceeded. Please try again later.'
          })
        });
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show rate limit error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible();

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/rate limit|too many|try again later/i);

      // Should show retry after information
      expect(errorText).toMatch(/60|minute|later/i);
    });
  });

  test.describe('Request Timeout Handling @error @network @timeout', () => {
    test('should handle request timeouts gracefully', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock timeout by never responding
      await page.route('**/api/search/**', route => {
        // Never call route.continue() or route.fulfill() to simulate timeout
      });

      const startTime = Date.now();

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show timeout error within reasonable time
      const errorMessage = page.locator('[data-testid="error-message"], [data-testid="timeout-error"]');
      await expect(errorMessage).toBeVisible({ timeout: 30000 });

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Should timeout within reasonable time (not hang indefinitely)
      expect(duration).toBeLessThan(35000); // 35 seconds max

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/timeout|slow|try again/i);
    });

    test('should handle partial response timeouts', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Mock partial response (start sending but never complete)
      await page.route('**/api/search/**', async route => {
        const response = await route.fetch();
        // Start the response but don't complete it
        route.fulfill({
          status: 200,
          headers: response.headers(),
          body: '{"partial": "response"' // Incomplete JSON
        });
      });

      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should handle incomplete response
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 15000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/error|failed|try again/i);
    });
  });

  test.describe('Offline Behavior @error @network @offline', () => {
    test('should detect offline state', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Simulate going offline
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: false
        });
        window.dispatchEvent(new Event('offline'));
      });

      // Should show offline indicator
      const offlineIndicator = page.locator('[data-testid="offline-indicator"], [data-testid="connection-status"]');
      if (await offlineIndicator.count() > 0) {
        await expect(offlineIndicator).toBeVisible();
      }

      // Attempt search while offline
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show offline error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible();

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/offline|connection|internet/i);
    });

    test('should handle reconnection', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Start offline
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: false
        });
        window.dispatchEvent(new Event('offline'));
      });

      // Attempt search while offline
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Should show offline error
      const errorMessage = page.locator('[data-testid="error-message"]');
      await expect(errorMessage).toBeVisible();

      // Simulate coming back online
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: true
        });
        window.dispatchEvent(new Event('online'));
      });

      // Should detect reconnection
      const reconnectMessage = page.locator('[data-testid="reconnect-message"], [data-testid="online-indicator"]');
      if (await reconnectMessage.count() > 0) {
        await expect(reconnectMessage).toBeVisible();
      }

      // Should be able to retry search
      const retryButton = page.locator('[data-testid="retry-button"]');
      if (await retryButton.count() > 0) {
        await retryButton.click();
        
        // Should now succeed
        await page.waitForSelector('[data-testid="search-results"], [data-testid="error-message"]', { timeout: 10000 });
      }
    });

    test('should cache data for offline use', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Perform successful search first
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Go offline
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: false
        });
        window.dispatchEvent(new Event('offline'));
      });

      // Block all network requests
      await page.route('**/*', route => {
        route.abort('failed');
      });

      // Try to access cached data
      await page.reload();

      // Should show some cached content or appropriate offline message
      const content = page.locator('[data-testid="cached-content"], [data-testid="offline-message"]');
      await expect(content).toBeVisible({ timeout: 10000 });
    });
  });
});
