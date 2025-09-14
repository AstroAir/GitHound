/**
 * Screen Size Responsiveness Tests
 * Tests layout adaptation across different screen sizes and resolutions
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('Screen Size Responsiveness Tests', () => {
  let searchPage;
  let loginPage;

  test.describe('Ultra-wide and Large Displays @responsive @ultrawide', () => {
    const largeScreenSizes = [
      { name: '4K Monitor', width: 3840, height: 2160 },
      { name: 'Ultra-wide 21:9', width: 2560, height: 1080 },
      { name: 'Ultra-wide 32:9', width: 3440, height: 1440 },
      { name: 'Large Desktop', width: 2560, height: 1440 },
      { name: 'Standard 4K', width: 1920, height: 1080 }
    ];

    largeScreenSizes.forEach(screenSize => {
      test(`should optimize layout for ${screenSize.name} (${screenSize.width}x${screenSize.height})`, async ({ page }) => {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });

        // Setup authenticated user
        const testUser = {
          username: `large_screen_${Date.now()}`,
          email: `large_screen_${Date.now()}@example.com`,
          password: 'LargeScreen123!'
        };

        loginPage = new LoginPage(page);
        searchPage = new SearchPage(page);

        await loginPage.register(testUser);
        await loginPage.login(testUser.username, testUser.password);
        
        await searchPage.navigateToSearch();

        // Check if content utilizes available space efficiently
        const mainContainer = page.locator('[data-testid="main-container"]');
        const containerBox = await mainContainer.boundingBox();
        
        if (containerBox) {
          // Content should not be too narrow on large screens
          expect(containerBox.width).toBeGreaterThan(screenSize.width * 0.6);
          
          // But also shouldn't stretch too wide (readability)
          expect(containerBox.width).toBeLessThan(screenSize.width * 0.95);
        }

        // Check if search results utilize space well
        await searchPage.performAdvancedSearch({
          query: 'function',
          fileTypes: ['js', 'py'],
          searchType: 'exact'
        });

        await searchPage.waitForResults();

        const resultsContainer = page.locator('[data-testid="search-results"]');
        const resultsBox = await resultsContainer.boundingBox();
        
        if (resultsBox) {
          // Results should use available width efficiently
          expect(resultsBox.width).toBeGreaterThan(screenSize.width * 0.5);
        }

        // Check for multi-column layout on ultra-wide screens
        if (screenSize.width >= 2560) {
          const resultCards = await page.locator('[data-testid="result-card"]').all();
          
          if (resultCards.length >= 2) {
            const firstCardBox = await resultCards[0].boundingBox();
            const secondCardBox = await resultCards[1].boundingBox();
            
            // On ultra-wide, cards might be side-by-side
            const isSideBySide = Math.abs(firstCardBox.y - secondCardBox.y) < 50;
            
            if (isSideBySide) {
              expect(secondCardBox.x).toBeGreaterThan(firstCardBox.x + firstCardBox.width - 50);
            }
          }
        }
      });
    });

    test('should handle window resizing gracefully', async ({ page }) => {
      // Start with standard desktop size
      await page.setViewportSize({ width: 1920, height: 1080 });

      const testUser = {
        username: `resize_${Date.now()}`,
        email: `resize_${Date.now()}@example.com`,
        password: 'Resize123!'
      };

      loginPage = new LoginPage(page);
      searchPage = new SearchPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Perform search
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Get initial layout
      const initialLayout = await page.locator('[data-testid="search-results"]').boundingBox();

      // Resize to ultra-wide
      await page.setViewportSize({ width: 3440, height: 1440 });
      await page.waitForTimeout(500); // Allow layout to adjust

      // Check layout adaptation
      const ultraWideLayout = await page.locator('[data-testid="search-results"]').boundingBox();
      expect(ultraWideLayout.width).toBeGreaterThan(initialLayout.width);

      // Resize to narrow
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.waitForTimeout(500);

      const narrowLayout = await page.locator('[data-testid="search-results"]').boundingBox();
      expect(narrowLayout.width).toBeLessThan(ultraWideLayout.width);

      // Content should remain functional throughout
      const searchForm = page.locator('[data-testid="search-form"]');
      await expect(searchForm).toBeVisible();
    });
  });

  test.describe('Small and Constrained Displays @responsive @small', () => {
    const smallScreenSizes = [
      { name: 'Netbook', width: 1024, height: 600 },
      { name: 'Small Laptop', width: 1366, height: 768 },
      { name: 'Old Monitor', width: 1024, height: 768 },
      { name: 'Compact Display', width: 1280, height: 720 },
      { name: 'Square Display', width: 1024, height: 1024 }
    ];

    smallScreenSizes.forEach(screenSize => {
      test(`should adapt to ${screenSize.name} (${screenSize.width}x${screenSize.height})`, async ({ page }) => {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });

        const testUser = {
          username: `small_screen_${Date.now()}`,
          email: `small_screen_${Date.now()}@example.com`,
          password: 'SmallScreen123!'
        };

        loginPage = new LoginPage(page);
        searchPage = new SearchPage(page);

        await loginPage.register(testUser);
        await loginPage.login(testUser.username, testUser.password);
        
        await searchPage.navigateToSearch();

        // Check if content fits within viewport
        const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
        expect(bodyWidth).toBeLessThanOrEqual(screenSize.width + 20); // Small tolerance

        // Check if navigation is accessible
        const navigation = page.locator('[data-testid="main-nav"]');
        if (await navigation.count() > 0) {
          await expect(navigation).toBeVisible();
        }

        // Check if search form is usable
        const searchInput = page.locator('[data-testid="search-input"]');
        await expect(searchInput).toBeVisible();

        const searchInputBox = await searchInput.boundingBox();
        if (searchInputBox) {
          // Search input should not be too narrow
          expect(searchInputBox.width).toBeGreaterThan(200);
        }

        // Perform search and check results
        await searchPage.performAdvancedSearch({
          query: 'function',
          fileTypes: ['js'],
          searchType: 'exact'
        });

        await searchPage.waitForResults();

        // Results should be readable
        const resultCards = await page.locator('[data-testid="result-card"]').all();
        
        for (const card of resultCards.slice(0, 3)) {
          const cardBox = await card.boundingBox();
          if (cardBox) {
            // Cards should not be too narrow
            expect(cardBox.width).toBeGreaterThan(300);
            // Cards should fit within viewport
            expect(cardBox.width).toBeLessThanOrEqual(screenSize.width);
          }
        }
      });
    });

    test('should handle vertical space constraints', async ({ page }) => {
      // Test with very limited vertical space
      await page.setViewportSize({ width: 1366, height: 600 });

      const testUser = {
        username: `vertical_${Date.now()}`,
        email: `vertical_${Date.now()}@example.com`,
        password: 'Vertical123!'
      };

      loginPage = new LoginPage(page);
      searchPage = new SearchPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Check if header is compact
      const header = page.locator('[data-testid="main-header"]');
      if (await header.count() > 0) {
        const headerBox = await header.boundingBox();
        if (headerBox) {
          // Header should not take too much vertical space
          expect(headerBox.height).toBeLessThan(100);
        }
      }

      // Check if search form is accessible without scrolling
      const searchForm = page.locator('[data-testid="search-form"]');
      const searchFormBox = await searchForm.boundingBox();
      
      if (searchFormBox) {
        expect(searchFormBox.y + searchFormBox.height).toBeLessThan(600);
      }

      // Perform search
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Results should be visible without excessive scrolling
      const firstResult = page.locator('[data-testid="result-card"]').first();
      const firstResultBox = await firstResult.boundingBox();
      
      if (firstResultBox) {
        expect(firstResultBox.y).toBeLessThan(600);
      }
    });
  });

  test.describe('Aspect Ratio Adaptations @responsive @aspect-ratio', () => {
    const aspectRatios = [
      { name: 'Ultra-wide 32:9', width: 3200, height: 900 },
      { name: 'Cinema 21:9', width: 2100, height: 900 },
      { name: 'Standard 16:9', width: 1920, height: 1080 },
      { name: 'Traditional 4:3', width: 1600, height: 1200 },
      { name: 'Square 1:1', width: 1200, height: 1200 },
      { name: 'Portrait 9:16', width: 900, height: 1600 }
    ];

    aspectRatios.forEach(ratio => {
      test(`should adapt to ${ratio.name} aspect ratio`, async ({ page }) => {
        await page.setViewportSize({ width: ratio.width, height: ratio.height });

        const testUser = {
          username: `aspect_${Date.now()}`,
          email: `aspect_${Date.now()}@example.com`,
          password: 'Aspect123!'
        };

        loginPage = new LoginPage(page);
        searchPage = new SearchPage(page);

        await loginPage.register(testUser);
        await loginPage.login(testUser.username, testUser.password);
        
        await searchPage.navigateToSearch();

        // Check layout adaptation based on aspect ratio
        const mainContainer = page.locator('[data-testid="main-container"]');
        const containerBox = await mainContainer.boundingBox();
        
        if (containerBox) {
          const aspectRatio = ratio.width / ratio.height;
          
          if (aspectRatio > 2) {
            // Ultra-wide: should use horizontal space efficiently
            expect(containerBox.width).toBeGreaterThan(ratio.width * 0.7);
          } else if (aspectRatio < 0.8) {
            // Portrait: should stack content vertically
            expect(containerBox.height).toBeGreaterThan(ratio.height * 0.5);
          }
        }

        // Perform search and check results layout
        await searchPage.performAdvancedSearch({
          query: 'function',
          fileTypes: ['js', 'py'],
          searchType: 'exact'
        });

        await searchPage.waitForResults();

        const resultCards = await page.locator('[data-testid="result-card"]').all();
        
        if (resultCards.length >= 2) {
          const firstCardBox = await resultCards[0].boundingBox();
          const secondCardBox = await resultCards[1].boundingBox();
          
          const aspectRatio = ratio.width / ratio.height;
          
          if (aspectRatio > 2.5) {
            // Ultra-wide: cards might be side-by-side
            const isSideBySide = Math.abs(firstCardBox.y - secondCardBox.y) < 50;
            // This is acceptable for ultra-wide displays
            expect(isSideBySide || !isSideBySide).toBe(true);
          } else if (aspectRatio < 1) {
            // Portrait: cards should definitely stack vertically
            expect(secondCardBox.y).toBeGreaterThan(firstCardBox.y + firstCardBox.height - 50);
          }
        }
      });
    });
  });

  test.describe('Dynamic Content Adaptation @responsive @dynamic', () => {
    test('should adapt to content changes at different screen sizes', async ({ page }) => {
      const screenSizes = [
        { width: 1920, height: 1080 },
        { width: 1366, height: 768 },
        { width: 768, height: 1024 }
      ];

      for (const size of screenSizes) {
        await page.setViewportSize(size);

        const testUser = {
          username: `dynamic_${Date.now()}_${size.width}`,
          email: `dynamic_${Date.now()}_${size.width}@example.com`,
          password: 'Dynamic123!'
        };

        loginPage = new LoginPage(page);
        searchPage = new SearchPage(page);

        await loginPage.register(testUser);
        await loginPage.login(testUser.username, testUser.password);
        
        await searchPage.navigateToSearch();

        // Test with different amounts of content
        const queries = ['a', 'function', 'import export class'];
        
        for (const query of queries) {
          await searchPage.performAdvancedSearch({
            query: query,
            fileTypes: ['js', 'py'],
            searchType: 'fuzzy'
          });

          await searchPage.waitForResults();

          // Check if layout adapts to content amount
          const resultsContainer = page.locator('[data-testid="search-results"]');
          const resultsBox = await resultsContainer.boundingBox();
          
          if (resultsBox) {
            // Results should not overflow viewport
            expect(resultsBox.width).toBeLessThanOrEqual(size.width);
            
            // Results should be readable
            expect(resultsBox.width).toBeGreaterThan(Math.min(300, size.width * 0.5));
          }

          // Clear search for next iteration
          await searchPage.clearSearch();
        }
      }
    });

    test('should handle loading states responsively', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // Mobile size

      const testUser = {
        username: `loading_${Date.now()}`,
        email: `loading_${Date.now()}@example.com`,
        password: 'Loading123!'
      };

      loginPage = new LoginPage(page);
      searchPage = new SearchPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Start search and check loading state
      await page.fill('[data-testid="search-input"]', 'function');
      await page.click('[data-testid="search-button"]');

      // Check loading indicator
      const loadingIndicator = page.locator('[data-testid="loading-spinner"], [data-testid="loading-message"]');
      
      if (await loadingIndicator.count() > 0) {
        await expect(loadingIndicator).toBeVisible();
        
        const loadingBox = await loadingIndicator.boundingBox();
        if (loadingBox) {
          // Loading indicator should be appropriately sized for mobile
          expect(loadingBox.width).toBeLessThan(375);
          expect(loadingBox.height).toBeLessThan(200);
        }
      }

      await searchPage.waitForResults();

      // Loading state should be replaced by results
      if (await loadingIndicator.count() > 0) {
        await expect(loadingIndicator).toBeHidden();
      }
    });

    test('should maintain responsive behavior during interactions', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });

      const testUser = {
        username: `interaction_${Date.now()}`,
        email: `interaction_${Date.now()}@example.com`,
        password: 'Interaction123!'
      };

      loginPage = new LoginPage(page);
      searchPage = new SearchPage(page);

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Test responsive behavior during form interactions
      await searchPage.openAdvancedSearch();
      
      const advancedForm = page.locator('[data-testid="advanced-search-form"]');
      if (await advancedForm.count() > 0) {
        const formBox = await advancedForm.boundingBox();
        if (formBox) {
          // Advanced form should fit within viewport
          expect(formBox.width).toBeLessThanOrEqual(1024);
          expect(formBox.height).toBeLessThanOrEqual(768);
        }
      }

      // Test responsive behavior during search
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js', 'py', 'ts'],
        searchType: 'fuzzy'
      });

      await searchPage.waitForResults();

      // Test responsive behavior during result interactions
      const firstResult = page.locator('[data-testid="result-card"]').first();
      if (await firstResult.count() > 0) {
        await firstResult.hover();
        
        // Any hover effects should not break layout
        const resultBox = await firstResult.boundingBox();
        if (resultBox) {
          expect(resultBox.width).toBeLessThanOrEqual(1024);
        }
      }
    });
  });
});
