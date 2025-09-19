/**
 * Authentication Manager Component
 *
 * Manages user authentication, registration, and session management.
 */

import { Component } from '../core/component.js';
import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

export class AuthManager extends Component {
  constructor(name, options = {}) {
    super(name, options);

    this.currentUser = null;
    this.authToken = null;
    this.refreshToken = null;
    this.tokenExpiryTime = null;
    this.refreshTimer = null;
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      autoRefresh: true,
      refreshThreshold: 5 * 60 * 1000, // 5 minutes before expiry
      storagePrefix: 'githound-auth'
    };
  }

  async onInit() {
    // Load existing authentication data
    this.loadAuthData();

    // Set up event listeners
    this.setupEventListeners();

    // Initialize UI state
    this.updateAuthState();

    // Set up token refresh if enabled
    if (this.options.autoRefresh && this.authToken) {
      this.setupTokenRefresh();
    }

    this.log('info', 'Authentication manager initialized');
  }

  setupEventListeners() {
    // Listen for login form submissions
    eventBus.on('auth:login', credentials => {
      this.login(credentials);
    });

    // Listen for registration form submissions
    eventBus.on('auth:register', userData => {
      this.register(userData);
    });

    // Listen for logout requests
    eventBus.on('auth:logout', () => {
      this.logout();
    });

    // Listen for password change requests
    eventBus.on('auth:changePassword', passwordData => {
      this.changePassword(passwordData);
    });

    // Listen for token refresh requests
    eventBus.on('auth:refreshToken', () => {
      this.refreshAuthToken();
    });
  }

  /**
   * Authenticate user with username and password
   */
  async login(credentials) {
    const { username, password } = credentials;

    try {
      this.emit('loginStarted');
      eventBus.emit('auth:loginStarted');

      // Validate credentials
      if (!username || !password) {
        throw new Error('Username and password are required');
      }

      // Make login request
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Store authentication data
      this.authToken = data.access_token;
      this.refreshToken = data.refresh_token;
      this.tokenExpiryTime = data.expires_at ? new Date(data.expires_at) : null;

      this.currentUser = {
        user_id: data.user_id,
        username,
        email: data.email,
        roles: data.roles || ['user'],
        permissions: data.permissions || []
      };

      // Save to storage
      this.saveAuthData();

      // Update state
      this.updateAuthState();

      // Set up token refresh
      if (this.options.autoRefresh) {
        this.setupTokenRefresh();
      }

      // Emit success events
      this.emit('loginSuccess', this.currentUser);
      eventBus.emit('auth:loginSuccess', this.currentUser);
      eventBus.emit('auth:tokenChanged', { token: this.authToken });

      this.log('info', `User ${username} logged in successfully`);
    } catch (error) {
      this.log('error', 'Login failed:', error);
      this.emit('loginFailed', error);
      eventBus.emit('auth:loginFailed', error);
      throw error;
    }
  }

  /**
   * Register a new user
   */
  async register(userData) {
    const { username, email, password, confirmPassword } = userData;

    try {
      this.emit('registrationStarted');
      eventBus.emit('auth:registrationStarted');

      // Validate user data
      this.validateRegistrationData(userData);

      // Make registration request
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      // Emit success events
      this.emit('registrationSuccess', data);
      eventBus.emit('auth:registrationSuccess', data);

      this.log('info', `User ${username} registered successfully`);
    } catch (error) {
      this.log('error', 'Registration failed:', error);
      this.emit('registrationFailed', error);
      eventBus.emit('auth:registrationFailed', error);
      throw error;
    }
  }

  /**
   * Logout current user
   */
  async logout() {
    try {
      // Make logout request if token exists
      if (this.authToken) {
        await fetch('/auth/logout', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${this.authToken}`
          }
        });
      }
    } catch (error) {
      this.log('warn', 'Logout request failed:', error);
    }

    // Clear authentication data
    this.clearAuthData();

    // Update state
    this.updateAuthState();

    // Clear token refresh
    this.clearTokenRefresh();

    // Emit logout events
    this.emit('logoutSuccess');
    eventBus.emit('auth:logoutSuccess');
    eventBus.emit('auth:tokenChanged', { token: null });

    this.log('info', 'User logged out successfully');
  }

  /**
   * Change user password
   */
  async changePassword(passwordData) {
    const { currentPassword, newPassword } = passwordData;

    try {
      this.emit('passwordChangeStarted');
      eventBus.emit('auth:passwordChangeStarted');

      if (!this.authToken) {
        throw new Error('User not authenticated');
      }

      // Validate password data
      if (!currentPassword || !newPassword) {
        throw new Error('Current and new passwords are required');
      }

      // Make password change request
      const response = await fetch('/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.authToken}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Password change failed');
      }

      // Emit success events
      this.emit('passwordChangeSuccess');
      eventBus.emit('auth:passwordChangeSuccess');

      this.log('info', 'Password changed successfully');
    } catch (error) {
      this.log('error', 'Password change failed:', error);
      this.emit('passwordChangeFailed', error);
      eventBus.emit('auth:passwordChangeFailed', error);
      throw error;
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshAuthToken() {
    if (!this.refreshToken) {
      this.log('warn', 'No refresh token available');
      return false;
    }

    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Token refresh failed');
      }

      // Update tokens
      this.authToken = data.access_token;
      if (data.refresh_token) {
        this.refreshToken = data.refresh_token;
      }
      this.tokenExpiryTime = data.expires_at ? new Date(data.expires_at) : null;

      // Save updated data
      this.saveAuthData();

      // Update state
      this.updateAuthState();

      // Set up next refresh
      if (this.options.autoRefresh) {
        this.setupTokenRefresh();
      }

      // Emit token changed event
      eventBus.emit('auth:tokenChanged', { token: this.authToken });

      this.log('info', 'Token refreshed successfully');
      return true;
    } catch (error) {
      this.log('error', 'Token refresh failed:', error);

      // If refresh fails, logout user
      this.logout();
      return false;
    }
  }

  /**
   * Validate registration data
   */
  validateRegistrationData(userData) {
    const { username, email, password, confirmPassword } = userData;

    if (!username || username.trim().length < 3) {
      throw new Error('Username must be at least 3 characters long');
    }

    if (!email || !this.isValidEmail(email)) {
      throw new Error('Valid email address is required');
    }

    if (!password || password.length < 8) {
      throw new Error('Password must be at least 8 characters long');
    }

    if (password !== confirmPassword) {
      throw new Error('Passwords do not match');
    }
  }

  /**
   * Validate email format
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!(this.authToken && this.currentUser);
  }

  /**
   * Check if user has specific role
   */
  hasRole(role) {
    return this.currentUser && this.currentUser.roles && this.currentUser.roles.includes(role);
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission) {
    return this.currentUser && this.currentUser.permissions && this.currentUser.permissions.includes(permission);
  }

  /**
   * Get current user information
   */
  getCurrentUser() {
    return this.currentUser ? { ...this.currentUser } : null;
  }

  /**
   * Get authentication token
   */
  getAuthToken() {
    return this.authToken;
  }

  /**
   * Load authentication data from storage
   */
  loadAuthData() {
    try {
      const token = localStorage.getItem(`${this.options.storagePrefix}-token`);
      const refreshToken = localStorage.getItem(`${this.options.storagePrefix}-refresh-token`);
      const user = localStorage.getItem(`${this.options.storagePrefix}-user`);
      const expiry = localStorage.getItem(`${this.options.storagePrefix}-expiry`);

      if (token && user) {
        this.authToken = token;
        this.refreshToken = refreshToken;
        this.currentUser = JSON.parse(user);
        this.tokenExpiryTime = expiry ? new Date(expiry) : null;

        // Check if token is expired
        if (this.tokenExpiryTime && this.tokenExpiryTime <= new Date()) {
          this.log('info', 'Token expired, clearing auth data');
          this.clearAuthData();
        }
      }
    } catch (error) {
      this.log('warn', 'Failed to load auth data:', error);
      this.clearAuthData();
    }
  }

  /**
   * Save authentication data to storage
   */
  saveAuthData() {
    try {
      if (this.authToken && this.currentUser) {
        localStorage.setItem(`${this.options.storagePrefix}-token`, this.authToken);
        localStorage.setItem(`${this.options.storagePrefix}-user`, JSON.stringify(this.currentUser));

        if (this.refreshToken) {
          localStorage.setItem(`${this.options.storagePrefix}-refresh-token`, this.refreshToken);
        }

        if (this.tokenExpiryTime) {
          localStorage.setItem(`${this.options.storagePrefix}-expiry`, this.tokenExpiryTime.toISOString());
        }
      }
    } catch (error) {
      this.log('warn', 'Failed to save auth data:', error);
    }
  }

  /**
   * Clear authentication data from storage
   */
  clearAuthData() {
    this.authToken = null;
    this.refreshToken = null;
    this.currentUser = null;
    this.tokenExpiryTime = null;

    // Clear from storage
    localStorage.removeItem(`${this.options.storagePrefix}-token`);
    localStorage.removeItem(`${this.options.storagePrefix}-refresh-token`);
    localStorage.removeItem(`${this.options.storagePrefix}-user`);
    localStorage.removeItem(`${this.options.storagePrefix}-expiry`);
  }

  /**
   * Set up automatic token refresh
   */
  setupTokenRefresh() {
    this.clearTokenRefresh();

    if (!this.tokenExpiryTime) {
      return;
    }

    const now = new Date();
    const timeUntilExpiry = this.tokenExpiryTime.getTime() - now.getTime();
    const refreshTime = timeUntilExpiry - this.options.refreshThreshold;

    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(() => {
        this.refreshAuthToken();
      }, refreshTime);

      this.log('debug', `Token refresh scheduled in ${Math.round(refreshTime / 1000)} seconds`);
    } else {
      // Token is about to expire or already expired
      this.refreshAuthToken();
    }
  }

  /**
   * Clear token refresh timer
   */
  clearTokenRefresh() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Update authentication state in global state manager
   */
  updateAuthState() {
    stateManager.setState({
      auth: {
        isAuthenticated: this.isAuthenticated(),
        user: this.getCurrentUser(),
        token: this.authToken,
        tokenExpiry: this.tokenExpiryTime
      }
    }, 'auth-manager');
  }

  /**
   * Get authentication status
   */
  getStatus() {
    return {
      isAuthenticated: this.isAuthenticated(),
      user: this.getCurrentUser(),
      hasToken: !!this.authToken,
      tokenExpiry: this.tokenExpiryTime,
      timeUntilExpiry: this.tokenExpiryTime ? this.tokenExpiryTime.getTime() - new Date().getTime() : null
    };
  }

  onDestroy() {
    this.clearTokenRefresh();
  }
}

export default AuthManager;
