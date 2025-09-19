/**
 * Unit tests for the ThemeManager component
 */

import { ThemeManager } from '../../components/ui/theme-manager.js';
import { MockEventBus, MockStateManager } from '../mocks/component-mocks.js';

describe('ThemeManager', () => {
  let themeManager;
  let mockEventBus;
  let mockStateManager;

  beforeEach(() => {
    mockEventBus = new MockEventBus();
    mockStateManager = new MockStateManager();

    global.EventBus = mockEventBus;
    global.StateManager = mockStateManager;

    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn()
      }))
    });

    themeManager = new ThemeManager();
  });

  afterEach(async () => {
    if (themeManager && !themeManager.destroyed) {
      await themeManager.destroy();
    }
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  describe('Initialization', () => {
    test('should initialize with default theme', async () => {
      await themeManager.init();

      expect(themeManager.initialized).toBe(true);
      expect(themeManager.state.currentTheme).toBe('light');
      expect(themeManager.state.availableThemes).toContain('light');
      expect(themeManager.state.availableThemes).toContain('dark');
    });

    test('should detect system theme preference', async () => {
      window.matchMedia.mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn()
      }));

      await themeManager.init();

      expect(themeManager.state.systemTheme).toBe('dark');
    });

    test('should restore saved theme from localStorage', async () => {
      localStorage.setItem('githound_theme', 'dark');

      await themeManager.init();

      expect(themeManager.state.currentTheme).toBe('dark');
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    test('should fall back to system theme if no saved theme', async () => {
      window.matchMedia.mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn()
      }));

      await themeManager.init();

      expect(themeManager.state.currentTheme).toBe('dark');
    });
  });

  describe('Theme Switching', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should switch to valid theme', () => {
      const result = themeManager.setTheme('dark');

      expect(result).toBe(true);
      expect(themeManager.state.currentTheme).toBe('dark');
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      expect(localStorage.getItem('githound_theme')).toBe('dark');
    });

    test('should reject invalid theme', () => {
      const result = themeManager.setTheme('invalid-theme');

      expect(result).toBe(false);
      expect(themeManager.state.currentTheme).not.toBe('invalid-theme');
    });

    test('should toggle between light and dark themes', () => {
      themeManager.setTheme('light');
      themeManager.toggleTheme();
      expect(themeManager.state.currentTheme).toBe('dark');

      themeManager.toggleTheme();
      expect(themeManager.state.currentTheme).toBe('light');
    });

    test('should emit theme change events', () => {
      const changeHandler = jest.fn();
      mockEventBus.on('theme:changed', changeHandler);

      themeManager.setTheme('dark');

      expect(changeHandler).toHaveBeenCalledWith({
        theme: 'dark',
        previousTheme: 'light'
      });
    });

    test('should update global state', () => {
      themeManager.setTheme('dark');

      expect(mockStateManager.getState('ui.theme')).toBe('dark');
    });
  });

  describe('System Theme Detection', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should detect system theme changes', () => {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const changeHandler = jest.fn();

      mockEventBus.on('theme:system-changed', changeHandler);

      // Simulate system theme change
      mediaQuery.matches = true;
      if (mediaQuery.onchange) {
        mediaQuery.onchange({ matches: true });
      }

      expect(themeManager.state.systemTheme).toBe('dark');
      expect(changeHandler).toHaveBeenCalledWith({ systemTheme: 'dark' });
    });

    test('should follow system theme when auto mode is enabled', () => {
      themeManager.setAutoMode(true);

      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.matches = true;
      if (mediaQuery.onchange) {
        mediaQuery.onchange({ matches: true });
      }

      expect(themeManager.state.currentTheme).toBe('dark');
    });

    test('should not follow system theme when auto mode is disabled', () => {
      themeManager.setTheme('light');
      themeManager.setAutoMode(false);

      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.matches = true;
      if (mediaQuery.onchange) {
        mediaQuery.onchange({ matches: true });
      }

      expect(themeManager.state.currentTheme).toBe('light');
    });
  });

  describe('Custom Themes', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should register custom theme', () => {
      const customTheme = {
        name: 'custom',
        displayName: 'Custom Theme',
        variables: {
          '--primary-color': '#ff0000',
          '--bg-color': '#ffffff'
        }
      };

      const result = themeManager.registerTheme(customTheme);

      expect(result).toBe(true);
      expect(themeManager.state.availableThemes).toContain('custom');
    });

    test('should apply custom theme variables', () => {
      const customTheme = {
        name: 'custom',
        displayName: 'Custom Theme',
        variables: {
          '--primary-color': '#ff0000',
          '--bg-color': '#ffffff'
        }
      };

      themeManager.registerTheme(customTheme);
      themeManager.setTheme('custom');

      const rootStyle = document.documentElement.style;
      expect(rootStyle.getPropertyValue('--primary-color')).toBe('#ff0000');
      expect(rootStyle.getPropertyValue('--bg-color')).toBe('#ffffff');
    });

    test('should unregister custom theme', () => {
      const customTheme = {
        name: 'custom',
        displayName: 'Custom Theme',
        variables: {}
      };

      themeManager.registerTheme(customTheme);
      expect(themeManager.state.availableThemes).toContain('custom');

      themeManager.unregisterTheme('custom');
      expect(themeManager.state.availableThemes).not.toContain('custom');
    });

    test('should not unregister built-in themes', () => {
      const result = themeManager.unregisterTheme('light');

      expect(result).toBe(false);
      expect(themeManager.state.availableThemes).toContain('light');
    });
  });

  describe('Theme Utilities', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should get current theme info', () => {
      themeManager.setTheme('dark');

      const themeInfo = themeManager.getCurrentThemeInfo();

      expect(themeInfo.name).toBe('dark');
      expect(themeInfo.displayName).toBe('Dark');
      expect(themeInfo.isDark).toBe(true);
    });

    test('should check if theme is dark', () => {
      expect(themeManager.isDarkTheme('dark')).toBe(true);
      expect(themeManager.isDarkTheme('light')).toBe(false);
      expect(themeManager.isDarkTheme('high-contrast')).toBe(false);
    });

    test('should get theme contrast ratio', () => {
      const lightRatio = themeManager.getContrastRatio('light');
      const darkRatio = themeManager.getContrastRatio('dark');
      const highContrastRatio = themeManager.getContrastRatio('high-contrast');

      expect(lightRatio).toBeGreaterThan(0);
      expect(darkRatio).toBeGreaterThan(0);
      expect(highContrastRatio).toBeGreaterThan(lightRatio);
      expect(highContrastRatio).toBeGreaterThan(darkRatio);
    });

    test('should get theme color palette', () => {
      const palette = themeManager.getThemePalette('dark');

      expect(palette).toHaveProperty('primary');
      expect(palette).toHaveProperty('background');
      expect(palette).toHaveProperty('text');
      expect(palette).toHaveProperty('border');
    });
  });

  describe('Accessibility Features', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should respect reduced motion preference', () => {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn()
        }))
      });

      themeManager.detectAccessibilityPreferences();

      expect(themeManager.state.reducedMotion).toBe(true);
      expect(document.documentElement.getAttribute('data-reduced-motion')).toBe('true');
    });

    test('should respect high contrast preference', () => {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn()
        }))
      });

      themeManager.detectAccessibilityPreferences();

      expect(themeManager.state.highContrast).toBe(true);
    });

    test('should automatically switch to high contrast theme', () => {
      themeManager.setAutoContrastMode(true);

      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn()
        }))
      });

      themeManager.detectAccessibilityPreferences();

      expect(themeManager.state.currentTheme).toBe('high-contrast');
    });
  });

  describe('Theme Persistence', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should save theme preferences', () => {
      themeManager.setTheme('dark');
      themeManager.setAutoMode(true);

      themeManager.savePreferences();

      const saved = JSON.parse(localStorage.getItem('githound_theme_preferences'));
      expect(saved.theme).toBe('dark');
      expect(saved.autoMode).toBe(true);
    });

    test('should load theme preferences', () => {
      const preferences = {
        theme: 'dark',
        autoMode: true,
        autoContrastMode: false
      };

      localStorage.setItem('githound_theme_preferences', JSON.stringify(preferences));

      themeManager.loadPreferences();

      expect(themeManager.state.currentTheme).toBe('dark');
      expect(themeManager.state.autoMode).toBe(true);
      expect(themeManager.state.autoContrastMode).toBe(false);
    });

    test('should export theme settings', () => {
      themeManager.setTheme('dark');
      themeManager.setAutoMode(true);

      const exported = themeManager.exportSettings();

      expect(exported.theme).toBe('dark');
      expect(exported.autoMode).toBe(true);
      expect(exported.version).toBeDefined();
    });

    test('should import theme settings', () => {
      const settings = {
        theme: 'dark',
        autoMode: true,
        autoContrastMode: false,
        version: '1.0'
      };

      const result = themeManager.importSettings(settings);

      expect(result).toBe(true);
      expect(themeManager.state.currentTheme).toBe('dark');
      expect(themeManager.state.autoMode).toBe(true);
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      await themeManager.init();
    });

    test('should handle invalid theme gracefully', () => {
      const errorHandler = jest.fn();
      mockEventBus.on('theme:error', errorHandler);

      themeManager.setTheme('invalid-theme');

      expect(errorHandler).toHaveBeenCalledWith({
        error: 'Invalid theme: invalid-theme'
      });
    });

    test('should handle localStorage errors', () => {
      // Mock localStorage to throw error
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = jest.fn(() => {
        throw new Error('Storage quota exceeded');
      });

      const errorHandler = jest.fn();
      mockEventBus.on('theme:error', errorHandler);

      themeManager.setTheme('dark');

      expect(errorHandler).toHaveBeenCalled();

      // Restore localStorage
      localStorage.setItem = originalSetItem;
    });

    test('should handle CSS variable application errors', () => {
      const customTheme = {
        name: 'broken',
        displayName: 'Broken Theme',
        variables: {
          '--invalid-property': 'invalid-value'
        }
      };

      themeManager.registerTheme(customTheme);

      // Should not throw error
      expect(() => themeManager.setTheme('broken')).not.toThrow();
    });
  });
});
