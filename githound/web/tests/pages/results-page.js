/**
 * Results Page Object Model for GitHound web tests.
 * Handles search results display, filtering, and interaction.
 */

const { expect } = require('@playwright/test');
const BasePage = require('./base-page');

class ResultsPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Page elements
    this.elements = {
      // Results container
      resultsContainer: '[data-testid="search-results"]',
      resultCard: '[data-testid="result-card"]',
      noResults: '[data-testid="no-results"]',
      resultsCount: '[data-testid="results-count"]',
      
      // Result card elements
      filePath: '[data-testid="file-path"]',
      lineNumber: '[data-testid="line-number"]',
      codeContent: '[data-testid="code-content"]',
      commitHash: '[data-testid="commit-hash"]',
      commitMessage: '[data-testid="commit-message"]',
      author: '[data-testid="author"]',
      commitDate: '[data-testid="commit-date"]',
      
      // Result actions
      viewFileButton: '[data-testid="view-file"]',
      copyLinkButton: '[data-testid="copy-link"]',
      viewCommitButton: '[data-testid="view-commit"]',
      
      // Sorting and filtering
      sortDropdown: '[data-testid="sort-dropdown"]',
      sortByRelevance: '[data-testid="sort-relevance"]',
      sortByDate: '[data-testid="sort-date"]',
      sortByFile: '[data-testid="sort-file"]',
      
      // Result filtering
      filterByFileType: '[data-testid="filter-file-type"]',
      filterByAuthor: '[data-testid="filter-author"]',
      filterByDateRange: '[data-testid="filter-date-range"]',
      clearFilters: '[data-testid="clear-filters"]',
      
      // Pagination
      pagination: '[data-testid="pagination"]',
      firstPage: '[data-testid="first-page"]',
      prevPage: '[data-testid="prev-page"]',
      nextPage: '[data-testid="next-page"]',
      lastPage: '[data-testid="last-page"]',
      currentPage: '[data-testid="current-page"]',
      totalPages: '[data-testid="total-pages"]',
      pageSize: '[data-testid="page-size"]',
      
      // Bulk actions
      selectAllCheckbox: '[data-testid="select-all"]',
      resultCheckbox: '[data-testid="result-checkbox"]',
      bulkExport: '[data-testid="bulk-export"]',
      bulkDelete: '[data-testid="bulk-delete"]',
      selectedCount: '[data-testid="selected-count"]',
      
      // Result details modal
      resultModal: '[data-testid="result-modal"]',
      modalClose: '[data-testid="modal-close"]',
      modalContent: '[data-testid="modal-content"]',
      modalFilePath: '[data-testid="modal-file-path"]',
      modalCodeContent: '[data-testid="modal-code-content"]',
      
      // Loading and error states
      loadingSpinner: '[data-testid="loading-spinner"]',
      errorMessage: '[data-testid="error-message"]',
      retryButton: '[data-testid="retry-button"]'
    };
  }

  /**
   * Wait for results to load
   */
  async waitForResults(timeout = 30000) {
    try {
      await this.waitForElement(this.elements.resultsContainer, timeout);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get total number of results
   */
  async getResultCount() {
    await this.waitForResults();
    return await this.page.locator(this.elements.resultCard).count();
  }

  /**
   * Get results count text
   */
  async getResultsCountText() {
    if (await this.page.isVisible(this.elements.resultsCount)) {
      return await this.page.textContent(this.elements.resultsCount);
    }
    return null;
  }

  /**
   * Check if there are no results
   */
  async hasNoResults() {
    return await this.page.isVisible(this.elements.noResults);
  }

  /**
   * Get all result data
   */
  async getAllResults() {
    await this.waitForResults();
    
    const resultCards = this.page.locator(this.elements.resultCard);
    const count = await resultCards.count();
    const results = [];
    
    for (let i = 0; i < count; i++) {
      const card = resultCards.nth(i);
      
      const result = {
        filePath: await this.getCardText(card, this.elements.filePath),
        lineNumber: await this.getCardText(card, this.elements.lineNumber),
        codeContent: await this.getCardText(card, this.elements.codeContent),
        commitHash: await this.getCardText(card, this.elements.commitHash),
        commitMessage: await this.getCardText(card, this.elements.commitMessage),
        author: await this.getCardText(card, this.elements.author),
        commitDate: await this.getCardText(card, this.elements.commitDate)
      };
      
      results.push(result);
    }
    
    return results;
  }

  /**
   * Helper method to get text from card element
   */
  async getCardText(card, selector) {
    try {
      const element = card.locator(selector);
      if (await element.isVisible()) {
        return await element.textContent();
      }
    } catch (error) {
      // Element not found or not visible
    }
    return '';
  }

  /**
   * Get specific result by index
   */
  async getResult(index) {
    const resultCards = this.page.locator(this.elements.resultCard);
    const card = resultCards.nth(index);
    
    return {
      filePath: await this.getCardText(card, this.elements.filePath),
      lineNumber: await this.getCardText(card, this.elements.lineNumber),
      codeContent: await this.getCardText(card, this.elements.codeContent),
      commitHash: await this.getCardText(card, this.elements.commitHash),
      commitMessage: await this.getCardText(card, this.elements.commitMessage),
      author: await this.getCardText(card, this.elements.author),
      commitDate: await this.getCardText(card, this.elements.commitDate)
    };
  }

  /**
   * Click on a result to view details
   */
  async clickResult(index) {
    const resultCards = this.page.locator(this.elements.resultCard);
    await resultCards.nth(index).click();
  }

  /**
   * View file for a specific result
   */
  async viewFile(index) {
    const resultCards = this.page.locator(this.elements.resultCard);
    const card = resultCards.nth(index);
    await card.locator(this.elements.viewFileButton).click();
  }

  /**
   * View commit for a specific result
   */
  async viewCommit(index) {
    const resultCards = this.page.locator(this.elements.resultCard);
    const card = resultCards.nth(index);
    await card.locator(this.elements.viewCommitButton).click();
  }

  /**
   * Copy link for a specific result
   */
  async copyResultLink(index) {
    const resultCards = this.page.locator(this.elements.resultCard);
    const card = resultCards.nth(index);
    await card.locator(this.elements.copyLinkButton).click();
  }

  /**
   * Sort results
   */
  async sortResults(sortBy) {
    await this.page.click(this.elements.sortDropdown);
    
    switch (sortBy) {
      case 'relevance':
        await this.page.click(this.elements.sortByRelevance);
        break;
      case 'date':
        await this.page.click(this.elements.sortByDate);
        break;
      case 'file':
        await this.page.click(this.elements.sortByFile);
        break;
    }
    
    // Wait for results to reload
    await this.waitForResults();
  }

  /**
   * Navigate to specific page
   */
  async goToPage(pageNumber) {
    // If page number input exists, use it
    if (await this.page.isVisible('[data-testid="page-input"]')) {
      await this.page.fill('[data-testid="page-input"]', pageNumber.toString());
      await this.page.press('[data-testid="page-input"]', 'Enter');
    } else {
      // Otherwise use pagination buttons
      const currentPage = await this.getCurrentPage();
      const targetPage = parseInt(pageNumber);
      
      if (targetPage > currentPage) {
        for (let i = currentPage; i < targetPage; i++) {
          await this.goToNextPage();
        }
      } else if (targetPage < currentPage) {
        for (let i = currentPage; i > targetPage; i--) {
          await this.goToPreviousPage();
        }
      }
    }
    
    await this.waitForResults();
  }

  /**
   * Go to next page
   */
  async goToNextPage() {
    if (await this.page.isVisible(this.elements.nextPage)) {
      await this.page.click(this.elements.nextPage);
      await this.waitForResults();
    }
  }

  /**
   * Go to previous page
   */
  async goToPreviousPage() {
    if (await this.page.isVisible(this.elements.prevPage)) {
      await this.page.click(this.elements.prevPage);
      await this.waitForResults();
    }
  }

  /**
   * Go to first page
   */
  async goToFirstPage() {
    if (await this.page.isVisible(this.elements.firstPage)) {
      await this.page.click(this.elements.firstPage);
      await this.waitForResults();
    }
  }

  /**
   * Go to last page
   */
  async goToLastPage() {
    if (await this.page.isVisible(this.elements.lastPage)) {
      await this.page.click(this.elements.lastPage);
      await this.waitForResults();
    }
  }

  /**
   * Get current page number
   */
  async getCurrentPage() {
    if (await this.page.isVisible(this.elements.currentPage)) {
      const pageText = await this.page.textContent(this.elements.currentPage);
      return parseInt(pageText) || 1;
    }
    return 1;
  }

  /**
   * Get total pages
   */
  async getTotalPages() {
    if (await this.page.isVisible(this.elements.totalPages)) {
      const pagesText = await this.page.textContent(this.elements.totalPages);
      return parseInt(pagesText) || 1;
    }
    return 1;
  }

  /**
   * Select all results
   */
  async selectAllResults() {
    if (await this.page.isVisible(this.elements.selectAllCheckbox)) {
      await this.page.check(this.elements.selectAllCheckbox);
    }
  }

  /**
   * Select specific result
   */
  async selectResult(index) {
    const resultCards = this.page.locator(this.elements.resultCard);
    const card = resultCards.nth(index);
    const checkbox = card.locator(this.elements.resultCheckbox);
    
    if (await checkbox.isVisible()) {
      await checkbox.check();
    }
  }

  /**
   * Get selected results count
   */
  async getSelectedCount() {
    if (await this.page.isVisible(this.elements.selectedCount)) {
      const countText = await this.page.textContent(this.elements.selectedCount);
      return parseInt(countText) || 0;
    }
    return 0;
  }

  /**
   * Bulk export selected results
   */
  async bulkExportSelected() {
    if (await this.page.isVisible(this.elements.bulkExport)) {
      await this.page.click(this.elements.bulkExport);
    }
  }

  /**
   * Check if pagination is available
   */
  async hasPagination() {
    return await this.page.isVisible(this.elements.pagination);
  }

  /**
   * Check if results are loading
   */
  async isLoading() {
    return await this.page.isVisible(this.elements.loadingSpinner);
  }

  /**
   * Check if there's an error
   */
  async hasError() {
    return await this.page.isVisible(this.elements.errorMessage);
  }

  /**
   * Get error message
   */
  async getErrorMessage() {
    if (await this.hasError()) {
      return await this.page.textContent(this.elements.errorMessage);
    }
    return null;
  }

  /**
   * Retry loading results
   */
  async retryLoading() {
    if (await this.page.isVisible(this.elements.retryButton)) {
      await this.page.click(this.elements.retryButton);
      await this.waitForResults();
    }
  }
}

module.exports = ResultsPage;
