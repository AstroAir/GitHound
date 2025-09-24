/**
 * Coverage Reporter for GitHound Web Tests
 * Generates detailed code coverage reports for JavaScript and frontend code
 */

const fs = require('fs');
const path = require('path');

class CoverageReporter {
  constructor(options = {}) {
    this.options = {
      outputDir: options.outputDir || 'test-results/coverage',
      threshold: {
        statements: options.threshold?.statements || 80,
        branches: options.threshold?.branches || 75,
        functions: options.threshold?.functions || 80,
        lines: options.threshold?.lines || 80
      },
      includeUncovered: options.includeUncovered !== false,
      generateHtml: options.generateHtml !== false,
      ...options
    };

    this.coverage = {
      files: new Map(),
      summary: {
        statements: { total: 0, covered: 0, percentage: 0 },
        branches: { total: 0, covered: 0, percentage: 0 },
        functions: { total: 0, covered: 0, percentage: 0 },
        lines: { total: 0, covered: 0, percentage: 0 }
      },
      uncoveredLines: [],
      timestamp: new Date().toISOString()
    };
  }

  async collectCoverage(page) {
    try {
      // Collect JavaScript coverage from the page
      const jsCoverage = await page.coverage.stopJSCoverage();
      const cssCoverage = await page.coverage.stopCSSCoverage();

      // Process JavaScript coverage
      for (const entry of jsCoverage) {
        if (this.shouldIncludeFile(entry.url)) {
          this.processCoverageEntry(entry, 'javascript');
        }
      }

      // Process CSS coverage
      for (const entry of cssCoverage) {
        if (this.shouldIncludeFile(entry.url)) {
          this.processCoverageEntry(entry, 'css');
        }
      }

      // Collect runtime coverage data
      const runtimeCoverage = await page.evaluate(() => {
        if (window.__coverage__) {
          return window.__coverage__;
        }
        return null;
      });

      if (runtimeCoverage) {
        this.processRuntimeCoverage(runtimeCoverage);
      }

    } catch (error) {
      console.warn('Failed to collect coverage:', error.message);
    }
  }

  shouldIncludeFile(url) {
    // Include only our application files
    return url.includes('/static/') ||
           url.includes('app.js') ||
           url.includes('githound') ||
           (!url.includes('node_modules') &&
            !url.includes('playwright') &&
            !url.includes('test'));
  }

  processCoverageEntry(entry, type) {
    const fileName = this.getFileName(entry.url);

    if (!this.coverage.files.has(fileName)) {
      this.coverage.files.set(fileName, {
        url: entry.url,
        type: type,
        text: entry.text || '',
        ranges: [],
        statements: { total: 0, covered: 0 },
        branches: { total: 0, covered: 0 },
        functions: { total: 0, covered: 0 },
        lines: { total: 0, covered: 0 },
        uncoveredRanges: []
      });
    }

    const fileData = this.coverage.files.get(fileName);

    if (entry.ranges) {
      fileData.ranges = entry.ranges;
      this.calculateLineCoverage(fileData);
    }
  }

  processRuntimeCoverage(runtimeCoverage) {
    for (const [filePath, fileCoverage] of Object.entries(runtimeCoverage)) {
      const fileName = this.getFileName(filePath);

      if (!this.coverage.files.has(fileName)) {
        this.coverage.files.set(fileName, {
          url: filePath,
          type: 'javascript',
          statements: { total: 0, covered: 0 },
          branches: { total: 0, covered: 0 },
          functions: { total: 0, covered: 0 },
          lines: { total: 0, covered: 0 },
          uncoveredRanges: []
        });
      }

      const fileData = this.coverage.files.get(fileName);

      // Process statements
      if (fileCoverage.s) {
        fileData.statements.total = Object.keys(fileCoverage.s).length;
        fileData.statements.covered = Object.values(fileCoverage.s).filter(count => count > 0).length;
      }

      // Process branches
      if (fileCoverage.b) {
        fileData.branches.total = Object.values(fileCoverage.b).flat().length;
        fileData.branches.covered = Object.values(fileCoverage.b).flat().filter(count => count > 0).length;
      }

      // Process functions
      if (fileCoverage.f) {
        fileData.functions.total = Object.keys(fileCoverage.f).length;
        fileData.functions.covered = Object.values(fileCoverage.f).filter(count => count > 0).length;
      }

      // Process lines
      if (fileCoverage.l) {
        fileData.lines.total = Object.keys(fileCoverage.l).length;
        fileData.lines.covered = Object.values(fileCoverage.l).filter(count => count > 0).length;

        // Track uncovered lines
        const uncoveredLines = Object.entries(fileCoverage.l)
          .filter(([line, count]) => count === 0)
          .map(([line]) => parseInt(line));

        if (uncoveredLines.length > 0) {
          this.coverage.uncoveredLines.push({
            file: fileName,
            lines: uncoveredLines
          });
        }
      }
    }
  }

