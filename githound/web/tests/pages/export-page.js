/**
 * Export Page Object Model for GitHound web tests.
 * Handles export functionality, format selection, and download management.
 */

const { expect } = require('@playwright/test');
const BasePage = require('./base-page');

class ExportPage extends BasePage {
  constructor(page) {
    super(page);

    // Page elements
    this.elements = {
      // Export trigger elements
      exportButton: '[data-testid="export-button"]',
      exportModal: '[data-testid="export-modal"]',
      exportForm: '[data-testid="export-form"]',

      // Format selection
      formatDropdown: '[data-testid="export-format"]',
      jsonFormat: '[data-testid="format-json"]',
      csvFormat: '[data-testid="format-csv"]',
      yamlFormat: '[data-testid="format-yaml"]',
      xmlFormat: '[data-testid="format-xml"]',

      // Export options
      includeMetadata: '[data-testid="include-metadata"]',
      includeCommitInfo: '[data-testid="include-commit-info"]',
      includeFileContent: '[data-testid="include-file-content"]',
      compressOutput: '[data-testid="compress-output"]',

      // Field selection
      fieldSelection: '[data-testid="field-selection"]',
      selectAllFields: '[data-testid="select-all-fields"]',
      filePathField: '[data-testid="field-file-path"]',
      lineNumberField: '[data-testid="field-line-number"]',
      contentField: '[data-testid="field-content"]',
      authorField: '[data-testid="field-author"]',
      commitHashField: '[data-testid="field-commit-hash"]',
      commitDateField: '[data-testid="field-commit-date"]',
      commitMessageField: '[data-testid="field-commit-message"]',

      // File naming
      filenameInput: '[data-testid="export-filename"]',
      generateFilename: '[data-testid="generate-filename"]',

      // Export actions
      confirmExport: '[data-testid="confirm-export"]',
      cancelExport: '[data-testid="cancel-export"]',
      previewExport: '[data-testid="preview-export"]',

      // Progress and status
      exportProgress: '[data-testid="export-progress"]',
      progressBar: '[data-testid="progress-bar"]',
      progressText: '[data-testid="progress-text"]',
      exportStatus: '[data-testid="export-status"]',

      // Results and download
      exportComplete: '[data-testid="export-complete"]',
      downloadButton: '[data-testid="download-button"]',
      downloadLink: '[data-testid="download-link"]',
      fileSize: '[data-testid="file-size"]',
      exportSummary: '[data-testid="export-summary"]',

      // Error handling
      exportError: '[data-testid="export-error"]',
      errorMessage: '[data-testid="error-message"]',
      retryExport: '[data-testid="retry-export"]',

      // Export history
      exportHistory: '[data-testid="export-history"]',
      historyItem: '[data-testid="history-item"]',
      deleteHistoryItem: '[data-testid="delete-history-item"]',
      downloadHistoryItem: '[data-testid="download-history-item"]',

      // Preview modal
      previewModal: '[data-testid="preview-modal"]',
      previewContent: '[data-testid="preview-content"]',
      previewClose: '[data-testid="preview-close"]'
    };
  }

  /**
   * Open export modal
   */
  async openExportModal() {
    await this.page.click(this.elements.exportButton);
    await this.waitForElement(this.elements.exportModal);
  }

  /**
   * Select export format
   */
  async selectFormat(format) {
    await this.page.selectOption(this.elements.formatDropdown, format);
  }

  /**
   * Configure export options
   */
  async configureExportOptions(options = {}) {
    if (options.includeMetadata) {
      await this.page.check(this.elements.includeMetadata);
    }

    if (options.includeCommitInfo) {
      await this.page.check(this.elements.includeCommitInfo);
    }

    if (options.includeFileContent) {
      await this.page.check(this.elements.includeFileContent);
    }

    if (options.compressOutput) {
      await this.page.check(this.elements.compressOutput);
    }
  }

  /**
   * Select fields to include in export
   */
  async selectFields(fields = []) {
    if (fields.includes('all')) {
      await this.page.check(this.elements.selectAllFields);
      return;
    }

    const fieldMap = {
      'filePath': this.elements.filePathField,
      'lineNumber': this.elements.lineNumberField,
      'content': this.elements.contentField,
      'author': this.elements.authorField,
      'commitHash': this.elements.commitHashField,
      'commitDate': this.elements.commitDateField,
      'commitMessage': this.elements.commitMessageField
    };

    for (const field of fields) {
      if (fieldMap[field]) {
        await this.page.check(fieldMap[field]);
      }
    }
  }

  /**
   * Set custom filename
   */
  async setFilename(filename) {
    await this.page.fill(this.elements.filenameInput, filename);
  }

  /**
   * Generate automatic filename
   */
  async generateFilename() {
    await this.page.click(this.elements.generateFilename);
  }

  /**
   * Preview export before downloading
   */
  async previewExport() {
    await this.page.click(this.elements.previewExport);
    await this.waitForElement(this.elements.previewModal);
  }

  /**
   * Get preview content
   */
  async getPreviewContent() {
    if (await this.page.isVisible(this.elements.previewContent)) {
      return await this.page.textContent(this.elements.previewContent);
    }
    return null;
  }

  /**
   * Close preview modal
   */
  async closePreview() {
    await this.page.click(this.elements.previewClose);
  }

