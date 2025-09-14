/**
 * Base Page Object Model for GitHound web tests.
 * Provides common functionality and utilities for all page objects.
 */

const { expect } = require('@playwright/test');

class BasePage {
  constructor(page) {
    this.page = page;
    this.baseURL = process.env.BASE_URL || 'http://localhost:8000';
    this.timeout = 30000;
  }

  /**
   * Navigate to a specific URL
   */
  async goto(path = '') {
    const url = path.startsWith('http') ? path : `${this.baseURL}${path}`;
    await this.page.goto(url, { waitUntil: 'networkidle' });
  }

  /**
   * Wait for an element to be visible
   */
  async waitForElement(selector, timeout = this.timeout) {
    return await this.page.waitForSelector(selector, { timeout });
  }

  /**
   * Wait for an element by test ID
   */
  async waitForTestId(testId, timeout = this.timeout) {
    return await this.waitForElement(`[data-testid="${testId}"]`, timeout);
  }

  /**
   * Click an element by test ID
   */
  async clickTestId(testId) {
    await this.page.click(`[data-testid="${testId}"]`);
  }

  /**
   * Fill an input by test ID
   */
  async fillTestId(testId, value) {
    await this.page.fill(`[data-testid="${testId}"]`, value);
  }

  /**
   * Get text content by test ID
   */
  async getTextByTestId(testId) {
    return await this.page.textContent(`[data-testid="${testId}"]`);
  }

  /**
   * Check if element is visible by test ID
   */
  async isVisibleByTestId(testId) {
    return await this.page.isVisible(`[data-testid="${testId}"]`);
  }

  /**
   * Wait for page to load completely
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForSelector('body');
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(name) {
    return await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    });
  }

  /**
   * Wait for API response
   */
  async waitForApiResponse(urlPattern, timeout = this.timeout) {
    return await this.page.waitForResponse(
      response => response.url().includes(urlPattern) && response.status() === 200,
      { timeout }
    );
  }

  /**
   * Get current URL
   */
  getCurrentUrl() {
    return this.page.url();
  }

  /**
   * Get page title
   */
  async getTitle() {
    return await this.page.title();
  }

  /**
   * Reload the page
   */
  async reload() {
    await this.page.reload({ waitUntil: 'networkidle' });
  }

  /**
   * Go back in browser history
   */
  async goBack() {
    await this.page.goBack({ waitUntil: 'networkidle' });
  }

  /**
   * Execute JavaScript in the page context
   */
  async evaluate(fn, ...args) {
    return await this.page.evaluate(fn, ...args);
  }

  /**
   * Wait for a specific timeout
   */
  async wait(ms) {
    await this.page.waitForTimeout(ms);
  }

  /**
   * Check if element exists
   */
  async elementExists(selector) {
    return await this.page.locator(selector).count() > 0;
  }

  /**
   * Get element count
   */
  async getElementCount(selector) {
    return await this.page.locator(selector).count();
  }

  /**
   * Hover over an element
   */
  async hoverTestId(testId) {
    await this.page.hover(`[data-testid="${testId}"]`);
  }

  /**
   * Select option from dropdown
   */
  async selectOptionByTestId(testId, value) {
    await this.page.selectOption(`[data-testid="${testId}"]`, value);
  }

  /**
   * Check a checkbox
   */
  async checkByTestId(testId) {
    await this.page.check(`[data-testid="${testId}"]`);
  }

  /**
   * Uncheck a checkbox
   */
  async uncheckByTestId(testId) {
    await this.page.uncheck(`[data-testid="${testId}"]`);
  }

  /**
   * Upload a file
   */
  async uploadFileByTestId(testId, filePath) {
    await this.page.setInputFiles(`[data-testid="${testId}"]`, filePath);
  }

  /**
   * Press a key
   */
  async pressKey(key) {
    await this.page.keyboard.press(key);
  }

  /**
   * Type text
   */
  async typeText(text) {
    await this.page.keyboard.type(text);
  }

  /**
   * Clear input field
   */
  async clearInputByTestId(testId) {
    await this.page.fill(`[data-testid="${testId}"]`, '');
  }

  /**
   * Get input value
   */
  async getInputValueByTestId(testId) {
    return await this.page.inputValue(`[data-testid="${testId}"]`);
  }

  /**
   * Wait for element to be hidden
   */
  async waitForHidden(selector, timeout = this.timeout) {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  /**
   * Wait for element to be attached
   */
  async waitForAttached(selector, timeout = this.timeout) {
    await this.page.waitForSelector(selector, { state: 'attached', timeout });
  }

  /**
   * Get all text contents of elements
   */
  async getAllTextContents(selector) {
    return await this.page.locator(selector).allTextContents();
  }

  /**
   * Get element attribute
   */
  async getAttributeByTestId(testId, attribute) {
    return await this.page.getAttribute(`[data-testid="${testId}"]`, attribute);
  }

  /**
   * Check if element is enabled
   */
  async isEnabledByTestId(testId) {
    return await this.page.isEnabled(`[data-testid="${testId}"]`);
  }

  /**
   * Check if element is disabled
   */
  async isDisabledByTestId(testId) {
    return await this.page.isDisabled(`[data-testid="${testId}"]`);
  }

  /**
   * Check if checkbox is checked
   */
  async isCheckedByTestId(testId) {
    return await this.page.isChecked(`[data-testid="${testId}"]`);
  }

  /**
   * Drag and drop
   */
  async dragAndDrop(sourceTestId, targetTestId) {
    await this.page.dragAndDrop(
      `[data-testid="${sourceTestId}"]`,
      `[data-testid="${targetTestId}"]`
    );
  }

  /**
   * Right click on element
   */
  async rightClickByTestId(testId) {
    await this.page.click(`[data-testid="${testId}"]`, { button: 'right' });
  }

  /**
   * Double click on element
   */
  async doubleClickByTestId(testId) {
    await this.page.dblclick(`[data-testid="${testId}"]`);
  }

  /**
   * Focus on element
   */
  async focusOnTestId(testId) {
    await this.page.focus(`[data-testid="${testId}"]`);
  }

  /**
   * Blur element
   */
  async blurTestId(testId) {
    await this.page.evaluate((testId) => {
      document.querySelector(`[data-testid="${testId}"]`).blur();
    }, testId);
  }

  /**
   * Get CSS property value
   */
  async getCSSProperty(selector, property) {
    return await this.page.evaluate(
      ({ selector, property }) => {
        const element = document.querySelector(selector);
        return window.getComputedStyle(element).getPropertyValue(property);
      },
      { selector, property }
    );
  }

  /**
   * Scroll element into view
   */
  async scrollIntoViewByTestId(testId) {
    await this.page.evaluate((testId) => {
      document.querySelector(`[data-testid="${testId}"]`).scrollIntoView();
    }, testId);
  }

  /**
   * Get viewport size
   */
  async getViewportSize() {
    return this.page.viewportSize();
  }

  /**
   * Set viewport size
   */
  async setViewportSize(width, height) {
    await this.page.setViewportSize({ width, height });
  }
}

module.exports = BasePage;
