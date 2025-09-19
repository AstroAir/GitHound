/**
 * Unit tests for the AuthManager component
 */

import { AuthManager } from '../../components/auth/auth-manager.js';
import { MockEventBus, MockStateManager, mockAPI, testData } from '../mocks/component-mocks.js';

describe('AuthManager', () => {
  let authManager;
  let mockEventBus;
  let mockStateManager;
  let mockFetch;

  beforeEach(() => {
    mockEventBus = new MockEventBus();
    mockStateManager = new MockStateManager();
    mockFetch = jest.fn();

    global.EventBus = mockEventBus;
    global.StateManager = mockStateManager;
    global.fetch = mockFetch;

    authManager = new AuthManager();
  });

  afterEach(async () => {
    if (authManager && !authManager.destroyed) {
      await authManager.destroy();
    }
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('Initialization', () => {
    test('should initialize with default state', async () => {
      await authManager.init();

      expect(authManager.initialized).toBe(true);
      expect(authManager.state.isAuthenticated).toBe(false);
      expect(authManager.state.user).toBeNull();
      expect(authManager.state.token).toBeNull();
    });

    test('should restore session from localStorage', async () => {
      const user = testData.generateUser();
      const token = 'stored-token';

      localStorage.setItem('githound_user', JSON.stringify(user));
      localStorage.setItem('githound_token', token);

      await authManager.init();

      expect(authManager.state.isAuthenticated).toBe(true);
      expect(authManager.state.user).toEqual(user);
      expect(authManager.state.token).toBe(token);
    });

    test('should validate stored token', async () => {
      localStorage.setItem('githound_token', 'invalid-token');
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401
      });

      await authManager.init();

      expect(authManager.state.isAuthenticated).toBe(false);
      expect(localStorage.getItem('githound_token')).toBeNull();
    });
  });

  describe('Login', () => {
    beforeEach(async () => {
      await authManager.init();
    });

    test('should login with valid credentials', async () => {
      const credentials = { username: 'testuser', password: 'password' };
      const response = mockAPI.auth.login.success;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(response)
      });

      const result = await authManager.login(credentials);

      expect(result.success).toBe(true);
      expect(authManager.state.isAuthenticated).toBe(true);
      expect(authManager.state.user).toEqual(response.data.user);
      expect(authManager.state.token).toBe(response.data.token);
    });

    test('should handle login failure', async () => {
      const credentials = { username: 'testuser', password: 'wrong' };
      const response = mockAPI.auth.login.error;

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve(response)
      });

      const result = await authManager.login(credentials);

      expect(result.success).toBe(false);
      expect(result.error).toBe(response.message);
      expect(authManager.state.isAuthenticated).toBe(false);
    });

    test('should emit login events', async () => {
      const credentials = { username: 'testuser', password: 'password' };
      const response = mockAPI.auth.login.success;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(response)
      });

      const loginStartSpy = jest.fn();
      const loginSuccessSpy = jest.fn();

      mockEventBus.on('auth:login:start', loginStartSpy);
      mockEventBus.on('auth:login:success', loginSuccessSpy);

      await authManager.login(credentials);

      expect(loginStartSpy).toHaveBeenCalledWith({ username: credentials.username });
      expect(loginSuccessSpy).toHaveBeenCalledWith({ user: response.data.user });
    });

    test('should store credentials in localStorage', async () => {
      const credentials = { username: 'testuser', password: 'password' };
      const response = mockAPI.auth.login.success;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(response)
      });

      await authManager.login(credentials);

      expect(localStorage.getItem('githound_user')).toBe(
        JSON.stringify(response.data.user)
      );
      expect(localStorage.getItem('githound_token')).toBe(response.data.token);
    });

    test('should handle network errors', async () => {
      const credentials = { username: 'testuser', password: 'password' };

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await authManager.login(credentials);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Network error');
    });
  });

  describe('Logout', () => {
    beforeEach(async () => {
      await authManager.init();

      // Set up authenticated state
      const user = testData.generateUser();
      authManager.setState({
        isAuthenticated: true,
        user,
        token: 'test-token'
      });
      localStorage.setItem('githound_user', JSON.stringify(user));
      localStorage.setItem('githound_token', 'test-token');
    });

    test('should logout successfully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const result = await authManager.logout();

      expect(result.success).toBe(true);
      expect(authManager.state.isAuthenticated).toBe(false);
      expect(authManager.state.user).toBeNull();
      expect(authManager.state.token).toBeNull();
    });

    test('should clear localStorage on logout', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      await authManager.logout();

      expect(localStorage.getItem('githound_user')).toBeNull();
      expect(localStorage.getItem('githound_token')).toBeNull();
    });

    test('should emit logout events', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const logoutSpy = jest.fn();
      mockEventBus.on('auth:logout', logoutSpy);

      await authManager.logout();

      expect(logoutSpy).toHaveBeenCalled();
    });

    test('should handle logout API errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('API error'));

      const result = await authManager.logout();

      // Should still clear local state even if API call fails
      expect(result.success).toBe(true);
      expect(authManager.state.isAuthenticated).toBe(false);
    });
  });

  describe('Registration', () => {
    beforeEach(async () => {
      await authManager.init();
    });

    test('should register new user', async () => {
      const userData = {
        username: 'newuser',
        email: 'newuser@test.com',
        password: 'password'
      };

      const response = {
        status: 'success',
        data: {
          user: testData.generateUser(),
          token: 'new-token'
        }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(response)
      });

      const result = await authManager.register(userData);

      expect(result.success).toBe(true);
      expect(authManager.state.isAuthenticated).toBe(true);
      expect(authManager.state.user).toEqual(response.data.user);
    });

    test('should handle registration validation errors', async () => {
      const userData = {
        username: 'existing',
        email: 'invalid-email',
        password: '123'
      };

      const response = {
        status: 'error',
        message: 'Validation failed',
        errors: {
          username: 'Username already exists',
          email: 'Invalid email format',
          password: 'Password too short'
        }
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve(response)
      });

      const result = await authManager.register(userData);

      expect(result.success).toBe(false);
      expect(result.errors).toEqual(response.errors);
    });
  });

  describe('Token Management', () => {
    beforeEach(async () => {
      await authManager.init();
    });

    test('should refresh token automatically', async () => {
      const oldToken = 'old-token';
      const newToken = 'new-token';

      authManager.setState({ token: oldToken, isAuthenticated: true });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          data: { token: newToken }
        })
      });

      const result = await authManager.refreshToken();

      expect(result.success).toBe(true);
      expect(authManager.state.token).toBe(newToken);
      expect(localStorage.getItem('githound_token')).toBe(newToken);
    });

    test('should handle token refresh failure', async () => {
      authManager.setState({ token: 'old-token', isAuthenticated: true });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401
      });

      const result = await authManager.refreshToken();

      expect(result.success).toBe(false);
      expect(authManager.state.isAuthenticated).toBe(false);
    });

    test('should validate token format', () => {
      expect(authManager.isValidToken('valid.jwt.token')).toBe(true);
      expect(authManager.isValidToken('invalid-token')).toBe(false);
      expect(authManager.isValidToken('')).toBe(false);
      expect(authManager.isValidToken(null)).toBe(false);
    });

    test('should check token expiration', () => {
      const validToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjk5OTk5OTk5OTl9.signature';
      const expiredToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MzAwMDAwMDB9.signature';

      expect(authManager.isTokenExpired(validToken)).toBe(false);
      expect(authManager.isTokenExpired(expiredToken)).toBe(true);
    });
  });

  describe('User Management', () => {
    beforeEach(async () => {
      await authManager.init();
      authManager.setState({
        isAuthenticated: true,
        user: testData.generateUser(),
        token: 'test-token'
      });
    });

    test('should update user profile', async () => {
      const updates = { email: 'newemail@test.com' };
      const updatedUser = { ...authManager.state.user, ...updates };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          data: { user: updatedUser }
        })
      });

      const result = await authManager.updateProfile(updates);

      expect(result.success).toBe(true);
      expect(authManager.state.user).toEqual(updatedUser);
    });

    test('should change password', async () => {
      const passwordData = {
        currentPassword: 'oldpass',
        newPassword: 'newpass'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'success' })
      });

      const result = await authManager.changePassword(passwordData);

      expect(result.success).toBe(true);
    });

    test('should check user permissions', () => {
      authManager.setState({
        user: { ...testData.generateUser(), role: 'admin' }
      });

      expect(authManager.hasPermission('admin')).toBe(true);
      expect(authManager.hasPermission('user')).toBe(true);
      expect(authManager.hasPermission('superadmin')).toBe(false);
    });
  });

  describe('Session Management', () => {
    test('should handle session timeout', async () => {
      await authManager.init();
      authManager.setState({ isAuthenticated: true });

      const timeoutSpy = jest.fn();
      mockEventBus.on('auth:session:timeout', timeoutSpy);

      authManager.handleSessionTimeout();

      expect(authManager.state.isAuthenticated).toBe(false);
      expect(timeoutSpy).toHaveBeenCalled();
    });

    test('should extend session on activity', async () => {
      await authManager.init();
      authManager.setState({ isAuthenticated: true });

      const extendSpy = jest.spyOn(authManager, 'extendSession');

      authManager.handleUserActivity();

      expect(extendSpy).toHaveBeenCalled();
    });

    test('should track session duration', async () => {
      await authManager.init();

      const startTime = Date.now();
      authManager.setState({ isAuthenticated: true });

      // Simulate some time passing
      jest.advanceTimersByTime(5000);

      const duration = authManager.getSessionDuration();
      expect(duration).toBeGreaterThanOrEqual(5000);
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      await authManager.init();
    });

    test('should handle API errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const errorSpy = jest.fn();
      mockEventBus.on('auth:error', errorSpy);

      const result = await authManager.login({ username: 'test', password: 'test' });

      expect(result.success).toBe(false);
      expect(errorSpy).toHaveBeenCalled();
    });

    test('should handle malformed responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON'))
      });

      const result = await authManager.login({ username: 'test', password: 'test' });

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid JSON');
    });
  });
});
