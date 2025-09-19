/**
 * Mock objects and utilities for component testing
 */

// Mock Component base class
export class MockComponent {
  constructor(name, dependencies = []) {
    this.name = name;
    this.dependencies = dependencies;
    this.initialized = false;
    this.destroyed = false;
    this.state = {};
    this.eventListeners = new Map();
    this.element = null;
  }

  async init() {
    this.initialized = true;
    return this;
  }

  async destroy() {
    this.destroyed = true;
    this.eventListeners.clear();
    if (this.element && this.element.parentNode) {
      this.element.parentNode.removeChild(this.element);
    }
  }

  render() {
    this.element = document.createElement('div');
    this.element.className = `component-${this.name}`;
    return this.element;
  }

  on(event, handler) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(handler);
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(handler => handler(data));
    }
  }

  setState(newState) {
    this.state = { ...this.state, ...newState };
  }

  getState() {
    return { ...this.state };
  }
}

// Mock Registry
export class MockRegistry {
  constructor() {
    this.components = new Map();
    this.instances = new Map();
    this.initOrder = [];
  }

  register(name, componentClass, dependencies = []) {
    this.components.set(name, { componentClass, dependencies });
  }

  async initializeAll() {
    const sorted = this.topologicalSort();
    for (const name of sorted) {
      const { componentClass, dependencies } = this.components.get(name);
      const instance = new componentClass(name, dependencies);
      await instance.init();
      this.instances.set(name, instance);
      this.initOrder.push(name);
    }
  }

  get(name) {
    return this.instances.get(name);
  }

  topologicalSort() {
    // Simple topological sort for testing
    return Array.from(this.components.keys());
  }

  async destroyAll() {
    for (const instance of this.instances.values()) {
      await instance.destroy();
    }
    this.instances.clear();
    this.initOrder = [];
  }
}

// Mock EventBus
export class MockEventBus {
  constructor() {
    this.listeners = new Map();
    this.history = [];
  }

  on(event, handler, options = {}) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push({ handler, options });
  }

  once(event, handler) {
    this.on(event, handler, { once: true });
  }

  off(event, handler) {
    if (this.listeners.has(event)) {
      const handlers = this.listeners.get(event);
      const index = handlers.findIndex(h => h.handler === handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    this.history.push({ event, data, timestamp: Date.now() });

    if (this.listeners.has(event)) {
      const handlers = this.listeners.get(event).slice();
      handlers.forEach(({ handler, options }) => {
        handler(data);
        if (options.once) {
          this.off(event, handler);
        }
      });
    }
  }

  clear() {
    this.listeners.clear();
    this.history = [];
  }

  getHistory() {
    return [...this.history];
  }
}

// Mock StateManager
export class MockStateManager {
  constructor() {
    this.state = {};
    this.subscribers = new Map();
    this.history = [];
  }

  getState(path) {
    if (!path) { return { ...this.state }; }

    return path.split('.').reduce((obj, key) => obj?.[key], this.state);
  }

  setState(path, value) {
    const oldState = { ...this.state };

    if (typeof path === 'object') {
      this.state = { ...this.state, ...path };
    } else {
      const keys = path.split('.');
      let current = this.state;

      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) { current[keys[i]] = {}; }
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
    }

    this.history.push({ oldState, newState: { ...this.state }, timestamp: Date.now() });
    this.notifySubscribers(path, value, oldState);
  }

  subscribe(path, callback) {
    if (!this.subscribers.has(path)) {
      this.subscribers.set(path, []);
    }
    this.subscribers.get(path).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(path);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index !== -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  notifySubscribers(path, value, oldState) {
    // Notify exact path subscribers
    if (this.subscribers.has(path)) {
      this.subscribers.get(path).forEach(callback => {
        callback(value, oldState);
      });
    }

    // Notify wildcard subscribers
    if (this.subscribers.has('*')) {
      this.subscribers.get('*').forEach(callback => {
        callback(this.state, oldState);
      });
    }
  }

  reset() {
    this.state = {};
    this.history = [];
  }

  getHistory() {
    return [...this.history];
  }
}

// Mock WebSocket
export class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;
    this.sentMessages = [];

    // Simulate connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) { this.onopen(); }
    }, 10);
  }

  send(data) {
    if (this.readyState === WebSocket.OPEN) {
      this.sentMessages.push(data);
    } else {
      throw new Error('WebSocket is not open');
    }
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) { this.onclose(); }
  }

  // Test helper methods
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  simulateError(error) {
    if (this.onerror) {
      this.onerror(error);
    }
  }

  getSentMessages() {
    return [...this.sentMessages];
  }
}

// Mock DOM utilities
export const mockDOM = {
  createElement: (tag, attributes = {}, children = []) => {
    const element = document.createElement(tag);
    Object.entries(attributes).forEach(([key, value]) => {
      if (key.startsWith('data-')) {
        element.setAttribute(key, value);
      } else {
        element[key] = value;
      }
    });
    children.forEach(child => {
      if (typeof child === 'string') {
        element.appendChild(document.createTextNode(child));
      } else {
        element.appendChild(child);
      }
    });
    return element;
  },

  createForm: (fields = {}) => {
    const form = document.createElement('form');
    Object.entries(fields).forEach(([name, value]) => {
      const input = document.createElement('input');
      input.name = name;
      input.value = value;
      form.appendChild(input);
    });
    return form;
  },

  triggerEvent: (element, eventType, eventData = {}) => {
    const event = new Event(eventType, { bubbles: true, cancelable: true });
    Object.assign(event, eventData);
    element.dispatchEvent(event);
    return event;
  }
};

// Mock API responses
export const mockAPI = {
  search: {
    success: {
      status: 'success',
      data: {
        results: [
          { id: 1, file: 'test.js', line: 10, content: 'test content' },
          { id: 2, file: 'app.js', line: 25, content: 'another match' }
        ],
        total: 2,
        query: 'test'
      }
    },
    error: {
      status: 'error',
      message: 'Search failed',
      code: 'SEARCH_ERROR'
    }
  },

  auth: {
    login: {
      success: {
        status: 'success',
        data: {
          token: 'mock-jwt-token',
          user: { id: 1, username: 'testuser', role: 'user' }
        }
      },
      error: {
        status: 'error',
        message: 'Invalid credentials',
        code: 'AUTH_ERROR'
      }
    }
  }
};

// Test data generators
export const testData = {
  generateSearchResult: (id = 1) => ({
    id,
    file: `test-file-${id}.js`,
    line: Math.floor(Math.random() * 100) + 1,
    content: `Test content for result ${id}`,
    matches: [`match-${id}`]
  }),

  generateUser: (id = 1) => ({
    id,
    username: `user${id}`,
    email: `user${id}@test.com`,
    role: 'user',
    created: new Date().toISOString()
  }),

  generateWebSocketMessage: (type = 'search_progress') => ({
    type,
    data: {
      progress: Math.floor(Math.random() * 100),
      message: `Test message for ${type}`
    },
    timestamp: Date.now()
  })
};
