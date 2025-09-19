/**
 * Event Bus
 *
 * Global event system for component communication.
 */

export class EventBus {
  constructor() {
    this.listeners = new Map();
    this.onceListeners = new Map();
    this.debug = false;
  }

  /**
   * Add an event listener
   */
  on(event, handler, context = null) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }

    const listener = { handler, context };
    this.listeners.get(event).push(listener);

    if (this.debug) {
      console.log(`EventBus: Added listener for '${event}'`);
    }

    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  /**
   * Add a one-time event listener
   */
  once(event, handler, context = null) {
    if (!this.onceListeners.has(event)) {
      this.onceListeners.set(event, []);
    }

    const listener = { handler, context };
    this.onceListeners.get(event).push(listener);

    if (this.debug) {
      console.log(`EventBus: Added one-time listener for '${event}'`);
    }

    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  /**
   * Remove an event listener
   */
  off(event, handler) {
    // Remove from regular listeners
    if (this.listeners.has(event)) {
      const listeners = this.listeners.get(event);
      const index = listeners.findIndex(l => l.handler === handler);
      if (index > -1) {
        listeners.splice(index, 1);
        if (this.debug) {
          console.log(`EventBus: Removed listener for '${event}'`);
        }
      }
    }

    // Remove from once listeners
    if (this.onceListeners.has(event)) {
      const listeners = this.onceListeners.get(event);
      const index = listeners.findIndex(l => l.handler === handler);
      if (index > -1) {
        listeners.splice(index, 1);
        if (this.debug) {
          console.log(`EventBus: Removed one-time listener for '${event}'`);
        }
      }
    }
  }

  /**
   * Emit an event
   */
  emit(event, data = null) {
    if (this.debug) {
      console.log(`EventBus: Emitting '${event}'`, data);
    }

    // Handle regular listeners
    if (this.listeners.has(event)) {
      const listeners = [...this.listeners.get(event)];
      listeners.forEach(({ handler, context }) => {
        try {
          if (context) {
            handler.call(context, data);
          } else {
            handler(data);
          }
        } catch (error) {
          console.error(`EventBus: Error in listener for '${event}':`, error);
        }
      });
    }

    // Handle once listeners
    if (this.onceListeners.has(event)) {
      const listeners = [...this.onceListeners.get(event)];
      this.onceListeners.delete(event); // Remove all once listeners

      listeners.forEach(({ handler, context }) => {
        try {
          if (context) {
            handler.call(context, data);
          } else {
            handler(data);
          }
        } catch (error) {
          console.error(`EventBus: Error in one-time listener for '${event}':`, error);
        }
      });
    }
  }

  /**
   * Remove all listeners for an event
   */
  removeAllListeners(event) {
    if (event) {
      this.listeners.delete(event);
      this.onceListeners.delete(event);
      if (this.debug) {
        console.log(`EventBus: Removed all listeners for '${event}'`);
      }
    } else {
      this.listeners.clear();
      this.onceListeners.clear();
      if (this.debug) {
        console.log('EventBus: Removed all listeners');
      }
    }
  }

  /**
   * Get listener count for an event
   */
  listenerCount(event) {
    const regularCount = this.listeners.has(event) ? this.listeners.get(event).length : 0;
    const onceCount = this.onceListeners.has(event) ? this.onceListeners.get(event).length : 0;
    return regularCount + onceCount;
  }

  /**
   * Get all event names that have listeners
   */
  eventNames() {
    const events = new Set();
    for (const event of this.listeners.keys()) {
      events.add(event);
    }
    for (const event of this.onceListeners.keys()) {
      events.add(event);
    }
    return Array.from(events);
  }

  /**
   * Enable or disable debug logging
   */
  setDebug(enabled) {
    this.debug = enabled;
  }

  /**
   * Create a namespaced event bus
   */
  namespace(prefix) {
    return {
      on: (event, handler, context) => this.on(`${prefix}:${event}`, handler, context),
      once: (event, handler, context) => this.once(`${prefix}:${event}`, handler, context),
      off: (event, handler) => this.off(`${prefix}:${event}`, handler),
      emit: (event, data) => this.emit(`${prefix}:${event}`, data)
    };
  }
}

// Create global event bus instance
export const eventBus = new EventBus();

// Make it available globally
if (typeof window !== 'undefined') {
  window.GitHound = window.GitHound || {};
  window.GitHound.eventBus = eventBus;
}

export default eventBus;
