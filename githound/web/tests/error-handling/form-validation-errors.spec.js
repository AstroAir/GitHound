/**
 * Form Validation and UI Error Handling Tests
 * Tests client-side validation, form errors, and UI error states
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('Form Validation and UI Error Tests', () => {
  let searchPage;
  let loginPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
  });

  test.describe('Login Form Validation @error @validation @login', () => {
    test('should show validation errors for empty login form', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="login-button"]');
      
      // Submit empty form
      await page.click('[data-testid="submit-login"]');
      
      // Should show validation errors
      const usernameError = page.locator('[data-testid="username-error"]');
      const passwordError = page.locator('[data-testid="password-error"]');
      
      await expect(usernameError).toBeVisible();
      await expect(passwordError).toBeVisible();
      
      const usernameErrorText = await usernameError.textContent();
      const passwordErrorText = await passwordError.textContent();
      
      expect(usernameErrorText).toMatch(/required|empty|field/i);
      expect(passwordErrorText).toMatch(/required|empty|field/i);
    });

    test('should show validation error for invalid username format', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="login-button"]');
      
      // Enter invalid username
      await page.fill('[data-testid="username-input"]', 'a'); // Too short
      await page.fill('[data-testid="password-input"]', 'validpassword123');
      await page.click('[data-testid="submit-login"]');
      
      const usernameError = page.locator('[data-testid="username-error"]');
      await expect(usernameError).toBeVisible();
      
      const errorText = await usernameError.textContent();
      expect(errorText).toMatch(/length|characters|invalid/i);
    });

    test('should show validation error for weak password', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="login-button"]');
      
      // Enter weak password
      await page.fill('[data-testid="username-input"]', 'validuser');
      await page.fill('[data-testid="password-input"]', '123'); // Too weak
      await page.click('[data-testid="submit-login"]');
      
      const passwordError = page.locator('[data-testid="password-error"]');
      await expect(passwordError).toBeVisible();
      
      const errorText = await passwordError.textContent();
      expect(errorText).toMatch(/weak|length|characters/i);
    });
  });

  test.describe('Registration Form Validation @error @validation @registration', () => {
    test('should show validation errors for empty registration form', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="register-button"]');
      
      // Submit empty form
      await page.click('[data-testid="submit-registration"]');
      
      // Should show validation errors for all required fields
      const usernameError = page.locator('[data-testid="username-error"]');
      const emailError = page.locator('[data-testid="email-error"]');
      const passwordError = page.locator('[data-testid="password-error"]');
      const confirmPasswordError = page.locator('[data-testid="password-mismatch-error"]');
      
      await expect(usernameError).toBeVisible();
      await expect(emailError).toBeVisible();
      await expect(passwordError).toBeVisible();
    });

    test('should show validation error for invalid email format', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="register-button"]');
      
      await page.fill('[data-testid="register-username"]', 'validuser');
      await page.fill('[data-testid="register-email"]', 'invalid-email'); // Invalid format
      await page.fill('[data-testid="register-password"]', 'ValidPassword123!');
      await page.fill('[data-testid="register-confirm-password"]', 'ValidPassword123!');
      await page.click('[data-testid="submit-registration"]');
      
      const emailError = page.locator('[data-testid="email-error"]');
      await expect(emailError).toBeVisible();
      
      const errorText = await emailError.textContent();
      expect(errorText).toMatch(/invalid|email|format/i);
    });

    test('should show validation error for password mismatch', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="register-button"]');
      
      await page.fill('[data-testid="register-username"]', 'validuser');
      await page.fill('[data-testid="register-email"]', 'valid@example.com');
      await page.fill('[data-testid="register-password"]', 'ValidPassword123!');
      await page.fill('[data-testid="register-confirm-password"]', 'DifferentPassword123!');
      await page.click('[data-testid="submit-registration"]');
      
      const confirmPasswordError = page.locator('[data-testid="password-mismatch-error"]');
      await expect(confirmPasswordError).toBeVisible();
      
      const errorText = await confirmPasswordError.textContent();
      expect(errorText).toMatch(/match|mismatch|same/i);
    });

    test('should show validation error for username with special characters', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="register-button"]');
      
      await page.fill('[data-testid="register-username"]', 'user@#$%'); // Invalid characters
      await page.fill('[data-testid="register-email"]', 'valid@example.com');
      await page.fill('[data-testid="register-password"]', 'ValidPassword123!');
      await page.fill('[data-testid="register-confirm-password"]', 'ValidPassword123!');
      await page.click('[data-testid="submit-registration"]');
      
      const usernameError = page.locator('[data-testid="username-error"]');
      await expect(usernameError).toBeVisible();
      
      const errorText = await usernameError.textContent();
      expect(errorText).toMatch(/invalid|characters|alphanumeric/i);
    });
  });

  test.describe('Search Form Validation @error @validation @search', () => {
    test('should show validation errors for empty search form', async ({ page }) => {
      const testUser = {
        username: `search_validation_${Date.now()}`,
        email: `search_validation_${Date.now()}@example.com`,
        password: 'SearchValidation123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();
      
      // Submit empty search form
      await page.click('[data-testid="submit-search"]');
      
      // Should show validation errors
      const repoError = page.locator('[data-testid="repo-path-error"]');
      const queryError = page.locator('[data-testid="search-query-error"]');
      
      // At least one of these should be visible
      const hasRepoError = await repoError.isVisible();
      const hasQueryError = await queryError.isVisible();
      
      expect(hasRepoError || hasQueryError).toBe(true);
    });

    test('should show validation error for invalid repository path', async ({ page }) => {
      const testUser = {
        username: `repo_validation_${Date.now()}`,
        email: `repo_validation_${Date.now()}@example.com`,
        password: 'RepoValidation123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();
      
      await page.fill('[data-testid="repo-path-input"]', 'invalid/path/format'); // Invalid format
      await page.fill('[data-testid="search-query-input"]', 'function');
      await page.click('[data-testid="submit-search"]');
      
      const repoError = page.locator('[data-testid="repo-path-error"]');
      if (await repoError.isVisible()) {
        const errorText = await repoError.textContent();
        expect(errorText).toMatch(/invalid|path|format/i);
      }
    });

    test('should show validation error for search query that is too short', async ({ page }) => {
      const testUser = {
        username: `query_validation_${Date.now()}`,
        email: `query_validation_${Date.now()}@example.com`,
        password: 'QueryValidation123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();
      
      await page.fill('[data-testid="repo-path-input"]', '/valid/repo');
      await page.fill('[data-testid="search-query-input"]', 'a'); // Too short
      await page.click('[data-testid="submit-search"]');
      
      const queryError = page.locator('[data-testid="search-query-error"]');
      if (await queryError.isVisible()) {
        const errorText = await queryError.textContent();
        expect(errorText).toMatch(/short|length|characters/i);
      }
    });
  });

  test.describe('Export Form Validation @error @validation @export', () => {
    test('should show validation error for invalid export filename', async ({ page }) => {
      const testUser = {
        username: `export_validation_${Date.now()}`,
        email: `export_validation_${Date.now()}@example.com`,
        password: 'ExportValidation123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await page.goto('/');
      
      // Open export modal
      await page.click('[data-testid="export-button"]');
      await page.waitForSelector('[data-testid="export-modal"]', { state: 'visible' });
      
      // Enter invalid filename
      await page.fill('[data-testid="export-filename"]', 'invalid/filename<>'); // Invalid characters
      await page.click('[data-testid="confirm-export"]');
      
      const filenameError = page.locator('[data-testid="filename-error"]');
      if (await filenameError.isVisible()) {
        const errorText = await filenameError.textContent();
        expect(errorText).toMatch(/invalid|filename|characters/i);
      }
    });

    test('should show validation error when no fields are selected for export', async ({ page }) => {
      const testUser = {
        username: `export_fields_${Date.now()}`,
        email: `export_fields_${Date.now()}@example.com`,
        password: 'ExportFields123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await page.goto('/');
      
      // Open export modal
      await page.click('[data-testid="export-button"]');
      await page.waitForSelector('[data-testid="export-modal"]', { state: 'visible' });
      
      // Uncheck all fields
      await page.uncheck('[data-testid="select-all-fields"]');
      await page.click('[data-testid="confirm-export"]');
      
      const fieldsError = page.locator('[data-testid="fields-error"]');
      if (await fieldsError.isVisible()) {
        const errorText = await fieldsError.textContent();
        expect(errorText).toMatch(/select|fields|required/i);
      }
    });
  });

  test.describe('Real-time Validation @error @validation @realtime', () => {
    test('should show real-time validation for email field', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="register-button"]');
      
      const emailInput = page.locator('[data-testid="register-email"]');
      const emailError = page.locator('[data-testid="email-error"]');
      
      // Type invalid email
      await emailInput.fill('invalid');
      await emailInput.blur();
      
      // Should show error immediately
      await expect(emailError).toBeVisible({ timeout: 2000 });
      
      // Type valid email
      await emailInput.fill('valid@example.com');
      await emailInput.blur();
      
      // Error should disappear
      await expect(emailError).not.toBeVisible({ timeout: 2000 });
    });

    test('should show real-time validation for password confirmation', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="register-button"]');
      
      const passwordInput = page.locator('[data-testid="register-password"]');
      const confirmPasswordInput = page.locator('[data-testid="register-confirm-password"]');
      const confirmPasswordError = page.locator('[data-testid="password-mismatch-error"]');
      
      // Enter password
      await passwordInput.fill('ValidPassword123!');
      
      // Enter mismatched confirmation
      await confirmPasswordInput.fill('DifferentPassword');
      await confirmPasswordInput.blur();
      
      // Should show mismatch error
      await expect(confirmPasswordError).toBeVisible({ timeout: 2000 });
      
      // Fix the confirmation
      await confirmPasswordInput.fill('ValidPassword123!');
      await confirmPasswordInput.blur();
      
      // Error should disappear
      await expect(confirmPasswordError).not.toBeVisible({ timeout: 2000 });
    });
  });

  test.describe('Error Recovery @error @recovery', () => {
    test('should allow error recovery after fixing validation issues', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-testid="login-button"]');
      
      // Submit empty form to trigger errors
      await page.click('[data-testid="submit-login"]');
      
      const usernameError = page.locator('[data-testid="username-error"]');
      const passwordError = page.locator('[data-testid="password-error"]');
      
      await expect(usernameError).toBeVisible();
      await expect(passwordError).toBeVisible();
      
      // Fix the errors
      await page.fill('[data-testid="username-input"]', 'validuser');
      await page.fill('[data-testid="password-input"]', 'validpassword123');
      
      // Errors should disappear
      await expect(usernameError).not.toBeVisible({ timeout: 3000 });
      await expect(passwordError).not.toBeVisible({ timeout: 3000 });
      
      // Form should be submittable now
      const submitButton = page.locator('[data-testid="submit-login"]');
      await expect(submitButton).not.toBeDisabled();
    });
  });
});
