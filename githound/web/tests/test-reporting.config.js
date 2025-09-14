/**
 * Test Reporting Configuration for GitHound
 * Comprehensive configuration for test artifacts, screenshots, videos, and reporting
 */

const path = require('path');
const fs = require('fs');

// Ensure test results directories exist
const ensureDirectories = () => {
  const dirs = [
    'test-results',
    'test-results/screenshots',
    'test-results/videos',
    'test-results/traces',
    'test-results/coverage',
    'test-results/custom',
    'test-results/html-report',
    'test-results/artifacts'
  ];
  
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
};

// Test reporting configuration
const testReportingConfig = {
  // Base configuration
  outputDir: process.env.TEST_OUTPUT_DIR || 'test-results',
  
  // Screenshot configuration
  screenshots: {
    enabled: process.env.TAKE_SCREENSHOTS !== 'false',
    mode: process.env.SCREENSHOT_MODE || 'only-on-failure', // 'off', 'only-on-failure', 'on'
    fullPage: true,
    quality: 90,
    threshold: 0.2, // Visual diff threshold
    animations: 'disabled', // Disable animations for consistent screenshots
    outputDir: 'test-results/screenshots',
    naming: '{testName}-{projectName}-{timestamp}',
    formats: ['png'], // png, jpeg
    compression: {
      png: { compressionLevel: 6 },
      jpeg: { quality: 90 }
    }
  },
  
  // Video recording configuration
  videos: {
    enabled: process.env.RECORD_VIDEO !== 'false',
    mode: process.env.VIDEO_MODE || 'retain-on-failure', // 'off', 'on', 'retain-on-failure', 'on-first-retry'
    size: { width: 1280, height: 720 },
    fps: 25,
    outputDir: 'test-results/videos',
    naming: '{testName}-{projectName}-{timestamp}',
    format: 'webm', // webm, mp4
    quality: 'medium' // low, medium, high
  },
  
  // Trace configuration
  traces: {
    enabled: process.env.RECORD_TRACE !== 'false',
    mode: process.env.TRACE_MODE || 'retain-on-failure', // 'off', 'on', 'retain-on-failure', 'on-first-retry'
    screenshots: true,
    snapshots: true,
    sources: true,
    outputDir: 'test-results/traces',
    naming: '{testName}-{projectName}-{timestamp}'
  },
  
  // Coverage configuration
  coverage: {
    enabled: process.env.COLLECT_COVERAGE === 'true',
    outputDir: 'test-results/coverage',
    formats: ['html', 'json', 'lcov'],
    threshold: {
      statements: parseInt(process.env.COVERAGE_STATEMENTS_THRESHOLD) || 75,
      branches: parseInt(process.env.COVERAGE_BRANCHES_THRESHOLD) || 70,
      functions: parseInt(process.env.COVERAGE_FUNCTIONS_THRESHOLD) || 75,
      lines: parseInt(process.env.COVERAGE_LINES_THRESHOLD) || 75
    },
    exclude: [
      '**/node_modules/**',
      '**/test*/**',
      '**/*.test.*',
      '**/*.spec.*'
    ]
  },
  
  // HTML report configuration
  htmlReport: {
    enabled: true,
    outputDir: 'test-results/html-report',
    open: process.env.CI ? 'never' : 'on-failure',
    host: process.env.HTML_REPORT_HOST || 'localhost',
    port: parseInt(process.env.HTML_REPORT_PORT) || 9323,
    attachmentsBaseURL: process.env.HTML_REPORT_ATTACHMENTS_BASE_URL,
    theme: 'light' // light, dark
  },
  
  // JUnit XML report configuration
  junitReport: {
    enabled: true,
    outputFile: 'test-results/junit-results.xml',
    includeProjectInTestName: true,
    mergeReports: true,
    stripANSIControlSequences: true
  },
  
  // JSON report configuration
  jsonReport: {
    enabled: true,
    outputFile: 'test-results/test-results.json',
    includeAttachments: true
  },
  
  // Custom reporter configuration
  customReport: {
    enabled: true,
    outputDir: 'test-results/custom',
    includeScreenshots: true,
    includeVideos: true,
    includeTraces: true,
    generateSummary: true,
    generateArtifactsHtml: true
  },
  
  // Blob report configuration (for merging reports)
  blobReport: {
    enabled: process.env.CI === 'true',
    outputDir: 'test-results/blob-report'
  },
  
  // Artifact retention
  retention: {
    days: parseInt(process.env.ARTIFACT_RETENTION_DAYS) || 30,
    maxSizeMB: parseInt(process.env.ARTIFACT_MAX_SIZE_MB) || 1000,
    cleanupOnSuccess: process.env.CLEANUP_ON_SUCCESS === 'true',
    preserveFailures: true
  },
  
  // Performance monitoring
  performance: {
    enabled: true,
    collectMetrics: ['FCP', 'LCP', 'CLS', 'FID', 'TTFB'],
    thresholds: {
      FCP: 1800, // First Contentful Paint (ms)
      LCP: 2500, // Largest Contentful Paint (ms)
      CLS: 0.1,  // Cumulative Layout Shift
      FID: 100,  // First Input Delay (ms)
      TTFB: 600  // Time to First Byte (ms)
    }
  },
  
  // Accessibility reporting
  accessibility: {
    enabled: true,
    standards: ['WCAG2A', 'WCAG2AA', 'WCAG21AA'],
    outputDir: 'test-results/accessibility',
    includeViolations: true,
    includeIncomplete: true,
    includePasses: false
  },
  
  // Visual regression configuration
  visualRegression: {
    enabled: true,
    outputDir: 'test-results/visual',
    threshold: 0.2,
    thresholdType: 'percent', // 'percent' or 'pixel'
    animations: 'disabled',
    clip: null, // { x: 0, y: 0, width: 800, height: 600 }
    fullPage: true,
    omitBackground: false
  },
  
  // Notification configuration
  notifications: {
    enabled: process.env.ENABLE_NOTIFICATIONS === 'true',
    webhook: process.env.NOTIFICATION_WEBHOOK,
    channels: {
      slack: process.env.SLACK_WEBHOOK,
      teams: process.env.TEAMS_WEBHOOK,
      email: process.env.EMAIL_NOTIFICATION
    },
    onFailure: true,
    onSuccess: process.env.NOTIFY_ON_SUCCESS === 'true',
    includeArtifacts: true
  }
};

