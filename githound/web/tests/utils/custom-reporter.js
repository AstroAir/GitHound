/**
 * Custom Test Reporter for GitHound
 * Enhanced test reporting with detailed artifacts, coverage reports, and failure analysis
 */

const fs = require('fs');
const path = require('path');

class GitHoundTestReporter {
  constructor(options = {}) {
    this.options = {
      outputDir: options.outputDir || 'test-results',
      includeScreenshots: options.includeScreenshots !== false,
      includeVideos: options.includeVideos !== false,
      includeTraces: options.includeTraces !== false,
      generateSummary: options.generateSummary !== false,
      ...options
    };

    this.results = {
      startTime: null,
      endTime: null,
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      skippedTests: 0,
      flakyTests: 0,
      suites: [],
      errors: [],
      performance: {
        slowestTests: [],
        averageTestTime: 0,
        totalTestTime: 0
      },
      coverage: {
        statements: 0,
        branches: 0,
        functions: 0,
        lines: 0
      },
      artifacts: {
        screenshots: [],
        videos: [],
        traces: []
      }
    };
  }

  onBegin(config, suite) {
    this.results.startTime = new Date();
    this.results.totalTests = suite.allTests().length;

    console.log(`\n🐕 GitHound Test Suite Starting`);
    console.log(`📊 Total tests: ${this.results.totalTests}`);
    console.log(`🌐 Browsers: ${config.projects.map(p => p.name).join(', ')}`);
    console.log(`⚡ Workers: ${config.workers}`);
    console.log(`🔄 Retries: ${config.retries}`);

    // Ensure output directory exists
    if (!fs.existsSync(this.options.outputDir)) {
      fs.mkdirSync(this.options.outputDir, { recursive: true });
    }
  }

  onTestBegin(test) {
    test._startTime = Date.now();

    // Log test start for verbose mode
    if (process.env.VERBOSE) {
      console.log(`🧪 Starting: ${test.title}`);
    }
  }

  onTestEnd(test, result) {
    const testTime = Date.now() - test._startTime;
    this.results.totalTestTime += testTime;

    // Categorize test result
    switch (result.status) {
      case 'passed':
        this.results.passedTests++;
        break;
      case 'failed':
        this.results.failedTests++;
        this.results.errors.push({
          test: test.title,
          suite: test.parent.title,
          error: result.error?.message || 'Unknown error',
          stack: result.error?.stack,
          duration: testTime,
          retry: result.retry
        });
        break;
      case 'skipped':
        this.results.skippedTests++;
        break;
      case 'timedOut':
        this.results.failedTests++;
        this.results.errors.push({
          test: test.title,
          suite: test.parent.title,
          error: 'Test timed out',
          duration: testTime,
          retry: result.retry
        });
        break;
    }

    // Track flaky tests (tests that passed after retry)
    if (result.status === 'passed' && result.retry > 0) {
      this.results.flakyTests++;
    }

    // Track slow tests
    if (testTime > 10000) { // Tests taking more than 10 seconds
      this.results.performance.slowestTests.push({
        test: test.title,
        suite: test.parent.title,
        duration: testTime,
        browser: test.parent.project()?.name
      });
    }

    // Collect artifacts
    if (result.attachments) {
      result.attachments.forEach(attachment => {
        if (attachment.name === 'screenshot' && this.options.includeScreenshots) {
          this.results.artifacts.screenshots.push({
            test: test.title,
            path: attachment.path,
            contentType: attachment.contentType
          });
        } else if (attachment.name === 'video' && this.options.includeVideos) {
          this.results.artifacts.videos.push({
            test: test.title,
            path: attachment.path,
            contentType: attachment.contentType
          });
        } else if (attachment.name === 'trace' && this.options.includeTraces) {
          this.results.artifacts.traces.push({
            test: test.title,
            path: attachment.path,
            contentType: attachment.contentType
          });
        }
      });
    }

    // Log test completion
    const status = result.status === 'passed' ? '✅' :
                  result.status === 'failed' ? '❌' :
                  result.status === 'skipped' ? '⏭️' : '⏰';

    if (process.env.VERBOSE || result.status === 'failed') {
      console.log(`${status} ${test.title} (${testTime}ms)`);
      if (result.status === 'failed' && result.error) {
        console.log(`   Error: ${result.error.message}`);
      }
    }
  }

  onEnd(result) {
    this.results.endTime = new Date();
    this.results.performance.averageTestTime = this.results.totalTestTime / this.results.totalTests;

    // Sort slowest tests
    this.results.performance.slowestTests.sort((a, b) => b.duration - a.duration);
    this.results.performance.slowestTests = this.results.performance.slowestTests.slice(0, 10);

    // Generate reports
    this.generateSummaryReport();
    this.generateDetailedReport();
    this.generateArtifactsReport();

    // Console summary
    this.printConsoleSummary();
  }

