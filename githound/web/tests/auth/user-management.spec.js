/**
 * User Management Tests
 * Tests user profile management, settings, and account operations
 */

const { test, expect } = require('@playwright/test');
const { LoginPage, AdminPage } = require('../pages');

test.describe('User Management Tests', () => {
  let loginPage;
  let adminPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    adminPage = new AdminPage(page);
  });

  test.describe('User Profile Management @auth @profile', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `profile_${Date.now()}`,
        email: `profile_${Date.now()}@example.com`,
        password: 'Profile123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should display user profile information', async () => {
      const profile = await loginPage.getUserProfile();
      
      expect(profile.username).toBe(testUser.username);
      expect(profile.email).toBe(testUser.email);
      expect(profile.roles).toContain('user');
    });

    test('should allow updating profile information', async () => {
      const updatedData = {
        email: `updated_${Date.now()}@example.com`,
        firstName: 'Test',
        lastName: 'User'
      };

      const result = await loginPage.updateProfile(updatedData);
      
      expect(result.success).toBe(true);
      
      // Verify changes are reflected
      const profile = await loginPage.getUserProfile();
      expect(profile.email).toBe(updatedData.email);
    });

    test('should validate email format in profile update', async () => {
      const invalidData = {
        email: 'invalid-email-format'
      };

      const result = await loginPage.updateProfile(invalidData);
      
      expect(result.success).toBe(false);
      expect(result.error).toMatch(/email|format|invalid/i);
    });

    test('should prevent duplicate email addresses', async ({ page }) => {
      // Create another user first
      const otherUser = {
        username: `other_${Date.now()}`,
        email: `other_${Date.now()}@example.com`,
        password: 'Other123!'
      };

      await loginPage.logout();
      await loginPage.register(otherUser);
      await loginPage.logout();
      await loginPage.login(testUser.username, testUser.password);

      // Try to update to existing email
      const result = await loginPage.updateProfile({
        email: otherUser.email
      });
      
      expect(result.success).toBe(false);
      expect(result.error).toMatch(/already exists|duplicate/i);
    });
  });

  test.describe('Account Settings @auth @settings', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `settings_${Date.now()}`,
        email: `settings_${Date.now()}@example.com`,
        password: 'Settings123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should allow changing notification preferences', async () => {
      const preferences = {
        emailNotifications: false,
        searchAlerts: true,
        weeklyDigest: false
      };

      const result = await loginPage.updateNotificationPreferences(preferences);
      
      expect(result.success).toBe(true);
      
      // Verify preferences are saved
      const savedPreferences = await loginPage.getNotificationPreferences();
      expect(savedPreferences.emailNotifications).toBe(false);
      expect(savedPreferences.searchAlerts).toBe(true);
    });

    test('should allow changing privacy settings', async () => {
      const privacySettings = {
        profileVisibility: 'private',
        searchHistoryVisible: false,
        allowDataExport: true
      };

      const result = await loginPage.updatePrivacySettings(privacySettings);
      
      expect(result.success).toBe(true);
    });

    test('should allow setting search preferences', async () => {
      const searchPreferences = {
        defaultSearchType: 'fuzzy',
        resultsPerPage: 50,
        highlightMatches: true,
        saveSearchHistory: true
      };

      const result = await loginPage.updateSearchPreferences(searchPreferences);
      
      expect(result.success).toBe(true);
    });
  });

  test.describe('Account Security @auth @security', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `security_${Date.now()}`,
        email: `security_${Date.now()}@example.com`,
        password: 'Security123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should show login history', async () => {
      const loginHistory = await loginPage.getLoginHistory();
      
      expect(loginHistory).toBeTruthy();
      expect(loginHistory.length).toBeGreaterThan(0);
      expect(loginHistory[0]).toHaveProperty('timestamp');
      expect(loginHistory[0]).toHaveProperty('ipAddress');
      expect(loginHistory[0]).toHaveProperty('userAgent');
    });

    test('should allow enabling two-factor authentication', async () => {
      const result = await loginPage.enableTwoFactorAuth();
      
      expect(result.success).toBe(true);
      expect(result.qrCode).toBeTruthy();
      expect(result.backupCodes).toBeTruthy();
      expect(result.backupCodes.length).toBeGreaterThan(0);
    });

    test('should allow disabling two-factor authentication', async () => {
      // First enable 2FA
      await loginPage.enableTwoFactorAuth();
      
      // Then disable it
      const result = await loginPage.disableTwoFactorAuth(testUser.password);
      
      expect(result.success).toBe(true);
    });

    test('should show active sessions', async () => {
      const sessions = await loginPage.getActiveSessions();
      
      expect(sessions).toBeTruthy();
      expect(sessions.length).toBeGreaterThan(0);
      expect(sessions[0]).toHaveProperty('sessionId');
      expect(sessions[0]).toHaveProperty('lastActivity');
      expect(sessions[0]).toHaveProperty('ipAddress');
    });

    test('should allow terminating other sessions', async ({ browser }) => {
      // Create another session
      const secondContext = await browser.newContext();
      const secondPage = await secondContext.newPage();
      const secondLoginPage = new LoginPage(secondPage);
      
      await secondLoginPage.login(testUser.username, testUser.password);
      
      // Get sessions from first page
      const sessions = await loginPage.getActiveSessions();
      expect(sessions.length).toBeGreaterThan(1);
      
      // Terminate other sessions
      const result = await loginPage.terminateOtherSessions();
      expect(result.success).toBe(true);
      
      // Verify second session is terminated
      await secondPage.reload();
      const isLoggedInSecond = await secondLoginPage.isLoggedIn();
      expect(isLoggedInSecond).toBe(false);
      
      await secondContext.close();
    });
  });

  test.describe('Account Deletion @auth @deletion', () => {
    let testUser;

    test.beforeEach(async () => {
      testUser = {
        username: `deletion_${Date.now()}`,
        email: `deletion_${Date.now()}@example.com`,
        password: 'Deletion123!'
      };

      await loginPage.register(testUser);
      await loginPage.login(testUser.username, testUser.password);
    });

    test('should allow requesting account deletion', async () => {
      const result = await loginPage.requestAccountDeletion(testUser.password);
      
      expect(result.success).toBe(true);
      expect(result.message).toMatch(/deletion request|scheduled/i);
    });

    test('should require password confirmation for deletion', async () => {
      const result = await loginPage.requestAccountDeletion('wrong_password');
      
      expect(result.success).toBe(false);
      expect(result.error).toMatch(/password|incorrect/i);
    });

    test('should allow canceling account deletion', async () => {
      // Request deletion first
      await loginPage.requestAccountDeletion(testUser.password);
      
      // Then cancel it
      const result = await loginPage.cancelAccountDeletion();
      
      expect(result.success).toBe(true);
    });

    test('should export user data before deletion', async () => {
      const exportResult = await loginPage.exportUserData();
      
      expect(exportResult.success).toBe(true);
      expect(exportResult.downloadUrl).toBeTruthy();
    });
  });

  test.describe('Admin User Management @auth @admin', () => {
    let adminUser;
    let regularUser;

    test.beforeEach(async () => {
      adminUser = {
        username: `admin_${Date.now()}`,
        email: `admin_${Date.now()}@example.com`,
        password: 'Admin123!',
        roles: ['admin']
      };

      regularUser = {
        username: `regular_${Date.now()}`,
        email: `regular_${Date.now()}@example.com`,
        password: 'Regular123!'
      };

      // Create admin user (this would require backend support)
      await loginPage.register(adminUser);
      await loginPage.login(adminUser.username, adminUser.password);
      
      // Assume admin privileges are granted
      await adminPage.navigateToAdmin();
    });

    test('should display user management dashboard', async () => {
      await adminPage.navigateToUserManagement();
      
      const users = await adminPage.getAllUsers();
      expect(users).toBeTruthy();
      expect(users.length).toBeGreaterThan(0);
    });

    test('should allow creating new users', async () => {
      const result = await adminPage.addUser(regularUser);
      
      expect(result.success).toBe(true);
      
      // Verify user appears in list
      const users = await adminPage.getAllUsers();
      const createdUser = users.find(u => u.username === regularUser.username);
      expect(createdUser).toBeTruthy();
    });

    test('should allow editing user information', async () => {
      // Create user first
      await adminPage.addUser(regularUser);
      
      const users = await adminPage.getAllUsers();
      const userIndex = users.findIndex(u => u.username === regularUser.username);
      
      const updatedData = {
        email: `updated_${Date.now()}@example.com`,
        roles: 'moderator'
      };
      
      const result = await adminPage.editUser(userIndex, updatedData);
      expect(result.success).toBe(true);
    });

    test('should allow activating/deactivating users', async () => {
      // Create user first
      await adminPage.addUser(regularUser);
      
      const users = await adminPage.getAllUsers();
      const userIndex = users.findIndex(u => u.username === regularUser.username);
      
      // Deactivate user
      const deactivateResult = await adminPage.toggleUserStatus(userIndex, false);
      expect(deactivateResult.success).toBe(true);
      
      // Activate user
      const activateResult = await adminPage.toggleUserStatus(userIndex, true);
      expect(activateResult.success).toBe(true);
    });

    test('should allow deleting users', async () => {
      // Create user first
      await adminPage.addUser(regularUser);
      
      const users = await adminPage.getAllUsers();
      const userIndex = users.findIndex(u => u.username === regularUser.username);
      
      const result = await adminPage.deleteUser(userIndex);
      expect(result.success).toBe(true);
      
      // Verify user is removed
      const updatedUsers = await adminPage.getAllUsers();
      const deletedUser = updatedUsers.find(u => u.username === regularUser.username);
      expect(deletedUser).toBeFalsy();
    });

    test('should allow searching and filtering users', async () => {
      // Create multiple users for testing
      const testUsers = [
        { ...regularUser, username: `search1_${Date.now()}` },
        { ...regularUser, username: `search2_${Date.now()}` },
        { ...regularUser, username: `filter1_${Date.now()}` }
      ];

      for (const user of testUsers) {
        await adminPage.addUser(user);
      }

      // Test search
      await adminPage.searchUsers('search1');
      const searchResults = await adminPage.getAllUsers();
      expect(searchResults.some(u => u.username.includes('search1'))).toBe(true);

      // Test filter by status
      await adminPage.clearUserFilters();
      await adminPage.filterUsersByStatus('active');
      const activeUsers = await adminPage.getAllUsers();
      expect(activeUsers.every(u => u.status === 'active')).toBe(true);
    });
  });
});
