/**
 * WebSocket Manager Component
 *
 * Manages WebSocket connections with automatic reconnection and authentication.
 */

import { Component } from '../core/component.js';
import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

export class WebSocketManager extends Component {
  constructor(name, options = {}) {
    super(name, options);

    this.websocket = null;
    this.isConnectedFlag = false;
    this.isAuthenticatedFlag = false;
    this.messageHandlers = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = this.options.maxReconnectAttempts || 5;
    this.reconnectDelay = this.options.reconnectDelay || 1000;
    this.currentUrl = null;
    this.currentAuthToken = null;
    this.heartbeatInterval = null;
    this.heartbeatTimeout = this.options.heartbeatTimeout || 30000;
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      maxReconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatTimeout: 30000,
      autoReconnect: true
    };
  }

  async onInit() {
    // Set up event listeners
    this.setupEventListeners();

    // Initialize state
    this.updateConnectionState();

    this.log('info', 'WebSocket manager initialized');
  }

  setupEventListeners() {
    // Listen for authentication events
    eventBus.on('auth:tokenChanged', data => {
      this.currentAuthToken = data.token;
      if (this.isConnected() && data.token) {
        this.authenticate(data.token);
      }
    });

    // Listen for logout events
    eventBus.on('auth:logout', () => {
      this.currentAuthToken = null;
      this.isAuthenticatedFlag = false;
      this.updateConnectionState();
    });
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected() {
    return this.isConnectedFlag && this.websocket && this.websocket.readyState === WebSocket.OPEN;
  }

  /**
   * Check if WebSocket is authenticated
   */
  isAuthenticated() {
    return this.isAuthenticatedFlag;
  }

  /**
   * Add a message handler
   */
  onMessage(handler) {
    this.messageHandlers.push(handler);
    return () => {
      const index = this.messageHandlers.indexOf(handler);
      if (index > -1) {
        this.messageHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(url, authToken = null) {
    if (this.websocket && this.websocket.readyState === WebSocket.CONNECTING) {
      this.log('warn', 'WebSocket connection already in progress');
      return;
    }

    this.currentUrl = url;
    this.currentAuthToken = authToken;

    // Close existing connection
    if (this.websocket) {
      this.websocket.close();
    }

    this.log('info', `Connecting to WebSocket: ${url}`);
    this.websocket = new WebSocket(url);

    this.websocket.onopen = () => {
      this.log('info', 'WebSocket connected');
      this.isConnectedFlag = true;
      this.reconnectAttempts = 0;
      this.updateConnectionState();

      // Send authentication if token provided
      if (authToken) {
        this.authenticate(authToken);
      }

      // Start heartbeat
      this.startHeartbeat();

      // Emit connection event
      this.emit('connected');
      eventBus.emit('websocket:connected');
    };

    this.websocket.onmessage = event => {
      this.handleMessage(event);
    };

    this.websocket.onclose = event => {
      this.log('info', `WebSocket disconnected: ${event.code} ${event.reason}`);
      this.handleDisconnection();
    };

    this.websocket.onerror = error => {
      this.log('error', 'WebSocket error:', error);
      this.emit('error', error);
      eventBus.emit('websocket:error', error);
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);

      // Handle authentication response
      if (message.type === 'auth_success') {
        this.isAuthenticatedFlag = true;
        this.log('info', 'WebSocket authentication successful');
        this.emit('authenticated');
        eventBus.emit('websocket:authenticated');
      } else if (message.type === 'auth_failed') {
        this.isAuthenticatedFlag = false;
        this.log('warn', 'WebSocket authentication failed');
        this.emit('authenticationFailed');
        eventBus.emit('websocket:authenticationFailed');
      }

      // Handle heartbeat
      if (message.type === 'ping') {
        this.send({ type: 'pong' });
        return;
      }

      // Update connection state
      this.updateConnectionState();

      // Notify all handlers
      this.messageHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          this.log('error', 'Error in WebSocket message handler:', error);
        }
      });

      // Emit message event
      this.emit('message', message);
      eventBus.emit('websocket:message', message);
    } catch (error) {
      this.log('error', 'Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket disconnection
   */
  handleDisconnection() {
    this.isConnectedFlag = false;
    this.isAuthenticatedFlag = false;
    this.stopHeartbeat();
    this.updateConnectionState();

    this.emit('disconnected');
    eventBus.emit('websocket:disconnected');

    // Attempt reconnection if enabled
    if (this.options.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;

      this.log('info', `Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

      setTimeout(() => {
        if (this.currentUrl) {
          this.connect(this.currentUrl, this.currentAuthToken);
        }
      }, delay);
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.log('error', 'Max reconnection attempts reached');
      this.emit('maxReconnectAttemptsReached');
      eventBus.emit('websocket:maxReconnectAttemptsReached');
    }
  }

  /**
   * Send authentication message
   */
  authenticate(token) {
    if (this.isConnected()) {
      this.send({
        type: 'auth',
        token
      });
    }
  }

  /**
   * Send a message through WebSocket
   */
  send(message) {
    if (this.isConnected()) {
      try {
        this.websocket.send(JSON.stringify(message));
        return true;
      } catch (error) {
        this.log('error', 'Error sending WebSocket message:', error);
        return false;
      }
    } else {
      this.log('warn', 'Cannot send message: WebSocket not connected');
      return false;
    }
  }

  /**
   * Close WebSocket connection
   */
  close() {
    this.stopHeartbeat();

    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    this.isConnectedFlag = false;
    this.isAuthenticatedFlag = false;
    this.currentUrl = null;
    this.currentAuthToken = null;
    this.reconnectAttempts = 0;

    this.updateConnectionState();
    this.emit('closed');
    eventBus.emit('websocket:closed');
  }

  /**
   * Start heartbeat mechanism
   */
  startHeartbeat() {
    this.stopHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, this.heartbeatTimeout);
  }

  /**
   * Stop heartbeat mechanism
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Update connection state in global state manager
   */
  updateConnectionState() {
    stateManager.setState({
      websocket: {
        connected: this.isConnected(),
        authenticated: this.isAuthenticated(),
        reconnectAttempts: this.reconnectAttempts,
        maxReconnectAttempts: this.maxReconnectAttempts
      }
    }, 'websocket-manager');
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      connected: this.isConnected(),
      authenticated: this.isAuthenticated(),
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      url: this.currentUrl,
      readyState: this.websocket ? this.websocket.readyState : null
    };
  }

  onDestroy() {
    this.close();
    this.messageHandlers = [];
  }
}

export default WebSocketManager;
