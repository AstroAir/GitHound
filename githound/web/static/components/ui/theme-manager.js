/**
 * Theme Manager Component
 *
 * Manages application themes and visual preferences.
 */

import { Component } from '../core/component.js';
import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

export class ThemeManager extends Component {
  constructor(name, options = {}) {
    super(name, options);

    this.currentTheme = 'light';
    this.availableThemes = ['light', 'dark'];
    this.systemPreference = null;
    this.mediaQuery = null;
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      storageKey: 'githound-theme',
      autoDetectSystem: true,
      defaultTheme: 'light',
      persistPreference: true
    };
  }

  async onInit() {
    // Set up system preference detection
    if (this.options.autoDetectSystem) {
      this.setupSystemPreferenceDetection();
    }

    // Load saved theme or use default
    this.loadTheme();

    // Set up event listeners
    this.setupEventListeners();

    // Apply initial theme
    this.applyTheme(this.currentTheme);

    this.log('info', `Theme manager initialized with theme: ${this.currentTheme}`);
  }

  setupEventListeners() {
    // Listen for theme toggle requests
    eventBus.on('theme:toggle', () => {
      this.toggleTheme();
    });

    // Listen for specific theme set requests
    eventBus.on('theme:set', theme => {
      this.setTheme(theme);
    });

    // Listen for theme reset requests
    eventBus.on('theme:reset', () => {
      this.resetTheme();
    });

    // Set up DOM event listeners
    this.setupDOMEventListeners();
  }

  setupDOMEventListeners() {
    // Theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        this.toggleTheme();
      });
    }

    // Theme selector dropdown (if exists)
    const themeSelector = document.getElementById('themeSelector');
    if (themeSelector) {
      themeSelector.addEventListener('change', e => {
        this.setTheme(e.target.value);
      });
    }
  }

  /**
   * Set up system preference detection
   */
  setupSystemPreferenceDetection() {
    if (window.matchMedia) {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      this.systemPreference = this.mediaQuery.matches ? 'dark' : 'light';

      // Listen for system preference changes
      this.mediaQuery.addEventListener('change', e => {
        this.systemPreference = e.matches ? 'dark' : 'light';
        this.emit('systemPreferenceChanged', this.systemPreference);
        eventBus.emit('theme:systemPreferenceChanged', this.systemPreference);

        // Auto-apply if no user preference is saved
        if (!this.hasUserPreference()) {
          this.setTheme(this.systemPreference);
        }
      });
    }
  }

  /**
   * Load theme from storage or use default
   */
  loadTheme() {
    let theme = this.options.defaultTheme;

    if (this.options.persistPreference) {
      const savedTheme = localStorage.getItem(this.options.storageKey);
      if (savedTheme && this.availableThemes.includes(savedTheme)) {
        theme = savedTheme;
      } else if (this.options.autoDetectSystem && this.systemPreference) {
        theme = this.systemPreference;
      }
    }

    this.currentTheme = theme;
  }

  /**
   * Check if user has a saved theme preference
   */
  hasUserPreference() {
    return localStorage.getItem(this.options.storageKey) !== null;
  }

  /**
   * Toggle between available themes
   */
  toggleTheme() {
    const currentIndex = this.availableThemes.indexOf(this.currentTheme);
    const nextIndex = (currentIndex + 1) % this.availableThemes.length;
    const nextTheme = this.availableThemes[nextIndex];

    this.setTheme(nextTheme);
  }

  /**
   * Set specific theme
   */
  setTheme(theme) {
    if (!this.availableThemes.includes(theme)) {
      this.log('warn', `Invalid theme: ${theme}. Available themes: ${this.availableThemes.join(', ')}`);
      return;
    }

    const previousTheme = this.currentTheme;
    this.currentTheme = theme;

    // Apply theme
    this.applyTheme(theme);

    // Save preference
    if (this.options.persistPreference) {
      this.saveTheme(theme);
    }

    // Update state
    this.updateThemeState();

    // Emit events
    this.emit('themeChanged', { theme, previousTheme });
    eventBus.emit('theme:changed', { theme, previousTheme });

    this.log('info', `Theme changed from ${previousTheme} to ${theme}`);
  }

  /**
   * Apply theme to the document
   */
  applyTheme(theme) {
    // Set data attribute on document element
    document.documentElement.setAttribute('data-theme', theme);

    // Update theme toggle icon
    this.updateThemeIcon(theme);

    // Update theme selector
    this.updateThemeSelector(theme);

    // Apply theme-specific classes
    this.applyThemeClasses(theme);

    // Trigger custom theme application
    this.applyCustomThemeStyles(theme);
  }

  /**
   * Update theme toggle icon
   */
  updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
      // Update icon based on theme
      if (theme === 'dark') {
        themeIcon.className = 'fas fa-sun';
        themeIcon.title = 'Switch to light theme';
      } else {
        themeIcon.className = 'fas fa-moon';
        themeIcon.title = 'Switch to dark theme';
      }
    }
  }

  /**
   * Update theme selector dropdown
   */
  updateThemeSelector(theme) {
    const themeSelector = document.getElementById('themeSelector');
    if (themeSelector) {
      themeSelector.value = theme;
    }
  }

  /**
   * Apply theme-specific CSS classes
   */
  applyThemeClasses(theme) {
    const { body } = document;

    // Remove all theme classes
    this.availableThemes.forEach(t => {
      body.classList.remove(`theme-${t}`);
    });

    // Add current theme class
    body.classList.add(`theme-${theme}`);
  }

  /**
   * Apply custom theme styles
   */
  applyCustomThemeStyles(theme) {
    // This method can be extended to apply custom CSS variables
    // or other theme-specific styling

    const root = document.documentElement;

    if (theme === 'dark') {
      // Apply dark theme CSS variables
      root.style.setProperty('--bs-body-bg', '#1a1a1a');
      root.style.setProperty('--bs-body-color', '#ffffff');
      root.style.setProperty('--bs-border-color', '#404040');
    } else {
      // Apply light theme CSS variables
      root.style.setProperty('--bs-body-bg', '#ffffff');
      root.style.setProperty('--bs-body-color', '#212529');
      root.style.setProperty('--bs-border-color', '#dee2e6');
    }
  }

  /**
   * Save theme preference to storage
   */
  saveTheme(theme) {
    try {
      localStorage.setItem(this.options.storageKey, theme);
    } catch (error) {
      this.log('warn', 'Failed to save theme preference:', error);
    }
  }

  /**
   * Reset theme to default
   */
  resetTheme() {
    // Clear saved preference
    if (this.options.persistPreference) {
      localStorage.removeItem(this.options.storageKey);
    }

    // Use system preference or default
    const defaultTheme = this.systemPreference || this.options.defaultTheme;
    this.setTheme(defaultTheme);

    this.emit('themeReset', defaultTheme);
    eventBus.emit('theme:reset', defaultTheme);
  }

  /**
   * Get current theme
   */
  getCurrentTheme() {
    return this.currentTheme;
  }

  /**
   * Get available themes
   */
  getAvailableThemes() {
    return [...this.availableThemes];
  }

  /**
   * Get system preference
   */
  getSystemPreference() {
    return this.systemPreference;
  }

  /**
   * Check if theme is dark
   */
  isDarkTheme() {
    return this.currentTheme === 'dark';
  }

  /**
   * Check if theme is light
   */
  isLightTheme() {
    return this.currentTheme === 'light';
  }

  /**
   * Add custom theme
   */
  addTheme(themeName, themeConfig = {}) {
    if (!this.availableThemes.includes(themeName)) {
      this.availableThemes.push(themeName);

      this.emit('themeAdded', { themeName, themeConfig });
      eventBus.emit('theme:added', { themeName, themeConfig });

      this.log('info', `Added custom theme: ${themeName}`);
    }
  }

  /**
   * Remove custom theme
   */
  removeTheme(themeName) {
    if (themeName !== 'light' && themeName !== 'dark') {
      const index = this.availableThemes.indexOf(themeName);
      if (index > -1) {
        this.availableThemes.splice(index, 1);

        // Switch to default if current theme is being removed
        if (this.currentTheme === themeName) {
          this.setTheme(this.options.defaultTheme);
        }

        this.emit('themeRemoved', themeName);
        eventBus.emit('theme:removed', themeName);

        this.log('info', `Removed custom theme: ${themeName}`);
      }
    }
  }

  /**
   * Update theme state in global state manager
   */
  updateThemeState() {
    stateManager.setState({
      theme: {
        current: this.currentTheme,
        available: this.availableThemes,
        systemPreference: this.systemPreference,
        isDark: this.isDarkTheme(),
        isLight: this.isLightTheme()
      }
    }, 'theme-manager');
  }

  /**
   * Get theme status
   */
  getStatus() {
    return {
      current: this.currentTheme,
      available: this.availableThemes,
      systemPreference: this.systemPreference,
      hasUserPreference: this.hasUserPreference(),
      isDark: this.isDarkTheme(),
      isLight: this.isLightTheme()
    };
  }

  onDestroy() {
    // Clean up media query listener
    if (this.mediaQuery) {
      this.mediaQuery.removeEventListener('change', this.handleSystemPreferenceChange);
    }
  }
}

export default ThemeManager;
