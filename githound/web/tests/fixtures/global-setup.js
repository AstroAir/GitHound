// Enhanced global setup for Playwright tests
const { chromium } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

async function globalSetup(config) {
  console.log('🚀 Starting enhanced global test setup...');

  // Setup test environment variables
  process.env.TESTING = 'true';
  process.env.JWT_SECRET_KEY = 'test-secret-key-for-testing-only-do-not-use-in-production';
  process.env.REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/15';
  process.env.GITHOUND_LOG_LEVEL = 'WARNING';

  // Create test results directories
  const testResultsDir = path.join(__dirname, '..', 'test-results');
  const dirs = [
    'artifacts',
    'screenshots',
    'videos',
    'traces',
    'html-report',
    'accessibility-reports',
    'performance-reports'
  ];

  for (const dir of dirs) {
    const dirPath = path.join(testResultsDir, dir);
    try {
      await fs.mkdir(dirPath, { recursive: true });
      console.log(`📁 Created directory: ${dir}`);
    } catch (error) {
      console.warn(`⚠️  Could not create directory ${dir}:`, error.message);
    }
  }

  // Create a browser instance for setup tasks
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  try {
    // Wait for server to be ready with retries
    console.log('⏳ Waiting for server to be ready...');
    const baseURL = config.use?.baseURL || 'http://localhost:8000';
    let retries = 30;
    let serverReady = false;

    while (retries > 0 && !serverReady) {
      try {
        await page.goto(`${baseURL}/health`, { timeout: 5000 });
        const response = await page.textContent('body');
        if (response && response.includes('healthy')) {
          serverReady = true;
          console.log('✅ Server health check passed');
        }
      } catch (error) {
        retries--;
        if (retries > 0) {
          console.log(`⏳ Server not ready, retrying... (${retries} attempts left)`);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    }

    if (!serverReady) {
      throw new Error('Server failed to become ready within timeout period');
    }

    // Verify main page loads
    await page.goto(baseURL);
    await page.waitForSelector('body', { timeout: 10000 });
    console.log('✅ Main page loads successfully');

    // Initialize test data storage
    const testDataPath = path.join(testResultsDir, 'test-session-data.json');
    const sessionData = {
      startTime: new Date().toISOString(),
      baseURL: baseURL,
      testEnvironment: process.env.NODE_ENV || 'test',
      browserVersion: await browser.version(),
      setupCompleted: true
    };

    await fs.writeFile(testDataPath, JSON.stringify(sessionData, null, 2));
    console.log('✅ Test session data initialized');

  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }

  console.log('✅ Enhanced global test setup completed successfully');
}

module.exports = globalSetup;
