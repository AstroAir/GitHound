/**
 * Accessibility Manager for GitHound
 * Provides comprehensive accessibility features and WCAG compliance
 */

import { Component } from '../core/component.js';

export class AccessibilityManager extends Component {
  constructor() {
    super('accessibility-manager');

    this.focusHistory = [];
    this.announcements = [];
    this.keyboardNavigation = true;
    this.screenReaderMode = false;
    this.highContrastMode = false;
    this.reducedMotionMode = false;
    this.focusTrapStack = [];

    this.keyboardShortcuts = new Map();
    this.landmarkElements = new Map();
    this.skipLinks = [];
  }

  async init() {
    await super.init();

    this.detectAccessibilityPreferences();
    this.setupKeyboardNavigation();
    this.setupScreenReaderSupport();
    this.setupFocusManagement();
    this.setupSkipLinks();
    this.setupLandmarks();
    this.setupKeyboardShortcuts();
    this.setupARIALiveRegions();

    this.startAccessibilityMonitoring();
  }

  /**
   * Detect user accessibility preferences
   */
  detectAccessibilityPreferences() {
    // Detect reduced motion preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      this.reducedMotionMode = true;
      document.documentElement.setAttribute('data-reduced-motion', 'true');
      this.emit('accessibility:reduced-motion-enabled');
    }

    // Detect high contrast preference
    if (window.matchMedia('(prefers-contrast: high)').matches) {
      this.highContrastMode = true;
      document.documentElement.setAttribute('data-high-contrast', 'true');
      this.emit('accessibility:high-contrast-enabled');
    }

    // Detect screen reader usage
    this.detectScreenReader();

