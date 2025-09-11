// Global setup for Playwright tests
const { chromium } = require('@playwright/test');

async function globalSetup(config) {
  console.log('🚀 Starting global test setup...');
  
  // Set up test environment
  process.env.TESTING = 'true';
  process.env.JWT_SECRET_KEY = 'test-secret-key-for-testing-only';
  process.env.REDIS_URL = 'redis://localhost:6379/15';
  process.env.GITHOUND_LOG_LEVEL = 'WARNING';
  
  // Wait for server to be ready
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  const maxRetries = 30;
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const response = await page.goto('http://localhost:8000/health', {
        timeout: 5000,
        waitUntil: 'networkidle'
      });
      
      if (response && response.ok()) {
        console.log('✅ Server is ready');
        break;
      }
    } catch (error) {
      console.log(`⏳ Waiting for server... (attempt ${retries + 1}/${maxRetries})`);
    }
    
    retries++;
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  if (retries >= maxRetries) {
    throw new Error('❌ Server failed to start within timeout period');
  }
  
  await browser.close();
  console.log('✅ Global setup completed');
}

module.exports = globalSetup;