  calculateLineCoverage(fileData) {
    if (!fileData.text || !fileData.ranges) return;

    const lines = fileData.text.split('\n');
    const coveredLines = new Set();

    // Mark covered lines based on ranges
    for (const range of fileData.ranges) {
      const startLine = this.getLineNumber(fileData.text, range.start);
      const endLine = this.getLineNumber(fileData.text, range.end);

      for (let line = startLine; line <= endLine; line++) {
        if (lines[line - 1] && lines[line - 1].trim()) {
          coveredLines.add(line);
        }
      }
    }

    // Count total executable lines (non-empty, non-comment)
    const executableLines = lines
      .map((line, index) => ({ line: line.trim(), number: index + 1 }))
      .filter(({ line }) => line && !line.startsWith('//') && !line.startsWith('/*'))
      .map(({ number }) => number);

    fileData.lines.total = executableLines.length;
    fileData.lines.covered = executableLines.filter(line => coveredLines.has(line)).length;

    // Track uncovered lines
    const uncoveredLines = executableLines.filter(line => !coveredLines.has(line));
    if (uncoveredLines.length > 0) {
      fileData.uncoveredRanges = uncoveredLines;
    }
  }

  getLineNumber(text, offset) {
    return text.substring(0, offset).split('\n').length;
  }

  getFileName(url) {
    return url.split('/').pop() || url;
  }

  calculateSummary() {
    let totalStatements = 0, coveredStatements = 0;
    let totalBranches = 0, coveredBranches = 0;
    let totalFunctions = 0, coveredFunctions = 0;
    let totalLines = 0, coveredLines = 0;

    for (const fileData of this.coverage.files.values()) {
      totalStatements += fileData.statements.total;
      coveredStatements += fileData.statements.covered;
      totalBranches += fileData.branches.total;
      coveredBranches += fileData.branches.covered;
      totalFunctions += fileData.functions.total;
      coveredFunctions += fileData.functions.covered;
      totalLines += fileData.lines.total;
      coveredLines += fileData.lines.covered;
    }

    this.coverage.summary = {
      statements: {
        total: totalStatements,
        covered: coveredStatements,
        percentage: totalStatements > 0 ? (coveredStatements / totalStatements * 100).toFixed(2) : 0
      },
      branches: {
        total: totalBranches,
        covered: coveredBranches,
        percentage: totalBranches > 0 ? (coveredBranches / totalBranches * 100).toFixed(2) : 0
      },
      functions: {
        total: totalFunctions,
        covered: coveredFunctions,
        percentage: totalFunctions > 0 ? (coveredFunctions / totalFunctions * 100).toFixed(2) : 0
      },
      lines: {
        total: totalLines,
        covered: coveredLines,
        percentage: totalLines > 0 ? (coveredLines / totalLines * 100).toFixed(2) : 0
      }
    };
  }

  generateReports() {
    this.calculateSummary();

    // Ensure output directory exists
    if (!fs.existsSync(this.options.outputDir)) {
      fs.mkdirSync(this.options.outputDir, { recursive: true });
    }

    // Generate JSON report
    this.generateJsonReport();

    // Generate HTML report
    if (this.options.generateHtml) {
      this.generateHtmlReport();
    }

    // Generate console summary
    this.printConsoleSummary();

    // Check thresholds
    this.checkThresholds();
  }

  generateJsonReport() {
    const reportData = {
      summary: this.coverage.summary,
      files: Array.from(this.coverage.files.entries()).map(([name, data]) => ({
        name,
        ...data
      })),
      uncoveredLines: this.coverage.uncoveredLines,
      timestamp: this.coverage.timestamp
    };

    const reportPath = path.join(this.options.outputDir, 'coverage.json');
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
  }

