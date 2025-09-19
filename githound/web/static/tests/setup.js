/**
 * Jest test setup file for GitHound frontend components
 */

// Mock DOM APIs that might not be available in jsdom
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock Web APIs
global.fetch = jest.fn();
global.WebSocket = jest.fn();
global.localStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
};

global.sessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
};

// Mock console methods for cleaner test output
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
});

// Mock window.getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => '',
    setProperty: () => {},
    removeProperty: () => {}
  })
});

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 0));
global.cancelAnimationFrame = jest.fn(id => clearTimeout(id));

// Mock URL constructor
global.URL = class URL {
  constructor(url, base) {
    this.href = url;
    this.origin = base || 'http://localhost';
    this.protocol = 'http:';
    this.host = 'localhost';
    this.pathname = url.replace(/^https?:\/\/[^\/]+/, '');
    this.search = '';
    this.hash = '';
  }
};

// Mock Notification API
global.Notification = class Notification {
  constructor(title, options) {
    this.title = title;
    this.options = options;
  }

  static requestPermission() {
    return Promise.resolve('granted');
  }
};

// Mock File and FileReader APIs
global.File = class File {
  constructor(bits, name, options) {
    this.bits = bits;
    this.name = name;
    this.options = options;
    this.size = bits.length;
    this.type = options?.type || '';
  }
};

global.FileReader = class FileReader {
  constructor() {
    this.readyState = 0;
    this.result = null;
    this.error = null;
  }

  readAsText(file) {
    setTimeout(() => {
      this.readyState = 2;
      this.result = file.bits;
      if (this.onload) { this.onload(); }
    }, 0);
  }

  readAsDataURL(file) {
    setTimeout(() => {
      this.readyState = 2;
      this.result = `data:${file.type};base64,${btoa(file.bits)}`;
      if (this.onload) { this.onload(); }
    }, 0);
  }
};

// Mock Blob API
global.Blob = class Blob {
  constructor(parts, options) {
    this.parts = parts;
    this.options = options;
    this.size = parts.reduce((size, part) => size + part.length, 0);
    this.type = options?.type || '';
  }

  text() {
    return Promise.resolve(this.parts.join(''));
  }

  arrayBuffer() {
    return Promise.resolve(new ArrayBuffer(this.size));
  }
};

// Mock crypto API
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => `test-uuid-${Math.random().toString(36).substr(2, 9)}`,
    getRandomValues: arr => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }
  }
});

// Custom matchers
expect.extend({
  toBeComponent(received) {
    const pass = received
                 && typeof received.init === 'function'
                 && typeof received.destroy === 'function'
                 && typeof received.render === 'function';

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid component`,
        pass: true
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid component with init, destroy, and render methods`,
        pass: false
      };
    }
  },

  toHaveBeenCalledWithEvent(received, eventName, eventData) {
    const pass = received.mock.calls.some(call =>
      call[0] === eventName
      && (eventData ? JSON.stringify(call[1]) === JSON.stringify(eventData) : true)
    );

    if (pass) {
      return {
        message: () => `expected ${received} not to have been called with event ${eventName}`,
        pass: true
      };
    } else {
      return {
        message: () => `expected ${received} to have been called with event ${eventName}`,
        pass: false
      };
    }
  }
});

// Global test utilities
global.testUtils = {
  // Create a mock DOM element
  createElement: (tag, attributes = {}, children = []) => {
    const element = document.createElement(tag);
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key, value);
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

  // Wait for next tick
  nextTick: () => new Promise(resolve => setTimeout(resolve, 0)),

  // Wait for condition
  waitFor: (condition, timeout = 1000) => new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      if (condition()) {
        resolve();
      } else if (Date.now() - start > timeout) {
        reject(new Error('Timeout waiting for condition'));
      } else {
        setTimeout(check, 10);
      }
    };
    check();
  }),

  // Trigger event
  triggerEvent: (element, eventType, eventData = {}) => {
    const event = new Event(eventType, { bubbles: true, cancelable: true });
    Object.assign(event, eventData);
    element.dispatchEvent(event);
    return event;
  }
};

// Clean up after each test
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();

  // Reset DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Clear localStorage and sessionStorage
  localStorage.clear();
  sessionStorage.clear();

  // Reset console
  console.log.mockClear();
  console.warn.mockClear();
  console.error.mockClear();
});
