/**
 * Form Accessibility Tests
 * Tests form accessibility, validation, error handling, and user guidance
 */

const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const { SearchPage, LoginPage } = require('../pages');
const { AccessibilityTestHelper } = require('../utils/accessibility-helper');

test.describe('Form Accessibility Tests', () => {
  let searchPage;
  let loginPage;
  let a11yHelper;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    a11yHelper = new AccessibilityTestHelper(page);
  });

  test.describe('Registration Form Accessibility @accessibility @forms @registration', () => {
    test('should have accessible registration form', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Run axe scan on registration form
      const accessibilityResults = await new AxeBuilder({ page })
        .include('[data-testid="registration-form"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityResults.violations).toEqual([]);

      // Check form structure
      const formInputs = await page.locator('[data-testid="registration-form"] input').all();
      
      for (const input of formInputs) {
        // Each input should have a proper label
        const hasLabel = await a11yHelper.hasProperLabel(input);
        expect(hasLabel).toBe(true);

        // Should have proper input type
        const inputType = await input.getAttribute('type');
        expect(inputType).toBeTruthy();

        // Required fields should be marked
        const isRequired = await input.getAttribute('required') !== null;
        const hasAriaRequired = await input.getAttribute('aria-required') === 'true';
        
        if (isRequired || hasAriaRequired) {
          // Should indicate required status to screen readers
          const ariaLabel = await input.getAttribute('aria-label');
          const labelText = await a11yHelper.getLabelText(input);
          
          const hasRequiredIndicator = 
            (ariaLabel && ariaLabel.includes('required')) ||
            (labelText && labelText.includes('*')) ||
            hasAriaRequired;
            
          expect(hasRequiredIndicator).toBe(true);
        }
      }
    });

    test('should provide accessible form validation', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Submit form with invalid data to trigger validation
      await page.fill('[data-testid="username-input"]', 'a'); // Too short
      await page.fill('[data-testid="email-input"]', 'invalid-email'); // Invalid format
      await page.fill('[data-testid="password-input"]', '123'); // Too weak
      await page.click('[data-testid="register-button"]');

      // Wait for validation messages
      await page.waitForSelector('[role="alert"], [aria-live="polite"]', { timeout: 5000 });

      // Check validation message accessibility
      const validationMessages = await page.locator('[role="alert"], [aria-live="polite"], [aria-invalid="true"] + *').all();
      
      expect(validationMessages.length).toBeGreaterThan(0);

      for (const message of validationMessages) {
        // Validation messages should be announced to screen readers
        const role = await message.getAttribute('role');
        const ariaLive = await message.getAttribute('aria-live');
        
        expect(role === 'alert' || ariaLive === 'polite' || ariaLive === 'assertive').toBe(true);

        // Should have meaningful text
        const messageText = await message.textContent();
        expect(messageText?.trim().length).toBeGreaterThan(0);
      }

      // Invalid fields should be marked with aria-invalid
      const invalidInputs = await page.locator('[aria-invalid="true"]').all();
      expect(invalidInputs.length).toBeGreaterThan(0);

      // Each invalid input should be associated with its error message
      for (const input of invalidInputs) {
        const ariaDescribedBy = await input.getAttribute('aria-describedby');
        if (ariaDescribedBy) {
          const errorElement = page.locator(`#${ariaDescribedBy}`);
          expect(await errorElement.count()).toBeGreaterThan(0);
        }
      }
    });

    test('should support keyboard navigation in registration form', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Test tab order through form
      const tabOrder = await a11yHelper.getTabOrder('[data-testid="registration-form"]');
      
      expect(tabOrder.length).toBeGreaterThan(0);

      // Should be able to complete form using only keyboard
      await page.keyboard.press('Tab'); // Focus first input
      await page.keyboard.type('testuser123');
      
      await page.keyboard.press('Tab'); // Move to email
      await page.keyboard.type('testuser123@example.com');
      
      await page.keyboard.press('Tab'); // Move to password
      await page.keyboard.type('SecurePassword123!');
      
      await page.keyboard.press('Tab'); // Move to confirm password
      await page.keyboard.type('SecurePassword123!');
      
      await page.keyboard.press('Tab'); // Move to submit button
      await page.keyboard.press('Enter'); // Submit form

      // Should handle form submission
      const isSubmitted = await page.waitForSelector('[data-testid="registration-success"], [data-testid="login-form"]', { timeout: 10000 });
      expect(isSubmitted).toBeTruthy();
    });

    test('should provide helpful form instructions', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Check for form instructions and help text
      const helpTexts = await page.locator('[data-testid*="help"], [aria-describedby], [role="note"]').all();
      
      for (const helpText of helpTexts) {
        const textContent = await helpText.textContent();
        expect(textContent?.trim().length).toBeGreaterThan(0);

        // Help text should be associated with form controls
        const id = await helpText.getAttribute('id');
        if (id) {
          const associatedInput = page.locator(`[aria-describedby*="${id}"]`);
          expect(await associatedInput.count()).toBeGreaterThan(0);
        }
      }
    });
  });

  test.describe('Login Form Accessibility @accessibility @forms @login', () => {
    test('should have accessible login form', async ({ page }) => {
      await loginPage.navigateToLogin();

      // Run axe scan on login form
      const accessibilityResults = await new AxeBuilder({ page })
        .include('[data-testid="login-form"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityResults.violations).toEqual([]);

      // Check username/email field
      const usernameField = page.locator('[data-testid="username-input"]');
      const hasUsernameLabel = await a11yHelper.hasProperLabel(usernameField);
      expect(hasUsernameLabel).toBe(true);

      // Check password field
      const passwordField = page.locator('[data-testid="password-input"]');
      const hasPasswordLabel = await a11yHelper.hasProperLabel(passwordField);
      expect(hasPasswordLabel).toBe(true);

      // Password field should have proper type
      const passwordType = await passwordField.getAttribute('type');
      expect(passwordType).toBe('password');
    });

    test('should handle login errors accessibly', async ({ page }) => {
      await loginPage.navigateToLogin();

      // Attempt login with invalid credentials
      await page.fill('[data-testid="username-input"]', 'nonexistent');
      await page.fill('[data-testid="password-input"]', 'wrongpassword');
      await page.click('[data-testid="login-button"]');

      // Wait for error message
      await page.waitForSelector('[role="alert"], [data-testid="error-message"]', { timeout: 5000 });

      // Error should be announced to screen readers
      const errorMessage = page.locator('[role="alert"], [data-testid="error-message"]').first();
      const errorText = await errorMessage.textContent();
      
      expect(errorText?.trim().length).toBeGreaterThan(0);
      expect(errorText).not.toContain('undefined');

      // Error should be associated with the form
      const role = await errorMessage.getAttribute('role');
      const ariaLive = await errorMessage.getAttribute('aria-live');
      
      expect(role === 'alert' || ariaLive === 'polite' || ariaLive === 'assertive').toBe(true);
    });

    test('should support password visibility toggle', async ({ page }) => {
      await loginPage.navigateToLogin();

      const passwordField = page.locator('[data-testid="password-input"]');
      const toggleButton = page.locator('[data-testid="password-toggle"]');

      if (await toggleButton.count() > 0) {
        // Toggle button should be accessible
        const hasLabel = await a11yHelper.hasProperLabel(toggleButton);
        expect(hasLabel).toBe(true);

        // Should be keyboard accessible
        await toggleButton.focus();
        await page.keyboard.press('Enter');

        // Password field type should change
        const newType = await passwordField.getAttribute('type');
        expect(newType).toBe('text');

        // Toggle again
        await page.keyboard.press('Enter');
        const finalType = await passwordField.getAttribute('type');
        expect(finalType).toBe('password');
      }
    });
  });

  test.describe('Search Form Accessibility @accessibility @forms @search', () => {
    test('should have accessible search form', async ({ page }) => {
      // Setup authenticated user first
      const testUser = {
        username: `search_a11y_${Date.now()}`,
        email: `search_a11y_${Date.now()}@example.com`,
        password: 'SearchA11y123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      await searchPage.navigateToSearch();

      // Run axe scan on search form
      const accessibilityResults = await new AxeBuilder({ page })
        .include('[data-testid="search-form"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityResults.violations).toEqual([]);

      // Check search input accessibility
      const searchInput = page.locator('[data-testid="search-input"]');
      const hasLabel = await a11yHelper.hasProperLabel(searchInput);
      expect(hasLabel).toBe(true);

      // Should have proper input type
      const inputType = await searchInput.getAttribute('type');
      expect(['text', 'search']).toContain(inputType);

      // Should have placeholder or description
      const placeholder = await searchInput.getAttribute('placeholder');
      const ariaDescribedBy = await searchInput.getAttribute('aria-describedby');
      
      expect(placeholder || ariaDescribedBy).toBeTruthy();
    });

    test('should have accessible advanced search form', async ({ page }) => {
      const testUser = {
        username: `advanced_a11y_${Date.now()}`,
        email: `advanced_a11y_${Date.now()}@example.com`,
        password: 'AdvancedA11y123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      await searchPage.navigateToSearch();
      await searchPage.openAdvancedSearch();

      // Run axe scan on advanced search form
      const accessibilityResults = await new AxeBuilder({ page })
        .include('[data-testid="advanced-search-form"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityResults.violations).toEqual([]);

      // Check all form controls
      const formControls = await page.locator('[data-testid="advanced-search-form"] input, [data-testid="advanced-search-form"] select, [data-testid="advanced-search-form"] textarea').all();
      
      for (const control of formControls) {
        const hasLabel = await a11yHelper.hasProperLabel(control);
        expect(hasLabel).toBe(true);
      }

      // Check fieldsets and legends
      const fieldsets = await page.locator('[data-testid="advanced-search-form"] fieldset').all();
      
      for (const fieldset of fieldsets) {
        const legend = await fieldset.locator('legend').count();
        expect(legend).toBeGreaterThan(0);
      }
    });

    test('should provide accessible search suggestions', async ({ page }) => {
      const testUser = {
        username: `suggestions_a11y_${Date.now()}`,
        email: `suggestions_a11y_${Date.now()}@example.com`,
        password: 'SuggestionsA11y123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      await searchPage.navigateToSearch();

      const searchInput = page.locator('[data-testid="search-input"]');
      
      // Type to trigger suggestions
      await searchInput.fill('func');
      
      // Wait for suggestions to appear
      await page.waitForSelector('[data-testid="search-suggestions"], [role="listbox"]', { timeout: 5000 });

      const suggestionsContainer = page.locator('[data-testid="search-suggestions"], [role="listbox"]').first();
      
      if (await suggestionsContainer.count() > 0) {
        // Suggestions should have proper ARIA attributes
        const role = await suggestionsContainer.getAttribute('role');
        expect(role).toBe('listbox');

        // Search input should reference suggestions
        const ariaExpanded = await searchInput.getAttribute('aria-expanded');
        const ariaOwns = await searchInput.getAttribute('aria-owns');
        const ariaControls = await searchInput.getAttribute('aria-controls');
        
        expect(ariaExpanded).toBe('true');
        expect(ariaOwns || ariaControls).toBeTruthy();

        // Individual suggestions should be accessible
        const suggestions = await suggestionsContainer.locator('[role="option"]').all();
        
        for (const suggestion of suggestions.slice(0, 3)) {
          const role = await suggestion.getAttribute('role');
          expect(role).toBe('option');

          // Should be keyboard navigable
          await suggestion.focus();
          const isFocused = await a11yHelper.isElementFocused(suggestion);
          expect(isFocused).toBe(true);
        }
      }
    });

    test('should handle search form validation accessibly', async ({ page }) => {
      const testUser = {
        username: `validation_a11y_${Date.now()}`,
        email: `validation_a11y_${Date.now()}@example.com`,
        password: 'ValidationA11y123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);

      await searchPage.navigateToSearch();

      // Submit empty search form
      await page.click('[data-testid="search-button"]');

      // Wait for validation message
      await page.waitForSelector('[role="alert"], [aria-live="polite"]', { timeout: 5000 });

      const validationMessage = page.locator('[role="alert"], [aria-live="polite"]').first();
      
      if (await validationMessage.count() > 0) {
        // Validation message should be announced
        const messageText = await validationMessage.textContent();
        expect(messageText?.trim().length).toBeGreaterThan(0);

        // Should be associated with the search input
        const searchInput = page.locator('[data-testid="search-input"]');
        const ariaInvalid = await searchInput.getAttribute('aria-invalid');
        const ariaDescribedBy = await searchInput.getAttribute('aria-describedby');
        
        expect(ariaInvalid === 'true' || ariaDescribedBy).toBeTruthy();
      }
    });
  });

  test.describe('Form Error Recovery @accessibility @forms @errors', () => {
    test('should provide clear error recovery instructions', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Submit form with multiple errors
      await page.fill('[data-testid="username-input"]', ''); // Empty
      await page.fill('[data-testid="email-input"]', 'invalid'); // Invalid
      await page.fill('[data-testid="password-input"]', '123'); // Too weak
      await page.click('[data-testid="register-button"]');

      // Wait for error messages
      await page.waitForSelector('[role="alert"]', { timeout: 5000 });

      const errorMessages = await page.locator('[role="alert"], [aria-live="polite"]').all();
      
      for (const errorMessage of errorMessages) {
        const messageText = await errorMessage.textContent();
        
        // Error messages should be specific and actionable
        expect(messageText?.trim().length).toBeGreaterThan(0);
        expect(messageText).not.toContain('Error');
        expect(messageText).not.toContain('Invalid');
        
        // Should provide guidance on how to fix the error
        const hasGuidance = messageText?.includes('must') || 
                           messageText?.includes('should') || 
                           messageText?.includes('required') ||
                           messageText?.includes('at least') ||
                           messageText?.includes('format');
        
        expect(hasGuidance).toBe(true);
      }
    });

    test('should maintain form data during error correction', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Fill form with some valid and some invalid data
      await page.fill('[data-testid="username-input"]', 'validuser123');
      await page.fill('[data-testid="email-input"]', 'invalid-email'); // Invalid
      await page.fill('[data-testid="password-input"]', 'ValidPassword123!');
      await page.click('[data-testid="register-button"]');

      // Wait for validation
      await page.waitForSelector('[role="alert"]', { timeout: 5000 });

      // Valid data should be preserved
      const usernameValue = await page.inputValue('[data-testid="username-input"]');
      const passwordValue = await page.inputValue('[data-testid="password-input"]');
      
      expect(usernameValue).toBe('validuser123');
      expect(passwordValue).toBe('ValidPassword123!');

      // Focus should move to first invalid field
      const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
      expect(focusedElement).toBe('email-input');
    });

    test('should clear errors when corrected', async ({ page }) => {
      await loginPage.navigateToRegister();

      // Submit with invalid email
      await page.fill('[data-testid="email-input"]', 'invalid');
      await page.click('[data-testid="register-button"]');

      // Wait for error
      await page.waitForSelector('[role="alert"]', { timeout: 5000 });

      const emailInput = page.locator('[data-testid="email-input"]');
      
      // Should be marked as invalid
      let ariaInvalid = await emailInput.getAttribute('aria-invalid');
      expect(ariaInvalid).toBe('true');

      // Correct the email
      await emailInput.fill('valid@example.com');
      await emailInput.blur();

      // Wait for validation to clear
      await page.waitForTimeout(1000);

      // Should no longer be marked as invalid
      ariaInvalid = await emailInput.getAttribute('aria-invalid');
      expect(ariaInvalid === 'false' || ariaInvalid === null).toBe(true);

      // Error message should be removed or hidden
      const errorMessages = await page.locator('[role="alert"]:visible').all();
      const hasEmailError = await Promise.all(
        errorMessages.map(async msg => {
          const text = await msg.textContent();
          return text?.toLowerCase().includes('email');
        })
      );
      
      expect(hasEmailError.some(Boolean)).toBe(false);
    });
  });
});
