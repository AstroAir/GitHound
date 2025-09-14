// @ts-check
const { defineConfig, devices } = require('@playwright/test');
require('dotenv').config();

/**
 * Enhanced Playwright configuration for GitHound web testing
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: '.',
  /* Run tests in files in parallel */
  fullyParallel: !process.env.CI || process.env.PARALLEL_TESTS === 'true',
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 3 : 1,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 2 : process.env.WORKERS ? parseInt(process.env.WORKERS) : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: process.env.CI ? [
    ['github'],
    ['html', { outputFolder: 'test-results/html-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['blob', { outputDir: 'test-results/blob-report' }],
    ['./utils/custom-reporter.js', { outputDir: 'test-results/custom' }]
  ] : [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['./utils/custom-reporter.js', { outputDir: 'test-results/custom' }],
    ['line']
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.BASE_URL || 'http://localhost:8000',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: process.env.CI ? 'on-first-retry' : 'retain-on-failure',

    /* Take screenshot on failure */
    screenshot: process.env.CI ? 'only-on-failure' : 'on',

    /* Record video on failure */
    video: process.env.CI ? 'retain-on-failure' : 'on-first-retry',

    /* Global timeout for each action */
    actionTimeout: process.env.CI ? 45000 : 30000,

    /* Global timeout for navigation */
    navigationTimeout: process.env.CI ? 45000 : 30000,

    /* Extra HTTP headers */
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },

    /* Ignore HTTPS errors */
    ignoreHTTPSErrors: true,

    /* Locale for testing */
    locale: 'en-US',

    /* Timezone for testing */
    timezoneId: 'America/New_York',
  },

  /* Configure projects for major browsers */
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 }
      },
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 }
      },
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1280, height: 720 }
      },
    },

    // Branded browsers
    {
      name: 'Microsoft Edge',
      use: {
        ...devices['Desktop Edge'],
        channel: 'msedge',
        viewport: { width: 1280, height: 720 }
      },
    },
    {
      name: 'Google Chrome',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
        viewport: { width: 1280, height: 720 }
      },
    },

    // Mobile devices
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    {
      name: 'Mobile Firefox',
      use: { ...devices['Galaxy S9+'] },
    },

    // Tablet devices
    {
      name: 'iPad',
      use: { ...devices['iPad Pro'] },
    },
    {
      name: 'iPad Mini',
      use: { ...devices['iPad Mini'] },
    },

    // High DPI displays
    {
      name: 'High DPI',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 2
      },
    },

    // Accessibility testing project
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 }
      },
      testMatch: '**/accessibility/**/*.spec.js',
    },

    // Performance testing project
    {
      name: 'performance',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 }
      },
      testMatch: '**/performance/**/*.spec.js',
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: process.env.EXTERNAL_SERVER ? undefined : {
    command: 'python -m githound.web.main',
    url: 'http://localhost:8000',
    reuseExistingServer: !process.env.CI,
    timeout: 180 * 1000, // 3 minutes for server startup
    env: {
      'TESTING': 'true',
      'JWT_SECRET_KEY': 'test-secret-key-for-testing-only-do-not-use-in-production',
      'REDIS_URL': process.env.REDIS_URL || 'redis://localhost:6379/15',
      'GITHOUND_LOG_LEVEL': 'WARNING',
      'PYTHONPATH': process.cwd(),
    },
    stderr: 'pipe',
    stdout: 'pipe',
  },

  /* Global setup and teardown */
  globalSetup: require.resolve('./fixtures/global-setup.js'),
  globalTeardown: require.resolve('./fixtures/global-teardown.js'),

  /* Test timeout */
  timeout: process.env.CI ? 120000 : 60000, // 2 minutes on CI, 1 minute locally

  /* Expect timeout */
  expect: {
    timeout: process.env.CI ? 15000 : 10000,
    toHaveScreenshot: { threshold: 0.2, mode: 'percent' },
    toMatchSnapshot: { threshold: 0.2, mode: 'percent' },
  },

  /* Output directory for test artifacts */
  outputDir: 'test-results/artifacts',

  /* Test metadata */
  metadata: {
    'Test Environment': process.env.NODE_ENV || 'development',
    'Base URL': process.env.BASE_URL || 'http://localhost:8000',
    'CI': process.env.CI || 'false',
    'Browser Versions': 'Latest stable',
  },

  /* Maximum failures before stopping */
  maxFailures: process.env.CI ? 10 : 5,

  /* Global test setup */
  testIgnore: [
    '**/node_modules/**',
    '**/test-results/**',
    '**/playwright-report/**',
  ],
});
