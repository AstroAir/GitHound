/**
 * Lazy loading system for GitHound components
 * Provides dynamic import and on-demand loading capabilities
 */

export class LazyLoader {
  constructor() {
    this.loadedModules = new Map();
    this.loadingPromises = new Map();
    this.loadOrder = [];
    this.preloadQueue = [];
    this.intersectionObserver = null;
    this.loadingStrategies = new Map();

    this.initializeIntersectionObserver();
    this.setupLoadingStrategies();
  }

  /**
   * Initialize intersection observer for viewport-based loading
   */
  initializeIntersectionObserver() {
    if ('IntersectionObserver' in window) {
      this.intersectionObserver = new IntersectionObserver(
        entries => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const element = entry.target;
              const componentName = element.dataset.lazyComponent;
              if (componentName) {
                this.loadComponent(componentName);
                this.intersectionObserver.unobserve(element);
              }
            }
          });
        },
        {
          rootMargin: '50px',
          threshold: 0.1
        }
      );
    }
  }

  /**
   * Setup different loading strategies
   */
  setupLoadingStrategies() {
    this.loadingStrategies.set('immediate', () => true);
    this.loadingStrategies.set('idle', () => this.requestIdleCallback());
    this.loadingStrategies.set('interaction', element => this.onInteraction(element));
    this.loadingStrategies.set('viewport', element => this.onViewport(element));
    this.loadingStrategies.set('delay', (element, delay = 1000) => this.onDelay(delay));
  }

  /**
   * Load a component dynamically
   * @param {string} componentName - Name of the component to load
   * @param {Object} options - Loading options
   * @returns {Promise} Promise that resolves to the component class
   */
  async loadComponent(componentName, options = {}) {
    // Return cached module if already loaded
    if (this.loadedModules.has(componentName)) {
      return this.loadedModules.get(componentName);
    }

    // Return existing loading promise if already loading
    if (this.loadingPromises.has(componentName)) {
      return this.loadingPromises.get(componentName);
    }

    const loadingPromise = this.performLoad(componentName, options);
    this.loadingPromises.set(componentName, loadingPromise);

    try {
      const module = await loadingPromise;
      this.loadedModules.set(componentName, module);
      this.loadOrder.push(componentName);
      this.loadingPromises.delete(componentName);

      this.emitLoadEvent('component:loaded', { componentName, module });
      return module;
    } catch (error) {
      this.loadingPromises.delete(componentName);
      this.emitLoadEvent('component:load-error', { componentName, error });
      throw error;
    }
  }

  /**
   * Perform the actual module loading
   * @param {string} componentName - Component name
   * @param {Object} options - Loading options
   * @returns {Promise} Module loading promise
   */
  async performLoad(componentName, options = {}) {
    const { timeout = 10000, retries = 3 } = options;

    this.emitLoadEvent('component:loading', { componentName });

    const modulePath = this.getModulePath(componentName);

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const module = await this.loadWithTimeout(modulePath, timeout);
        return module;
      } catch (error) {
        if (attempt === retries) {
          throw new Error(`Failed to load component ${componentName} after ${retries} attempts: ${error.message}`);
        }

        // Wait before retry with exponential backoff
        await this.delay(Math.pow(2, attempt) * 100);
      }
    }
  }

  /**
   * Load module with timeout
   * @param {string} modulePath - Path to the module
   * @param {number} timeout - Timeout in milliseconds
   * @returns {Promise} Module loading promise
   */
  async loadWithTimeout(modulePath, timeout) {
    return Promise.race([
      import(modulePath),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Load timeout')), timeout)
      )
    ]);
  }

  /**
   * Get module path for component
   * @param {string} componentName - Component name
   * @returns {string} Module path
   */
  getModulePath(componentName) {
    const pathMap = {
      'auth-manager': './auth/auth-manager.js',
      'search-manager': './search/search-manager.js',
      'theme-manager': './ui/theme-manager.js',
      'notification-manager': './ui/notification-manager.js',
      'websocket-manager': './websocket/websocket-manager.js',
      'export-manager': './utils/export-manager.js'
    };

    const path = pathMap[componentName];
    if (!path) {
      throw new Error(`Unknown component: ${componentName}`);
    }

    return path;
  }

  /**
   * Preload components for better performance
   * @param {Array} componentNames - Components to preload
   * @param {string} strategy - Loading strategy
   */
  preloadComponents(componentNames, strategy = 'idle') {
    componentNames.forEach(componentName => {
      this.preloadQueue.push({ componentName, strategy });
    });

    this.processPreloadQueue();
  }

  /**
   * Process the preload queue
   */
  async processPreloadQueue() {
    while (this.preloadQueue.length > 0) {
      const { componentName, strategy } = this.preloadQueue.shift();

      if (this.loadedModules.has(componentName)) {
        continue;
      }

      const shouldLoad = await this.executeStrategy(strategy);
      if (shouldLoad) {
        try {
          await this.loadComponent(componentName);
        } catch (error) {
          console.warn(`Failed to preload component ${componentName}:`, error);
        }
      } else {
        // Put back in queue if strategy says not to load yet
        this.preloadQueue.push({ componentName, strategy });
        break;
      }
    }
  }

  /**
   * Execute loading strategy
   * @param {string} strategy - Strategy name
   * @param {HTMLElement} element - Target element (if applicable)
   * @returns {Promise<boolean>} Whether to load now
   */
  async executeStrategy(strategy, element = null) {
    const strategyFn = this.loadingStrategies.get(strategy);
    if (!strategyFn) {
      throw new Error(`Unknown loading strategy: ${strategy}`);
    }

    return await strategyFn(element);
  }

  /**
   * Load component when element enters viewport
   * @param {HTMLElement} element - Target element
   */
  onViewport(element) {
    if (this.intersectionObserver) {
      this.intersectionObserver.observe(element);
      return false; // Don't load immediately
    }
    return true; // Fallback to immediate loading
  }

  /**
   * Load component on user interaction
   * @param {HTMLElement} element - Target element
   */
  onInteraction(element) {
    const events = ['click', 'mouseenter', 'touchstart', 'focus'];

    const loadOnInteraction = () => {
      const componentName = element.dataset.lazyComponent;
      if (componentName) {
        this.loadComponent(componentName);
      }

      // Remove event listeners
      events.forEach(event => {
        element.removeEventListener(event, loadOnInteraction);
      });
    };

    events.forEach(event => {
      element.addEventListener(event, loadOnInteraction, { once: true });
    });

    return false; // Don't load immediately
  }

  /**
   * Load component after delay
   * @param {number} delay - Delay in milliseconds
   */
  async onDelay(delay) {
    await this.delay(delay);
    return true;
  }

  /**
   * Request idle callback wrapper
   * @returns {Promise<boolean>} Whether to load
   */
  requestIdleCallback() {
    return new Promise(resolve => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => resolve(true));
      } else {
        setTimeout(() => resolve(true), 0);
      }
    });
  }

  /**
   * Delay utility
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise} Delay promise
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Setup lazy loading for elements with data-lazy-component attribute
   */
  setupLazyElements() {
    const lazyElements = document.querySelectorAll('[data-lazy-component]');

    lazyElements.forEach(element => {
      const componentName = element.dataset.lazyComponent;
      const strategy = element.dataset.lazyStrategy || 'viewport';

      this.executeStrategy(strategy, element);
    });
  }

  /**
   * Prefetch critical components
   */
  prefetchCritical() {
    const criticalComponents = [
      'theme-manager',
      'notification-manager'
    ];

    this.preloadComponents(criticalComponents, 'immediate');
  }

  /**
   * Prefetch components likely to be needed
   */
  prefetchLikely() {
    const likelyComponents = [
      'auth-manager',
      'search-manager'
    ];

    this.preloadComponents(likelyComponents, 'idle');
  }

  /**
   * Get loading statistics
   * @returns {Object} Loading statistics
   */
  getStats() {
    return {
      loaded: this.loadedModules.size,
      loading: this.loadingPromises.size,
      queued: this.preloadQueue.length,
      loadOrder: [...this.loadOrder],
      loadedComponents: Array.from(this.loadedModules.keys())
    };
  }

  /**
   * Check if component is loaded
   * @param {string} componentName - Component name
   * @returns {boolean} Whether component is loaded
   */
  isLoaded(componentName) {
    return this.loadedModules.has(componentName);
  }

  /**
   * Check if component is loading
   * @param {string} componentName - Component name
   * @returns {boolean} Whether component is loading
   */
  isLoading(componentName) {
    return this.loadingPromises.has(componentName);
  }

  /**
   * Emit loading events
   * @param {string} eventName - Event name
   * @param {Object} data - Event data
   */
  emitLoadEvent(eventName, data) {
    if (typeof EventBus !== 'undefined') {
      EventBus.emit(eventName, data);
    }
  }

  /**
   * Clear all loaded modules (for testing)
   */
  clear() {
    this.loadedModules.clear();
    this.loadingPromises.clear();
    this.loadOrder = [];
    this.preloadQueue = [];
  }

  /**
   * Destroy the lazy loader
   */
  destroy() {
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    this.clear();
  }
}

// Create global instance
export const lazyLoader = new LazyLoader();
