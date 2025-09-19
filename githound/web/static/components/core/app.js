/**
 * Main Application Component
 *
 * Orchestrates all other components and manages the overall application lifecycle.
 */

import { Component } from './component.js';
import registry from './registry.js';
import eventBus from './event-bus.js';
import stateManager from './state-manager.js';

// Import all components
import WebSocketManager from '../websocket/websocket-manager.js';
import SearchManager from '../search/search-manager.js';
import AuthManager from '../auth/auth-manager.js';
import ThemeManager from '../ui/theme-manager.js';
import NotificationManager from '../ui/notification-manager.js';
import ExportManager from '../utils/export-manager.js';

export class GitHoundApp extends Component {
  constructor(name = 'app', options = {}) {
    super(name, options);

    this.version = '2.0.0';
    this.initialized = false;
    this.components = {};
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      enableKeyboardShortcuts: true,
      enableAutoSave: true,
      autoSaveInterval: 30000, // 30 seconds
      enableAnalytics: false
    };
  }

  async onInit() {
    this.log('info', `Initializing GitHound App v${this.version}`);

    // Register all components
    this.registerComponents();

    // Initialize all components
    await this.initializeComponents();

    // Set up global event listeners
    this.setupGlobalEventListeners();

    // Set up keyboard shortcuts
    if (this.options.enableKeyboardShortcuts) {
      this.setupKeyboardShortcuts();
    }

    // Set up auto-save
    if (this.options.enableAutoSave) {
      this.setupAutoSave();
    }

    // Initialize UI
    this.initializeUI();

    // Set up error handling
    this.setupErrorHandling();

    // Register Service Worker
    await this.registerServiceWorker();

    // Mark as initialized
    this.initialized = true;

    // Emit app ready event
    this.emit('appReady');
    eventBus.emit('app:ready');

    this.log('info', 'GitHound App initialized successfully');
  }

  /**
   * Register all components with the registry
   */
  registerComponents() {
    // Core components
    registry.register('websocket', WebSocketManager, {
      dependencies: []
    });

    registry.register('auth', AuthManager, {
      dependencies: []
    });

    registry.register('theme', ThemeManager, {
      dependencies: []
    });

    registry.register('notifications', NotificationManager, {
      dependencies: ['theme']
    });

    registry.register('search', SearchManager, {
      dependencies: ['websocket', 'auth']
    });

    registry.register('export', ExportManager, {
      dependencies: ['search', 'notifications']
    });

    this.log('info', 'All components registered');
  }

  /**
   * Initialize all components
   */
  async initializeComponents() {
    try {
      await registry.initializeAll();

      // Store component references for easy access
      this.components = {
        websocket: registry.get('websocket'),
        auth: registry.get('auth'),
        theme: registry.get('theme'),
        notifications: registry.get('notifications'),
        search: registry.get('search'),
        export: registry.get('export')
      };

      // Make components globally available for debugging
      if (typeof window !== 'undefined') {
        window.GitHound = window.GitHound || {};
        window.GitHound.app = this;
        window.GitHound.components = this.components;
        window.GitHound.notificationManager = this.components.notifications;
      }
    } catch (error) {
      this.log('error', 'Failed to initialize components:', error);
      throw error;
    }
  }

  /**
   * Set up global event listeners
   */
  setupGlobalEventListeners() {
    // Listen for component errors
    eventBus.on('component:error', error => {
      this.handleComponentError(error);
    });

    // Listen for state changes
    stateManager.subscribe(null, state => {
      this.handleStateChange(state);
    });

    // Listen for window events
    window.addEventListener('beforeunload', () => {
      this.handleBeforeUnload();
    });

    window.addEventListener('online', () => {
      eventBus.emit('app:online');
    });

    window.addEventListener('offline', () => {
      eventBus.emit('app:offline');
    });
  }

  /**
   * Set up keyboard shortcuts
   */
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', e => {
      // Ctrl/Cmd + Enter: Start search
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        eventBus.emit('search:start');
      }

      // Escape: Cancel search or close modals
      if (e.key === 'Escape') {
        eventBus.emit('search:cancel');
        eventBus.emit('modal:close');
      }

      // Ctrl/Cmd + K: Focus search input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('[data-testid="content-pattern"]');
        if (searchInput) {
          searchInput.focus();
        }
      }

      // Ctrl/Cmd + /: Show help
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        eventBus.emit('help:show');
      }
    });
  }

  /**
   * Set up auto-save functionality
   */
  setupAutoSave() {
    setInterval(() => {
      this.autoSave();
    }, this.options.autoSaveInterval);

    // Save on form changes
    eventBus.on('form:changed', () => {
      this.debouncedAutoSave();
    });
  }

  /**
   * Auto-save form data
   */
  autoSave() {
    try {
      const searchForm = document.getElementById('searchForm');
      if (searchForm) {
        const formData = new FormData(searchForm);
        const formState = {};

        for (const [key, value] of formData.entries()) {
          formState[key] = value;
        }

        localStorage.setItem('githound-form-state', JSON.stringify(formState));
        this.log('debug', 'Form state auto-saved');
      }
    } catch (error) {
      this.log('warn', 'Auto-save failed:', error);
    }
  }

  /**
   * Debounced auto-save
   */
  debouncedAutoSave = this.debounce(this.autoSave.bind(this), 1000);

  /**
   * Initialize UI elements
   */
  initializeUI() {
    // Load saved form state
    this.loadFormState();

    // Set up form change listeners
    this.setupFormListeners();

    // Initialize highlight.js if available
    if (typeof hljs !== 'undefined') {
      hljs.configure({
        languages: ['javascript', 'python', 'java', 'cpp', 'html', 'css', 'json', 'xml', 'markdown', 'yaml', 'bash', 'sql']
      });
    }

    // Add initial animations
    setTimeout(() => {
      document.querySelectorAll('.fade-in-up').forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
        el.classList.add('animate');
      });
    }, 100);
  }

  /**
   * Load saved form state
   */
  loadFormState() {
    try {
      const savedState = localStorage.getItem('githound-form-state');
      if (savedState) {
        const formState = JSON.parse(savedState);
        Object.keys(formState).forEach(key => {
          const element = document.getElementById(key);
          if (element) {
            if (element.type === 'checkbox') {
              element.checked = formState[key] === 'on';
            } else {
              element.value = formState[key];
            }
          }
        });
      }
    } catch (error) {
      this.log('warn', 'Failed to load form state:', error);
    }
  }

  /**
   * Set up form change listeners
   */
  setupFormListeners() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
      searchForm.addEventListener('input', () => {
        eventBus.emit('form:changed');
      });

      searchForm.addEventListener('submit', e => {
        e.preventDefault();
        this.handleSearchSubmit();
      });
    }
  }

  /**
   * Handle search form submission
   */
  handleSearchSubmit() {
    const searchForm = document.getElementById('searchForm');
    if (!searchForm) { return; }

    const formData = new FormData(searchForm);
    const searchRequest = {};

    for (const [key, value] of formData.entries()) {
      if (value.trim()) {
        searchRequest[key] = value;
      }
    }

    // Validate required fields
    if (!searchRequest.repo_path) {
      eventBus.emit('notification:error', 'Repository path is required');
      return;
    }

    // Check if at least one search criterion is provided
    const criteria = ['content_pattern', 'commit_hash', 'author_pattern', 'message_pattern', 'file_path_pattern'];
    const hasCriteria = criteria.some(field => searchRequest[field]);

    if (!hasCriteria) {
      eventBus.emit('notification:error', 'At least one search criterion is required');
      return;
    }

    // Emit search start event
    eventBus.emit('search:start', searchRequest);
  }

  /**
   * Set up error handling
   */
  setupErrorHandling() {
    // Global error handler
    window.addEventListener('error', event => {
      this.handleGlobalError(event.error);
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', event => {
      this.handleGlobalError(event.reason);
    });
  }

  /**
   * Handle component errors
   */
  handleComponentError(error) {
    this.log('error', 'Component error:', error);
    eventBus.emit('notification:error', `Component error: ${error.message}`);
  }

  /**
   * Handle global errors
   */
  handleGlobalError(error) {
    this.log('error', 'Global error:', error);

    // Don't show notifications for network errors or common issues
    if (error.name === 'NetworkError' || error.message.includes('fetch')) {
      return;
    }

    eventBus.emit('notification:error', `Unexpected error: ${error.message}`);
  }

  /**
   * Handle state changes
   */
  handleStateChange(state) {
    // Update UI based on state changes
    this.updateConnectionStatus(state);
    this.updateSearchStatus(state);
    this.updateAuthStatus(state);
  }

  /**
   * Update connection status UI
   */
  updateConnectionStatus(state) {
    const websocketState = state.websocket;
    if (!websocketState) { return; }

    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
      if (websocketState.connected) {
        statusElement.textContent = 'Connected';
        statusElement.className = 'badge bg-success';
      } else {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'badge bg-danger';
      }
    }
  }

  /**
   * Update search status UI
   */
  updateSearchStatus(state) {
    const searchState = state.search;
    if (!searchState) { return; }

    const statusElement = document.getElementById('searchStatus');
    if (statusElement) {
      if (searchState.isSearching) {
        statusElement.textContent = 'Searching...';
        statusElement.className = 'badge bg-primary';
      } else {
        statusElement.textContent = 'Ready';
        statusElement.className = 'badge bg-secondary';
      }
    }
  }

  /**
   * Update authentication status UI
   */
  updateAuthStatus(state) {
    const authState = state.auth;
    if (!authState) {}

    // This will be handled by the auth component's UI updates
  }

  /**
   * Handle before unload
   */
  handleBeforeUnload() {
    // Save current state
    this.autoSave();

    // Clean up components
    if (this.initialized) {
      registry.destroyAll();
    }
  }

  /**
   * Debounce utility
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Get application status
   */
  getStatus() {
    return {
      version: this.version,
      initialized: this.initialized,
      components: Object.keys(this.components),
      registryStatus: registry.getStatus()
    };
  }

  /**
   * Register Service Worker for caching and offline support
   */
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.log('info', 'Registering Service Worker...');

        const registration = await navigator.serviceWorker.register('/service-worker.js', {
          scope: '/'
        });

        this.log('info', 'Service Worker registered successfully', registration);

        // Listen for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New content is available
                this.emit('serviceWorker:updateAvailable');
                eventBus.emit('notification:info',
                  'New version available. Refresh to update.');
              }
            });
          }
        });

        // Handle controller change
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          this.emit('serviceWorker:controllerChanged');
          eventBus.emit('notification:success', 'App updated successfully!');
        });
      } catch (error) {
        this.log('warn', 'Service Worker registration failed:', error);
        // Don't throw error - app should work without SW
      }
    } else {
      this.log('info', 'Service Worker not supported in this browser');
    }
  }

  onDestroy() {
    // Clean up global event listeners
    window.removeEventListener('beforeunload', this.handleBeforeUnload);

    // Destroy all components
    registry.destroyAll();

    this.initialized = false;
  }
}

export default GitHoundApp;
