/**
 * Notification Manager Component
 *
 * Manages application notifications and alerts.
 */

import { Component } from '../core/component.js';
import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

export class NotificationManager extends Component {
  constructor(name, options = {}) {
    super(name, options);

    this.notifications = new Map();
    this.notificationCounter = 0;
    this.container = null;
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      position: 'top-right',
      maxNotifications: 5,
      defaultDuration: 5000,
      autoRemove: true,
      showProgress: true,
      enableSound: false,
      containerClass: 'notification-container'
    };
  }

  async onInit() {
    // Create notification container
    this.createContainer();

    // Set up event listeners
    this.setupEventListeners();

    // Update state
    this.updateNotificationState();

    this.log('info', 'Notification manager initialized');
  }

  setupEventListeners() {
    // Listen for notification requests
    eventBus.on('notification:show', data => {
      this.show(data);
    });

    eventBus.on('notification:success', message => {
      this.success(message);
    });

    eventBus.on('notification:error', message => {
      this.error(message);
    });

    eventBus.on('notification:warning', message => {
      this.warning(message);
    });

    eventBus.on('notification:info', message => {
      this.info(message);
    });

    // Listen for notification removal
    eventBus.on('notification:remove', id => {
      this.remove(id);
    });

    eventBus.on('notification:clear', () => {
      this.clear();
    });
  }

  /**
   * Create notification container
   */
  createContainer() {
    this.container = document.createElement('div');
    this.container.className = `${this.options.containerClass} position-fixed`;
    this.container.style.zIndex = '9999';

    // Set position
    this.setContainerPosition();

    document.body.appendChild(this.container);
  }

  /**
   * Set container position based on options
   */
  setContainerPosition() {
    const positions = {
      'top-right': { top: '20px', right: '20px' },
      'top-left': { top: '20px', left: '20px' },
      'bottom-right': { bottom: '20px', right: '20px' },
      'bottom-left': { bottom: '20px', left: '20px' },
      'top-center': { top: '20px', left: '50%', transform: 'translateX(-50%)' },
      'bottom-center': { bottom: '20px', left: '50%', transform: 'translateX(-50%)' }
    };

    const position = positions[this.options.position] || positions['top-right'];
    Object.assign(this.container.style, position);
  }

  /**
   * Show a notification
   */
  show(options) {
    if (typeof options === 'string') {
      options = { message: options };
    }

    const notification = {
      id: ++this.notificationCounter,
      type: options.type || 'info',
      title: options.title || '',
      message: options.message || '',
      duration: options.duration !== undefined ? options.duration : this.options.defaultDuration,
      persistent: options.persistent || false,
      actions: options.actions || [],
      timestamp: new Date(),
      element: null,
      timer: null
    };

    // Create notification element
    notification.element = this.createNotificationElement(notification);

    // Add to container
    this.container.appendChild(notification.element);

    // Store notification
    this.notifications.set(notification.id, notification);

    // Remove oldest if exceeding max
    this.enforceMaxNotifications();

    // Set auto-remove timer
    if (this.options.autoRemove && notification.duration > 0 && !notification.persistent) {
      notification.timer = setTimeout(() => {
        this.remove(notification.id);
      }, notification.duration);
    }

    // Update state
    this.updateNotificationState();

    // Emit events
    this.emit('notificationShown', notification);
    eventBus.emit('notification:shown', notification);

    // Play sound if enabled
    if (this.options.enableSound) {
      this.playNotificationSound(notification.type);
    }

    return notification.id;
  }

  /**
   * Create notification DOM element
   */
  createNotificationElement(notification) {
    const element = document.createElement('div');
    element.className = `alert alert-${this.getBootstrapType(notification.type)} alert-dismissible fade show mb-2`;
    element.setAttribute('role', 'alert');
    element.style.minWidth = '300px';
    element.style.maxWidth = '400px';

    // Create content
    let content = '';

    if (notification.title) {
      content += `<strong>${this.escapeHtml(notification.title)}</strong><br>`;
    }

    content += this.escapeHtml(notification.message);

    // Add actions
    if (notification.actions.length > 0) {
      content += '<div class="mt-2">';
      notification.actions.forEach(action => {
        content += `<button type="button" class="btn btn-sm btn-outline-${this.getBootstrapType(notification.type)} me-2" 
                    onclick="window.GitHound.notificationManager.handleAction('${notification.id}', '${action.id}')">${action.label}</button>`;
      });
      content += '</div>';
    }

    element.innerHTML = `
      ${content}
      <button type="button" class="btn-close" onclick="window.GitHound.notificationManager.remove('${notification.id}')"></button>
    `;

    // Add progress bar if enabled
    if (this.options.showProgress && notification.duration > 0 && !notification.persistent) {
      const progressBar = document.createElement('div');
      progressBar.className = 'progress mt-2';
      progressBar.style.height = '2px';
      progressBar.innerHTML = `<div class="progress-bar" style="width: 100%; transition: width ${notification.duration}ms linear;"></div>`;
      element.appendChild(progressBar);

      // Animate progress bar
      setTimeout(() => {
        const bar = progressBar.querySelector('.progress-bar');
        bar.style.width = '0%';
      }, 10);
    }

    // Add animation
    element.style.animation = 'slideInRight 0.3s ease-out';

    return element;
  }

  /**
   * Convert notification type to Bootstrap alert type
   */
  getBootstrapType(type) {
    const typeMap = {
      success: 'success',
      error: 'danger',
      warning: 'warning',
      info: 'info'
    };
    return typeMap[type] || 'info';
  }

  /**
   * Handle notification action clicks
   */
  handleAction(notificationId, actionId) {
    const notification = this.notifications.get(parseInt(notificationId));
    if (notification) {
      const action = notification.actions.find(a => a.id === actionId);
      if (action && action.handler) {
        action.handler(notification);
      }

      // Remove notification after action
      this.remove(notificationId);
    }
  }

  /**
   * Remove a notification
   */
  remove(id) {
    const notification = this.notifications.get(id);
    if (!notification) { return; }

    // Clear timer
    if (notification.timer) {
      clearTimeout(notification.timer);
    }

    // Animate out
    if (notification.element) {
      notification.element.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => {
        if (notification.element && notification.element.parentNode) {
          notification.element.parentNode.removeChild(notification.element);
        }
      }, 300);
    }

    // Remove from map
    this.notifications.delete(id);

    // Update state
    this.updateNotificationState();

    // Emit events
    this.emit('notificationRemoved', id);
    eventBus.emit('notification:removed', id);
  }

  /**
   * Clear all notifications
   */
  clear() {
    const ids = Array.from(this.notifications.keys());
    ids.forEach(id => this.remove(id));

    this.emit('notificationsCleared');
    eventBus.emit('notification:cleared');
  }

  /**
   * Enforce maximum number of notifications
   */
  enforceMaxNotifications() {
    if (this.notifications.size > this.options.maxNotifications) {
      const oldestId = Math.min(...this.notifications.keys());
      this.remove(oldestId);
    }
  }

  /**
   * Show success notification
   */
  success(message, options = {}) {
    return this.show({ ...options, message, type: 'success' });
  }

  /**
   * Show error notification
   */
  error(message, options = {}) {
    return this.show({ ...options, message, type: 'error', persistent: true });
  }

  /**
   * Show warning notification
   */
  warning(message, options = {}) {
    return this.show({ ...options, message, type: 'warning' });
  }

  /**
   * Show info notification
   */
  info(message, options = {}) {
    return this.show({ ...options, message, type: 'info' });
  }

  /**
   * Play notification sound
   */
  playNotificationSound(type) {
    // This can be implemented to play different sounds for different types
    if ('Audio' in window) {
      try {
        const audio = new Audio(`/static/sounds/notification-${type}.mp3`);
        audio.volume = 0.3;
        audio.play().catch(() => {
          // Ignore audio play errors
        });
      } catch (error) {
        // Ignore audio errors
      }
    }
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Update notification state in global state manager
   */
  updateNotificationState() {
    const notifications = Array.from(this.notifications.values()).map(n => ({
      id: n.id,
      type: n.type,
      title: n.title,
      message: n.message,
      timestamp: n.timestamp,
      persistent: n.persistent
    }));

    stateManager.setState({
      notifications: {
        count: this.notifications.size,
        items: notifications
      }
    }, 'notification-manager');
  }

  /**
   * Get notification status
   */
  getStatus() {
    return {
      count: this.notifications.size,
      maxNotifications: this.options.maxNotifications,
      position: this.options.position,
      notifications: Array.from(this.notifications.values())
    };
  }

  onDestroy() {
    // Clear all notifications
    this.clear();

    // Remove container
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
  }
}

// Make it available globally for onclick handlers
if (typeof window !== 'undefined') {
  window.GitHound = window.GitHound || {};
  window.GitHound.notificationManager = null; // Will be set by registry
}

export default NotificationManager;
