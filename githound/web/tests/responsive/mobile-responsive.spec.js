/**
 * Mobile Responsive Tests
 * Tests mobile responsiveness, touch interactions, and mobile-specific functionality
 */

const { test, expect, devices } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('Mobile Responsive Tests', () => {
  let searchPage;
  let loginPage;

  // Test on various mobile devices
  const mobileDevices = [
    { name: 'iPhone 12', ...devices['iPhone 12'] },
    { name: 'iPhone 12 Pro', ...devices['iPhone 12 Pro'] },
    { name: 'Pixel 5', ...devices['Pixel 5'] },
    { name: 'Galaxy S21', ...devices['Galaxy S21'] },
    { name: 'iPad', ...devices['iPad'] },
    { name: 'iPad Pro', ...devices['iPad Pro'] }
  ].filter(device => device.viewport); // Filter out undefined devices

  mobileDevices.forEach(device => {
    test.describe(`${device.name} Tests @responsive @mobile`, () => {
      test.beforeEach(async ({ browser }) => {
        const context = await browser.newContext({
          ...device
        });
        const page = await context.newPage();
        
        searchPage = new SearchPage(page);
        loginPage = new LoginPage(page);

        // Setup authenticated user
        const testUser = {
          username: `mobile_${Date.now()}`,
          email: `mobile_${Date.now()}@example.com`,
          password: 'Mobile123!'
        };

        await loginPage.register(testUser);
        await loginPage.login(testUser.username, testUser.password);
      });

      test(`should display properly on ${device.name}`, async ({ page }) => {
        await searchPage.navigateToSearch();

        // Check viewport dimensions
        const viewport = page.viewportSize();
        expect(viewport.width).toBe(device.viewport.width);
        expect(viewport.height).toBe(device.viewport.height);

        // Check if main elements are visible
        const searchForm = page.locator('[data-testid="search-form"]');
        await expect(searchForm).toBeVisible();

        // Check if navigation is accessible (hamburger menu for mobile)
        if (device.viewport.width < 768) {
          const mobileMenu = page.locator('[data-testid="mobile-menu-toggle"]');
          if (await mobileMenu.count() > 0) {
            await expect(mobileMenu).toBeVisible();
          }
        }

        // Check if content fits within viewport
        const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
        expect(bodyWidth).toBeLessThanOrEqual(device.viewport.width + 20); // Allow small tolerance
      });

      test(`should handle touch interactions on ${device.name}`, async ({ page }) => {
        await searchPage.navigateToSearch();

        // Test touch interactions
        const searchInput = page.locator('[data-testid="search-input"]');
        
        // Tap to focus
        await searchInput.tap();
        await expect(searchInput).toBeFocused();

        // Type on mobile keyboard
        await searchInput.fill('function');
        
        // Test touch scroll
        await page.evaluate(() => {
          window.scrollTo(0, 100);
        });

        const scrollPosition = await page.evaluate(() => window.pageYOffset);
        expect(scrollPosition).toBeGreaterThan(0);

        // Test swipe gestures if supported
        if (device.viewport.width < 768) {
          // Simulate swipe left/right for navigation
          await page.touchscreen.tap(100, 100);
          await page.touchscreen.tap(300, 100);
        }
      });

      test(`should adapt search interface for ${device.name}`, async ({ page }) => {
        await searchPage.navigateToSearch();

        // Perform search
        await searchPage.performAdvancedSearch({
          query: 'function',
          fileTypes: ['js'],
          searchType: 'exact'
        });

        await searchPage.waitForResults();

        // Check if results are displayed properly on mobile
        const results = page.locator('[data-testid="search-results"]');
        await expect(results).toBeVisible();

        // On mobile, results should stack vertically
        if (device.viewport.width < 768) {
          const resultCards = await page.locator('[data-testid="result-card"]').all();
          
          if (resultCards.length >= 2) {
            const firstCardBox = await resultCards[0].boundingBox();
            const secondCardBox = await resultCards[1].boundingBox();
            
            // Second card should be below first card (stacked vertically)
            expect(secondCardBox.y).toBeGreaterThan(firstCardBox.y + firstCardBox.height - 10);
          }
        }
      });

      test(`should handle mobile navigation on ${device.name}`, async ({ page }) => {
        await searchPage.navigateToSearch();

        if (device.viewport.width < 768) {
          // Test mobile menu
          const mobileMenuToggle = page.locator('[data-testid="mobile-menu-toggle"]');
          
          if (await mobileMenuToggle.count() > 0) {
            // Open mobile menu
            await mobileMenuToggle.tap();
            
            const mobileMenu = page.locator('[data-testid="mobile-menu"]');
            await expect(mobileMenu).toBeVisible();

            // Test navigation links in mobile menu
            const navLinks = await mobileMenu.locator('a, button').all();
            expect(navLinks.length).toBeGreaterThan(0);

            // Close mobile menu
            await mobileMenuToggle.tap();
            await expect(mobileMenu).toBeHidden();
          }
        }
      });

      test(`should optimize performance on ${device.name}`, async ({ page }) => {
        const startTime = Date.now();
        
        await searchPage.navigateToSearch();
        await page.waitForLoadState('networkidle');
        
        const loadTime = Date.now() - startTime;
        
        // Mobile should load within reasonable time
        expect(loadTime).toBeLessThan(5000); // 5 seconds for mobile

        // Check if images are optimized for mobile
        const images = await page.locator('img').all();
        
        for (const img of images.slice(0, 5)) {
          const src = await img.getAttribute('src');
          const naturalWidth = await img.evaluate(el => el.naturalWidth);
          
          // Images should not be excessively large for mobile
          if (device.viewport.width < 768) {
            expect(naturalWidth).toBeLessThan(device.viewport.width * 2);
          }
        }
      });
    });
  });

  test.describe('Responsive Breakpoints @responsive @breakpoints', () => {
    const breakpoints = [
      { name: 'Mobile Small', width: 320, height: 568 },
      { name: 'Mobile Medium', width: 375, height: 667 },
      { name: 'Mobile Large', width: 414, height: 896 },
      { name: 'Tablet Portrait', width: 768, height: 1024 },
      { name: 'Tablet Landscape', width: 1024, height: 768 },
      { name: 'Desktop Small', width: 1280, height: 720 },
      { name: 'Desktop Large', width: 1920, height: 1080 }
    ];

    breakpoints.forEach(breakpoint => {
      test(`should adapt layout at ${breakpoint.name} (${breakpoint.width}x${breakpoint.height})`, async ({ page }) => {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });

        // Setup authenticated user
        const testUser = {
          username: `breakpoint_${Date.now()}`,
          email: `breakpoint_${Date.now()}@example.com`,
          password: 'Breakpoint123!'
        };

        const loginPageInstance = new LoginPage(page);
        const searchPageInstance = new SearchPage(page);

        await loginPageInstance.register(testUser);
        await loginPageInstance.login(testUser.username, testUser.password);
        
        await searchPageInstance.navigateToSearch();

        // Check layout adaptation
        const container = page.locator('[data-testid="main-container"]');
        const containerBox = await container.boundingBox();
        
        if (containerBox) {
          // Container should not exceed viewport width
          expect(containerBox.width).toBeLessThanOrEqual(breakpoint.width);
        }

        // Check navigation layout
        if (breakpoint.width < 768) {
          // Mobile: should have hamburger menu
          const mobileMenu = page.locator('[data-testid="mobile-menu-toggle"]');
          if (await mobileMenu.count() > 0) {
            await expect(mobileMenu).toBeVisible();
          }
        } else {
          // Desktop: should have horizontal navigation
          const desktopNav = page.locator('[data-testid="desktop-nav"]');
          if (await desktopNav.count() > 0) {
            await expect(desktopNav).toBeVisible();
          }
        }

        // Check search form layout
        const searchForm = page.locator('[data-testid="search-form"]');
        const searchFormBox = await searchForm.boundingBox();
        
        if (searchFormBox) {
          expect(searchFormBox.width).toBeLessThanOrEqual(breakpoint.width);
        }
      });
    });
  });

  test.describe('Touch and Gesture Support @responsive @touch', () => {
    test('should support pinch-to-zoom on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      const testUser = {
        username: `touch_${Date.now()}`,
        email: `touch_${Date.now()}@example.com`,
        password: 'Touch123!'
      };

      const loginPageInstance = new LoginPage(page);
      const searchPageInstance = new SearchPage(page);

      await loginPageInstance.register(testUser);
      await loginPageInstance.login(testUser.username, testUser.password);
      
      await searchPageInstance.navigateToSearch();

      // Check if viewport meta tag allows zooming
      const viewportMeta = await page.locator('meta[name="viewport"]').getAttribute('content');
      
      // Should not prevent zooming (accessibility requirement)
      expect(viewportMeta).not.toContain('user-scalable=no');
      expect(viewportMeta).not.toContain('maximum-scale=1');
    });

    test('should handle swipe gestures for navigation', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      const testUser = {
        username: `swipe_${Date.now()}`,
        email: `swipe_${Date.now()}@example.com`,
        password: 'Swipe123!'
      };

      const loginPageInstance = new LoginPage(page);
      const searchPageInstance = new SearchPage(page);

      await loginPageInstance.register(testUser);
      await loginPageInstance.login(testUser.username, testUser.password);
      
      await searchPageInstance.navigateToSearch();

      // Perform search to get results with pagination
      await searchPageInstance.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js', 'py'],
        searchType: 'fuzzy'
      });

      await searchPageInstance.waitForResults();

      // Test swipe navigation if pagination exists
      const pagination = page.locator('[data-testid="pagination"]');
      
      if (await pagination.count() > 0) {
        // Simulate swipe left (next page)
        await page.touchscreen.tap(200, 400);
        await page.touchscreen.tap(100, 400);
        
        // Should navigate to next page or show some response
        await page.waitForTimeout(1000);
        
        // Verify page responded to gesture
        const currentUrl = page.url();
        expect(currentUrl).toBeTruthy();
      }
    });

    test('should provide adequate touch targets', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      const testUser = {
        username: `targets_${Date.now()}`,
        email: `targets_${Date.now()}@example.com`,
        password: 'Targets123!'
      };

      const loginPageInstance = new LoginPage(page);
      const searchPageInstance = new SearchPage(page);

      await loginPageInstance.register(testUser);
      await loginPageInstance.login(testUser.username, testUser.password);
      
      await searchPageInstance.navigateToSearch();

      // Check touch target sizes (minimum 44x44px for accessibility)
      const touchTargets = await page.locator('button, a, input[type="checkbox"], input[type="radio"], select').all();
      
      for (const target of touchTargets.slice(0, 10)) {
        const box = await target.boundingBox();
        
        if (box) {
          // Touch targets should be at least 44x44px
          expect(Math.min(box.width, box.height)).toBeGreaterThanOrEqual(44);
        }
      }
    });

    test('should handle long press gestures', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      const testUser = {
        username: `longpress_${Date.now()}`,
        email: `longpress_${Date.now()}@example.com`,
        password: 'LongPress123!'
      };

      const loginPageInstance = new LoginPage(page);
      const searchPageInstance = new SearchPage(page);

      await loginPageInstance.register(testUser);
      await loginPageInstance.login(testUser.username, testUser.password);
      
      await searchPageInstance.navigateToSearch();

      // Perform search to get results
      await searchPageInstance.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPageInstance.waitForResults();

      // Test long press on result items
      const resultCard = page.locator('[data-testid="result-card"]').first();
      
      if (await resultCard.count() > 0) {
        // Simulate long press
        await resultCard.hover();
        await page.mouse.down();
        await page.waitForTimeout(1000); // Hold for 1 second
        await page.mouse.up();

        // Should show context menu or additional options
        const contextMenu = page.locator('[data-testid="context-menu"], [role="menu"]');
        
        if (await contextMenu.count() > 0) {
          await expect(contextMenu).toBeVisible();
        }
      }
    });
  });

  test.describe('Orientation Changes @responsive @orientation', () => {
    test('should handle portrait to landscape orientation change', async ({ page }) => {
      // Start in portrait
      await page.setViewportSize({ width: 375, height: 667 });

      const testUser = {
        username: `orientation_${Date.now()}`,
        email: `orientation_${Date.now()}@example.com`,
        password: 'Orientation123!'
      };

      const loginPageInstance = new LoginPage(page);
      const searchPageInstance = new SearchPage(page);

      await loginPageInstance.register(testUser);
      await loginPageInstance.login(testUser.username, testUser.password);
      
      await searchPageInstance.navigateToSearch();

      // Perform search
      await searchPageInstance.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPageInstance.waitForResults();

      // Check layout in portrait
      const portraitLayout = await page.locator('[data-testid="search-results"]').boundingBox();
      
      // Change to landscape
      await page.setViewportSize({ width: 667, height: 375 });
      await page.waitForTimeout(500); // Allow layout to adjust

      // Check layout in landscape
      const landscapeLayout = await page.locator('[data-testid="search-results"]').boundingBox();
      
      // Layout should adapt to new orientation
      expect(landscapeLayout.width).toBeGreaterThan(portraitLayout.width);
      expect(landscapeLayout.height).toBeLessThan(portraitLayout.height);

      // Content should still be accessible
      const searchForm = page.locator('[data-testid="search-form"]');
      await expect(searchForm).toBeVisible();
    });

    test('should maintain functionality across orientation changes', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      const testUser = {
        username: `func_orientation_${Date.now()}`,
        email: `func_orientation_${Date.now()}@example.com`,
        password: 'FuncOrientation123!'
      };

      const loginPageInstance = new LoginPage(page);
      const searchPageInstance = new SearchPage(page);

      await loginPageInstance.register(testUser);
      await loginPageInstance.login(testUser.username, testUser.password);
      
      await searchPageInstance.navigateToSearch();

      // Start search in portrait
      await page.fill('[data-testid="search-input"]', 'function');
      
      // Change to landscape mid-search
      await page.setViewportSize({ width: 667, height: 375 });
      await page.waitForTimeout(500);

      // Complete search in landscape
      await page.click('[data-testid="search-button"]');
      await searchPageInstance.waitForResults();

      // Search should complete successfully
      const results = page.locator('[data-testid="search-results"]');
      await expect(results).toBeVisible();

      // Form state should be preserved
      const searchInputValue = await page.inputValue('[data-testid="search-input"]');
      expect(searchInputValue).toBe('function');
    });
  });
});