    // Listen for preference changes
    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', e => {
      this.reducedMotionMode = e.matches;
      document.documentElement.setAttribute('data-reduced-motion', e.matches);
      this.emit('accessibility:reduced-motion-changed', { enabled: e.matches });
    });

    window.matchMedia('(prefers-contrast: high)').addEventListener('change', e => {
      this.highContrastMode = e.matches;
      document.documentElement.setAttribute('data-high-contrast', e.matches);
      this.emit('accessibility:high-contrast-changed', { enabled: e.matches });
    });
  }

  /**
   * Detect screen reader usage
   */
  detectScreenReader() {
    // Check for common screen reader indicators
    const indicators = [
      () => navigator.userAgent.includes('NVDA'),
      () => navigator.userAgent.includes('JAWS'),
      () => navigator.userAgent.includes('VoiceOver'),
      () => window.speechSynthesis && window.speechSynthesis.getVoices().length > 0,
      () => 'speechSynthesis' in window
    ];

    this.screenReaderMode = indicators.some(check => check());

    if (this.screenReaderMode) {
      document.documentElement.setAttribute('data-screen-reader', 'true');
      this.emit('accessibility:screen-reader-detected');
    }
  }

  /**
   * Setup keyboard navigation
   */
  setupKeyboardNavigation() {
    document.addEventListener('keydown', this.handleKeyboardNavigation.bind(this));

    // Add visible focus indicators
    document.addEventListener('keydown', e => {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
      }
    });

    document.addEventListener('mousedown', () => {
      document.body.classList.remove('keyboard-navigation');
    });

    // Ensure all interactive elements are focusable
    this.ensureFocusableElements();
  }

  /**
   * Handle keyboard navigation
   */
  handleKeyboardNavigation(event) {
    const { key, ctrlKey, altKey, shiftKey } = event;

    // Handle escape key
    if (key === 'Escape') {
      this.handleEscape();
      return;
    }

    // Handle arrow key navigation
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
      this.handleArrowNavigation(event);
    }

    // Handle tab navigation
    if (key === 'Tab') {
      this.handleTabNavigation(event);
    }

    // Handle keyboard shortcuts
    const shortcutKey = this.getShortcutKey(event);
    if (this.keyboardShortcuts.has(shortcutKey)) {
      event.preventDefault();
      const handler = this.keyboardShortcuts.get(shortcutKey);
      handler(event);
    }
  }

  /**
   * Handle escape key press
   */
  handleEscape() {
    // Close modals, dropdowns, etc.
    const activeModal = document.querySelector('.modal.active, .dropdown.open');
    if (activeModal) {
      this.closeModal(activeModal);
      return;
    }

    // Return focus to previous element
    if (this.focusHistory.length > 0) {
      const previousFocus = this.focusHistory.pop();
      if (previousFocus && previousFocus.focus) {
        previousFocus.focus();
      }
    }
  }

  /**
   * Handle arrow key navigation
   */
  handleArrowNavigation(event) {
    const { key, target } = event;
    const role = target.getAttribute('role');

    // Handle specific ARIA roles
    switch (role) {
      case 'tablist':
        this.handleTablistNavigation(event);
        break;
      case 'menu':
      case 'menubar':
        this.handleMenuNavigation(event);
        break;
      case 'grid':
      case 'treegrid':
        this.handleGridNavigation(event);
        break;
      case 'listbox':
        this.handleListboxNavigation(event);
        break;
    }
  }

  /**
   * Setup screen reader support
   */
  setupScreenReaderSupport() {
    // Create announcement region
    this.createAnnouncementRegion();

    // Add screen reader only text for complex interactions
    this.addScreenReaderText();

    // Setup dynamic content announcements
    this.setupDynamicAnnouncements();
  }

  /**
   * Create ARIA live region for announcements
   */
  createAnnouncementRegion() {
    const liveRegion = document.createElement('div');
    liveRegion.id = 'aria-live-region';
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.style.cssText = `
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    `;

    document.body.appendChild(liveRegion);
    this.liveRegion = liveRegion;

    // Create assertive region for urgent announcements
    const assertiveRegion = liveRegion.cloneNode();
    assertiveRegion.id = 'aria-live-region-assertive';
    assertiveRegion.setAttribute('aria-live', 'assertive');
    document.body.appendChild(assertiveRegion);
    this.assertiveRegion = assertiveRegion;
  }

  /**
   * Announce message to screen readers
   */
  announce(message, priority = 'polite') {
    const region = priority === 'assertive' ? this.assertiveRegion : this.liveRegion;

    if (region) {
      // Clear previous announcement
      region.textContent = '';

      // Add new announcement after a brief delay
      setTimeout(() => {
        region.textContent = message;
        this.announcements.push({
          message,
          priority,
          timestamp: Date.now()
        });
      }, 100);
    }

    this.emit('accessibility:announced', { message, priority });
  }

  /**
   * Setup focus management
   */
  setupFocusManagement() {
    // Track focus changes
    document.addEventListener('focusin', this.handleFocusIn.bind(this));
    document.addEventListener('focusout', this.handleFocusOut.bind(this));

    // Setup focus traps for modals
    this.setupFocusTraps();
  }

  /**
   * Handle focus in events
   */
  handleFocusIn(event) {
    const { target } = event;

    // Add to focus history
    this.focusHistory.push(target);

    // Limit history size
    if (this.focusHistory.length > 10) {
      this.focusHistory.shift();
    }

    // Announce focused element if needed
    this.announceFocusedElement(target);
  }

  /**
   * Handle focus out events
   */
  handleFocusOut(event) {
    // Clean up any temporary focus indicators
    this.cleanupFocusIndicators();
  }

  /**
   * Announce focused element to screen readers
   */
  announceFocusedElement(element) {
    if (!this.screenReaderMode) { return; }

    const announcement = this.getFocusAnnouncement(element);
    if (announcement) {
      this.announce(announcement);
    }
  }

  /**
   * Get focus announcement for element
   */
  getFocusAnnouncement(element) {
    const role = element.getAttribute('role');
    const ariaLabel = element.getAttribute('aria-label');
    const ariaLabelledBy = element.getAttribute('aria-labelledby');

    if (ariaLabel) {
      return ariaLabel;
    }

    if (ariaLabelledBy) {
      const labelElement = document.getElementById(ariaLabelledBy);
      if (labelElement) {
        return labelElement.textContent;
      }
    }

    // Generate announcement based on element type
    switch (element.tagName.toLowerCase()) {
      case 'button':
        return `Button: ${element.textContent || element.value}`;
      case 'input':
        return this.getInputAnnouncement(element);
      case 'select':
        return `Dropdown: ${element.options[element.selectedIndex]?.text}`;
      case 'a':
        return `Link: ${element.textContent}`;
      default:
        if (role) {
          return `${role}: ${element.textContent}`;
        }
        return null;
    }
  }

  /**
   * Get input announcement
   */
  getInputAnnouncement(input) {
    const { type } = input;
    const label = this.getInputLabel(input);
    const { value } = input;

    switch (type) {
      case 'text':
      case 'email':
      case 'password':
        return `${label || 'Text input'}: ${value || 'empty'}`;
      case 'checkbox':
        return `${label || 'Checkbox'}: ${input.checked ? 'checked' : 'unchecked'}`;
      case 'radio':
        return `${label || 'Radio button'}: ${input.checked ? 'selected' : 'not selected'}`;
      default:
        return `${label || `${type} input`}: ${value || 'empty'}`;
    }
  }

  /**
   * Get input label
   */
  getInputLabel(input) {
    const { id } = input;
    if (id) {
      const label = document.querySelector(`label[for="${id}"]`);
      if (label) {
        return label.textContent;
      }
    }

    const parentLabel = input.closest('label');
    if (parentLabel) {
      return parentLabel.textContent.replace(input.value, '').trim();
    }

    return input.getAttribute('placeholder') || input.getAttribute('aria-label');
  }

  /**
   * Setup skip links
   */
  setupSkipLinks() {
    const skipLinksContainer = document.createElement('div');
    skipLinksContainer.className = 'skip-links';
    skipLinksContainer.innerHTML = `
      <a href="#main-content" class="skip-link">Skip to main content</a>
      <a href="#navigation" class="skip-link">Skip to navigation</a>
      <a href="#search" class="skip-link">Skip to search</a>
    `;

    document.body.insertBefore(skipLinksContainer, document.body.firstChild);
  }

  /**
   * Setup landmarks
   */
  setupLandmarks() {
    // Ensure main landmarks exist
    this.ensureLandmark('main', 'main-content');
    this.ensureLandmark('navigation', 'navigation');
    this.ensureLandmark('search', 'search');
    this.ensureLandmark('banner', 'header');
    this.ensureLandmark('contentinfo', 'footer');
  }

  /**
   * Ensure landmark exists
   */
  ensureLandmark(role, id) {
    let element = document.getElementById(id);

    if (!element) {
      element = document.querySelector(`[role="${role}"]`);
    }

    if (element) {
      element.setAttribute('role', role);
      if (!element.id) {
        element.id = id;
      }
      this.landmarkElements.set(role, element);
    }
  }

  /**
   * Setup keyboard shortcuts
   */
  setupKeyboardShortcuts() {
    // Common accessibility shortcuts
    this.registerShortcut('Alt+1', () => this.focusLandmark('main'));
    this.registerShortcut('Alt+2', () => this.focusLandmark('navigation'));
    this.registerShortcut('Alt+3', () => this.focusLandmark('search'));
    this.registerShortcut('Alt+0', () => this.showShortcutHelp());

    // Application shortcuts
    this.registerShortcut('Ctrl+/', () => this.focusSearch());
    this.registerShortcut('Ctrl+k', () => this.focusSearch());
    this.registerShortcut('Escape', () => this.handleEscape());
  }

  /**
   * Register keyboard shortcut
   */
  registerShortcut(keys, handler) {
    this.keyboardShortcuts.set(keys, handler);
  }

  /**
   * Get shortcut key string from event
   */
  getShortcutKey(event) {
    const parts = [];

    if (event.ctrlKey) { parts.push('Ctrl'); }
    if (event.altKey) { parts.push('Alt'); }
    if (event.shiftKey) { parts.push('Shift'); }
    if (event.metaKey) { parts.push('Meta'); }

    parts.push(event.key);

    return parts.join('+');
  }

  /**
   * Focus landmark element
   */
  focusLandmark(role) {
    const element = this.landmarkElements.get(role);
    if (element) {
      element.focus();
      this.announce(`Navigated to ${role}`);
    }
  }

  /**
   * Focus search input
   */
  focusSearch() {
    const searchInput = document.querySelector('input[type="search"], #search-input, .search-input');
    if (searchInput) {
      searchInput.focus();
      this.announce('Search focused');
    }
  }

  /**
   * Show keyboard shortcut help
   */
  showShortcutHelp() {
    const shortcuts = Array.from(this.keyboardShortcuts.keys()).join(', ');
    this.announce(`Available shortcuts: ${shortcuts}`);
  }

  /**
   * Setup ARIA live regions
   */
  setupARIALiveRegions() {
    // Monitor dynamic content changes
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          this.handleDynamicContentChange(mutation);
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  /**
   * Handle dynamic content changes
   */
  handleDynamicContentChange(mutation) {
    const { target, addedNodes } = mutation;

    // Announce important content additions
    addedNodes.forEach(node => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        this.announceNewContent(node);
      }
    });
  }

  /**
   * Announce new content
   */
  announceNewContent(element) {
    // Check if element should be announced
    const shouldAnnounce = element.hasAttribute('data-announce')
                          || element.classList.contains('notification')
                          || element.classList.contains('alert')
                          || element.classList.contains('error');

    if (shouldAnnounce) {
      const message = element.textContent || element.getAttribute('data-announce');
      if (message) {
        this.announce(message, 'assertive');
      }
    }
  }

  /**
   * Ensure all interactive elements are focusable
   */
  ensureFocusableElements() {
    const interactiveElements = document.querySelectorAll(`
      button:not([tabindex="-1"]),
      [role="button"]:not([tabindex="-1"]),
      a[href]:not([tabindex="-1"]),
      input:not([disabled]):not([tabindex="-1"]),
      select:not([disabled]):not([tabindex="-1"]),
      textarea:not([disabled]):not([tabindex="-1"]),
      [tabindex]:not([tabindex="-1"])
    `);

    interactiveElements.forEach(element => {
      if (!element.hasAttribute('tabindex')) {
        element.setAttribute('tabindex', '0');
      }
    });
  }

  /**
   * Start accessibility monitoring
   */
  startAccessibilityMonitoring() {
    // Monitor for accessibility violations
    setInterval(() => {
      this.checkAccessibilityViolations();
    }, 5000);
  }

  /**
   * Check for common accessibility violations
   */
  checkAccessibilityViolations() {
    const violations = [];

    // Check for images without alt text
    const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');
    if (imagesWithoutAlt.length > 0) {
      violations.push(`${imagesWithoutAlt.length} images without alt text`);
    }

    // Check for buttons without accessible names
    const buttonsWithoutNames = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
    buttonsWithoutNames.forEach(button => {
      if (!button.textContent.trim()) {
        violations.push('Button without accessible name');
      }
    });

    // Check for form inputs without labels
    const inputsWithoutLabels = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
    inputsWithoutLabels.forEach(input => {
      const { id } = input;
      if (!id || !document.querySelector(`label[for="${id}"]`)) {
        violations.push('Form input without label');
      }
    });

    if (violations.length > 0) {
      this.emit('accessibility:violations-detected', { violations });
    }
  }

  /**
   * Get accessibility report
   */
  getAccessibilityReport() {
    return {
      screenReaderMode: this.screenReaderMode,
      highContrastMode: this.highContrastMode,
      reducedMotionMode: this.reducedMotionMode,
      keyboardNavigation: this.keyboardNavigation,
      announcements: this.announcements.slice(-10),
      shortcuts: Array.from(this.keyboardShortcuts.keys()),
      landmarks: Array.from(this.landmarkElements.keys())
    };
  }

  /**
   * Cleanup focus indicators
   */
  cleanupFocusIndicators() {
    // Remove any temporary focus indicators
    document.querySelectorAll('.temp-focus-indicator').forEach(el => {
      el.remove();
    });
  }

  async destroy() {
    // Remove event listeners
    document.removeEventListener('keydown', this.handleKeyboardNavigation);
    document.removeEventListener('focusin', this.handleFocusIn);
    document.removeEventListener('focusout', this.handleFocusOut);

    // Remove live regions
    if (this.liveRegion) {
      this.liveRegion.remove();
    }
    if (this.assertiveRegion) {
      this.assertiveRegion.remove();
    }

    await super.destroy();
  }
}
