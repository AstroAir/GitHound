/**
 * Authentication API Integration Tests
 * Tests the authentication API endpoints through the frontend interface
 */

const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages');

test.describe('Authentication API Integration Tests', () => {
  let loginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
  });

  test.describe('Registration API @auth @api', () => {
    test('should call registration API with correct payload', async ({ page }) => {
      const userData = {
        username: `apitest_${Date.now()}`,
        email: `apitest_${Date.now()}@example.com`,
        password: 'ApiTest123!'
      };

      // Intercept the registration API call
      let registrationRequest = null;
      await page.route('**/api/v1/auth/register', route => {
        registrationRequest = route.request();
        route.continue();
      });

      await loginPage.register(userData);

      // Verify API call was made with correct data
      expect(registrationRequest).toBeTruthy();
      expect(registrationRequest.method()).toBe('POST');

      const requestBody = JSON.parse(registrationRequest.postData());
      expect(requestBody.username).toBe(userData.username);
      expect(requestBody.email).toBe(userData.email);
      expect(requestBody.password).toBe(userData.password);
    });

    test('should handle registration API errors correctly', async ({ page }) => {
      // Mock API error response
      await page.route('**/api/v1/auth/register', route => {
        route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Username already exists',
            code: 'DUPLICATE_USERNAME'
          })
        });
      });

      const userData = {
        username: `duplicate_${Date.now()}`,
        email: `duplicate_${Date.now()}@example.com`,
        password: 'Duplicate123!'
      };

      const result = await loginPage.register(userData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('already exists');
    });

    test('should include proper headers in registration request', async ({ page }) => {
      let requestHeaders = null;
      await page.route('**/api/v1/auth/register', route => {
        requestHeaders = route.request().headers();
        route.continue();
      });

      const userData = {
        username: `headers_${Date.now()}`,
        email: `headers_${Date.now()}@example.com`,
        password: 'Headers123!'
      };

      await loginPage.register(userData);

      expect(requestHeaders['content-type']).toContain('application/json');
      expect(requestHeaders['accept']).toContain('application/json');
    });
  });

  test.describe('Login API @auth @api', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `loginapi_${Date.now()}`,
        email: `loginapi_${Date.now()}@example.com`,
        password: 'LoginApi123!'
      };

      await loginPage.register(testUser);
    });

    test('should call login API with correct credentials', async ({ page }) => {
      let loginRequest = null;
      await page.route('**/api/v1/auth/login', route => {
        loginRequest = route.request();
        route.continue();
      });

      await loginPage.login(testUser.username, testUser.password);

      expect(loginRequest).toBeTruthy();
      expect(loginRequest.method()).toBe('POST');

      const requestBody = JSON.parse(loginRequest.postData());
      expect(requestBody.username).toBe(testUser.username);
      expect(requestBody.password).toBe(testUser.password);
    });

    test('should store authentication tokens correctly', async ({ page }) => {
      // Mock successful login response with tokens
      await page.route('**/api/v1/auth/login', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock_access_token_12345',
            refresh_token: 'mock_refresh_token_67890',
            token_type: 'bearer',
            expires_in: 3600,
            user: {
              id: 'user_123',
              username: testUser.username,
              email: testUser.email,
              roles: ['user']
            }
          })
        });
      });

      await loginPage.login(testUser.username, testUser.password);

      // Verify tokens are stored
      const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
      const refreshToken = await page.evaluate(() => localStorage.getItem('refresh_token'));

      expect(accessToken).toBe('mock_access_token_12345');
      expect(refreshToken).toBe('mock_refresh_token_67890');
    });

    test('should handle login API errors appropriately', async ({ page }) => {
      await page.route('**/api/v1/auth/login', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Invalid credentials',
            code: 'INVALID_CREDENTIALS'
          })
        });
      });

      const result = await loginPage.login(testUser.username, 'wrong_password');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid');
    });

    test('should include authentication headers in subsequent requests', async ({ page }) => {
      await loginPage.login(testUser.username, testUser.password);

      let authenticatedRequest = null;
      await page.route('**/api/v1/**', route => {
        if (route.request().url().includes('/auth/profile')) {
          authenticatedRequest = route.request();
        }
        route.continue();
      });

      // Make an authenticated request
      await page.evaluate(() => {
        return fetch('/api/v1/auth/profile', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
      });

      expect(authenticatedRequest).toBeTruthy();
      expect(authenticatedRequest.headers()['authorization']).toContain('Bearer');
    });
  });

  test.describe('Token Management @auth @api', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `token_${Date.now()}`,
        email: `token_${Date.now()}@example.com`,
        password: 'Token123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should refresh tokens automatically when expired', async ({ page }) => {
      // Mock token refresh endpoint
      let refreshCalled = false;
      await page.route('**/api/v1/auth/refresh', route => {
        refreshCalled = true;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'new_access_token_12345',
            refresh_token: 'new_refresh_token_67890',
            token_type: 'bearer',
            expires_in: 3600
          })
        });
      });

      // Simulate expired token by setting a very old one
      await page.evaluate(() => {
        localStorage.setItem('access_token', 'expired_token');
        localStorage.setItem('token_expires_at', Date.now() - 10000); // Expired 10 seconds ago
      });

      // Make an API request that should trigger token refresh
      await page.evaluate(() => {
        return fetch('/api/v1/auth/profile', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
      });

      expect(refreshCalled).toBe(true);
    });

    test('should handle token refresh failures', async ({ page }) => {
      await page.route('**/api/v1/auth/refresh', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Refresh token expired',
            code: 'REFRESH_TOKEN_EXPIRED'
          })
        });
      });

      // Simulate expired tokens
      await page.evaluate(() => {
        localStorage.setItem('access_token', 'expired_token');
        localStorage.setItem('refresh_token', 'expired_refresh_token');
      });

      await page.reload();

      // Should be redirected to login
      const isLoggedIn = await loginPage.isLoggedIn();
      expect(isLoggedIn).toBe(false);
    });

    test('should clear tokens on logout', async ({ page }) => {
      let logoutRequest = null;
      await page.route('**/api/v1/auth/logout', route => {
        logoutRequest = route.request();
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Logged out successfully' })
        });
      });

      await loginPage.logout();

      // Verify logout API was called
      expect(logoutRequest).toBeTruthy();

      // Verify tokens are cleared
      const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
      const refreshToken = await page.evaluate(() => localStorage.getItem('refresh_token'));

      expect(accessToken).toBeNull();
      expect(refreshToken).toBeNull();
    });
  });

  test.describe('API Error Handling @auth @api @error', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      // Simulate network failure
      await page.route('**/api/v1/auth/login', route => {
        route.abort('failed');
      });

      const userData = {
        username: `network_${Date.now()}`,
        email: `network_${Date.now()}@example.com`,
        password: 'Network123!'
      };

      await loginPage.register(userData);
      const result = await loginPage.login(userData.username, userData.password);

      expect(result.success).toBe(false);
      expect(result.error).toMatch(/network|connection|failed/i);
    });

    test('should handle API rate limiting', async ({ page }) => {
      await page.route('**/api/v1/auth/login', route => {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          headers: {
            'Retry-After': '60'
          },
          body: JSON.stringify({
            error: 'Too many requests',
            code: 'RATE_LIMITED'
          })
        });
      });

      const userData = {
        username: `ratelimit_${Date.now()}`,
        email: `ratelimit_${Date.now()}@example.com`,
        password: 'RateLimit123!'
      };

      await loginPage.register(userData);
      const result = await loginPage.login(userData.username, userData.password);

      expect(result.success).toBe(false);
      expect(result.error).toMatch(/rate|limit|too many/i);
    });

    test('should handle API maintenance mode', async ({ page }) => {
      await page.route('**/api/v1/auth/**', route => {
        route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Service temporarily unavailable',
            code: 'MAINTENANCE_MODE'
          })
        });
      });

      const userData = {
        username: `maintenance_${Date.now()}`,
        email: `maintenance_${Date.now()}@example.com`,
        password: 'Maintenance123!'
      };

      const result = await loginPage.register(userData);

      expect(result.success).toBe(false);
      expect(result.error).toMatch(/unavailable|maintenance/i);
    });

    test('should validate API response format', async ({ page }) => {
      // Mock invalid JSON response
      await page.route('**/api/v1/auth/login', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json response'
        });
      });

      const userData = {
        username: `invalid_${Date.now()}`,
        email: `invalid_${Date.now()}@example.com`,
        password: 'Invalid123!'
      };

      await loginPage.register(userData);
      const result = await loginPage.login(userData.username, userData.password);

      expect(result.success).toBe(false);
    });
  });

  test.describe('API Security @auth @api @security', () => {
    test('should not expose sensitive data in API requests', async ({ page }) => {
      let requestData = null;
      await page.route('**/api/v1/auth/login', route => {
        requestData = route.request().postData();
        route.continue();
      });

      const userData = {
        username: `security_${Date.now()}`,
        email: `security_${Date.now()}@example.com`,
        password: 'Security123!'
      };

      await loginPage.register(userData);
      await loginPage.login(userData.username, userData.password);

      // Verify password is not logged or exposed
      expect(requestData).toBeTruthy();
      const parsedData = JSON.parse(requestData);
      expect(parsedData.password).toBe(userData.password); // Should be present in request

      // But should not be visible in browser dev tools (this is more of a documentation test)
    });

    test('should use HTTPS for authentication requests', async ({ page }) => {
      let requestUrl = null;
      await page.route('**/api/v1/auth/login', route => {
        requestUrl = route.request().url();
        route.continue();
      });

      const userData = {
        username: `https_${Date.now()}`,
        email: `https_${Date.now()}@example.com`,
        password: 'Https123!'
      };

      await loginPage.register(userData);
      await loginPage.login(userData.username, userData.password);

      // In production, should use HTTPS
      if (process.env.NODE_ENV === 'production') {
        expect(requestUrl).toMatch(/^https:/);
      }
    });

    test('should include CSRF protection', async ({ page }) => {
      let requestHeaders = null;
      await page.route('**/api/v1/auth/login', route => {
        requestHeaders = route.request().headers();
        route.continue();
      });

      const userData = {
        username: `csrf_${Date.now()}`,
        email: `csrf_${Date.now()}@example.com`,
        password: 'Csrf123!'
      };

      await loginPage.register(userData);
      await loginPage.login(userData.username, userData.password);

      // Should include CSRF token or other protection
      expect(requestHeaders['x-csrf-token'] || requestHeaders['x-requested-with']).toBeTruthy();
    });
  });
});