  /**
   * Start export process
   */
  async startExport() {
    await this.page.click(this.elements.confirmExport);
    await this.waitForElement(this.elements.exportProgress);
  }

  /**
   * Cancel export process
   */
  async cancelExport() {
    await this.page.click(this.elements.cancelExport);
  }

  /**
   * Wait for export to complete
   */
  async waitForExportComplete(timeout = 60000) {
    try {
      await this.waitForElement(this.elements.exportComplete, timeout);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getExportError();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Get export progress
   */
  async getExportProgress() {
    if (await this.page.isVisible(this.elements.progressText)) {
      return await this.page.textContent(this.elements.progressText);
    }
    return null;
  }

  /**
   * Get export status
   */
  async getExportStatus() {
    if (await this.page.isVisible(this.elements.exportStatus)) {
      return await this.page.textContent(this.elements.exportStatus);
    }
    return null;
  }

  /**
   * Download exported file
   */
  async downloadFile() {
    const downloadPromise = this.page.waitForDownload();
    await this.page.click(this.elements.downloadButton);
    const download = await downloadPromise;
    return download;
  }

  /**
   * Get file size
   */
  async getFileSize() {
    if (await this.page.isVisible(this.elements.fileSize)) {
      return await this.page.textContent(this.elements.fileSize);
    }
    return null;
  }

  /**
   * Get export summary
   */
  async getExportSummary() {
    if (await this.page.isVisible(this.elements.exportSummary)) {
      return await this.page.textContent(this.elements.exportSummary);
    }
    return null;
  }

  /**
   * Get export error message
   */
  async getExportError() {
    if (await this.page.isVisible(this.elements.exportError)) {
      return await this.page.textContent(this.elements.errorMessage);
    }
    return null;
  }

  /**
   * Retry failed export
   */
  async retryExport() {
    if (await this.page.isVisible(this.elements.retryExport)) {
      await this.page.click(this.elements.retryExport);
      await this.waitForElement(this.elements.exportProgress);
    }
  }

  /**
   * Complete export workflow
   */
  async performExport(options = {}) {
    const {
      format = 'json',
      fields = ['all'],
      filename = null,
      exportOptions = {},
      preview = false
    } = options;

    // Open export modal
    await this.openExportModal();

    // Configure export
    await this.selectFormat(format);
    await this.selectFields(fields);
    await this.configureExportOptions(exportOptions);

    if (filename) {
      await this.setFilename(filename);
    } else {
      await this.generateFilename();
    }

    // Preview if requested
    if (preview) {
      await this.previewExport();
      const previewContent = await this.getPreviewContent();
      await this.closePreview();

      if (!previewContent) {
        throw new Error('Preview content is empty');
      }
    }

    // Start export
    await this.startExport();

    // Wait for completion
    const result = await this.waitForExportComplete();

    if (result.success) {
      const summary = await this.getExportSummary();
      const fileSize = await this.getFileSize();

      return {
        success: true,
        summary,
        fileSize
      };
    } else {
      return result;
    }
  }

  /**
   * Get export history
   */
  async getExportHistory() {
    if (await this.page.isVisible(this.elements.exportHistory)) {
      const historyItems = this.page.locator(this.elements.historyItem);
      const count = await historyItems.count();
      const history = [];

      for (let i = 0; i < count; i++) {
        const item = await historyItems.nth(i).textContent();
        history.push(item);
      }

      return history;
    }
    return [];
  }

  /**
   * Download from history
   */
  async downloadFromHistory(index) {
    const historyItems = this.page.locator(this.elements.historyItem);
    const item = historyItems.nth(index);

    const downloadPromise = this.page.waitForDownload();
    await item.locator(this.elements.downloadHistoryItem).click();
    const download = await downloadPromise;
    return download;
  }

  /**
   * Delete history item
   */
  async deleteHistoryItem(index) {
    const historyItems = this.page.locator(this.elements.historyItem);
    const item = historyItems.nth(index);
    await item.locator(this.elements.deleteHistoryItem).click();
  }

  /**
   * Check if export is in progress
   */
  async isExportInProgress() {
    return await this.page.isVisible(this.elements.exportProgress);
  }

  /**
   * Check if export is complete
   */
  async isExportComplete() {
    return await this.page.isVisible(this.elements.exportComplete);
  }

  /**
   * Check if export has error
   */
  async hasExportError() {
    return await this.page.isVisible(this.elements.exportError);
  }

  /**
   * Validate export file content
   */
  async validateExportContent(download, expectedFormat) {
    const path = await download.path();
    const fs = require('fs');
    const content = fs.readFileSync(path, 'utf8');

    let isValid = false;
    let parsedContent = null;

    try {
      switch (expectedFormat) {
        case 'json':
          parsedContent = JSON.parse(content);
          isValid = Array.isArray(parsedContent) || typeof parsedContent === 'object';
          break;
        case 'csv':
          isValid = content.includes(',') && content.includes('\n');
          break;
        case 'yaml':
          isValid = content.includes(':') && (content.includes('-') || content.includes('\n'));
          break;
        case 'xml':
          isValid = content.includes('<') && content.includes('>');
          break;
      }
    } catch (error) {
      isValid = false;
    }

    return {
      isValid,
      content: content.substring(0, 500), // First 500 chars for inspection
      parsedContent,
      fileSize: content.length
    };
  }
}

module.exports = ExportPage;
