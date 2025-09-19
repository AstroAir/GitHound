/**
 * DOM Utilities
 *
 * Helper functions for DOM manipulation and queries.
 */

/**
 * Query selector with optional context
 */
export function $(selector, context = document) {
  return context.querySelector(selector);
}

/**
 * Query selector all with optional context
 */
export function $$(selector, context = document) {
  return Array.from(context.querySelectorAll(selector));
}

/**
 * Get element by ID
 */
export function byId(id) {
  return document.getElementById(id);
}

/**
 * Create element with attributes and content
 */
export function createElement(tag, attributes = {}, content = '') {
  const element = document.createElement(tag);

  // Set attributes
  Object.entries(attributes).forEach(([key, value]) => {
    if (key === 'className') {
      element.className = value;
    } else if (key === 'innerHTML') {
      element.innerHTML = value;
    } else if (key === 'textContent') {
      element.textContent = value;
    } else if (key.startsWith('data-')) {
      element.setAttribute(key, value);
    } else {
      element[key] = value;
    }
  });

  // Set content
  if (content) {
    if (typeof content === 'string') {
      element.innerHTML = content;
    } else if (content instanceof Node) {
      element.appendChild(content);
    } else if (Array.isArray(content)) {
      content.forEach(child => {
        if (typeof child === 'string') {
          element.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
          element.appendChild(child);
        }
      });
    }
  }

  return element;
}

/**
 * Add class to element(s)
 */
export function addClass(elements, className) {
  const els = Array.isArray(elements) ? elements : [elements];
  els.forEach(el => {
    if (el && el.classList) {
      el.classList.add(className);
    }
  });
}

/**
 * Remove class from element(s)
 */
export function removeClass(elements, className) {
  const els = Array.isArray(elements) ? elements : [elements];
  els.forEach(el => {
    if (el && el.classList) {
      el.classList.remove(className);
    }
  });
}

/**
 * Toggle class on element(s)
 */
export function toggleClass(elements, className) {
  const els = Array.isArray(elements) ? elements : [elements];
  els.forEach(el => {
    if (el && el.classList) {
      el.classList.toggle(className);
    }
  });
}

/**
 * Check if element has class
 */
export function hasClass(element, className) {
  return element && element.classList && element.classList.contains(className);
}

/**
 * Show element(s)
 */
export function show(elements) {
  const els = Array.isArray(elements) ? elements : [elements];
  els.forEach(el => {
    if (el) {
      el.style.display = '';
    }
  });
}

/**
 * Hide element(s)
 */
export function hide(elements) {
  const els = Array.isArray(elements) ? elements : [elements];
  els.forEach(el => {
    if (el) {
      el.style.display = 'none';
    }
  });
}

/**
 * Toggle visibility of element(s)
 */
export function toggle(elements) {
  const els = Array.isArray(elements) ? elements : [elements];
  els.forEach(el => {
    if (el) {
      el.style.display = el.style.display === 'none' ? '' : 'none';
    }
  });
}

/**
 * Set text content safely
 */
export function setText(element, text) {
  if (element) {
    element.textContent = text;
  }
}

/**
 * Set HTML content safely
 */
export function setHTML(element, html) {
  if (element) {
    element.innerHTML = html;
  }
}

/**
 * Get form data as object
 */
export function getFormData(form) {
  const formData = new FormData(form);
  const data = {};

  for (const [key, value] of formData.entries()) {
    if (data[key]) {
      // Handle multiple values (checkboxes, etc.)
      if (Array.isArray(data[key])) {
        data[key].push(value);
      } else {
        data[key] = [data[key], value];
      }
    } else {
      data[key] = value;
    }
  }

  return data;
}

/**
 * Set form data from object
 */
export function setFormData(form, data) {
  Object.entries(data).forEach(([key, value]) => {
    const element = form.elements[key];
    if (element) {
      if (element.type === 'checkbox' || element.type === 'radio') {
        element.checked = Boolean(value);
      } else {
        element.value = value;
      }
    }
  });
}

/**
 * Clear form
 */
export function clearForm(form) {
  if (form && form.reset) {
    form.reset();
  }
}

/**
 * Add event listener with automatic cleanup
 */
export function addEventListener(element, event, handler, options = {}) {
  if (!element || !element.addEventListener) { return null; }

  element.addEventListener(event, handler, options);

  // Return cleanup function
  return () => {
    element.removeEventListener(event, handler, options);
  };
}

/**
 * Delegate event handling
 */
export function delegate(container, selector, event, handler) {
  const delegateHandler = e => {
    const target = e.target.closest(selector);
    if (target && container.contains(target)) {
      handler.call(target, e);
    }
  };

  return addEventListener(container, event, delegateHandler);
}

/**
 * Wait for DOM ready
 */
export function ready(callback) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', callback);
  } else {
    callback();
  }
}

/**
 * Wait for element to exist
 */
export function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const element = $(selector);
    if (element) {
      resolve(element);
      return;
    }

    const observer = new MutationObserver(() => {
      const element = $(selector);
      if (element) {
        observer.disconnect();
        resolve(element);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}

/**
 * Get element position relative to viewport
 */
export function getElementPosition(element) {
  const rect = element.getBoundingClientRect();
  return {
    top: rect.top,
    left: rect.left,
    bottom: rect.bottom,
    right: rect.right,
    width: rect.width,
    height: rect.height
  };
}

/**
 * Check if element is in viewport
 */
export function isInViewport(element, threshold = 0) {
  const rect = element.getBoundingClientRect();
  const windowHeight = window.innerHeight || document.documentElement.clientHeight;
  const windowWidth = window.innerWidth || document.documentElement.clientWidth;

  return (
    rect.top >= -threshold
    && rect.left >= -threshold
    && rect.bottom <= windowHeight + threshold
    && rect.right <= windowWidth + threshold
  );
}

/**
 * Scroll element into view smoothly
 */
export function scrollIntoView(element, options = {}) {
  if (element && element.scrollIntoView) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'nearest',
      ...options
    });
  }
}

/**
 * Escape HTML to prevent XSS
 */
export function escapeHTML(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Parse HTML string safely
 */
export function parseHTML(htmlString) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, 'text/html');
  return doc.body.firstChild;
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      console.warn('Clipboard API failed, falling back to execCommand');
    }
  }

  // Fallback for older browsers
  const textArea = createElement('textarea', {
    value: text,
    style: 'position: fixed; top: -9999px; left: -9999px;'
  });

  document.body.appendChild(textArea);
  textArea.select();

  try {
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    return successful;
  } catch (error) {
    document.body.removeChild(textArea);
    return false;
  }
}

/**
 * Debounce function calls
 */
export function debounce(func, wait, immediate = false) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      timeout = null;
      if (!immediate) { func.apply(this, args); }
    };
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) { func.apply(this, args); }
  };
}

/**
 * Throttle function calls
 */
export function throttle(func, limit) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

export default {
  $,
  $$,
  byId,
  createElement,
  addClass,
  removeClass,
  toggleClass,
  hasClass,
  show,
  hide,
  toggle,
  setText,
  setHTML,
  getFormData,
  setFormData,
  clearForm,
  addEventListener,
  delegate,
  ready,
  waitForElement,
  getElementPosition,
  isInViewport,
  scrollIntoView,
  escapeHTML,
  parseHTML,
  copyToClipboard,
  debounce,
  throttle
};