// Helper functions for test reporting
const reportingHelpers = {
  // Generate unique filename with timestamp
  generateFilename: (template, context) => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    return template
      .replace('{testName}', context.testName || 'unknown')
      .replace('{projectName}', context.projectName || 'default')
      .replace('{timestamp}', timestamp)
      .replace('{browser}', context.browser || 'unknown');
  },
  
  // Clean up old artifacts based on retention policy
  cleanupArtifacts: async () => {
    const { retention } = testReportingConfig;
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - retention.days);
    
    const cleanupDir = async (dirPath) => {
      if (!fs.existsSync(dirPath)) return;
      
      const files = fs.readdirSync(dirPath);
      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stats = fs.statSync(filePath);
        
        if (stats.mtime < cutoffDate) {
          if (stats.isDirectory()) {
            fs.rmSync(filePath, { recursive: true, force: true });
          } else {
            fs.unlinkSync(filePath);
          }
        }
      }
    };
    
    // Clean up various artifact directories
    await cleanupDir(testReportingConfig.screenshots.outputDir);
    await cleanupDir(testReportingConfig.videos.outputDir);
    await cleanupDir(testReportingConfig.traces.outputDir);
  },
  
  // Calculate total artifact size
  calculateArtifactSize: () => {
    const calculateDirSize = (dirPath) => {
      if (!fs.existsSync(dirPath)) return 0;
      
      let totalSize = 0;
      const files = fs.readdirSync(dirPath);
      
      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stats = fs.statSync(filePath);
        
        if (stats.isDirectory()) {
          totalSize += calculateDirSize(filePath);
        } else {
          totalSize += stats.size;
        }
      }
      
      return totalSize;
    };
    
    const totalBytes = calculateDirSize(testReportingConfig.outputDir);
    return {
      bytes: totalBytes,
      mb: (totalBytes / (1024 * 1024)).toFixed(2),
      gb: (totalBytes / (1024 * 1024 * 1024)).toFixed(2)
    };
  },
  
  // Generate artifact summary
  generateArtifactSummary: () => {
    const summary = {
      timestamp: new Date().toISOString(),
      size: reportingHelpers.calculateArtifactSize(),
      files: {
        screenshots: 0,
        videos: 0,
        traces: 0,
        reports: 0
      }
    };
    
    // Count files in each category
    const countFiles = (dirPath) => {
      if (!fs.existsSync(dirPath)) return 0;
      return fs.readdirSync(dirPath).length;
    };
    
    summary.files.screenshots = countFiles(testReportingConfig.screenshots.outputDir);
    summary.files.videos = countFiles(testReportingConfig.videos.outputDir);
    summary.files.traces = countFiles(testReportingConfig.traces.outputDir);
    summary.files.reports = countFiles(testReportingConfig.htmlReport.outputDir);
    
    return summary;
  },
  
  // Send notification
  sendNotification: async (message, type = 'info') => {
    const { notifications } = testReportingConfig;
    
    if (!notifications.enabled) return;
    
    const payload = {
      message,
      type,
      timestamp: new Date().toISOString(),
      project: 'GitHound Web Frontend Tests'
    };
    
    // Send to configured channels
    if (notifications.channels.slack) {
      // Implement Slack notification
      console.log('Slack notification:', payload);
    }
    
    if (notifications.channels.teams) {
      // Implement Teams notification
      console.log('Teams notification:', payload);
    }
    
    if (notifications.channels.email) {
      // Implement email notification
      console.log('Email notification:', payload);
    }
  }
};

// Initialize directories on module load
ensureDirectories();

module.exports = {
  testReportingConfig,
  reportingHelpers,
  ensureDirectories
};
