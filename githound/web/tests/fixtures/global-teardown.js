// Global teardown for Playwright tests

async function globalTeardown(config) {
  console.log('🧹 Starting global test teardown...');
  
  // Clean up any global resources
  // The server will be stopped automatically by the webServer configuration
  
  console.log('✅ Global teardown completed');
}

module.exports = globalTeardown;
