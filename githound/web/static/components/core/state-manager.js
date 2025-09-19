/**
 * State Manager
 *
 * Global state management for the GitHound application.
 */

import eventBus from './event-bus.js';

export class StateManager {
  constructor() {
    this.state = {};
    this.subscribers = new Map();
    this.middleware = [];
    this.debug = false;
  }

  /**
   * Get the current state
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Get a specific state value
   */
  get(path) {
    return this.getNestedValue(this.state, path);
  }

  /**
   * Set state values
   */
  setState(updates, source = 'unknown') {
    const oldState = { ...this.state };
    const newState = { ...this.state, ...updates };

    // Apply middleware
    const action = { type: 'SET_STATE', payload: updates, source };
    const processedAction = this.applyMiddleware(action, oldState);

    if (processedAction) {
      this.state = { ...this.state, ...processedAction.payload };

      if (this.debug) {
        console.log('StateManager: State updated', {
          source,
          oldState,
          newState: this.state,
          updates
        });
      }

      // Notify subscribers
      this.notifySubscribers(oldState, this.state, updates);

      // Emit global event
      eventBus.emit('stateChanged', {
        oldState,
        newState: this.state,
        updates,
        source
      });
    }
  }

  /**
   * Set a nested state value
   */
  set(path, value, source = 'unknown') {
    const updates = this.setNestedValue({}, path, value);
    this.setState(updates, source);
  }

  /**
   * Subscribe to state changes
   */
  subscribe(selector, callback, options = {}) {
    const id = this.generateId();
    const subscription = {
      id,
      selector,
      callback,
      options,
      lastValue: selector ? selector(this.state) : this.state
    };

    if (!this.subscribers.has(id)) {
      this.subscribers.set(id, subscription);
    }

    if (this.debug) {
      console.log(`StateManager: Added subscription ${id}`);
    }

    // Return unsubscribe function
    return () => this.unsubscribe(id);
  }

  /**
   * Unsubscribe from state changes
   */
  unsubscribe(id) {
    if (this.subscribers.has(id)) {
      this.subscribers.delete(id);
      if (this.debug) {
        console.log(`StateManager: Removed subscription ${id}`);
      }
    }
  }

  /**
   * Add middleware
   */
  use(middleware) {
    this.middleware.push(middleware);
  }

  /**
   * Apply middleware to an action
   */
  applyMiddleware(action, state) {
    let processedAction = action;

    for (const middleware of this.middleware) {
      try {
        processedAction = middleware(processedAction, state);
        if (!processedAction) {
          // Middleware cancelled the action
          return null;
        }
      } catch (error) {
        console.error('StateManager: Middleware error:', error);
      }
    }

    return processedAction;
  }

  /**
   * Notify subscribers of state changes
   */
  notifySubscribers(oldState, newState, updates) {
    for (const [id, subscription] of this.subscribers) {
      try {
        const { selector, callback, lastValue, options } = subscription;

        let currentValue;
        if (selector) {
          currentValue = selector(newState);
        } else {
          currentValue = newState;
        }

        // Check if value changed
        const hasChanged = options.deep
          ? !this.deepEqual(lastValue, currentValue)
          : lastValue !== currentValue;

        if (hasChanged) {
          subscription.lastValue = currentValue;
          callback(currentValue, lastValue, { oldState, newState, updates });
        }
      } catch (error) {
        console.error(`StateManager: Error in subscription ${id}:`, error);
      }
    }
  }

  /**
   * Reset state to initial values
   */
  reset(initialState = {}) {
    const oldState = { ...this.state };
    this.state = { ...initialState };

    if (this.debug) {
      console.log('StateManager: State reset', { oldState, newState: this.state });
    }

    this.notifySubscribers(oldState, this.state, this.state);
    eventBus.emit('stateReset', { oldState, newState: this.state });
  }

  /**
   * Get nested value from object
   */
  getNestedValue(obj, path) {
    if (typeof path === 'string') {
      path = path.split('.');
    }

    return path.reduce((current, key) => (current && current[key] !== undefined ? current[key] : undefined), obj);
  }

  /**
   * Set nested value in object
   */
  setNestedValue(obj, path, value) {
    if (typeof path === 'string') {
      path = path.split('.');
    }

    const result = { ...obj };
    let current = result;

    for (let i = 0; i < path.length - 1; i++) {
      const key = path[i];
      if (!current[key] || typeof current[key] !== 'object') {
        current[key] = {};
      } else {
        current[key] = { ...current[key] };
      }
      current = current[key];
    }

    current[path[path.length - 1]] = value;
    return result;
  }

  /**
   * Deep equality check
   */
  deepEqual(a, b) {
    if (a === b) { return true; }
    if (a == null || b == null) { return false; }
    if (typeof a !== typeof b) { return false; }
    if (typeof a !== 'object') { return false; }

    const keysA = Object.keys(a);
    const keysB = Object.keys(b);

    if (keysA.length !== keysB.length) { return false; }

    for (const key of keysA) {
      if (!keysB.includes(key)) { return false; }
      if (!this.deepEqual(a[key], b[key])) { return false; }
    }

    return true;
  }

  /**
   * Generate unique ID
   */
  generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  /**
   * Enable or disable debug logging
   */
  setDebug(enabled) {
    this.debug = enabled;
  }

  /**
   * Get debug information
   */
  getDebugInfo() {
    return {
      state: this.state,
      subscriberCount: this.subscribers.size,
      middlewareCount: this.middleware.length,
      subscribers: Array.from(this.subscribers.keys())
    };
  }
}

// Create global state manager instance
export const stateManager = new StateManager();

// Make it available globally
if (typeof window !== 'undefined') {
  window.GitHound = window.GitHound || {};
  window.GitHound.stateManager = stateManager;
}

export default stateManager;
