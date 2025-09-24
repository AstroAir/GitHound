/**
 * Export Functionality Tests
 * Tests export features in different formats with comprehensive validation
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage, ExportPage } = require('../pages');

test.describe('Export Functionality Tests', () => {
  let searchPage;
  let loginPage;
  let exportPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    exportPage = new ExportPage(page);

    // Setup authenticated user
    const testUser = {
      username: `export_${Date.now()}`,
      email: `export_${Date.now()}@example.com`,
      password: 'Export123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);

    // Perform a search to have results to export
    await searchPage.navigateToSearch();
    await searchPage.performAdvancedSearch({
      query: 'function',
      fileTypes: ['js', 'py'],
      searchType: 'exact'
    });

    // Wait for search results
    await searchPage.waitForResults();
  });

  test.describe('JSON Export Tests @export @json', () => {
    test('should export search results to JSON format', async () => {
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true,
          includeCommitInfo: true
        }
      });

      expect(exportResult.success).toBe(true);
      expect(exportResult.fileSize).toBeTruthy();

      // Download and validate the file
      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');

      expect(validation.isValid).toBe(true);
      expect(validation.parsedContent).toBeTruthy();
      expect(Array.isArray(validation.parsedContent) || typeof validation.parsedContent === 'object').toBe(true);
    });

    test('should export with custom field selection in JSON', async () => {
      const selectedFields = ['filePath', 'lineNumber', 'content', 'author'];

      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: selectedFields,
        exportOptions: {
          includeMetadata: false
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');

      expect(validation.isValid).toBe(true);

      // Verify only selected fields are included
      if (Array.isArray(validation.parsedContent) && validation.parsedContent.length > 0) {
        const firstResult = validation.parsedContent[0];
        selectedFields.forEach(field => {
          expect(firstResult).toHaveProperty(field);
        });

        // Should not have excluded fields
        expect(firstResult).not.toHaveProperty('commitHash');
        expect(firstResult).not.toHaveProperty('commitMessage');
      }
    });

    test('should handle large JSON exports', async () => {
      // Perform a search that might return many results
      await searchPage.performAdvancedSearch({
        query: 'import',
        fileTypes: ['js', 'py', 'ts'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true,
          includeCommitInfo: true,
          includeFileContent: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');

      expect(validation.isValid).toBe(true);
      expect(validation.fileSize).toBeGreaterThan(1000); // Should be substantial
    });

    test('should compress JSON exports when requested', async () => {
      const uncompressedResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          compressOutput: false
        }
      });

      const compressedResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          compressOutput: true
        }
      });

      expect(uncompressedResult.success).toBe(true);
      expect(compressedResult.success).toBe(true);

      // Compressed file should be smaller (this is a simplified check)
      const uncompressedSize = parseInt(uncompressedResult.fileSize.replace(/[^\d]/g, ''));
      const compressedSize = parseInt(compressedResult.fileSize.replace(/[^\d]/g, ''));

      expect(compressedSize).toBeLessThan(uncompressedSize);
    });
  });

  test.describe('CSV Export Tests @export @csv', () => {
    test('should export search results to CSV format', async () => {
      const exportResult = await exportPage.performExport({
        format: 'csv',
        fields: ['filePath', 'lineNumber', 'content', 'author'],
        exportOptions: {
          includeMetadata: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'csv');

      expect(validation.isValid).toBe(true);
      expect(validation.content).toContain(','); // Should have CSV delimiters
      expect(validation.content).toContain('\n'); // Should have line breaks

      // Should have header row
      const lines = validation.content.split('\n');
      expect(lines[0]).toContain('filePath');
      expect(lines[0]).toContain('lineNumber');
    });

    test('should handle CSV special characters correctly', async () => {
      // Search for content that might contain CSV special characters
      await searchPage.performAdvancedSearch({
        query: 'console.log',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      const exportResult = await exportPage.performExport({
        format: 'csv',
        fields: ['filePath', 'content'],
        exportOptions: {
          includeMetadata: false
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'csv');

      expect(validation.isValid).toBe(true);

      // CSV should properly escape quotes and commas
      const lines = validation.content.split('\n');
      lines.forEach(line => {
        if (line.includes(',') && line.includes('"')) {
          // If line contains commas and quotes, it should be properly escaped
          expect(line).toMatch(/^".*"$|^[^",]*$/);
        }
      });
    });

    test('should export CSV with custom delimiters', async () => {
      // This test assumes the export functionality supports custom delimiters
      const exportResult = await exportPage.performExport({
        format: 'csv',
        fields: ['filePath', 'lineNumber', 'content'],
        exportOptions: {
          delimiter: ';', // Semicolon delimiter
          includeMetadata: false
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'csv');

      expect(validation.isValid).toBe(true);
      expect(validation.content).toContain(';'); // Should use semicolon delimiter
    });
  });

  test.describe('YAML Export Tests @export @yaml', () => {
    test('should export search results to YAML format', async () => {
      const exportResult = await exportPage.performExport({
        format: 'yaml',
        fields: ['filePath', 'lineNumber', 'content', 'commitHash'],
        exportOptions: {
          includeMetadata: true,
          includeCommitInfo: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'yaml');

      expect(validation.isValid).toBe(true);
      expect(validation.content).toContain(':'); // YAML key-value separator
      expect(validation.content).toContain('-'); // YAML list indicator
    });

    test('should handle YAML special characters and formatting', async () => {
      const exportResult = await exportPage.performExport({
        format: 'yaml',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'yaml');

      expect(validation.isValid).toBe(true);

      // YAML should be properly formatted
      const lines = validation.content.split('\n');
      let hasProperIndentation = false;

      lines.forEach(line => {
        if (line.startsWith('  ') || line.startsWith('- ')) {
          hasProperIndentation = true;
        }
      });

      expect(hasProperIndentation).toBe(true);
    });
  });

  test.describe('XML Export Tests @export @xml', () => {
    test('should export search results to XML format', async () => {
      const exportResult = await exportPage.performExport({
        format: 'xml',
        fields: ['filePath', 'lineNumber', 'content'],
        exportOptions: {
          includeMetadata: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'xml');

      expect(validation.isValid).toBe(true);
      expect(validation.content).toContain('<'); // XML opening tags
      expect(validation.content).toContain('>'); // XML closing tags
      expect(validation.content).toContain('</'); // XML closing tag syntax
    });

    test('should handle XML special characters correctly', async () => {
      const exportResult = await exportPage.performExport({
        format: 'xml',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'xml');

      expect(validation.isValid).toBe(true);

      // XML should properly escape special characters
      expect(validation.content).not.toContain('&<'); // Should be escaped as &amp;&lt;
      expect(validation.content).not.toContain('>"'); // Should be escaped properly
    });
  });

  test.describe('Export Options and Customization @export @options', () => {
    test('should allow custom filename specification', async () => {
      const customFilename = `custom_export_${Date.now()}`;

      await exportPage.openExportModal();
      await exportPage.selectFormat('json');
      await exportPage.setFilename(customFilename);

      const exportResult = await exportPage.performExport({
        format: 'json',
        filename: customFilename,
        fields: ['filePath', 'content']
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      expect(download.suggestedFilename()).toContain(customFilename);
    });

    test('should generate automatic filenames', async () => {
      await exportPage.openExportModal();
      await exportPage.selectFormat('csv');
      await exportPage.generateFilename();

      const exportResult = await exportPage.performExport({
        format: 'csv',
        fields: ['all']
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const filename = download.suggestedFilename();

      // Should contain timestamp and format
      expect(filename).toMatch(/\d{4}-\d{2}-\d{2}/); // Date format
      expect(filename).toContain('.csv');
    });

    test('should preview export before download', async () => {
      await exportPage.openExportModal();
      await exportPage.selectFormat('json');
      await exportPage.selectFields(['filePath', 'lineNumber', 'content']);

      await exportPage.previewExport();

      const previewContent = await exportPage.getPreviewContent();
      expect(previewContent).toBeTruthy();
      expect(previewContent).toContain('{'); // JSON format

      await exportPage.closePreview();

      // Should be able to proceed with export after preview
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['filePath', 'lineNumber', 'content']
      });

      expect(exportResult.success).toBe(true);
    });

    test('should handle export with metadata inclusion', async () => {
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true,
          includeCommitInfo: true,
          includeFileContent: true
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');

      expect(validation.isValid).toBe(true);

      // Should include metadata fields
      if (validation.parsedContent && validation.parsedContent.metadata) {
        expect(validation.parsedContent.metadata.exportDate).toBeTruthy();
        expect(validation.parsedContent.metadata.searchQuery).toBeTruthy();
        expect(validation.parsedContent.metadata.totalResults).toBeTruthy();
      }
    });

    test('should handle export without metadata', async () => {
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['filePath', 'content'],
        exportOptions: {
          includeMetadata: false,
          includeCommitInfo: false
        }
      });

      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');

      expect(validation.isValid).toBe(true);

      // Should not include metadata
      if (Array.isArray(validation.parsedContent)) {
        validation.parsedContent.forEach(item => {
          expect(item).not.toHaveProperty('metadata');
          expect(item).not.toHaveProperty('exportInfo');
        });
      }
    });
  });

  test.describe('Export Error Handling @export @error', () => {
    test('should handle export with no search results', async () => {
      // Perform a search that returns no results
      await searchPage.performAdvancedSearch({
        query: 'nonexistent_function_name_12345',
        fileTypes: ['js'],
        searchType: 'exact'
      });

      await searchPage.waitForResults();

      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all']
      });

      // Should handle gracefully
      expect(exportResult.success).toBe(true);

      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');

      expect(validation.isValid).toBe(true);
      // Should be empty array or indicate no results
      if (Array.isArray(validation.parsedContent)) {
        expect(validation.parsedContent.length).toBe(0);
      }
    });

    test('should handle invalid filename characters', async () => {
      const invalidFilename = 'invalid<>:"/\\|?*filename';

      await exportPage.openExportModal();
      await exportPage.selectFormat('json');
      await exportPage.setFilename(invalidFilename);

      const exportResult = await exportPage.performExport({
        format: 'json',
        filename: invalidFilename,
        fields: ['filePath', 'content']
      });

      // Should either sanitize filename or show error
      if (exportResult.success) {
        const download = await exportPage.downloadFile();
        const filename = download.suggestedFilename();

        // Should not contain invalid characters
        expect(filename).not.toMatch(/[<>:"/\\|?*]/);
      } else {
        expect(exportResult.error).toContain('filename');
      }
    });

    test('should handle export cancellation', async () => {
      await exportPage.openExportModal();
      await exportPage.selectFormat('json');
      await exportPage.selectFields(['all']);

      // Start export and immediately cancel
      await exportPage.startExport();
      await exportPage.cancelExport();

      // Should handle cancellation gracefully
      const isExportInProgress = await exportPage.isExportInProgress();
      expect(isExportInProgress).toBe(false);
    });

    test('should handle export timeout', async ({ page }) => {
      // Mock slow export response
      await page.route('**/api/export/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 30000)); // 30 second delay
        route.continue();
      });

      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all']
      });

      // Should timeout gracefully
      expect(exportResult.success).toBe(false);
      expect(exportResult.error).toMatch(/timeout|time/i);
    });

    test('should handle server errors during export', async ({ page }) => {
      // Mock server error
      await page.route('**/api/export/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Export service unavailable',
            code: 'EXPORT_ERROR'
          })
        });
      });

      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all']
      });

      expect(exportResult.success).toBe(false);
      expect(exportResult.error).toContain('unavailable');
    });

    test('should handle network errors during export', async ({ page }) => {
      // Mock network failure
      await page.route('**/api/export/**', route => {
        route.abort('failed');
      });

      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all']
      });

      expect(exportResult.success).toBe(false);
      expect(exportResult.error).toMatch(/network|connection|failed/i);
    });

    test('should retry failed exports', async ({ page }) => {
      let attemptCount = 0;

      // Mock failure on first attempt, success on second
      await page.route('**/api/export/**', route => {
        attemptCount++;
        if (attemptCount === 1) {
          route.fulfill({
            status: 500,
            body: JSON.stringify({ error: 'Temporary failure' })
          });
        } else {
          route.continue();
        }
      });

      // First attempt should fail
      const firstResult = await exportPage.performExport({
        format: 'json',
        fields: ['all']
      });

      expect(firstResult.success).toBe(false);

      // Retry should succeed
      await exportPage.retryExport();
      const retryResult = await exportPage.waitForExportComplete();

      expect(retryResult.success).toBe(true);
    });
  });

  test.describe('Export History and Management @export @history', () => {
    test('should maintain export history', async () => {
      // Perform multiple exports
      const formats = ['json', 'csv', 'yaml'];

      for (const format of formats) {
        await exportPage.performExport({
          format: format,
          fields: ['filePath', 'content']
        });

        await exportPage.downloadFile();
      }

      // Check export history
      const history = await exportPage.getExportHistory();
      expect(history.length).toBeGreaterThanOrEqual(formats.length);

      // Should contain exports for each format
      formats.forEach(format => {
        const hasFormat = history.some(item => item.includes(format));
        expect(hasFormat).toBe(true);
      });
    });

    test('should allow downloading from export history', async () => {
      // Perform an export first
      await exportPage.performExport({
        format: 'json',
        fields: ['filePath', 'content']
      });

      await exportPage.downloadFile();

      // Download from history
      const download = await exportPage.downloadFromHistory(0);
      expect(download).toBeTruthy();

      const validation = await exportPage.validateExportContent(download, 'json');
      expect(validation.isValid).toBe(true);
    });

    test('should allow deleting export history items', async () => {
      // Perform an export
      await exportPage.performExport({
        format: 'json',
        fields: ['filePath', 'content']
      });

      await exportPage.downloadFile();

      const historyBefore = await exportPage.getExportHistory();
      expect(historyBefore.length).toBeGreaterThan(0);

      // Delete first item
      await exportPage.deleteHistoryItem(0);

      const historyAfter = await exportPage.getExportHistory();
      expect(historyAfter.length).toBe(historyBefore.length - 1);
    });
  });
});