  generateSummaryReport() {
    const duration = this.results.endTime - this.results.startTime;
    const successRate = ((this.results.passedTests / this.results.totalTests) * 100).toFixed(2);

    const summary = {
      timestamp: this.results.endTime.toISOString(),
      duration: duration,
      totalTests: this.results.totalTests,
      passed: this.results.passedTests,
      failed: this.results.failedTests,
      skipped: this.results.skippedTests,
      flaky: this.results.flakyTests,
      successRate: `${successRate}%`,
      averageTestTime: `${this.results.performance.averageTestTime.toFixed(2)}ms`,
      artifacts: {
        screenshots: this.results.artifacts.screenshots.length,
        videos: this.results.artifacts.videos.length,
        traces: this.results.artifacts.traces.length
      }
    };

    const summaryPath = path.join(this.options.outputDir, 'summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  }

  generateDetailedReport() {
    const detailedPath = path.join(this.options.outputDir, 'detailed-report.json');
    fs.writeFileSync(detailedPath, JSON.stringify(this.results, null, 2));
  }

  generateArtifactsReport() {
    if (!this.options.generateSummary) return;

    const artifactsHtml = this.generateArtifactsHtml();
    const artifactsPath = path.join(this.options.outputDir, 'artifacts.html');
    fs.writeFileSync(artifactsPath, artifactsHtml);
  }

  generateArtifactsHtml() {
    const screenshots = this.results.artifacts.screenshots.map(s =>
      `<div class="artifact">
        <h4>${s.test}</h4>
        <img src="${path.relative(this.options.outputDir, s.path)}" alt="Screenshot" style="max-width: 300px;">
      </div>`
    ).join('');

    const videos = this.results.artifacts.videos.map(v =>
      `<div class="artifact">
        <h4>${v.test}</h4>
        <video controls style="max-width: 300px;">
          <source src="${path.relative(this.options.outputDir, v.path)}" type="${v.contentType}">
        </video>
      </div>`
    ).join('');

    return `
<!DOCTYPE html>
<html>
<head>
    <title>GitHound Test Artifacts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .artifact { margin: 20px 0; padding: 10px; border: 1px solid #ddd; }
        .section { margin: 30px 0; }
        h2 { color: #333; border-bottom: 2px solid #007acc; }
        h4 { color: #666; margin: 0 0 10px 0; }
    </style>
</head>
<body>
    <h1>🐕 GitHound Test Artifacts</h1>

    <div class="section">
        <h2>📸 Screenshots (${this.results.artifacts.screenshots.length})</h2>
        ${screenshots}
    </div>

    <div class="section">
        <h2>🎥 Videos (${this.results.artifacts.videos.length})</h2>
        ${videos}
    </div>

    <div class="section">
        <h2>🔍 Traces (${this.results.artifacts.traces.length})</h2>
        ${this.results.artifacts.traces.map(t =>
          `<div class="artifact">
            <h4>${t.test}</h4>
            <a href="${path.relative(this.options.outputDir, t.path)}" target="_blank">View Trace</a>
          </div>`
        ).join('')}
    </div>
</body>
</html>`;
  }

  printConsoleSummary() {
    const duration = this.results.endTime - this.results.startTime;
    const successRate = ((this.results.passedTests / this.results.totalTests) * 100).toFixed(2);

    console.log('\n' + '='.repeat(60));
    console.log('🐕 GitHound Test Results Summary');
    console.log('='.repeat(60));
    console.log(`⏱️  Duration: ${(duration / 1000).toFixed(2)}s`);
    console.log(`📊 Total Tests: ${this.results.totalTests}`);
    console.log(`✅ Passed: ${this.results.passedTests}`);
    console.log(`❌ Failed: ${this.results.failedTests}`);
    console.log(`⏭️  Skipped: ${this.results.skippedTests}`);
    console.log(`🔄 Flaky: ${this.results.flakyTests}`);
    console.log(`📈 Success Rate: ${successRate}%`);
    console.log(`⚡ Average Test Time: ${this.results.performance.averageTestTime.toFixed(2)}ms`);

    if (this.results.artifacts.screenshots.length > 0) {
      console.log(`📸 Screenshots: ${this.results.artifacts.screenshots.length}`);
    }
    if (this.results.artifacts.videos.length > 0) {
      console.log(`🎥 Videos: ${this.results.artifacts.videos.length}`);
    }
    if (this.results.artifacts.traces.length > 0) {
      console.log(`🔍 Traces: ${this.results.artifacts.traces.length}`);
    }

    if (this.results.performance.slowestTests.length > 0) {
      console.log('\n🐌 Slowest Tests:');
      this.results.performance.slowestTests.slice(0, 5).forEach((test, index) => {
        console.log(`  ${index + 1}. ${test.test} (${test.duration}ms)`);
      });
    }

    if (this.results.failedTests > 0) {
      console.log('\n❌ Failed Tests:');
      this.results.errors.slice(0, 5).forEach(error => {
        console.log(`  • ${error.test}: ${error.error}`);
      });
    }

    console.log(`\n📁 Reports saved to: ${this.options.outputDir}`);
    console.log('='.repeat(60));
  }
}

module.exports = GitHoundTestReporter;
