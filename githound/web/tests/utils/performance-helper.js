/**
 * Performance testing utilities for GitHound web tests.
 * Provides helpers for measuring and validating performance metrics.
 */

class PerformanceTestHelper {
  constructor() {
    this.metrics = new Map();
    this.thresholds = {
      pageLoad: 3000,        // 3 seconds
      apiResponse: 2000,     // 2 seconds
      searchResponse: 5000,  // 5 seconds
      exportGeneration: 10000, // 10 seconds
      firstContentfulPaint: 1500, // 1.5 seconds
      largestContentfulPaint: 2500, // 2.5 seconds
      cumulativeLayoutShift: 0.1,
      firstInputDelay: 100
    };
  }

  /**
   * Measure page load performance
   */
  async measurePageLoad(page, url) {
    const startTime = Date.now();

    // Start performance measurement
    await page.goto(url, { waitUntil: 'networkidle' });

    const loadTime = Date.now() - startTime;

    // Get Web Vitals metrics
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        const metrics = {};

        // First Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.name === 'first-contentful-paint') {
              metrics.firstContentfulPaint = entry.startTime;
            }
          });
        }).observe({ entryTypes: ['paint'] });

        // Largest Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          metrics.largestContentfulPaint = lastEntry.startTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // Cumulative Layout Shift
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          metrics.cumulativeLayoutShift = clsValue;
        }).observe({ entryTypes: ['layout-shift'] });

        // First Input Delay
        new PerformanceObserver((list) => {
          const firstInput = list.getEntries()[0];
          if (firstInput) {
            metrics.firstInputDelay = firstInput.processingStart - firstInput.startTime;
          }
        }).observe({ entryTypes: ['first-input'] });

        // Resolve after a short delay to collect metrics
        setTimeout(() => resolve(metrics), 1000);
      });
    });

    const performanceMetrics = {
      url,
      loadTime,
      ...webVitals,
      timestamp: new Date().toISOString()
    };

    this.metrics.set(`pageLoad_${url}`, performanceMetrics);
    return performanceMetrics;
  }

  /**
   * Measure API response time
   */
  async measureApiResponse(page, endpoint, requestData = null) {
    const startTime = Date.now();

    const response = await page.evaluate(async (endpoint, data) => {
      const options = {
        method: data ? 'POST' : 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(endpoint, options);
      return {
        status: response.status,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries())
      };
    }, endpoint, requestData);

    const responseTime = Date.now() - startTime;

    const metrics = {
      endpoint,
      responseTime,
      status: response.status,
      success: response.ok,
      timestamp: new Date().toISOString()
    };

    this.metrics.set(`api_${endpoint}`, metrics);
    return metrics;
  }

  /**
   * Measure search performance
   */
  async measureSearchPerformance(page, searchData) {
    const startTime = Date.now();

    // Fill search form
    await page.fill('[data-testid="repo-path-input"]', searchData.repoPath);
    await page.fill('[data-testid="search-query-input"]', searchData.query);

    // Start search
    await page.click('[data-testid="submit-search"]');

    // Wait for search to complete
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 30000 });

    const searchTime = Date.now() - startTime;

    // Count results
    const resultCount = await page.locator('[data-testid="result-card"]').count();

    const metrics = {
      searchQuery: searchData.query,
      searchTime,
      resultCount,
      throughput: resultCount / (searchTime / 1000), // results per second
      timestamp: new Date().toISOString()
    };

    this.metrics.set(`search_${searchData.query}`, metrics);
    return metrics;
  }

  /**
   * Measure memory usage
   */
  async measureMemoryUsage(page) {
    const memoryInfo = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });

    if (memoryInfo) {
      const metrics = {
        ...memoryInfo,
        memoryUsagePercent: (memoryInfo.usedJSHeapSize / memoryInfo.totalJSHeapSize) * 100,
        timestamp: new Date().toISOString()
      };

      this.metrics.set('memory_usage', metrics);
      return metrics;
    }

    return null;
  }

  /**
   * Run concurrent user simulation
   */
  async simulateConcurrentUsers(browser, userCount, testFunction) {
    const startTime = Date.now();
    const userPromises = [];

    for (let i = 0; i < userCount; i++) {
      const userPromise = (async () => {
        const context = await browser.newContext();
        const page = await context.newPage();

        try {
          const userStartTime = Date.now();
          await testFunction(page, i);
          const userEndTime = Date.now();

          return {
            userId: i,
            duration: userEndTime - userStartTime,
            success: true
          };
        } catch (error) {
          return {
            userId: i,
            error: error.message,
            success: false
          };
        } finally {
          await context.close();
        }
      })();

      userPromises.push(userPromise);
    }

    const results = await Promise.all(userPromises);
    const totalTime = Date.now() - startTime;

    const successfulUsers = results.filter(r => r.success);
    const failedUsers = results.filter(r => !r.success);

    const metrics = {
      userCount,
      totalTime,
      successfulUsers: successfulUsers.length,
      failedUsers: failedUsers.length,
      successRate: (successfulUsers.length / userCount) * 100,
      averageUserTime: successfulUsers.reduce((sum, r) => sum + r.duration, 0) / successfulUsers.length,
      results,
      timestamp: new Date().toISOString()
    };

    this.metrics.set('concurrent_users', metrics);
    return metrics;
  }

  /**
   * Validate performance against thresholds
   */
  validatePerformance(metricKey, customThresholds = {}) {
    const metrics = this.metrics.get(metricKey);
    if (!metrics) {
      throw new Error(`Metrics not found for key: ${metricKey}`);
    }

    const thresholds = { ...this.thresholds, ...customThresholds };
    const violations = [];

    // Check various performance thresholds
    if (metrics.loadTime && metrics.loadTime > thresholds.pageLoad) {
      violations.push(`Page load time ${metrics.loadTime}ms exceeds threshold ${thresholds.pageLoad}ms`);
    }

    if (metrics.responseTime && metrics.responseTime > thresholds.apiResponse) {
      violations.push(`API response time ${metrics.responseTime}ms exceeds threshold ${thresholds.apiResponse}ms`);
    }

    if (metrics.searchTime && metrics.searchTime > thresholds.searchResponse) {
      violations.push(`Search time ${metrics.searchTime}ms exceeds threshold ${thresholds.searchResponse}ms`);
    }

    if (metrics.firstContentfulPaint && metrics.firstContentfulPaint > thresholds.firstContentfulPaint) {
      violations.push(`First Contentful Paint ${metrics.firstContentfulPaint}ms exceeds threshold ${thresholds.firstContentfulPaint}ms`);
    }

    if (metrics.largestContentfulPaint && metrics.largestContentfulPaint > thresholds.largestContentfulPaint) {
      violations.push(`Largest Contentful Paint ${metrics.largestContentfulPaint}ms exceeds threshold ${thresholds.largestContentfulPaint}ms`);
    }

    if (metrics.cumulativeLayoutShift && metrics.cumulativeLayoutShift > thresholds.cumulativeLayoutShift) {
      violations.push(`Cumulative Layout Shift ${metrics.cumulativeLayoutShift} exceeds threshold ${thresholds.cumulativeLayoutShift}`);
    }

    if (metrics.firstInputDelay && metrics.firstInputDelay > thresholds.firstInputDelay) {
      violations.push(`First Input Delay ${metrics.firstInputDelay}ms exceeds threshold ${thresholds.firstInputDelay}ms`);
    }

    return {
      passed: violations.length === 0,
      violations,
      metrics
    };
  }

  /**
   * Get all collected metrics
   */
  getAllMetrics() {
    return Object.fromEntries(this.metrics);
  }

  /**
   * Generate performance report
   */
  generateReport() {
    const allMetrics = this.getAllMetrics();
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: this.metrics.size,
        thresholds: this.thresholds
      },
      metrics: allMetrics
    };

    return report;
  }

  /**
   * Clear all metrics
   */
  clearMetrics() {
    this.metrics.clear();
  }
}

module.exports = PerformanceTestHelper;
