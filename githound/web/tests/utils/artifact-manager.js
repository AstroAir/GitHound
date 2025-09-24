/**
 * Artifact Manager for GitHound Tests
 * Manages test artifacts including screenshots, videos, traces, and reports
 */

const fs = require('fs');
const path = require('path');
const { testReportingConfig, reportingHelpers } = require('../test-reporting.config');

class ArtifactManager {
  constructor(options = {}) {
    this.config = {
      ...testReportingConfig,
      ...options
    };

    this.artifacts = {
      screenshots: [],
      videos: [],
      traces: [],
      reports: [],
      coverage: []
    };

    this.metadata = {
      startTime: new Date(),
      endTime: null,
      totalTests: 0,
      testResults: {},
      performance: {},
      errors: []
    };
  }

  // Initialize artifact directories
  async initialize() {
    const dirs = [
      this.config.outputDir,
      this.config.screenshots.outputDir,
      this.config.videos.outputDir,
      this.config.traces.outputDir,
      this.config.coverage.outputDir,
      this.config.htmlReport.outputDir,
      this.config.customReport.outputDir
    ];

    for (const dir of dirs) {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    }

    console.log('🗂️  Artifact directories initialized');
  }

  // Capture screenshot
  async captureScreenshot(page, testInfo, options = {}) {
    if (!this.config.screenshots.enabled) return null;

    try {
      const filename = reportingHelpers.generateFilename(
        this.config.screenshots.naming + '.png',
        {
          testName: testInfo.title.replace(/[^a-zA-Z0-9]/g, '-'),
          projectName: testInfo.project?.name || 'default',
          browser: testInfo.project?.name || 'unknown'
        }
      );

      const screenshotPath = path.join(this.config.screenshots.outputDir, filename);

      await page.screenshot({
        path: screenshotPath,
        fullPage: this.config.screenshots.fullPage,
        quality: this.config.screenshots.quality,
        animations: this.config.screenshots.animations,
        ...options
      });

      const artifact = {
        type: 'screenshot',
        path: screenshotPath,
        filename: filename,
        testName: testInfo.title,
        timestamp: new Date().toISOString(),
        size: fs.statSync(screenshotPath).size
      };

      this.artifacts.screenshots.push(artifact);

      // Attach to test
      await testInfo.attach('screenshot', {
        path: screenshotPath,
        contentType: 'image/png'
      });

      return artifact;
    } catch (error) {
      console.error('Failed to capture screenshot:', error);
      this.metadata.errors.push({
        type: 'screenshot',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      return null;
    }
  }

  // Start video recording
  async startVideoRecording(page, testInfo) {
    if (!this.config.videos.enabled) return null;

    try {
      const filename = reportingHelpers.generateFilename(
        this.config.videos.naming + '.webm',
        {
          testName: testInfo.title.replace(/[^a-zA-Z0-9]/g, '-'),
          projectName: testInfo.project?.name || 'default',
          browser: testInfo.project?.name || 'unknown'
        }
      );

      const videoPath = path.join(this.config.videos.outputDir, filename);

      // Video recording is typically handled by Playwright's built-in functionality
      // This method tracks the video for our artifact management

      const artifact = {
        type: 'video',
        path: videoPath,
        filename: filename,
        testName: testInfo.title,
        timestamp: new Date().toISOString(),
        status: 'recording'
      };

      this.artifacts.videos.push(artifact);
      return artifact;
    } catch (error) {
      console.error('Failed to start video recording:', error);
      this.metadata.errors.push({
        type: 'video',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      return null;
    }
  }

  // Stop video recording
  async stopVideoRecording(videoArtifact) {
    if (!videoArtifact) return;

    try {
      videoArtifact.status = 'completed';
      videoArtifact.endTime = new Date().toISOString();

      if (fs.existsSync(videoArtifact.path)) {
        videoArtifact.size = fs.statSync(videoArtifact.path).size;
      }
    } catch (error) {
      console.error('Failed to finalize video recording:', error);
      videoArtifact.status = 'error';
    }
  }

  // Start trace recording
  async startTraceRecording(page, testInfo) {
    if (!this.config.traces.enabled) return null;

    try {
      const filename = reportingHelpers.generateFilename(
        this.config.traces.naming + '.zip',
        {
          testName: testInfo.title.replace(/[^a-zA-Z0-9]/g, '-'),
          projectName: testInfo.project?.name || 'default',
          browser: testInfo.project?.name || 'unknown'
        }
      );

      const tracePath = path.join(this.config.traces.outputDir, filename);

      await page.context().tracing.start({
        screenshots: this.config.traces.screenshots,
        snapshots: this.config.traces.snapshots,
        sources: this.config.traces.sources
      });

      const artifact = {
        type: 'trace',
        path: tracePath,
        filename: filename,
        testName: testInfo.title,
        timestamp: new Date().toISOString(),
        status: 'recording'
      };

      this.artifacts.traces.push(artifact);
      return artifact;
    } catch (error) {
      console.error('Failed to start trace recording:', error);
      this.metadata.errors.push({
        type: 'trace',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      return null;
    }
  }

  // Stop trace recording
  async stopTraceRecording(page, traceArtifact, testInfo) {
    if (!traceArtifact) return;

    try {
      await page.context().tracing.stop({ path: traceArtifact.path });

      traceArtifact.status = 'completed';
      traceArtifact.endTime = new Date().toISOString();

      if (fs.existsSync(traceArtifact.path)) {
        traceArtifact.size = fs.statSync(traceArtifact.path).size;
      }

      // Attach to test
      await testInfo.attach('trace', {
        path: traceArtifact.path,
        contentType: 'application/zip'
      });
    } catch (error) {
      console.error('Failed to stop trace recording:', error);
      traceArtifact.status = 'error';
    }
  }

  // Collect performance metrics
  async collectPerformanceMetrics(page, testInfo) {
    if (!this.config.performance.enabled) return null;

    try {
      const metrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');

        const result = {
          timestamp: new Date().toISOString(),
          navigation: {
            domContentLoaded: navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart,
            loadComplete: navigation?.loadEventEnd - navigation?.loadEventStart,
            firstByte: navigation?.responseStart - navigation?.requestStart
          },
          paint: {}
        };

        paint.forEach(entry => {
          result.paint[entry.name] = entry.startTime;
        });

        // Collect Core Web Vitals if available
        if (window.webVitals) {
          result.webVitals = window.webVitals;
        }

        return result;
      });

      this.metadata.performance[testInfo.title] = metrics;
      return metrics;
    } catch (error) {
      console.error('Failed to collect performance metrics:', error);
      return null;
    }
  }

  // Generate artifact summary
  generateSummary() {
    this.metadata.endTime = new Date();

    const summary = {
      metadata: this.metadata,
      artifacts: {
        screenshots: {
          count: this.artifacts.screenshots.length,
          totalSize: this.artifacts.screenshots.reduce((sum, a) => sum + (a.size || 0), 0),
          files: this.artifacts.screenshots
        },
        videos: {
          count: this.artifacts.videos.length,
          totalSize: this.artifacts.videos.reduce((sum, a) => sum + (a.size || 0), 0),
          files: this.artifacts.videos
        },
        traces: {
          count: this.artifacts.traces.length,
          totalSize: this.artifacts.traces.reduce((sum, a) => sum + (a.size || 0), 0),
          files: this.artifacts.traces
        }
      },
      performance: this.metadata.performance,
      errors: this.metadata.errors,
      duration: this.metadata.endTime - this.metadata.startTime
    };

    return summary;
  }

  // Save artifact summary to file
  async saveSummary() {
    const summary = this.generateSummary();
    const summaryPath = path.join(this.config.outputDir, 'artifact-summary.json');

    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

    console.log(`📊 Artifact summary saved to: ${summaryPath}`);
    return summaryPath;
  }

  // Generate HTML artifact viewer
  async generateArtifactViewer() {
    const summary = this.generateSummary();

    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>GitHound Test Artifacts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007acc; }
        .artifact-section { margin: 30px 0; }
        .artifact-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .artifact-item { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: white; }
        .artifact-preview { max-width: 100%; height: 200px; object-fit: cover; border-radius: 3px; }
        .performance-chart { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .error-list { background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐕 GitHound Test Artifacts</h1>
            <p>Generated: ${summary.metadata.endTime}</p>
            <p>Duration: ${Math.round(summary.duration / 1000)}s</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${summary.artifacts.screenshots.count}</div>
                <div>Screenshots</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${summary.artifacts.videos.count}</div>
                <div>Videos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${summary.artifacts.traces.count}</div>
                <div>Traces</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${Object.keys(summary.performance).length}</div>
                <div>Performance Tests</div>
            </div>
        </div>

        <div class="artifact-section">
            <h2>📸 Screenshots</h2>
            <div class="artifact-grid">
                ${summary.artifacts.screenshots.files.map(screenshot => `
                    <div class="artifact-item">
                        <h4>${screenshot.testName}</h4>
                        <img src="${path.relative(this.config.outputDir, screenshot.path)}"
                             alt="Screenshot" class="artifact-preview">
                        <p><small>${screenshot.timestamp}</small></p>
                        <p>Size: ${(screenshot.size / 1024).toFixed(1)} KB</p>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="artifact-section">
            <h2>🎥 Videos</h2>
            <div class="artifact-grid">
                ${summary.artifacts.videos.files.map(video => `
                    <div class="artifact-item">
                        <h4>${video.testName}</h4>
                        <video controls class="artifact-preview">
                            <source src="${path.relative(this.config.outputDir, video.path)}" type="video/webm">
                        </video>
                        <p><small>${video.timestamp}</small></p>
                        <p>Size: ${video.size ? (video.size / 1024 / 1024).toFixed(1) + ' MB' : 'Unknown'}</p>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="artifact-section">
            <h2>🔍 Traces</h2>
            <div class="artifact-grid">
                ${summary.artifacts.traces.files.map(trace => `
                    <div class="artifact-item">
                        <h4>${trace.testName}</h4>
                        <p><a href="${path.relative(this.config.outputDir, trace.path)}"
                              target="_blank">Download Trace</a></p>
                        <p><small>${trace.timestamp}</small></p>
                        <p>Size: ${trace.size ? (trace.size / 1024).toFixed(1) + ' KB' : 'Unknown'}</p>
                    </div>
                `).join('')}
            </div>
        </div>

        ${summary.errors.length > 0 ? `
        <div class="artifact-section">
            <h2>⚠️ Errors</h2>
            <div class="error-list">
                ${summary.errors.map(error => `
                    <div>
                        <strong>${error.type}:</strong> ${error.error}
                        <small>(${error.timestamp})</small>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
    </div>
</body>
</html>`;

    const viewerPath = path.join(this.config.outputDir, 'artifact-viewer.html');
    fs.writeFileSync(viewerPath, html);

    console.log(`🌐 Artifact viewer generated: ${viewerPath}`);
    return viewerPath;
  }

  // Clean up old artifacts
  async cleanup() {
    if (!this.config.retention.cleanupOnSuccess) return;

    try {
      await reportingHelpers.cleanupArtifacts();
      console.log('🧹 Artifact cleanup completed');
    } catch (error) {
      console.error('Failed to cleanup artifacts:', error);
    }
  }

  // Get artifact statistics
  getStatistics() {
    const summary = this.generateSummary();

    return {
      totalArtifacts: summary.artifacts.screenshots.count +
                     summary.artifacts.videos.count +
                     summary.artifacts.traces.count,
      totalSize: summary.artifacts.screenshots.totalSize +
                summary.artifacts.videos.totalSize +
                summary.artifacts.traces.totalSize,
      duration: summary.duration,
      errors: summary.errors.length,
      performance: Object.keys(summary.performance).length
    };
  }
}

module.exports = ArtifactManager;
