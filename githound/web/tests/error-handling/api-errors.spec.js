/**
 * API Error Handling Tests
 * Tests application behavior during API failures, invalid responses, and server errors
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('API Error Handling Tests', () => {
  let searchPage;
  let loginPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
  });

  test.describe('Authentication API Errors @error @api @auth', () => {
    test('should handle login API 500 errors', async ({ page }) => {
      // Mock 500 error for login API
      await page.route('**/api/v1/auth/login', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });

      await page.goto('/');
      await page.click('[data-testid="login-button"]');

      await page.fill('[data-testid="username-input"]', 'testuser');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="submit-login"]');

      // Should show error message
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 5000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/server error|failed|error/i);
    });

    test('should handle registration API 400 errors', async ({ page }) => {
      // Mock 400 error for registration API
      await page.route('**/api/v1/auth/register', route => {
        route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Validation failed',
            details: { username: 'Username already exists' }
          })
        });
      });

      await page.goto('/');
      await page.click('[data-testid="register-button"]');

      await page.fill('[data-testid="register-username"]', 'existinguser');
      await page.fill('[data-testid="register-email"]', 'test@example.com');
      await page.fill('[data-testid="register-password"]', 'password123');
      await page.fill('[data-testid="register-confirm-password"]', 'password123');
      await page.click('[data-testid="submit-registration"]');

      // Should show validation error
      const errorMessage = page.locator('[data-testid="username-error"]');
      await expect(errorMessage).toBeVisible({ timeout: 5000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/already exists|validation/i);
    });

    test('should handle authentication token expiry', async ({ page }) => {
      // Setup authenticated user first
      const testUser = {
        username: `token_expiry_${Date.now()}`,
        email: `token_expiry_${Date.now()}@example.com`,
        password: 'TokenExpiry123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock 401 error for subsequent API calls
      await page.route('**/api/v1/**', route => {
        if (route.request().url().includes('/auth/')) {
          route.continue();
        } else {
          route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Token expired' })
          });
        }
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should redirect to login or show auth error
      await expect(page.locator('[data-testid="login-button"]')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Search API Errors @error @api @search', () => {
    test('should handle search API timeout', async ({ page }) => {
      const testUser = {
        username: `search_timeout_${Date.now()}`,
        email: `search_timeout_${Date.now()}@example.com`,
        password: 'SearchTimeout123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock slow/timeout response
      await page.route('**/api/v1/search', route => {
        // Don't respond to simulate timeout
        setTimeout(() => {
          route.fulfill({
            status: 408,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Request timeout' })
          });
        }, 30000);
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should show timeout error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 35000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/timeout|slow|failed/i);
    });

    test('should handle malformed search API response', async ({ page }) => {
      const testUser = {
        username: `malformed_response_${Date.now()}`,
        email: `malformed_response_${Date.now()}@example.com`,
        password: 'MalformedResponse123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock malformed JSON response
      await page.route('**/api/v1/search', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json response {'
        });
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should handle parsing error gracefully
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/error|failed|invalid/i);
    });

    test('should handle search API rate limiting', async ({ page }) => {
      const testUser = {
        username: `rate_limit_${Date.now()}`,
        email: `rate_limit_${Date.now()}@example.com`,
        password: 'RateLimit123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock rate limit response
      await page.route('**/api/v1/search', route => {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          headers: {
            'Retry-After': '60'
          },
          body: JSON.stringify({
            error: 'Rate limit exceeded',
            retry_after: 60
          })
        });
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should show rate limit error with retry information
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 5000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/rate limit|too many|retry/i);
    });
  });

  test.describe('Export API Errors @error @api @export', () => {
    test('should handle export API failures', async ({ page }) => {
      const testUser = {
        username: `export_error_${Date.now()}`,
        email: `export_error_${Date.now()}@example.com`,
        password: 'ExportError123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock export API error
      await page.route('**/api/v1/export/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Export generation failed' })
        });
      });

      await page.goto('/');

      // Try to export (assuming there are results)
      await page.click('[data-testid="export-button"]');
      await page.waitForSelector('[data-testid="export-modal"]', { state: 'visible' });

      await page.selectOption('[data-testid="export-format"]', 'json');
      await page.click('[data-testid="confirm-export"]');

      // Should show export error
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });

      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/export.*failed|generation.*error/i);
    });
  });

  test.describe('WebSocket Errors @error @websocket', () => {
    test('should handle WebSocket connection failures', async ({ page }) => {
      const testUser = {
        username: `ws_error_${Date.now()}`,
        email: `ws_error_${Date.now()}@example.com`,
        password: 'WsError123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Block WebSocket connections
      await page.route('**/ws/**', route => {
        route.abort('failed');
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should fall back to polling or show connection error
      const connectionStatus = page.locator('[data-testid="connection-status"]');
      if (await connectionStatus.isVisible()) {
        const statusText = await connectionStatus.textContent();
        expect(statusText).toMatch(/disconnected|offline|error/i);
      }

      // Search should still work via polling
      const progressMessage = page.locator('[data-testid="progress-message"]');
      await expect(progressMessage).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Edge Case Errors @error @edge-cases', () => {
    test('should handle empty API responses', async ({ page }) => {
      const testUser = {
        username: `empty_response_${Date.now()}`,
        email: `empty_response_${Date.now()}@example.com`,
        password: 'EmptyResponse123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock empty response
      await page.route('**/api/v1/search', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: ''
        });
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should handle empty response gracefully
      const resultsContainer = page.locator('[data-testid="results-container"]');
      await expect(resultsContainer).toBeVisible({ timeout: 10000 });
    });

    test('should handle very large error responses', async ({ page }) => {
      const testUser = {
        username: `large_error_${Date.now()}`,
        email: `large_error_${Date.now()}@example.com`,
        password: 'LargeError123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock very large error response
      const largeErrorMessage = 'Error: ' + 'x'.repeat(10000);
      await page.route('**/api/v1/search', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: largeErrorMessage })
        });
      });

      await searchPage.navigateToSearch();

      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');

      // Should truncate or handle large error message appropriately
      const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessage).toBeVisible({ timeout: 5000 });

      const errorText = await errorMessage.textContent();
      expect(errorText.length).toBeLessThan(1000); // Should be truncated
    });

    test('should handle concurrent error scenarios', async ({ page }) => {
      const testUser = {
        username: `concurrent_error_${Date.now()}`,
        email: `concurrent_error_${Date.now()}@example.com`,
        password: 'ConcurrentError123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      // Mock different errors for different endpoints
      await page.route('**/api/v1/search', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Search service unavailable' })
        });
      });

      await page.route('**/api/v1/export/**', route => {
        route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Export service unavailable' })
        });
      });

      await searchPage.navigateToSearch();

      // Trigger multiple concurrent errors
      const searchPromise = (async () => {
        await page.fill('[data-testid="repo-path-input"]', '/test/repo');
        await page.fill('[data-testid="search-query-input"]', 'function');
        await page.click('[data-testid="submit-search"]');
      })();

      const exportPromise = (async () => {
        await page.click('[data-testid="export-button"]');
        await page.waitForSelector('[data-testid="export-modal"]', { state: 'visible' });
        await page.click('[data-testid="confirm-export"]');
      })();

      await Promise.all([searchPromise, exportPromise]);

      // Should handle multiple errors gracefully
      const errorMessages = page.locator('[data-testid="error-message"], [role="alert"]');
      await expect(errorMessages.first()).toBeVisible({ timeout: 10000 });
    });
  });
});
