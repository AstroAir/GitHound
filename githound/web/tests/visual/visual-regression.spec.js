/**
 * Visual Regression Tests
 * Tests UI consistency and catches visual changes across different browsers and screen sizes
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('Visual Regression Tests', () => {
  let searchPage;
  let loginPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
  });

  test.describe('Homepage Visual Tests @visual @homepage', () => {
    test('should match homepage layout', async ({ page }) => {
      await page.goto('/');
      
      // Wait for page to fully load
      await page.waitForLoadState('networkidle');
      
      // Hide dynamic elements that change between test runs
      await page.addStyleTag({
        content: `
          [data-testid="search-id"],
          [data-testid="results-count"],
          .toast,
          .alert {
            visibility: hidden !important;
          }
        `
      });
      
      // Take full page screenshot
      await expect(page).toHaveScreenshot('homepage-full.png', {
        fullPage: true,
        animations: 'disabled'
      });
      
      // Take viewport screenshot
      await expect(page).toHaveScreenshot('homepage-viewport.png', {
        animations: 'disabled'
      });
    });

    test('should match navigation layout', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const navigation = page.locator('nav[data-testid="desktop-navigation"]');
      await expect(navigation).toHaveScreenshot('navigation-desktop.png');
    });
  });

  test.describe('Authentication Visual Tests @visual @auth', () => {
    test('should match login modal layout', async ({ page }) => {
      await page.goto('/');
      
      // Open login modal
      await page.click('[data-testid="login-button"]');
      await page.waitForSelector('[data-testid="login-form"]', { state: 'visible' });
      
      const loginModal = page.locator('#loginModal');
      await expect(loginModal).toHaveScreenshot('login-modal.png');
    });

    test('should match registration modal layout', async ({ page }) => {
      await page.goto('/');
      
      // Open registration modal
      await page.click('[data-testid="register-button"]');
      await page.waitForSelector('[data-testid="registration-form"]', { state: 'visible' });
      
      const registerModal = page.locator('#registerModal');
      await expect(registerModal).toHaveScreenshot('registration-modal.png');
    });

    test('should match authenticated user interface', async ({ page }) => {
      // Setup authenticated user
      const testUser = {
        username: `visual_${Date.now()}`,
        email: `visual_${Date.now()}@example.com`,
        password: 'Visual123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Hide dynamic username
      await page.addStyleTag({
        content: `
          [data-testid="username-display"] {
            visibility: hidden !important;
          }
        `
      });
      
      const userMenu = page.locator('[data-testid="user-menu"]');
      await expect(userMenu).toHaveScreenshot('user-menu.png');
    });
  });

  test.describe('Search Interface Visual Tests @visual @search', () => {
    test('should match search form layout', async ({ page }) => {
      // Setup authenticated user
      const testUser = {
        username: `search_visual_${Date.now()}`,
        email: `search_visual_${Date.now()}@example.com`,
        password: 'SearchVisual123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();
      await page.waitForLoadState('networkidle');
      
      const searchForm = page.locator('[data-testid="search-form"]');
      await expect(searchForm).toHaveScreenshot('search-form.png');
    });

    test('should match search tabs layout', async ({ page }) => {
      const testUser = {
        username: `tabs_visual_${Date.now()}`,
        email: `tabs_visual_${Date.now()}@example.com`,
        password: 'TabsVisual123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();
      
      const searchTabs = page.locator('.nav-tabs');
      await expect(searchTabs).toHaveScreenshot('search-tabs.png');
    });

    test('should match empty results state', async ({ page }) => {
      const testUser = {
        username: `empty_visual_${Date.now()}`,
        email: `empty_visual_${Date.now()}@example.com`,
        password: 'EmptyVisual123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();
      
      const resultsContainer = page.locator('[data-testid="results-container"]');
      await expect(resultsContainer).toHaveScreenshot('empty-results.png');
    });
  });

  test.describe('Export Modal Visual Tests @visual @export', () => {
    test('should match export modal layout', async ({ page }) => {
      const testUser = {
        username: `export_visual_${Date.now()}`,
        email: `export_visual_${Date.now()}@example.com`,
        password: 'ExportVisual123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await page.goto('/');
      
      // Open export modal (assuming there are results to export)
      await page.click('[data-testid="export-button"]');
      await page.waitForSelector('[data-testid="export-modal"]', { state: 'visible' });
      
      const exportModal = page.locator('#exportModal');
      await expect(exportModal).toHaveScreenshot('export-modal.png');
    });
  });

  test.describe('Responsive Visual Tests @visual @responsive', () => {
    test('should match mobile layout', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Hide dynamic elements
      await page.addStyleTag({
        content: `
          [data-testid="search-id"],
          [data-testid="results-count"] {
            visibility: hidden !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('mobile-homepage.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match tablet layout', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 }); // iPad
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await page.addStyleTag({
        content: `
          [data-testid="search-id"],
          [data-testid="results-count"] {
            visibility: hidden !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('tablet-homepage.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match mobile navigation menu', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto('/');
      
      // Open mobile menu
      await page.click('[data-testid="mobile-menu-button"]');
      await page.waitForSelector('[data-testid="mobile-menu"]', { state: 'visible' });
      
      const mobileMenu = page.locator('[data-testid="mobile-menu"]');
      await expect(mobileMenu).toHaveScreenshot('mobile-menu.png');
    });
  });

  test.describe('Error States Visual Tests @visual @errors', () => {
    test('should match form validation errors', async ({ page }) => {
      await page.goto('/');
      
      // Open login modal and trigger validation errors
      await page.click('[data-testid="login-button"]');
      await page.waitForSelector('[data-testid="login-form"]', { state: 'visible' });
      
      // Submit empty form to trigger validation
      await page.click('[data-testid="submit-login"]');
      
      // Wait for validation errors to appear
      await page.waitForTimeout(500);
      
      const loginModal = page.locator('#loginModal');
      await expect(loginModal).toHaveScreenshot('login-validation-errors.png');
    });
  });

  test.describe('Dark Mode Visual Tests @visual @darkmode', () => {
    test('should match dark mode layout', async ({ page }) => {
      // Enable dark mode (if implemented)
      await page.goto('/');
      
      // Add dark mode class or toggle dark mode
      await page.evaluate(() => {
        document.body.classList.add('dark-mode');
      });
      
      await page.waitForLoadState('networkidle');
      
      await page.addStyleTag({
        content: `
          [data-testid="search-id"],
          [data-testid="results-count"] {
            visibility: hidden !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('dark-mode-homepage.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });
});
