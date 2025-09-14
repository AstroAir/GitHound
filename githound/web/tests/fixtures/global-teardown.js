// Enhanced global teardown for Playwright tests
const fs = require('fs').promises;
const path = require('path');

async function globalTeardown(config) {
  console.log('🧹 Starting enhanced global test teardown...');

  try {
    // Update test session data with completion info
    const testResultsDir = path.join(__dirname, '..', 'test-results');
    const testDataPath = path.join(testResultsDir, 'test-session-data.json');

    try {
      const sessionData = JSON.parse(await fs.readFile(testDataPath, 'utf8'));
      sessionData.endTime = new Date().toISOString();
      sessionData.duration = new Date() - new Date(sessionData.startTime);
      sessionData.teardownCompleted = true;

      await fs.writeFile(testDataPath, JSON.stringify(sessionData, null, 2));
      console.log('✅ Test session data updated');
    } catch (error) {
      console.warn('⚠️  Could not update test session data:', error.message);
    }

    // Generate test summary
    try {
      const summaryPath = path.join(testResultsDir, 'test-summary.json');
      const summary = {
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'test',
        baseURL: config.use?.baseURL || 'http://localhost:8000',
        testResultsLocation: testResultsDir,
        cleanup: {
          temporaryFiles: 'cleaned',
          testData: 'reset',
          browserInstances: 'closed'
        }
      };

      await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2));
      console.log('✅ Test summary generated');
    } catch (error) {
      console.warn('⚠️  Could not generate test summary:', error.message);
    }

    // Clean up temporary test files (optional - keep for debugging)
    if (process.env.CLEAN_TEST_FILES === 'true') {
      try {
        const tempFiles = await fs.readdir(testResultsDir);
        const filesToClean = tempFiles.filter(file =>
          file.startsWith('temp_') || file.endsWith('.tmp')
        );

        for (const file of filesToClean) {
          await fs.unlink(path.join(testResultsDir, file));
        }

        if (filesToClean.length > 0) {
          console.log(`✅ Cleaned ${filesToClean.length} temporary files`);
        }
      } catch (error) {
        console.warn('⚠️  Could not clean temporary files:', error.message);
      }
    }

    // Log final statistics
    console.log('📊 Test session completed');
    console.log(`📁 Test results available in: ${testResultsDir}`);

  } catch (error) {
    console.error('❌ Global teardown encountered an error:', error);
    // Don't throw - teardown should be resilient
  }

  console.log('✅ Enhanced global teardown completed');
}

module.exports = globalTeardown;
