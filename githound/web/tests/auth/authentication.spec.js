/**
 * Comprehensive Authentication Tests for GitHound Web Interface
 * Tests authentication flows, security scenarios, and edge cases
 */

const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages');

test.describe('Authentication Flow Tests', () => {
  let loginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
  });

  test.describe('User Registration @auth @smoke', () => {
    test('should successfully register a new user', async () => {
      const userData = {
        username: `testuser_${Date.now()}`,
        email: `test_${Date.now()}@example.com`,
        password: 'SecurePassword123!'
      };

      const result = await loginPage.register(userData);
      
      expect(result.success).toBe(true);
    });

    test('should show validation errors for empty registration form', async () => {
      const result = await loginPage.verifyRegistrationFormValidation();
      
      expect(result.hasUsernameError).toBe(true);
      expect(result.hasEmailError).toBe(true);
      expect(result.hasPasswordError).toBe(true);
    });

    test('should show error for password mismatch', async () => {
      const userData = {
        username: `testuser_${Date.now()}`,
        email: `test_${Date.now()}@example.com`,
        password: 'SecurePassword123!'
      };

      const result = await loginPage.testPasswordMismatchValidation(userData);
      
      expect(result.hasPasswordMismatchError).toBe(true);
      expect(result.error).toContain('password');
    });

    test('should reject duplicate username registration', async ({ page }) => {
      const userData = {
        username: `duplicate_${Date.now()}`,
        email: `test1_${Date.now()}@example.com`,
        password: 'SecurePassword123!'
      };

      // Register first user
      await loginPage.register(userData);

      // Try to register with same username but different email
      const duplicateData = {
        ...userData,
        email: `test2_${Date.now()}@example.com`
      };

      const result = await loginPage.register(duplicateData);
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('already exists');
    });

    test('should validate email format', async () => {
      const userData = {
        username: `testuser_${Date.now()}`,
        email: 'invalid-email-format',
        password: 'SecurePassword123!'
      };

      const result = await loginPage.register(userData);
      
      expect(result.success).toBe(false);
    });

    test('should enforce password strength requirements', async () => {
      const weakPasswords = [
        '123',           // Too short
        'password',      // No numbers/special chars
        '12345678',      // No letters
        'Password',      // No numbers/special chars
      ];

      for (const weakPassword of weakPasswords) {
        const userData = {
          username: `testuser_${Date.now()}_${Math.random()}`,
          email: `test_${Date.now()}_${Math.random()}@example.com`,
          password: weakPassword
        };

        const result = await loginPage.register(userData);
        expect(result.success).toBe(false);
      }
    });
  });

  test.describe('User Login @auth @smoke', () => {
    let testUser;

    test.beforeEach(async () => {
      // Create a test user for login tests
      testUser = {
        username: `logintest_${Date.now()}`,
        email: `logintest_${Date.now()}@example.com`,
        password: 'LoginTest123!'
      };

      await loginPage.register(testUser);
    });

    test('should successfully login with valid credentials', async () => {
      const result = await loginPage.login(testUser.username, testUser.password);
      
      expect(result.success).toBe(true);
      
      const isLoggedIn = await loginPage.isLoggedIn();
      expect(isLoggedIn).toBe(true);
      
      const username = await loginPage.getLoggedInUsername();
      expect(username).toContain(testUser.username);
    });

    test('should reject invalid username', async () => {
      const result = await loginPage.login('nonexistent_user', testUser.password);
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid username or password');
    });

    test('should reject invalid password', async () => {
      const result = await loginPage.login(testUser.username, 'wrong_password');
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid username or password');
    });

    test('should show validation errors for empty login form', async () => {
      const result = await loginPage.verifyLoginFormValidation();
      
      expect(result.hasUsernameError).toBe(true);
      expect(result.hasPasswordError).toBe(true);
    });

    test('should handle case-sensitive username correctly', async () => {
      const upperCaseUsername = testUser.username.toUpperCase();
      const result = await loginPage.login(upperCaseUsername, testUser.password);
      
      // Assuming usernames are case-sensitive
      expect(result.success).toBe(false);
    });

    test('should trim whitespace from username', async () => {
      const usernameWithSpaces = `  ${testUser.username}  `;
      const result = await loginPage.login(usernameWithSpaces, testUser.password);
      
      // Should succeed if whitespace is properly trimmed
      expect(result.success).toBe(true);
    });
  });

  test.describe('User Logout @auth', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `logouttest_${Date.now()}`,
        email: `logouttest_${Date.now()}@example.com`,
        password: 'LogoutTest123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should successfully logout user', async () => {
      await loginPage.logout();
      
      const isLoggedIn = await loginPage.isLoggedIn();
      expect(isLoggedIn).toBe(false);
    });

    test('should redirect to login page after logout', async () => {
      await loginPage.logout();
      
      // Should be able to see login button again
      await loginPage.waitForElement(loginPage.elements.loginButton);
    });
  });

  test.describe('Session Management @auth', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `sessiontest_${Date.now()}`,
        email: `sessiontest_${Date.now()}@example.com`,
        password: 'SessionTest123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should persist session across page reloads', async () => {
      const result = await loginPage.testSessionPersistence();
      
      expect(result.persistedSession).toBe(true);
      expect(result.usernameMatches).toBe(true);
    });

    test('should handle session expiration gracefully', async ({ page }) => {
      // Simulate session expiration by clearing localStorage
      await page.evaluate(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      });

      await page.reload();
      
      // Should be redirected to login
      const isLoggedIn = await loginPage.isLoggedIn();
      expect(isLoggedIn).toBe(false);
    });

    test('should refresh token automatically', async ({ page }) => {
      // Get initial token
      const initialToken = await page.evaluate(() => localStorage.getItem('access_token'));
      
      // Wait for potential token refresh (simulate time passing)
      await page.waitForTimeout(2000);
      
      // Make an API request that might trigger token refresh
      const response = await page.evaluate(async () => {
        return fetch('/api/v1/auth/profile', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
      });

      expect(response).toBeTruthy();
    });
  });

  test.describe('Password Management @auth', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `passwordtest_${Date.now()}`,
        email: `passwordtest_${Date.now()}@example.com`,
        password: 'PasswordTest123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should successfully change password', async () => {
      const newPassword = 'NewPassword123!';
      const result = await loginPage.changePassword(testUser.password, newPassword);
      
      expect(result.success).toBe(true);
      
      // Verify can login with new password
      await loginPage.logout();
      const loginResult = await loginPage.login(testUser.username, newPassword);
      expect(loginResult.success).toBe(true);
    });

    test('should reject incorrect current password', async () => {
      const result = await loginPage.changePassword('wrong_password', 'NewPassword123!');
      
      expect(result.success).toBe(false);
    });

    test('should enforce password strength on change', async () => {
      const weakPassword = '123';
      const result = await loginPage.changePassword(testUser.password, weakPassword);
      
      expect(result.success).toBe(false);
    });
  });

  test.describe('Role-Based Access Control @auth', () => {
    test('should allow admin access to admin panel', async () => {
      const adminUser = {
        username: `admin_${Date.now()}`,
        email: `admin_${Date.now()}@example.com`,
        password: 'AdminTest123!',
        roles: ['admin']
      };

      // Note: This would require backend support for role assignment
      await loginPage.register(adminUser);
      await loginPage.login(adminUser.username, adminUser.password);
      
      const hasAdminAccess = await loginPage.hasAdminAccess();
      expect(hasAdminAccess).toBe(true);
    });

    test('should deny admin access to regular users', async () => {
      const regularUser = {
        username: `user_${Date.now()}`,
        email: `user_${Date.now()}@example.com`,
        password: 'UserTest123!'
      };

      await loginPage.register(regularUser);
      await loginPage.login(regularUser.username, regularUser.password);
      
      const hasAdminAccess = await loginPage.hasAdminAccess();
      expect(hasAdminAccess).toBe(false);
    });
  });

  test.describe('Security Tests @auth @security', () => {
    test('should prevent SQL injection in login', async () => {
      const sqlInjectionAttempts = [
        "admin'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'/*",
        "' UNION SELECT * FROM users --"
      ];

      for (const maliciousInput of sqlInjectionAttempts) {
        const result = await loginPage.login(maliciousInput, 'password');
        expect(result.success).toBe(false);
      }
    });

    test('should prevent XSS in registration', async () => {
      const xssPayloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "';alert('xss');//"
      ];

      for (const payload of xssPayloads) {
        const userData = {
          username: payload,
          email: `test_${Date.now()}@example.com`,
          password: 'SecurePassword123!'
        };

        const result = await loginPage.register(userData);
        // Should either reject or sanitize the input
        expect(result.success).toBe(false);
      }
    });

    test('should implement rate limiting for login attempts', async () => {
      const userData = {
        username: `ratetest_${Date.now()}`,
        email: `ratetest_${Date.now()}@example.com`,
        password: 'RateTest123!'
      };

      await loginPage.register(userData);

      // Attempt multiple failed logins
      const maxAttempts = 10;
      let blockedAttempt = false;

      for (let i = 0; i < maxAttempts; i++) {
        const result = await loginPage.login(userData.username, 'wrong_password');

        if (result.error && result.error.includes('rate limit')) {
          blockedAttempt = true;
          break;
        }
      }

      // Should eventually be rate limited
      expect(blockedAttempt).toBe(true);
    });

    test('should handle concurrent login attempts', async ({ browser }) => {
      const userData = {
        username: `concurrent_${Date.now()}`,
        email: `concurrent_${Date.now()}@example.com`,
        password: 'ConcurrentTest123!'
      };

      // Create user first
      await loginPage.register(userData);

      // Create multiple concurrent login attempts
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const loginPromises = contexts.map(async (context) => {
        const page = await context.newPage();
        const loginPageInstance = new LoginPage(page);
        return loginPageInstance.login(userData.username, userData.password);
      });

      const results = await Promise.all(loginPromises);

      // All should succeed (or handle gracefully)
      results.forEach(result => {
        expect(result.success).toBe(true);
      });

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should protect against CSRF attacks', async ({ page }) => {
      // Test that forms include CSRF tokens
      await loginPage.navigateToLogin();
      await loginPage.openLoginForm();

      const csrfToken = await page.evaluate(() => {
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        return tokenInput ? tokenInput.value : null;
      });

      // Should have CSRF protection
      expect(csrfToken).toBeTruthy();
    });

    test('should enforce secure password policies', async () => {
      const weakPasswords = [
        'password123',      // Common password
        'qwerty',          // Keyboard pattern
        '12345678',        // Sequential numbers
        'aaaaaaaa',        // Repeated characters
        'Password',        // No numbers or special chars
        'password!',       // No uppercase or numbers
        'PASSWORD123!',    // No lowercase
        'Pass1!',          // Too short
      ];

      for (const weakPassword of weakPasswords) {
        const userData = {
          username: `weakpass_${Date.now()}_${Math.random()}`,
          email: `weakpass_${Date.now()}_${Math.random()}@example.com`,
          password: weakPassword
        };

        const result = await loginPage.register(userData);
        expect(result.success).toBe(false);
      }
    });

    test('should handle account lockout after failed attempts', async () => {
      const userData = {
        username: `lockout_${Date.now()}`,
        email: `lockout_${Date.now()}@example.com`,
        password: 'LockoutTest123!'
      };

      await loginPage.register(userData);

      // Attempt multiple failed logins to trigger lockout
      for (let i = 0; i < 5; i++) {
        await loginPage.login(userData.username, 'wrong_password');
      }

      // Account should be locked
      const result = await loginPage.login(userData.username, userData.password);
      expect(result.success).toBe(false);
      expect(result.error).toMatch(/locked|blocked|suspended/i);
    });
  });

  test.describe('Edge Cases and Error Handling @auth @edge-cases', () => {
    test('should handle extremely long usernames', async () => {
      const longUsername = 'a'.repeat(1000);
      const userData = {
        username: longUsername,
        email: `test_${Date.now()}@example.com`,
        password: 'SecurePassword123!'
      };

      const result = await loginPage.register(userData);
      expect(result.success).toBe(false);
    });

    test('should handle special characters in usernames', async () => {
      const specialCharUsernames = [
        'user@name',
        'user name',
        'user#name',
        'user$name',
        'user%name',
        'user&name'
      ];

      for (const username of specialCharUsernames) {
        const userData = {
          username: username,
          email: `test_${Date.now()}_${Math.random()}@example.com`,
          password: 'SecurePassword123!'
        };

        const result = await loginPage.register(userData);
        // Should handle gracefully (either accept or reject consistently)
        expect(typeof result.success).toBe('boolean');
      }
    });

    test('should handle network timeouts gracefully', async ({ page }) => {
      // Simulate slow network
      await page.route('**/api/v1/auth/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
        route.continue();
      });

      const userData = {
        username: `timeout_${Date.now()}`,
        email: `timeout_${Date.now()}@example.com`,
        password: 'TimeoutTest123!'
      };

      const startTime = Date.now();
      const result = await loginPage.register(userData);
      const endTime = Date.now();

      // Should timeout gracefully within reasonable time
      expect(endTime - startTime).toBeLessThan(15000);
      expect(result.success).toBe(false);
    });

    test('should handle server errors gracefully', async ({ page }) => {
      // Simulate server error
      await page.route('**/api/v1/auth/register', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });

      const userData = {
        username: `servererror_${Date.now()}`,
        email: `servererror_${Date.now()}@example.com`,
        password: 'ServerError123!'
      };

      const result = await loginPage.register(userData);
      expect(result.success).toBe(false);
      expect(result.error).toContain('server error');
    });

    test('should handle malformed server responses', async ({ page }) => {
      // Simulate malformed response
      await page.route('**/api/v1/auth/login', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json response'
        });
      });

      const userData = {
        username: `malformed_${Date.now()}`,
        email: `malformed_${Date.now()}@example.com`,
        password: 'Malformed123!'
      };

      await loginPage.register(userData);
      const result = await loginPage.login(userData.username, userData.password);

      expect(result.success).toBe(false);
    });

    test('should handle browser back/forward navigation', async ({ page }) => {
      const userData = {
        username: `navigation_${Date.now()}`,
        email: `navigation_${Date.now()}@example.com`,
        password: 'Navigation123!'
      };

      await loginPage.register(userData);
      await loginPage.login(userData.username, userData.password);

      // Navigate away and back
      await page.goto('/search');
      await page.goBack();

      // Should still be logged in
      const isLoggedIn = await loginPage.isLoggedIn();
      expect(isLoggedIn).toBe(true);
    });

    test('should handle multiple tabs/windows', async ({ browser }) => {
      const userData = {
        username: `multitab_${Date.now()}`,
        email: `multitab_${Date.now()}@example.com`,
        password: 'MultiTab123!'
      };

      // Create user and login in first tab
      await loginPage.register(userData);
      await loginPage.login(userData.username, userData.password);

      // Open second tab
      const secondPage = await browser.newPage();
      const secondLoginPage = new LoginPage(secondPage);

      await secondLoginPage.navigateToLogin();

      // Should be logged in automatically or handle gracefully
      const isLoggedInSecondTab = await secondLoginPage.isLoggedIn();

      // Either should be logged in or should be able to login
      if (!isLoggedInSecondTab) {
        const result = await secondLoginPage.login(userData.username, userData.password);
        expect(result.success).toBe(true);
      }

      await secondPage.close();
    });
  });
});
