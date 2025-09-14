/**
 * Performance Benchmark Tests
 * Comprehensive performance benchmarking for GitHound web interface
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');
const { PerformanceTestHelper } = require('../utils/performance-helper');

test.describe('Performance Benchmarks', () => {
  let searchPage;
  let loginPage;
  let perfHelper;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    perfHelper = new PerformanceTestHelper(page);
  });

  test.describe('Core Web Vitals @performance @vitals', () => {
    test('should meet Core Web Vitals thresholds', async ({ page }) => {
      // Navigate to homepage
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Measure Core Web Vitals
      const vitals = await page.evaluate(() => {
        return new Promise((resolve) => {
          const metrics = {};
          let metricsCollected = 0;
          const totalMetrics = 3;

          // First Contentful Paint (FCP)
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach((entry) => {
              if (entry.name === 'first-contentful-paint') {
                metrics.fcp = entry.startTime;
                metricsCollected++;
                if (metricsCollected === totalMetrics) resolve(metrics);
              }
            });
          }).observe({ entryTypes: ['paint'] });

          // Largest Contentful Paint (LCP)
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            if (lastEntry) {
              metrics.lcp = lastEntry.startTime;
              metricsCollected++;
              if (metricsCollected === totalMetrics) resolve(metrics);
            }
          }).observe({ entryTypes: ['largest-contentful-paint'] });

          // Cumulative Layout Shift (CLS)
          new PerformanceObserver((list) => {
            let clsValue = 0;
            const entries = list.getEntries();
            entries.forEach((entry) => {
              if (!entry.hadRecentInput) {
                clsValue += entry.value;
              }
            });
            metrics.cls = clsValue;
            metricsCollected++;
            if (metricsCollected === totalMetrics) resolve(metrics);
          }).observe({ entryTypes: ['layout-shift'] });

          // Fallback timeout
          setTimeout(() => {
            resolve(metrics);
          }, 5000);
        });
      });

      // Assert Core Web Vitals thresholds
      if (vitals.fcp) {
        expect(vitals.fcp).toBeLessThan(1800); // Good FCP < 1.8s
      }
      if (vitals.lcp) {
        expect(vitals.lcp).toBeLessThan(2500); // Good LCP < 2.5s
      }
      if (vitals.cls !== undefined) {
        expect(vitals.cls).toBeLessThan(0.1); // Good CLS < 0.1
      }
    });

    test('should have fast First Input Delay', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Simulate user interaction and measure FID
      const fidStart = Date.now();
      await page.click('[data-testid="login-button"]');
      const fidEnd = Date.now();
      
      const fid = fidEnd - fidStart;
      expect(fid).toBeLessThan(100); // Good FID < 100ms
    });
  });

  test.describe('Search Performance Benchmarks @performance @search', () => {
    test('should perform search operations within time limits', async ({ page }) => {
      // Setup authenticated user
      const testUser = {
        username: `search_perf_${Date.now()}`,
        email: `search_perf_${Date.now()}@example.com`,
        password: 'SearchPerf123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Measure search form interaction time
      const formStartTime = Date.now();
      await page.fill('[data-testid="repo-path-input"]', '/test/repo');
      await page.fill('[data-testid="search-query-input"]', 'function');
      const formEndTime = Date.now();
      
      const formInteractionTime = formEndTime - formStartTime;
      expect(formInteractionTime).toBeLessThan(500); // Form should be responsive

      // Measure search submission time
      const searchStartTime = Date.now();
      await page.click('[data-testid="submit-search"]');
      
      // Wait for search to start (not complete)
      await page.waitForSelector('[data-testid="progress-message"]', { state: 'visible' });
      const searchInitTime = Date.now() - searchStartTime;
      
      expect(searchInitTime).toBeLessThan(1000); // Search should start quickly
    });

    test('should handle large result sets efficiently', async ({ page }) => {
      const testUser = {
        username: `large_results_${Date.now()}`,
        email: `large_results_${Date.now()}@example.com`,
        password: 'LargeResults123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Simulate search with many results
      await page.fill('[data-testid="repo-path-input"]', '/large/repo');
      await page.fill('[data-testid="search-query-input"]', 'common_term');
      
      const renderStartTime = Date.now();
      await page.click('[data-testid="submit-search"]');
      
      // Wait for results to appear
      await page.waitForSelector('[data-testid="results-container"]', { state: 'visible' });
      const renderTime = Date.now() - renderStartTime;
      
      expect(renderTime).toBeLessThan(3000); // Results should render quickly
    });
  });

  test.describe('Memory Usage Benchmarks @performance @memory', () => {
    test('should maintain reasonable memory usage', async ({ page }) => {
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

      if (initialMemory) {
        // Perform memory-intensive operations
        const testUser = {
          username: `memory_test_${Date.now()}`,
          email: `memory_test_${Date.now()}@example.com`,
          password: 'MemoryTest123!'
        };

        await loginPage.register(testUser);
        await loginPage.login(testUser.username, testUser.password);
        
        // Navigate through multiple pages
        await page.goto('/search');
        await page.goto('/profile');
        await page.goto('/');
        
        // Get final memory usage
        const finalMemory = await page.evaluate(() => {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        });

        // Memory usage should not increase dramatically
        const memoryIncrease = finalMemory.used - initialMemory.used;
        const memoryIncreasePercent = (memoryIncrease / initialMemory.used) * 100;
        
        expect(memoryIncreasePercent).toBeLessThan(50); // Memory should not increase by more than 50%
      }
    });
  });

  test.describe('Network Performance Benchmarks @performance @network', () => {
    test('should minimize network requests', async ({ page }) => {
      const requests = [];
      
      page.on('request', request => {
        requests.push({
          url: request.url(),
          method: request.method(),
          resourceType: request.resourceType()
        });
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Count different types of requests
      const requestTypes = requests.reduce((acc, req) => {
        acc[req.resourceType] = (acc[req.resourceType] || 0) + 1;
        return acc;
      }, {});

      // Should not have excessive requests
      expect(requests.length).toBeLessThan(50); // Total requests should be reasonable
      expect(requestTypes.script || 0).toBeLessThan(10); // JavaScript files
      expect(requestTypes.stylesheet || 0).toBeLessThan(5); // CSS files
      expect(requestTypes.image || 0).toBeLessThan(20); // Images
    });

    test('should have efficient resource loading', async ({ page }) => {
      const resourceTimings = [];
      
      page.on('response', async response => {
        const timing = await response.timing();
        resourceTimings.push({
          url: response.url(),
          status: response.status(),
          timing: timing
        });
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Check resource loading times
      const slowResources = resourceTimings.filter(resource => {
        const totalTime = resource.timing.responseEnd - resource.timing.requestStart;
        return totalTime > 2000; // Resources taking more than 2 seconds
      });

      expect(slowResources.length).toBeLessThan(3); // Should have few slow resources
    });
  });

  test.describe('Rendering Performance Benchmarks @performance @rendering', () => {
    test('should have smooth animations and transitions', async ({ page }) => {
      await page.goto('/');
      
      // Measure frame rate during animations
      const frameRate = await page.evaluate(() => {
        return new Promise((resolve) => {
          let frames = 0;
          const startTime = performance.now();
          
          function countFrames() {
            frames++;
            if (performance.now() - startTime < 1000) {
              requestAnimationFrame(countFrames);
            } else {
              resolve(frames);
            }
          }
          
          requestAnimationFrame(countFrames);
        });
      });

      // Should maintain reasonable frame rate (at least 30 FPS)
      expect(frameRate).toBeGreaterThan(30);
    });

    test('should handle DOM manipulation efficiently', async ({ page }) => {
      const testUser = {
        username: `dom_perf_${Date.now()}`,
        email: `dom_perf_${Date.now()}@example.com`,
        password: 'DomPerf123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
      
      await searchPage.navigateToSearch();

      // Measure DOM manipulation time
      const domStartTime = Date.now();
      
      // Simulate adding many search results
      await page.evaluate(() => {
        const container = document.querySelector('[data-testid="results-container"]');
        for (let i = 0; i < 100; i++) {
          const div = document.createElement('div');
          div.className = 'result-item';
          div.innerHTML = `<p>Result ${i}</p>`;
          container.appendChild(div);
        }
      });
      
      const domEndTime = Date.now();
      const domManipulationTime = domEndTime - domStartTime;
      
      expect(domManipulationTime).toBeLessThan(1000); // DOM updates should be fast
    });
  });
});