  generateHtmlReport() {
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>GitHound Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .metric { display: inline-block; margin: 10px 20px; }
        .percentage { font-weight: bold; font-size: 1.2em; }
        .good { color: #28a745; }
        .warning { color: #ffc107; }
        .danger { color: #dc3545; }
        .file-list { margin-top: 20px; }
        .file-item { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .uncovered { background: #fff3cd; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🐕 GitHound Coverage Report</h1>
    <p>Generated: ${this.coverage.timestamp}</p>

    <div class="summary">
        <h2>Summary</h2>
        ${this.generateSummaryHtml()}
    </div>

    <div class="file-list">
        <h2>File Coverage</h2>
        ${this.generateFileListHtml()}
    </div>

    ${this.options.includeUncovered ? this.generateUncoveredHtml() : ''}
</body>
</html>`;

    const reportPath = path.join(this.options.outputDir, 'coverage.html');
    fs.writeFileSync(reportPath, html);
  }

  generateSummaryHtml() {
    const getClass = (percentage) => {
      if (percentage >= 80) return 'good';
      if (percentage >= 60) return 'warning';
      return 'danger';
    };

    return `
        <div class="metric">
            <div>Statements</div>
            <div class="percentage ${getClass(this.coverage.summary.statements.percentage)}">
                ${this.coverage.summary.statements.percentage}%
            </div>
            <div>${this.coverage.summary.statements.covered}/${this.coverage.summary.statements.total}</div>
        </div>
        <div class="metric">
            <div>Branches</div>
            <div class="percentage ${getClass(this.coverage.summary.branches.percentage)}">
                ${this.coverage.summary.branches.percentage}%
            </div>
            <div>${this.coverage.summary.branches.covered}/${this.coverage.summary.branches.total}</div>
        </div>
        <div class="metric">
            <div>Functions</div>
            <div class="percentage ${getClass(this.coverage.summary.functions.percentage)}">
                ${this.coverage.summary.functions.percentage}%
            </div>
            <div>${this.coverage.summary.functions.covered}/${this.coverage.summary.functions.total}</div>
        </div>
        <div class="metric">
            <div>Lines</div>
            <div class="percentage ${getClass(this.coverage.summary.lines.percentage)}">
                ${this.coverage.summary.lines.percentage}%
            </div>
            <div>${this.coverage.summary.lines.covered}/${this.coverage.summary.lines.total}</div>
        </div>
    `;
  }

  generateFileListHtml() {
    return Array.from(this.coverage.files.entries())
      .map(([name, data]) => {
        const linePercentage = data.lines.total > 0 ?
          (data.lines.covered / data.lines.total * 100).toFixed(2) : 0;

        return `
            <div class="file-item">
                <h4>${name}</h4>
                <p>Lines: ${linePercentage}% (${data.lines.covered}/${data.lines.total})</p>
                <p>Type: ${data.type}</p>
            </div>
        `;
      }).join('');
  }

  generateUncoveredHtml() {
    if (this.coverage.uncoveredLines.length === 0) {
      return '<div class="uncovered"><h2>🎉 All lines covered!</h2></div>';
    }

    return `
        <div class="uncovered">
            <h2>Uncovered Lines</h2>
            ${this.coverage.uncoveredLines.map(item => `
                <div>
                    <strong>${item.file}:</strong> Lines ${item.lines.join(', ')}
                </div>
            `).join('')}
        </div>
    `;
  }

  printConsoleSummary() {
    console.log('\n📊 Coverage Summary:');
    console.log(`  Statements: ${this.coverage.summary.statements.percentage}% (${this.coverage.summary.statements.covered}/${this.coverage.summary.statements.total})`);
    console.log(`  Branches: ${this.coverage.summary.branches.percentage}% (${this.coverage.summary.branches.covered}/${this.coverage.summary.branches.total})`);
    console.log(`  Functions: ${this.coverage.summary.functions.percentage}% (${this.coverage.summary.functions.covered}/${this.coverage.summary.functions.total})`);
    console.log(`  Lines: ${this.coverage.summary.lines.percentage}% (${this.coverage.summary.lines.covered}/${this.coverage.summary.lines.total})`);
  }

  checkThresholds() {
    const failures = [];

    if (this.coverage.summary.statements.percentage < this.options.threshold.statements) {
      failures.push(`Statements coverage ${this.coverage.summary.statements.percentage}% below threshold ${this.options.threshold.statements}%`);
    }

    if (this.coverage.summary.branches.percentage < this.options.threshold.branches) {
      failures.push(`Branches coverage ${this.coverage.summary.branches.percentage}% below threshold ${this.options.threshold.branches}%`);
    }

    if (this.coverage.summary.functions.percentage < this.options.threshold.functions) {
      failures.push(`Functions coverage ${this.coverage.summary.functions.percentage}% below threshold ${this.options.threshold.functions}%`);
    }

    if (this.coverage.summary.lines.percentage < this.options.threshold.lines) {
      failures.push(`Lines coverage ${this.coverage.summary.lines.percentage}% below threshold ${this.options.threshold.lines}%`);
    }

    if (failures.length > 0) {
      console.log('\n❌ Coverage thresholds not met:');
      failures.forEach(failure => console.log(`  • ${failure}`));
      return false;
    } else {
      console.log('\n✅ All coverage thresholds met!');
      return true;
    }
  }
}

module.exports = CoverageReporter;
