/**
 * Search Page Object Model for GitHound web tests.
 * Handles search functionality, filters, and result interactions.
 */

const { expect } = require('@playwright/test');
const BasePage = require('./base-page');

class SearchPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Page elements
    this.elements = {
      // Search form elements
      repoPathInput: '[data-testid="repo-path-input"]',
      searchQueryInput: '[data-testid="search-query-input"]',
      submitSearchButton: '[data-testid="submit-search"]',
      cancelSearchButton: '[data-testid="cancel-search"]',
      
      // Search type tabs
      advancedSearchTab: '[data-testid="advanced-search-tab"]',
      fuzzySearchTab: '[data-testid="fuzzy-search-tab"]',
      historicalSearchTab: '[data-testid="historical-search-tab"]',
      
      // Fuzzy search elements
      fuzzyQueryInput: '[data-testid="fuzzy-query-input"]',
      fuzzyThresholdInput: '[data-testid="fuzzy-threshold"]',
      submitFuzzySearchButton: '[data-testid="submit-fuzzy-search"]',
      
      // Historical search elements
      historicalQueryInput: '[data-testid="historical-query-input"]',
      commitFromInput: '[data-testid="commit-from"]',
      commitToInput: '[data-testid="commit-to"]',
      submitHistoricalSearchButton: '[data-testid="submit-historical-search"]',
      
      // Filter elements
      filtersTab: '[data-testid="filters-tab"]',
      fileTypePy: '[data-testid="file-type-py"]',
      fileTypeJs: '[data-testid="file-type-js"]',
      fileTypeTs: '[data-testid="file-type-ts"]',
      fileTypeJava: '[data-testid="file-type-java"]',
      authorFilter: '[data-testid="author-filter"]',
      dateFromFilter: '[data-testid="date-from"]',
      dateToFilter: '[data-testid="date-to"]',
      maxResultsInput: '[data-testid="max-results"]',
      caseSensitiveCheckbox: '[data-testid="case-sensitive"]',
      includeBinaryCheckbox: '[data-testid="include-binary"]',
      
      // Search progress and status
      searchProgress: '[data-testid="search-progress"]',
      searchStatus: '[data-testid="search-status"]',
      searchTypeIndicator: '[data-testid="search-type-indicator"]',
      searchCancelled: '[data-testid="search-cancelled"]',
      
      // Results elements
      searchResults: '[data-testid="search-results"]',
      resultCard: '[data-testid="result-card"]',
      filePath: '[data-testid="file-path"]',
      lineNumber: '[data-testid="line-number"]',
      codeContent: '[data-testid="code-content"]',
      commitInfo: '[data-testid="commit-info"]',
      
      // Pagination elements
      pagination: '[data-testid="pagination"]',
      nextPage: '[data-testid="next-page"]',
      prevPage: '[data-testid="prev-page"]',
      currentPage: '[data-testid="current-page"]',
      
      // Export elements
      exportButton: '[data-testid="export-button"]',
      exportFormat: '[data-testid="export-format"]',
      confirmExport: '[data-testid="confirm-export"]',
      exportProgress: '[data-testid="export-progress"]',
      
      // Search history
      searchHistoryTab: '[data-testid="search-history-tab"]',
      historyItem: '[data-testid="history-item"]',
      
      // Error elements
      searchError: '[data-testid="search-error"]',
      repoPathError: '[data-testid="repo-path-error"]',
      queryError: '[data-testid="query-error"]'
    };
  }

  /**
   * Navigate to search page
   */
  async navigateToSearch() {
    await this.goto('/search');
    await this.waitForElement(this.elements.searchQueryInput);
  }

  /**
   * Fill basic search form
   */
  async fillBasicSearch(repoPath, query) {
    await this.page.fill(this.elements.repoPathInput, repoPath);
    await this.page.fill(this.elements.searchQueryInput, query);
  }

  /**
   * Submit search
   */
  async submitSearch() {
    await this.page.click(this.elements.submitSearchButton);
  }

  /**
   * Perform advanced search
   */
  async performAdvancedSearch(searchData) {
    await this.navigateToSearch();
    
    // Fill basic search fields
    await this.fillBasicSearch(searchData.repoPath, searchData.query);
    
    // Apply filters if provided
    if (searchData.filters) {
      await this.applyFilters(searchData.filters);
    }
    
    await this.submitSearch();
    
    // Wait for search to start
    await this.waitForElement(this.elements.searchProgress);
  }

  /**
   * Apply search filters
   */
  async applyFilters(filters) {
    await this.page.click(this.elements.filtersTab);
    
    if (filters.fileTypes) {
      for (const fileType of filters.fileTypes) {
        const checkbox = `[data-testid="file-type-${fileType}"]`;
        await this.page.check(checkbox);
      }
    }
    
    if (filters.author) {
      await this.page.fill(this.elements.authorFilter, filters.author);
    }
    
    if (filters.dateFrom) {
      await this.page.fill(this.elements.dateFromFilter, filters.dateFrom);
    }
    
    if (filters.dateTo) {
      await this.page.fill(this.elements.dateToFilter, filters.dateTo);
    }
    
    if (filters.maxResults) {
      await this.page.fill(this.elements.maxResultsInput, filters.maxResults.toString());
    }
    
    if (filters.caseSensitive) {
      await this.page.check(this.elements.caseSensitiveCheckbox);
    }
    
    if (filters.includeBinary) {
      await this.page.check(this.elements.includeBinaryCheckbox);
    }
  }

  /**
   * Perform fuzzy search
   */
  async performFuzzySearch(repoPath, query, threshold = '0.8') {
    await this.navigateToSearch();
    await this.page.click(this.elements.fuzzySearchTab);
    
    await this.page.fill(this.elements.repoPathInput, repoPath);
    await this.page.fill(this.elements.fuzzyQueryInput, query);
    await this.page.fill(this.elements.fuzzyThresholdInput, threshold);
    
    await this.page.click(this.elements.submitFuzzySearchButton);
    await this.waitForElement(this.elements.searchProgress);
  }

  /**
   * Perform historical search
   */
  async performHistoricalSearch(repoPath, query, commitFrom, commitTo) {
    await this.navigateToSearch();
    await this.page.click(this.elements.historicalSearchTab);
    
    await this.page.fill(this.elements.repoPathInput, repoPath);
    await this.page.fill(this.elements.historicalQueryInput, query);
    await this.page.fill(this.elements.commitFromInput, commitFrom);
    await this.page.fill(this.elements.commitToInput, commitTo);
    
    await this.page.click(this.elements.submitHistoricalSearchButton);
    await this.waitForElement(this.elements.searchProgress);
  }

  /**
   * Wait for search to complete
   */
  async waitForSearchComplete(timeout = 30000) {
    try {
      await this.waitForElement(this.elements.searchResults, timeout);
      return { completed: true };
    } catch (error) {
      // Check if search was cancelled or errored
      const cancelled = await this.page.isVisible(this.elements.searchCancelled);
      const errorMessage = await this.getSearchError();
      
      return { 
        completed: false, 
        cancelled, 
        error: errorMessage 
      };
    }
  }

  /**
   * Cancel ongoing search
   */
  async cancelSearch() {
    if (await this.page.isVisible(this.elements.cancelSearchButton)) {
      await this.page.click(this.elements.cancelSearchButton);
      await this.waitForElement(this.elements.searchCancelled);
    }
  }

  /**
   * Get search results
   */
  async getSearchResults() {
    await this.waitForElement(this.elements.searchResults);
    
    const resultCards = this.page.locator(this.elements.resultCard);
    const count = await resultCards.count();
    const results = [];
    
    for (let i = 0; i < Math.min(count, 10); i++) { // Limit to first 10 for performance
      const card = resultCards.nth(i);
      
      const result = {
        filePath: await card.locator(this.elements.filePath).textContent(),
        lineNumber: await card.locator(this.elements.lineNumber).textContent(),
        codeContent: await card.locator(this.elements.codeContent).textContent(),
        commitInfo: await card.locator(this.elements.commitInfo).textContent()
      };
      
      results.push(result);
    }
    
    return {
      count,
      results
    };
  }

  /**
   * Get search result count
   */
  async getResultCount() {
    await this.waitForElement(this.elements.searchResults);
    return await this.page.locator(this.elements.resultCard).count();
  }

  /**
   * Navigate to next page of results
   */
  async goToNextPage() {
    if (await this.page.isVisible(this.elements.nextPage)) {
      await this.page.click(this.elements.nextPage);
      await this.waitForElement(this.elements.searchResults);
    }
  }

  /**
   * Navigate to previous page of results
   */
  async goToPreviousPage() {
    if (await this.page.isVisible(this.elements.prevPage)) {
      await this.page.click(this.elements.prevPage);
      await this.waitForElement(this.elements.searchResults);
    }
  }

  /**
   * Get current page number
   */
  async getCurrentPageNumber() {
    if (await this.page.isVisible(this.elements.currentPage)) {
      return await this.page.textContent(this.elements.currentPage);
    }
    return '1';
  }

  /**
   * Export search results
   */
  async exportResults(format = 'json') {
    await this.waitForElement(this.elements.exportButton);
    await this.page.click(this.elements.exportButton);
    
    await this.page.selectOption(this.elements.exportFormat, format);
    await this.page.click(this.elements.confirmExport);
    
    // Wait for export to start
    await this.waitForElement(this.elements.exportProgress);
  }

  /**
   * Get search error message
   */
  async getSearchError() {
    try {
      if (await this.page.isVisible(this.elements.searchError)) {
        return await this.page.textContent(this.elements.searchError);
      }
    } catch (error) {
      // Ignore
    }
    return null;
  }

  /**
   * Get validation errors
   */
  async getValidationErrors() {
    const errors = {};
    
    if (await this.page.isVisible(this.elements.repoPathError)) {
      errors.repoPath = await this.page.textContent(this.elements.repoPathError);
    }
    
    if (await this.page.isVisible(this.elements.queryError)) {
      errors.query = await this.page.textContent(this.elements.queryError);
    }
    
    return errors;
  }

  /**
   * Verify search form validation
   */
  async verifySearchFormValidation() {
    await this.navigateToSearch();
    
    // Try to submit empty form
    await this.submitSearch();
    
    const errors = await this.getValidationErrors();
    return {
      hasRepoPathError: !!errors.repoPath,
      hasQueryError: !!errors.query,
      errors
    };
  }

  /**
   * Get search history
   */
  async getSearchHistory() {
    await this.page.click(this.elements.searchHistoryTab);
    await this.waitForElement(this.elements.historyItem);
    
    const historyItems = this.page.locator(this.elements.historyItem);
    const count = await historyItems.count();
    const history = [];
    
    for (let i = 0; i < count; i++) {
      const item = await historyItems.nth(i).textContent();
      history.push(item);
    }
    
    return history;
  }

  /**
   * Click on search history item
   */
  async clickHistoryItem(index = 0) {
    await this.page.click(this.elements.searchHistoryTab);
    await this.waitForElement(this.elements.historyItem);
    
    const historyItems = this.page.locator(this.elements.historyItem);
    await historyItems.nth(index).click();
  }

  /**
   * Get search status
   */
  async getSearchStatus() {
    try {
      if (await this.page.isVisible(this.elements.searchStatus)) {
        return await this.page.textContent(this.elements.searchStatus);
      }
    } catch (error) {
      // Ignore
    }
    return null;
  }

  /**
   * Get search type indicator
   */
  async getSearchTypeIndicator() {
    try {
      if (await this.page.isVisible(this.elements.searchTypeIndicator)) {
        return await this.page.textContent(this.elements.searchTypeIndicator);
      }
    } catch (error) {
      // Ignore
    }
    return null;
  }

  /**
   * Check if search is in progress
   */
  async isSearchInProgress() {
    return await this.page.isVisible(this.elements.searchProgress);
  }

  /**
   * Check if results are displayed
   */
  async hasResults() {
    return await this.page.isVisible(this.elements.searchResults);
  }

  /**
   * Check if pagination is available
   */
  async hasPagination() {
    return await this.page.isVisible(this.elements.pagination);
  }

  /**
   * Validate search results contain expected file types
   */
  async validateResultFileTypes(expectedTypes) {
    const results = await this.getSearchResults();
    const violations = [];

    for (const result of results.results) {
      const filePath = result.filePath;
      const hasExpectedType = expectedTypes.some(type =>
        filePath.endsWith(`.${type}`)
      );

      if (!hasExpectedType) {
        violations.push(`File ${filePath} does not match expected types: ${expectedTypes.join(', ')}`);
      }
    }

    return {
      valid: violations.length === 0,
      violations
    };
  }
}

module.exports = SearchPage;
