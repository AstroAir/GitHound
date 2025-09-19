/**
 * Base Component Class
 *
 * Provides a foundation for all GitHound web components with lifecycle management,
 * event handling, and dependency injection capabilities.
 */

export class Component {
  constructor(name, options = {}) {
    this.name = name;
    this.options = { ...this.getDefaultOptions(), ...options };
    this.initialized = false;
    this.destroyed = false;
    this.dependencies = [];
    this.eventListeners = new Map();
    this.state = {};

    // Bind lifecycle methods
    this.init = this.init.bind(this);
    this.destroy = this.destroy.bind(this);
    this.render = this.render.bind(this);
  }

  /**
   * Get default options for this component
   * Override in subclasses to provide component-specific defaults
   */
  getDefaultOptions() {
    return {
      autoInit: true,
      debug: false
    };
  }

  /**
   * Initialize the component
   * Override in subclasses to provide initialization logic
   */
  async init() {
    if (this.initialized) {
      this.log('warn', 'Component already initialized');
      return;
    }

    this.log('info', 'Initializing component');

    try {
      await this.beforeInit();
      await this.onInit();
      await this.afterInit();

      this.initialized = true;
      this.emit('initialized');
      this.log('info', 'Component initialized successfully');
    } catch (error) {
      this.log('error', 'Failed to initialize component', error);
      throw error;
    }
  }

  /**
   * Lifecycle hook: before initialization
   */
  async beforeInit() {
    // Override in subclasses
  }

  /**
   * Lifecycle hook: main initialization
   */
  async onInit() {
    // Override in subclasses
  }

  /**
   * Lifecycle hook: after initialization
   */
  async afterInit() {
    // Override in subclasses
  }

  /**
   * Render the component
   * Override in subclasses to provide rendering logic
   */
  render() {
    // Override in subclasses
  }

  /**
   * Destroy the component and clean up resources
   */
  destroy() {
    if (this.destroyed) {
      this.log('warn', 'Component already destroyed');
      return;
    }

    this.log('info', 'Destroying component');

    try {
      this.beforeDestroy();
      this.onDestroy();
      this.afterDestroy();

      // Clean up event listeners
      this.eventListeners.clear();

      this.destroyed = true;
      this.initialized = false;
      this.log('info', 'Component destroyed successfully');
    } catch (error) {
      this.log('error', 'Failed to destroy component', error);
    }
  }

  /**
   * Lifecycle hook: before destruction
   */
  beforeDestroy() {
    // Override in subclasses
  }

  /**
   * Lifecycle hook: main destruction
   */
  onDestroy() {
    // Override in subclasses
  }

  /**
   * Lifecycle hook: after destruction
   */
  afterDestroy() {
    // Override in subclasses
  }

  /**
   * Add an event listener
   */
  on(event, handler) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(handler);
  }

  /**
   * Remove an event listener
   */
  off(event, handler) {
    if (!this.eventListeners.has(event)) { return; }

    const handlers = this.eventListeners.get(event);
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
  }

  /**
   * Emit an event
   */
  emit(event, data = null) {
    if (!this.eventListeners.has(event)) { return; }

    const handlers = this.eventListeners.get(event);
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        this.log('error', `Error in event handler for ${event}`, error);
      }
    });
  }

  /**
   * Set component state
   */
  setState(newState) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...newState };
    this.emit('stateChanged', { oldState, newState: this.state });
  }

  /**
   * Get component state
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Add a dependency
   */
  addDependency(dependency) {
    if (!this.dependencies.includes(dependency)) {
      this.dependencies.push(dependency);
    }
  }

  /**
   * Check if all dependencies are satisfied
   */
  areDependenciesSatisfied() {
    return this.dependencies.every(dep => {
      const component = window.GitHound?.registry?.get(dep);
      return component && component.initialized;
    });
  }

  /**
   * Log a message with component context
   */
  log(level, message, ...args) {
    if (!this.options.debug && level === 'debug') { return; }

    const prefix = `[${this.name}]`;
    console[level](prefix, message, ...args);
  }

  /**
   * Get a DOM element by selector within component scope
   */
  $(selector) {
    return document.querySelector(selector);
  }

  /**
   * Get multiple DOM elements by selector within component scope
   */
  $$(selector) {
    return document.querySelectorAll(selector);
  }
}

export default Component;
