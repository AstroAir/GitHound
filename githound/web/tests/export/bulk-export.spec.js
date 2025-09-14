/**
 * Bulk Export Tests
 * Tests bulk export operations, batch processing, and large dataset handling
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage, ExportPage, ResultsPage } = require('../pages');

test.describe('Bulk Export Tests', () => {
  let searchPage;
  let loginPage;
  let exportPage;
  let resultsPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);
    exportPage = new ExportPage(page);
    resultsPage = new ResultsPage(page);

    // Setup authenticated user
    const testUser = {
      username: `bulk_export_${Date.now()}`,
      email: `bulk_export_${Date.now()}@example.com`,
      password: 'BulkExport123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
    
    // Perform a comprehensive search to have many results
    await searchPage.navigateToSearch();
    await searchPage.performAdvancedSearch({
      query: 'import',
      fileTypes: ['js', 'py', 'ts', 'jsx'],
      searchType: 'exact'
    });
    
    await searchPage.waitForResults();
  });

  test.describe('Bulk Selection and Export @export @bulk @selection', () => {
    test('should export all search results', async () => {
      // Select all results
      await resultsPage.selectAllResults();
      
      const selectedCount = await resultsPage.getSelectedCount();
      expect(selectedCount).toBeGreaterThan(0);
      
      // Bulk export selected results
      await resultsPage.bulkExportSelected();
      
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true
        }
      });

      expect(exportResult.success).toBe(true);
      
      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');
      
      expect(validation.isValid).toBe(true);
      
      // Should contain all selected results
      if (Array.isArray(validation.parsedContent)) {
        expect(validation.parsedContent.length).toBe(selectedCount);
      }
    });

    test('should export selected subset of results', async () => {
      // Select specific results
      const indicesToSelect = [0, 2, 4, 6, 8]; // Select every other result
      
      for (const index of indicesToSelect) {
        await resultsPage.selectResult(index);
      }
      
      const selectedCount = await resultsPage.getSelectedCount();
      expect(selectedCount).toBe(indicesToSelect.length);
      
      // Export selected results
      await resultsPage.bulkExportSelected();
      
      const exportResult = await exportPage.performExport({
        format: 'csv',
        fields: ['filePath', 'lineNumber', 'content']
      });

      expect(exportResult.success).toBe(true);
      
      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'csv');
      
      expect(validation.isValid).toBe(true);
      
      // Should contain only selected results
      const lines = validation.content.split('\n').filter(line => line.trim());
      expect(lines.length - 1).toBe(selectedCount); // -1 for header row
    });

    test('should handle bulk export across multiple pages', async () => {
      // Navigate through pages and select results
      let totalSelected = 0;
      const maxPages = 3;
      
      for (let page = 1; page <= maxPages; page++) {
        if (page > 1) {
          await resultsPage.goToPage(page);
        }
        
        // Select some results on this page
        const resultCount = await resultsPage.getResultCount();
        if (resultCount > 0) {
          const selectCount = Math.min(5, resultCount);
          for (let i = 0; i < selectCount; i++) {
            await resultsPage.selectResult(i);
          }
          totalSelected += selectCount;
        }
        
        // Check if there are more pages
        const hasNextPage = await resultsPage.hasPagination();
        if (!hasNextPage) break;
      }
      
      expect(totalSelected).toBeGreaterThan(0);
      
      // Export all selected results
      await resultsPage.bulkExportSelected();
      
      const exportResult = await exportPage.performExport({
        format: 'yaml',
        fields: ['filePath', 'content', 'author']
      });

      expect(exportResult.success).toBe(true);
    });

    test('should maintain selection state during export', async () => {
      // Select results
      await resultsPage.selectResult(0);
      await resultsPage.selectResult(1);
      await resultsPage.selectResult(2);
      
      const initialSelectedCount = await resultsPage.getSelectedCount();
      expect(initialSelectedCount).toBe(3);
      
      // Start export process
      await resultsPage.bulkExportSelected();
      await exportPage.openExportModal();
      
      // Selection should still be maintained
      const selectedCountDuringExport = await resultsPage.getSelectedCount();
      expect(selectedCountDuringExport).toBe(initialSelectedCount);
      
      // Cancel export and verify selection is still there
      await exportPage.cancelExport();
      
      const selectedCountAfterCancel = await resultsPage.getSelectedCount();
      expect(selectedCountAfterCancel).toBe(initialSelectedCount);
    });
  });

  test.describe('Large Dataset Export @export @bulk @performance', () => {
    test('should handle export of large result sets', async () => {
      // Perform search that returns many results
      await searchPage.performAdvancedSearch({
        query: 'function',
        fileTypes: ['js', 'py', 'ts', 'jsx', 'tsx'],
        searchType: 'fuzzy'
      });
      
      await searchPage.waitForResults();
      
      // Select all results
      await resultsPage.selectAllResults();
      
      const selectedCount = await resultsPage.getSelectedCount();
      expect(selectedCount).toBeGreaterThan(50); // Should have many results
      
      // Export with progress monitoring
      await resultsPage.bulkExportSelected();
      
      const startTime = Date.now();
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['all'],
        exportOptions: {
          includeMetadata: true,
          includeCommitInfo: true
        }
      });
      const endTime = Date.now();

      expect(exportResult.success).toBe(true);
      
      // Should complete within reasonable time (5 minutes for large dataset)
      expect(endTime - startTime).toBeLessThan(300000);
      
      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');
      
      expect(validation.isValid).toBe(true);
      expect(validation.fileSize).toBeGreaterThan(10000); // Should be substantial
    });

    test('should show progress for large exports', async () => {
      // Select many results
      await resultsPage.selectAllResults();
      await resultsPage.bulkExportSelected();
      
      // Start export and monitor progress
      await exportPage.startExport();
      
      // Should show progress indicators
      const isExportInProgress = await exportPage.isExportInProgress();
      expect(isExportInProgress).toBe(true);
      
      const progress = await exportPage.getExportProgress();
      expect(progress).toBeTruthy();
      
      // Wait for completion
      const result = await exportPage.waitForExportComplete(120000); // 2 minutes timeout
      expect(result.success).toBe(true);
    });

    test('should handle memory efficiently during large exports', async ({ page }) => {
      // Monitor memory before export
      const memoryBefore = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      // Select all results and export
      await resultsPage.selectAllResults();
      await resultsPage.bulkExportSelected();
      
      const exportResult = await exportPage.performExport({
        format: 'csv',
        fields: ['filePath', 'lineNumber', 'content'],
        exportOptions: {
          compressOutput: true
        }
      });

      expect(exportResult.success).toBe(true);
      
      // Monitor memory after export
      const memoryAfter = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      // Memory usage should not increase dramatically
      if (memoryBefore && memoryAfter) {
        const memoryIncrease = memoryAfter.used - memoryBefore.used;
        expect(memoryIncrease).toBeLessThan(200 * 1024 * 1024); // Less than 200MB increase
      }
    });
  });

  test.describe('Batch Export Operations @export @bulk @batch', () => {
    test('should export multiple formats simultaneously', async () => {
      // Select results
      await resultsPage.selectResult(0);
      await resultsPage.selectResult(1);
      await resultsPage.selectResult(2);
      
      const formats = ['json', 'csv', 'yaml'];
      const exportPromises = [];
      
      // Start multiple exports
      for (const format of formats) {
        await resultsPage.bulkExportSelected();
        
        const exportPromise = exportPage.performExport({
          format: format,
          fields: ['filePath', 'content'],
          filename: `batch_export_${format}_${Date.now()}`
        });
        
        exportPromises.push(exportPromise);
      }
      
      // Wait for all exports to complete
      const results = await Promise.all(exportPromises);
      
      // All exports should succeed
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
      });
    });

    test('should handle concurrent bulk exports', async ({ browser }) => {
      // Create multiple browser contexts for concurrent exports
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const exportPromises = contexts.map(async (context, index) => {
        const page = await context.newPage();
        const loginPageInstance = new LoginPage(page);
        const searchPageInstance = new SearchPage(page);
        const resultsPageInstance = new ResultsPage(page);
        const exportPageInstance = new ExportPage(page);
        
        // Setup user and search
        const testUser = {
          username: `concurrent_bulk_${Date.now()}_${index}`,
          email: `concurrent_bulk_${Date.now()}_${index}@example.com`,
          password: 'ConcurrentBulk123!'
        };
        
        await loginPageInstance.register(testUser);
        await loginPageInstance.login(testUser.username, testUser.password);
        
        await searchPageInstance.navigateToSearch();
        await searchPageInstance.performAdvancedSearch({
          query: `test${index}`,
          fileTypes: ['js'],
          searchType: 'exact'
        });
        
        await searchPageInstance.waitForResults();
        
        // Select and export results
        await resultsPageInstance.selectAllResults();
        await resultsPageInstance.bulkExportSelected();
        
        return exportPageInstance.performExport({
          format: 'json',
          fields: ['filePath', 'content']
        });
      });

      const results = await Promise.all(exportPromises);
      
      // All concurrent exports should succeed
      results.forEach(result => {
        expect(result.success).toBe(true);
      });

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should queue exports when system is busy', async () => {
      // Start multiple exports rapidly
      await resultsPage.selectAllResults();
      
      const exportCount = 5;
      const exportPromises = [];
      
      for (let i = 0; i < exportCount; i++) {
        await resultsPage.bulkExportSelected();
        
        const exportPromise = exportPage.performExport({
          format: 'json',
          fields: ['filePath', 'content'],
          filename: `queued_export_${i}_${Date.now()}`
        });
        
        exportPromises.push(exportPromise);
      }
      
      // Some exports might be queued
      const results = await Promise.all(exportPromises);
      
      // Most should succeed, some might be queued
      const successCount = results.filter(r => r.success).length;
      const queuedCount = results.filter(r => r.queued).length;
      
      expect(successCount + queuedCount).toBe(exportCount);
      expect(successCount).toBeGreaterThan(0);
    });
  });

  test.describe('Export Validation and Quality @export @bulk @validation', () => {
    test('should validate exported data integrity', async () => {
      // Get original results data
      const originalResults = await resultsPage.getAllResults();
      expect(originalResults.length).toBeGreaterThan(0);
      
      // Select and export all results
      await resultsPage.selectAllResults();
      await resultsPage.bulkExportSelected();
      
      const exportResult = await exportPage.performExport({
        format: 'json',
        fields: ['filePath', 'lineNumber', 'content', 'author']
      });

      expect(exportResult.success).toBe(true);
      
      const download = await exportPage.downloadFile();
      const validation = await exportPage.validateExportContent(download, 'json');
      
      expect(validation.isValid).toBe(true);
      
      // Validate data integrity
      if (Array.isArray(validation.parsedContent)) {
        expect(validation.parsedContent.length).toBe(originalResults.length);
        
        // Spot check some results
        for (let i = 0; i < Math.min(5, originalResults.length); i++) {
          const original = originalResults[i];
          const exported = validation.parsedContent[i];
          
          expect(exported.filePath).toBe(original.filePath);
          expect(exported.lineNumber).toBe(original.lineNumber);
          expect(exported.content).toBe(original.codeContent);
        }
      }
    });

    test('should handle special characters in bulk export', async () => {
      // Search for content with special characters
      await searchPage.performAdvancedSearch({
        query: 'console.log',
        fileTypes: ['js'],
        searchType: 'exact'
      });
      
      await searchPage.waitForResults();
      
      // Select and export results
      await resultsPage.selectAllResults();
      await resultsPage.bulkExportSelected();
      
      const formats = ['json', 'csv', 'xml'];
      
      for (const format of formats) {
        const exportResult = await exportPage.performExport({
          format: format,
          fields: ['filePath', 'content']
        });

        expect(exportResult.success).toBe(true);
        
        const download = await exportPage.downloadFile();
        const validation = await exportPage.validateExportContent(download, format);
        
        expect(validation.isValid).toBe(true);
        
        // Should properly handle special characters
        expect(validation.content).not.toContain('undefined');
        expect(validation.content).not.toContain('null');
      }
    });

    test('should maintain consistent export format across batches', async () => {
      // Export in multiple batches
      const batchSize = 10;
      const batches = [];
      
      for (let batch = 0; batch < 3; batch++) {
        // Select a batch of results
        for (let i = 0; i < batchSize; i++) {
          const resultIndex = batch * batchSize + i;
          await resultsPage.selectResult(resultIndex);
        }
        
        await resultsPage.bulkExportSelected();
        
        const exportResult = await exportPage.performExport({
          format: 'json',
          fields: ['filePath', 'lineNumber', 'content'],
          filename: `batch_${batch}_${Date.now()}`
        });

        expect(exportResult.success).toBe(true);
        
        const download = await exportPage.downloadFile();
        const validation = await exportPage.validateExportContent(download, 'json');
        
        expect(validation.isValid).toBe(true);
        batches.push(validation.parsedContent);
        
        // Clear selection for next batch
        await resultsPage.selectAllResults(); // Deselect all
      }
      
      // Verify consistent format across batches
      batches.forEach(batch => {
        if (Array.isArray(batch) && batch.length > 0) {
          const firstItem = batch[0];
          expect(firstItem).toHaveProperty('filePath');
          expect(firstItem).toHaveProperty('lineNumber');
          expect(firstItem).toHaveProperty('content');
        }
      });
    });
  });
});
