/**
 * WCAG Compliance Tests
 * Tests accessibility compliance using axe-playwright and manual accessibility checks
 */

const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const { SearchPage, LoginPage } = require('../pages');
const { AccessibilityTestHelper } = require('../utils/accessibility-helper');

test.describe('WCAG Compliance Tests', () => {
  let searchPage;
  let loginPage;
  let a11yHelper;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    a11yHelper = new AccessibilityTestHelper(page);

    // Setup authenticated user
    const testUser = {
      username: `a11y_${Date.now()}`,
      email: `a11y_${Date.now()}@example.com`,
      password: 'Accessibility123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
  });

  test.describe('Automated Accessibility Testing @accessibility @axe', () => {
    test('should pass axe accessibility tests on main pages', async ({ page }) => {
      const pages = [
        { path: '/', name: 'Home' },
        { path: '/search', name: 'Search' },
        { path: '/profile', name: 'Profile' },
        { path: '/settings', name: 'Settings' }
      ];

      for (const pageInfo of pages) {
        await page.goto(pageInfo.path);
        await page.waitForLoadState('networkidle');

        // Run axe accessibility scan
        const accessibilityScanResults = await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
          .analyze();

        // Should have no accessibility violations
        expect(accessibilityScanResults.violations).toEqual([]);

        console.log(`${pageInfo.name} page: ${accessibilityScanResults.passes.length} accessibility checks passed`);
      }
    });

    test('should pass axe tests on search results page', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Perform search to get results
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Run accessibility scan on results page
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .exclude('[data-testid="loading-spinner"]') // Exclude loading elements
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('should pass axe tests on forms and interactive elements', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Test search form accessibility
      const searchFormResults = await new AxeBuilder({ page })
        .include('[data-testid="search-form"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(searchFormResults.violations).toEqual([]);

      // Test advanced search form
      await searchPage.openAdvancedSearch();

      const advancedFormResults = await new AxeBuilder({ page })
        .include('[data-testid="advanced-search-form"]')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(advancedFormResults.violations).toEqual([]);
    });

    test('should pass axe tests with custom rules', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Run with custom accessibility rules
      const customResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .withRules(['color-contrast', 'keyboard-navigation', 'focus-management'])
        .analyze();

      expect(customResults.violations).toEqual([]);

      // Check specific accessibility concerns
      const colorContrastResults = await new AxeBuilder({ page })
        .withRules(['color-contrast'])
        .analyze();

      expect(colorContrastResults.violations).toEqual([]);
    });

    test('should handle dynamic content accessibility', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Initial accessibility check
      const initialResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(initialResults.violations).toEqual([]);

      // Perform search to add dynamic content
      await searchPage.performAdvancedSearch({
        query: 'import',
        fileTypes: ['py'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Check accessibility after dynamic content is loaded
      const dynamicResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .exclude('[data-testid="loading-spinner"]')
        .analyze();

      expect(dynamicResults.violations).toEqual([]);
    });
  });

  test.describe('Keyboard Navigation Tests @accessibility @keyboard', () => {
    test('should support full keyboard navigation', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Test tab navigation through main elements
      const tabOrder = await a11yHelper.getTabOrder();

      expect(tabOrder.length).toBeGreaterThan(0);

      // Should be able to reach all interactive elements
      const interactiveElements = [
        '[data-testid="search-input"]',
        '[data-testid="search-button"]',
        '[data-testid="advanced-toggle"]',
        '[data-testid="file-type-select"]'
      ];

      for (const selector of interactiveElements) {
        const isReachable = await a11yHelper.isElementReachableByKeyboard(selector);
        expect(isReachable).toBe(true);
      }
    });

    test('should handle keyboard shortcuts correctly', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Test common keyboard shortcuts
      const shortcuts = [
        { key: 'Tab', description: 'Navigate forward' },
        { key: 'Shift+Tab', description: 'Navigate backward' },
        { key: 'Enter', description: 'Activate element' },
        { key: 'Space', description: 'Activate button/checkbox' },
        { key: 'Escape', description: 'Close modal/dropdown' }
      ];

      for (const shortcut of shortcuts) {
        const result = await a11yHelper.testKeyboardShortcut(shortcut.key);
        expect(result.handled).toBe(true);
      }
    });

    test('should provide proper focus management', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Test focus indicators
      const focusableElements = await page.locator('[tabindex]:not([tabindex="-1"]), button, input, select, textarea, a[href]').all();

      for (const element of focusableElements.slice(0, 5)) { // Test first 5 elements
        await element.focus();

        // Check if focus is visible
        const hasFocusIndicator = await a11yHelper.hasFocusIndicator(element);
        expect(hasFocusIndicator).toBe(true);
      }
    });

    test('should handle modal keyboard navigation', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Open a modal (e.g., advanced search)
      await searchPage.openAdvancedSearch();

      // Test focus trap in modal
      const isFocusTrapped = await a11yHelper.testFocusTrap('[data-testid="advanced-search-modal"]');
      expect(isFocusTrapped).toBe(true);

      // Test escape key closes modal
      await page.keyboard.press('Escape');

      const isModalClosed = await page.locator('[data-testid="advanced-search-modal"]').isHidden();
      expect(isModalClosed).toBe(true);
    });

    test('should support arrow key navigation in lists', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Perform search to get results
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Test arrow key navigation in search results
      const resultsList = page.locator('[data-testid="search-results"]');
      await resultsList.focus();

      // Test down arrow navigation
      await page.keyboard.press('ArrowDown');
      const firstItemFocused = await a11yHelper.isElementFocused('[data-testid="result-card"]:first-child');
      expect(firstItemFocused).toBe(true);

      // Test up arrow navigation
      await page.keyboard.press('ArrowUp');
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('ArrowDown');

      const secondItemFocused = await a11yHelper.isElementFocused('[data-testid="result-card"]:nth-child(2)');
      expect(secondItemFocused).toBe(true);
    });
  });

  test.describe('Screen Reader Compatibility @accessibility @screenreader', () => {
    test('should provide proper ARIA labels and descriptions', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Check for proper ARIA labels
      const elementsWithAriaLabels = await page.locator('[aria-label], [aria-labelledby], [aria-describedby]').all();

      expect(elementsWithAriaLabels.length).toBeGreaterThan(0);

      // Verify ARIA labels are meaningful
      for (const element of elementsWithAriaLabels.slice(0, 10)) {
        const ariaLabel = await element.getAttribute('aria-label');
        const ariaLabelledBy = await element.getAttribute('aria-labelledby');
        const ariaDescribedBy = await element.getAttribute('aria-describedby');

        if (ariaLabel) {
          expect(ariaLabel.trim().length).toBeGreaterThan(0);
          expect(ariaLabel).not.toBe('undefined');
        }

        if (ariaLabelledBy) {
          const labelElement = page.locator(`#${ariaLabelledBy}`);
          expect(await labelElement.count()).toBeGreaterThan(0);
        }

        if (ariaDescribedBy) {
          const descElement = page.locator(`#${ariaDescribedBy}`);
          expect(await descElement.count()).toBeGreaterThan(0);
        }
      }
    });

    test('should provide proper heading structure', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Check heading hierarchy
      const headings = await a11yHelper.getHeadingStructure();

      expect(headings.length).toBeGreaterThan(0);

      // Should start with h1
      expect(headings[0].level).toBe(1);

      // Should not skip heading levels
      for (let i = 1; i < headings.length; i++) {
        const currentLevel = headings[i].level;
        const previousLevel = headings[i - 1].level;

        // Should not skip more than one level
        expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
      }
    });

    test('should provide proper form labels and descriptions', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Check form inputs have proper labels
      const formInputs = await page.locator('input, select, textarea').all();

      for (const input of formInputs) {
        const hasLabel = await a11yHelper.hasProperLabel(input);
        expect(hasLabel).toBe(true);
      }
    });

    test('should announce dynamic content changes', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Check for ARIA live regions
      const liveRegions = await page.locator('[aria-live], [role="status"], [role="alert"]').all();
      expect(liveRegions.length).toBeGreaterThan(0);

      // Perform search to trigger dynamic content
      await searchPage.performAdvancedSearch({
        query: 'test',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      // Check if search status is announced
      const searchStatus = page.locator('[data-testid="search-status"][aria-live]');
      expect(await searchStatus.count()).toBeGreaterThan(0);
    });

    test('should provide proper table accessibility', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Perform search to get results in table format
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Check if results table has proper accessibility
      const tables = await page.locator('table').all();

      for (const table of tables) {
        // Should have table headers
        const headers = await table.locator('th').all();
        expect(headers.length).toBeGreaterThan(0);

        // Headers should have proper scope
        for (const header of headers) {
          const scope = await header.getAttribute('scope');
          expect(['col', 'row', 'colgroup', 'rowgroup']).toContain(scope);
        }

        // Should have caption or aria-label
        const hasCaption = await table.locator('caption').count() > 0;
        const hasAriaLabel = await table.getAttribute('aria-label') !== null;

        expect(hasCaption || hasAriaLabel).toBe(true);
      }
    });
  });

  test.describe('Color and Contrast Tests @accessibility @contrast', () => {
    test('should meet WCAG color contrast requirements', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Test color contrast using axe
      const contrastResults = await new AxeBuilder({ page })
        .withRules(['color-contrast'])
        .analyze();

      expect(contrastResults.violations).toEqual([]);
    });

    test('should be usable without color alone', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Simulate color blindness by removing color information
      await page.addStyleTag({
        content: `
          * {
            filter: grayscale(100%) !important;
          }
        `
      });

      // Perform search
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      // Should still be able to distinguish different states/types
      const statusIndicators = await page.locator('[data-testid*="status"], [data-testid*="type"]').all();

      for (const indicator of statusIndicators) {
        // Should have text content or other non-color indicators
        const textContent = await indicator.textContent();
        const hasIcon = await indicator.locator('svg, i, [class*="icon"]').count() > 0;
        const hasPattern = await indicator.evaluate(el => {
          const style = window.getComputedStyle(el);
          return style.backgroundImage !== 'none' || style.textDecoration !== 'none';
        });

        expect(textContent?.trim().length > 0 || hasIcon || hasPattern).toBe(true);
      }
    });

    test('should support high contrast mode', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Simulate high contrast mode
      await page.addStyleTag({
        content: `
          @media (prefers-contrast: high) {
            * {
              background: black !important;
              color: white !important;
              border-color: white !important;
            }
          }
        `
      });

      // Force high contrast media query
      await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });

      // Check if interface is still usable
      const isSearchFormVisible = await searchPage.isSearchFormVisible();
      expect(isSearchFormVisible).toBe(true);

      // Run accessibility scan in high contrast mode
      const highContrastResults = await new AxeBuilder({ page })
        .withTags(['wcag2aa'])
        .analyze();

      expect(highContrastResults.violations).toEqual([]);
    });
  });

  test.describe('Motion and Animation Accessibility @accessibility @motion', () => {
    test('should respect reduced motion preferences', async ({ page }) => {
      // Set reduced motion preference
      await page.emulateMedia({ reducedMotion: 'reduce' });

      await searchPage.navigateToSearch();

      // Check if animations are disabled or reduced
      const animatedElements = await page.locator('[class*="animate"], [class*="transition"]').all();

      for (const element of animatedElements.slice(0, 5)) {
        const animationDuration = await element.evaluate(el => {
          const style = window.getComputedStyle(el);
          return style.animationDuration;
        });

        // Animation should be disabled or very short
        expect(animationDuration === '0s' || animationDuration === 'none').toBe(true);
      }
    });

    test('should provide pause controls for auto-playing content', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Look for auto-playing content
      const autoPlayElements = await page.locator('[autoplay], [data-autoplay]').all();

      for (const element of autoPlayElements) {
        // Should have pause/stop controls nearby
        const pauseControl = await element.locator('xpath=..//*[contains(@aria-label, "pause") or contains(@aria-label, "stop")]').count();
        expect(pauseControl).toBeGreaterThan(0);
      }
    });

    test('should not trigger seizures with flashing content', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Check for potentially problematic flashing content
      const flashingElements = await page.locator('[class*="flash"], [class*="blink"]').all();

      for (const element of flashingElements) {
        // Should not flash more than 3 times per second
        const animationIterationCount = await element.evaluate(el => {
          const style = window.getComputedStyle(el);
          return style.animationIterationCount;
        });

        const animationDuration = await element.evaluate(el => {
          const style = window.getComputedStyle(el);
          return parseFloat(style.animationDuration);
        });

        if (animationIterationCount === 'infinite' && animationDuration > 0) {
          const flashesPerSecond = 1 / animationDuration;
          expect(flashesPerSecond).toBeLessThanOrEqual(3);
        }
      }
    });
  });
});
