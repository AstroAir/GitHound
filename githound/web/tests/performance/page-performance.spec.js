/**
 * Page Performance Tests
 * Tests page load times, rendering performance, and user interaction responsiveness
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');
const { PerformanceTestHelper } = require('../utils/performance-helper');

test.describe('Page Performance Tests', () => {
  let searchPage;
  let loginPage;
  let perfHelper;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    perfHelper = new PerformanceTestHelper(page);

    // Setup authenticated user
    const testUser = {
      username: `perf_${Date.now()}`,
      email: `perf_${Date.now()}@example.com`,
      password: 'Performance123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
  });

  test.describe('Page Load Performance @performance @load', () => {
    test('should load main pages within acceptable time limits', async ({ page }) => {
      const pages = [
        { path: '/', name: 'Home' },
        { path: '/search', name: 'Search' },
        { path: '/profile', name: 'Profile' },
        { path: '/settings', name: 'Settings' }
      ];

      for (const pageInfo of pages) {
        const startTime = Date.now();
        
        await page.goto(pageInfo.path);
        await page.waitForLoadState('networkidle');
        
        const loadTime = Date.now() - startTime;
        
        // Page should load within 3 seconds
        expect(loadTime).toBeLessThan(3000);
        
        // Measure Web Vitals
        const webVitals = await perfHelper.measureWebVitals();
        
        // First Contentful Paint should be under 1.8s
        expect(webVitals.fcp).toBeLessThan(1800);
        
        // Largest Contentful Paint should be under 2.5s
        expect(webVitals.lcp).toBeLessThan(2500);
        
        // Cumulative Layout Shift should be minimal
        expect(webVitals.cls).toBeLessThan(0.1);
        
        console.log(`${pageInfo.name} page - Load: ${loadTime}ms, FCP: ${webVitals.fcp}ms, LCP: ${webVitals.lcp}ms, CLS: ${webVitals.cls}`);
      }
    });

    test('should handle slow network conditions gracefully', async ({ page }) => {
      // Simulate slow 3G network
      const client = await page.context().newCDPSession(page);
      await client.send('Network.emulateNetworkConditions', {
        offline: false,
        downloadThroughput: 1.5 * 1024 * 1024 / 8, // 1.5 Mbps
        uploadThroughput: 750 * 1024 / 8,           // 750 Kbps
        latency: 300 // 300ms latency
      });

      const startTime = Date.now();
      
      await searchPage.navigateToSearch();
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      
      // Should still load within reasonable time on slow network (10 seconds)
      expect(loadTime).toBeLessThan(10000);
      
      // Page should be functional
      const isSearchFormVisible = await searchPage.isSearchFormVisible();
      expect(isSearchFormVisible).toBe(true);

      // Restore normal network conditions
      await client.send('Network.emulateNetworkConditions', {
        offline: false,
        downloadThroughput: -1,
        uploadThroughput: -1,
        latency: 0
      });
    });

    test('should optimize resource loading', async ({ page }) => {
      // Monitor network requests
      const requests = [];
      page.on('request', request => {
        requests.push({
          url: request.url(),
          resourceType: request.resourceType(),
          size: request.postDataBuffer()?.length || 0
        });
      });

      await searchPage.navigateToSearch();
      await page.waitForLoadState('networkidle');

      // Analyze resource loading
      const jsRequests = requests.filter(r => r.resourceType === 'script');
      const cssRequests = requests.filter(r => r.resourceType === 'stylesheet');
      const imageRequests = requests.filter(r => r.resourceType === 'image');

      // Should not load excessive resources
      expect(jsRequests.length).toBeLessThan(20);
      expect(cssRequests.length).toBeLessThan(10);
      
      // Images should be optimized
      imageRequests.forEach(img => {
        expect(img.size).toBeLessThan(500 * 1024); // Under 500KB per image
      });
    });

    test('should cache resources effectively', async ({ page }) => {
      // First visit
      await searchPage.navigateToSearch();
      await page.waitForLoadState('networkidle');

      const firstVisitRequests = [];
      page.on('request', request => {
        firstVisitRequests.push(request.url());
      });

      // Second visit (should use cache)
      await page.reload();
      await page.waitForLoadState('networkidle');

      const secondVisitRequests = [];
      page.on('request', request => {
        secondVisitRequests.push(request.url());
      });

      // Second visit should have fewer requests due to caching
      expect(secondVisitRequests.length).toBeLessThan(firstVisitRequests.length);
    });
  });

  test.describe('Search Performance @performance @search', () => {
    test('should perform searches within acceptable time limits', async () => {
      await searchPage.navigateToSearch();

      const searchQueries = [
        { query: 'function', type: 'exact' },
        { query: 'import', type: 'fuzzy' },
        { query: 'console.log', type: 'exact' },
        { query: 'async await', type: 'fuzzy' }
      ];

      for (const searchQuery of searchQueries) {
        const startTime = Date.now();
        
        await searchPage.performAdvancedSearch({
          query: searchQuery.query,
          fileTypes: ['js', 'py'],
          searchType: searchQuery.type
        });
        
        await searchPage.waitForResults();
        
        const searchTime = Date.now() - startTime;
        
        // Search should complete within 10 seconds
        expect(searchTime).toBeLessThan(10000);
        
        console.log(`Search "${searchQuery.query}" (${searchQuery.type}) completed in ${searchTime}ms`);
      }
    });

    test('should handle large result sets efficiently', async () => {
      await searchPage.navigateToSearch();

      // Perform search that returns many results
      const startTime = Date.now();
      
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js', 'py', 'ts', 'jsx'],
        searchType: 'fuzzy'
      });
      
      await searchPage.waitForResults();
      
      const searchTime = Date.now() - startTime;
      
      // Should handle large result sets within 15 seconds
      expect(searchTime).toBeLessThan(15000);
      
      // Check if results are paginated properly
      const hasPagination = await searchPage.hasPagination();
      if (hasPagination) {
        // Test pagination performance
        const paginationStartTime = Date.now();
        
        await searchPage.goToNextPage();
        await searchPage.waitForResults();
        
        const paginationTime = Date.now() - paginationStartTime;
        
        // Pagination should be fast (under 2 seconds)
        expect(paginationTime).toBeLessThan(2000);
      }
    });

    test('should maintain performance with complex search filters', async () => {
      await searchPage.navigateToSearch();

      const complexSearch = {
        query: 'function async await',
        fileTypes: ['js', 'ts', 'jsx', 'tsx'],
        searchType: 'fuzzy',
        dateRange: {
          from: '2023-01-01',
          to: '2024-12-31'
        },
        author: 'test',
        includeGlobs: ['src/**', 'lib/**'],
        excludeGlobs: ['node_modules/**', 'dist/**']
      };

      const startTime = Date.now();
      
      await searchPage.performAdvancedSearch(complexSearch);
      await searchPage.waitForResults();
      
      const searchTime = Date.now() - startTime;
      
      // Complex search should complete within 20 seconds
      expect(searchTime).toBeLessThan(20000);
    });

    test('should handle concurrent searches efficiently', async ({ browser }) => {
      const concurrentSearches = 5;
      const contexts = [];
      const searchPromises = [];

      try {
        // Create multiple browser contexts
        for (let i = 0; i < concurrentSearches; i++) {
          const context = await browser.newContext();
          contexts.push(context);
          
          const searchPromise = (async () => {
            const page = await context.newPage();
            const loginPageInstance = new LoginPage(page);
            const searchPageInstance = new SearchPage(page);
            
            // Setup user
            const testUser = {
              username: `concurrent_search_${Date.now()}_${i}`,
              email: `concurrent_search_${Date.now()}_${i}@example.com`,
              password: 'ConcurrentSearch123!'
            };
            
            await loginPageInstance.register(testUser);
            await loginPageInstance.login(testUser.username, testUser.password);
            
            // Perform search
            await searchPageInstance.navigateToSearch();
            
            const startTime = Date.now();
            
            await searchPageInstance.performAdvancedSearch({
              query: `search_${i}`,
              fileTypes: ['js'],
              searchType: 'exact'
            });
            
            await searchPageInstance.waitForResults();
            
            const searchTime = Date.now() - startTime;
            
            return {
              searchIndex: i,
              searchTime,
              success: true
            };
          })();
          
          searchPromises.push(searchPromise);
        }

        const results = await Promise.all(searchPromises);
        
        // All searches should complete successfully
        results.forEach(result => {
          expect(result.success).toBe(true);
          expect(result.searchTime).toBeLessThan(30000); // 30 seconds max for concurrent searches
        });
        
        // Average search time should be reasonable
        const averageTime = results.reduce((sum, r) => sum + r.searchTime, 0) / results.length;
        expect(averageTime).toBeLessThan(15000); // 15 seconds average

      } finally {
        // Cleanup
        await Promise.all(contexts.map(context => context.close()));
      }
    });
  });

  test.describe('UI Responsiveness @performance @ui', () => {
    test('should respond to user interactions quickly', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Test form interactions
      const interactions = [
        { action: 'fill search input', element: '[data-testid="search-input"]', value: 'test' },
        { action: 'select file type', element: '[data-testid="file-type-select"]', value: 'js' },
        { action: 'toggle advanced options', element: '[data-testid="advanced-toggle"]' }
      ];

      for (const interaction of interactions) {
        const startTime = Date.now();
        
        if (interaction.value) {
          await page.fill(interaction.element, interaction.value);
        } else {
          await page.click(interaction.element);
        }
        
        // Wait for any visual feedback
        await page.waitForTimeout(100);
        
        const responseTime = Date.now() - startTime;
        
        // UI should respond within 200ms
        expect(responseTime).toBeLessThan(200);
        
        console.log(`${interaction.action} response time: ${responseTime}ms`);
      }
    });

    test('should handle rapid user interactions', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Rapid typing simulation
      const searchInput = '[data-testid="search-input"]';
      const testText = 'rapid typing test';
      
      const startTime = Date.now();
      
      // Type rapidly (one character every 50ms)
      for (const char of testText) {
        await page.type(searchInput, char, { delay: 50 });
      }
      
      const typingTime = Date.now() - startTime;
      
      // Should handle rapid typing without lag
      expect(typingTime).toBeLessThan(testText.length * 100); // Allow 100ms per character max
      
      // Final value should be correct
      const finalValue = await page.inputValue(searchInput);
      expect(finalValue).toContain(testText);
    });

    test('should maintain performance during result rendering', async ({ page }) => {
      await searchPage.navigateToSearch();

      // Monitor rendering performance
      await page.evaluate(() => {
        window.renderingMetrics = {
          startTime: performance.now(),
          frameCount: 0
        };
        
        // Monitor frame rate
        function countFrames() {
          window.renderingMetrics.frameCount++;
          requestAnimationFrame(countFrames);
        }
        requestAnimationFrame(countFrames);
      });

      // Perform search that returns results
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });
      
      await searchPage.waitForResults();
      
      // Check rendering performance
      const renderingMetrics = await page.evaluate(() => {
        const endTime = performance.now();
        const duration = endTime - window.renderingMetrics.startTime;
        const fps = (window.renderingMetrics.frameCount / duration) * 1000;
        
        return {
          duration,
          frameCount: window.renderingMetrics.frameCount,
          fps
        };
      });

      // Should maintain reasonable frame rate (at least 30 FPS)
      expect(renderingMetrics.fps).toBeGreaterThan(30);
      
      console.log(`Rendering: ${renderingMetrics.fps.toFixed(2)} FPS over ${renderingMetrics.duration.toFixed(2)}ms`);
    });

    test('should handle scroll performance efficiently', async ({ page }) => {
      await searchPage.navigateToSearch();
      
      // Perform search to get results
      await searchPage.performAdvancedSearch({
        query: 'import',
        fileTypes: ['js', 'py'],
        searchType: 'exact'
      });
      
      await searchPage.waitForResults();

      // Test scroll performance
      const scrollStartTime = Date.now();
      
      // Scroll through results
      for (let i = 0; i < 10; i++) {
        await page.evaluate(() => {
          window.scrollBy(0, 200);
        });
        await page.waitForTimeout(50);
      }
      
      const scrollTime = Date.now() - scrollStartTime;
      
      // Scrolling should be smooth (under 1 second for 10 scrolls)
      expect(scrollTime).toBeLessThan(1000);
      
      // Check for scroll jank
      const scrollMetrics = await page.evaluate(() => {
        return {
          scrollTop: window.pageYOffset,
          documentHeight: document.documentElement.scrollHeight
        };
      });
      
      expect(scrollMetrics.scrollTop).toBeGreaterThan(0);
    });
  });

  test.describe('Memory Performance @performance @memory', () => {
    test('should manage memory efficiently during extended use', async ({ page }) => {
      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      await searchPage.navigateToSearch();

      // Perform multiple searches to simulate extended use
      const searches = [
        'function', 'import', 'export', 'class', 'const',
        'async', 'await', 'promise', 'callback', 'event'
      ];

      for (const query of searches) {
        await searchPage.performAdvancedSearch({
          query: query,
          fileTypes: ['js'],
          searchType: 'exact'
        });
        
        await searchPage.waitForResults();
        
        // Clear results before next search
        await searchPage.clearSearch();
      }

      // Get final memory usage
      const finalMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      if (initialMemory && finalMemory) {
        const memoryIncrease = finalMemory.used - initialMemory.used;
        const memoryIncreasePercent = (memoryIncrease / initialMemory.used) * 100;
        
        // Memory increase should be reasonable (less than 100% increase)
        expect(memoryIncreasePercent).toBeLessThan(100);
        
        // Should not approach memory limit
        const memoryUsagePercent = (finalMemory.used / finalMemory.limit) * 100;
        expect(memoryUsagePercent).toBeLessThan(80);
        
        console.log(`Memory usage: ${memoryIncreasePercent.toFixed(2)}% increase, ${memoryUsagePercent.toFixed(2)}% of limit`);
      }
    });

    test('should handle memory pressure gracefully', async ({ page }) => {
      // Create memory pressure
      await page.evaluate(() => {
        window.memoryPressureTest = [];
        
        // Gradually increase memory usage
        for (let i = 0; i < 1000; i++) {
          window.memoryPressureTest.push(new Array(1000).fill(`memory test data ${i}`));
        }
      });

      await searchPage.navigateToSearch();

      // Application should still function under memory pressure
      const searchStartTime = Date.now();
      
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js'],
        searchType: 'exact'
      });
      
      await searchPage.waitForResults();
      
      const searchTime = Date.now() - searchStartTime;
      
      // Should still complete search within reasonable time
      expect(searchTime).toBeLessThan(15000);
      
      // Clean up memory pressure
      await page.evaluate(() => {
        window.memoryPressureTest = null;
      });
    });
  });
});
