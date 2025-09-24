/**
 * WebSocket testing utilities for GitHound web tests.
 * Provides helpers for testing real-time features and WebSocket connections.
 */

const WebSocket = require('ws');

class WebSocketTestHelper {
  constructor(baseURL = 'ws://localhost:8000') {
    this.baseURL = baseURL;
    this.connections = new Map();
    this.messageHandlers = new Map();
    this.connectionTimeout = 5000;
    this.messageTimeout = 1000;
  }

  /**
   * Create a WebSocket connection for testing
   */
  async createConnection(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const connectionId = options.id || `conn_${Date.now()}`;

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(url, options.protocols);
      const timeout = setTimeout(() => {
        reject(new Error(`WebSocket connection timeout after ${this.connectionTimeout}ms`));
      }, this.connectionTimeout);

      ws.on('open', () => {
        clearTimeout(timeout);
        this.connections.set(connectionId, ws);
        console.log(`✅ WebSocket connected: ${connectionId}`);
        resolve({ connectionId, ws });
      });

      ws.on('error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });

      ws.on('close', () => {
        this.connections.delete(connectionId);
        console.log(`🔌 WebSocket disconnected: ${connectionId}`);
      });
    });
  }

  /**
   * Send a message and wait for a response
   */
  async sendAndWaitForResponse(connectionId, message, expectedType = null) {
    const ws = this.connections.get(connectionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found: ${connectionId}`);
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Message response timeout after ${this.messageTimeout}ms`));
      }, this.messageTimeout);

      const messageHandler = (data) => {
        try {
          const response = JSON.parse(data);
          if (!expectedType || response.type === expectedType) {
            clearTimeout(timeout);
            ws.removeListener('message', messageHandler);
            resolve(response);
          }
        } catch (error) {
          clearTimeout(timeout);
          ws.removeListener('message', messageHandler);
          reject(error);
        }
      };

      ws.on('message', messageHandler);
      ws.send(JSON.stringify(message));
    });
  }

  /**
   * Listen for specific message types
   */
  async waitForMessage(connectionId, messageType, timeout = null) {
    const ws = this.connections.get(connectionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found: ${connectionId}`);
    }

    const waitTimeout = timeout || this.messageTimeout;

    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error(`Timeout waiting for message type: ${messageType}`));
      }, waitTimeout);

      const messageHandler = (data) => {
        try {
          const message = JSON.parse(data);
          if (message.type === messageType) {
            clearTimeout(timeoutId);
            ws.removeListener('message', messageHandler);
            resolve(message);
          }
        } catch (error) {
          // Ignore parsing errors, continue waiting
        }
      };

      ws.on('message', messageHandler);
    });
  }

  /**
   * Test search progress updates via WebSocket
   */
  async testSearchProgress(connectionId, searchRequest) {
    const progressMessages = [];
    const ws = this.connections.get(connectionId);

    if (!ws) {
      throw new Error(`WebSocket connection not found: ${connectionId}`);
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Search progress test timeout'));
      }, 30000); // 30 second timeout for search

      const messageHandler = (data) => {
        try {
          const message = JSON.parse(data);
          progressMessages.push(message);

          if (message.type === 'search_progress') {
            console.log(`📊 Search progress: ${message.data.progress}%`);
          } else if (message.type === 'search_complete') {
            clearTimeout(timeout);
            ws.removeListener('message', messageHandler);
            resolve({
              progressMessages,
              finalResult: message
            });
          } else if (message.type === 'search_error') {
            clearTimeout(timeout);
            ws.removeListener('message', messageHandler);
            reject(new Error(`Search error: ${message.data.error}`));
          }
        } catch (error) {
          console.warn('Failed to parse WebSocket message:', error);
        }
      };

      ws.on('message', messageHandler);

      // Start the search
      ws.send(JSON.stringify({
        type: 'start_search',
        data: searchRequest
      }));
    });
  }

  /**
   * Test WebSocket connection stability
   */
  async testConnectionStability(connectionId, duration = 10000) {
    const ws = this.connections.get(connectionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found: ${connectionId}`);
    }

    const startTime = Date.now();
    const pingInterval = 1000; // Ping every second
    let pingsReceived = 0;
    let pongsSent = 0;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        clearInterval(pingTimer);
        resolve({
          duration: Date.now() - startTime,
          pingsReceived,
          pongsSent,
          connectionStable: ws.readyState === WebSocket.OPEN
        });
      }, duration);

      const pingTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.ping();
          pongsSent++;
        }
      }, pingInterval);

      ws.on('pong', () => {
        pingsReceived++;
      });

      ws.on('close', () => {
        clearTimeout(timeout);
        clearInterval(pingTimer);
        reject(new Error('WebSocket connection closed during stability test'));
      });

      ws.on('error', (error) => {
        clearTimeout(timeout);
        clearInterval(pingTimer);
        reject(error);
      });
    });
  }

  /**
   * Close a specific connection
   */
  async closeConnection(connectionId) {
    const ws = this.connections.get(connectionId);
    if (ws) {
      ws.close();
      this.connections.delete(connectionId);
      console.log(`🔌 Closed WebSocket connection: ${connectionId}`);
    }
  }

  /**
   * Close all connections
   */
  async closeAllConnections() {
    const promises = Array.from(this.connections.keys()).map(id =>
      this.closeConnection(id)
    );
    await Promise.all(promises);
    console.log('🔌 All WebSocket connections closed');
  }

  /**
   * Get connection status
   */
  getConnectionStatus(connectionId) {
    const ws = this.connections.get(connectionId);
    if (!ws) {
      return 'not_found';
    }

    switch (ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'open';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'unknown';
    }
  }

  /**
   * Get all active connections
   */
  getActiveConnections() {
    return Array.from(this.connections.keys()).map(id => ({
      id,
      status: this.getConnectionStatus(id)
    }));
  }
}

module.exports = WebSocketTestHelper;
