/**
 * Admin Page Object Model for GitHound web tests.
 * Handles admin panel functionality, user management, and system settings.
 */

const { expect } = require('@playwright/test');
const BasePage = require('./base-page');

class AdminPage extends BasePage {
  constructor(page) {
    super(page);

    // Page elements
    this.elements = {
      // Admin dashboard
      adminDashboard: '[data-testid="admin-dashboard"]',
      dashboardStats: '[data-testid="dashboard-stats"]',
      totalUsers: '[data-testid="total-users"]',
      activeUsers: '[data-testid="active-users"]',
      totalSearches: '[data-testid="total-searches"]',
      systemHealth: '[data-testid="system-health"]',

      // Navigation
      userManagementTab: '[data-testid="user-management"]',
      systemSettingsTab: '[data-testid="system-settings"]',
      logsTab: '[data-testid="logs-tab"]',
      analyticsTab: '[data-testid="analytics-tab"]',

      // User management
      userTable: '[data-testid="user-table"]',
      userRow: '[data-testid="user-row"]',
      addUserButton: '[data-testid="add-user"]',
      editUserButton: '[data-testid="edit-user"]',
      deleteUserButton: '[data-testid="delete-user"]',
      activateUserButton: '[data-testid="activate-user"]',
      deactivateUserButton: '[data-testid="deactivate-user"]',

      // User form
      userForm: '[data-testid="user-form"]',
      userFormUsername: '[data-testid="user-form-username"]',
      userFormEmail: '[data-testid="user-form-email"]',
      userFormPassword: '[data-testid="user-form-password"]',
      userFormRoles: '[data-testid="user-form-roles"]',
      userFormActive: '[data-testid="user-form-active"]',
      saveUserButton: '[data-testid="save-user"]',
      cancelUserButton: '[data-testid="cancel-user"]',

      // User search and filter
      userSearchInput: '[data-testid="user-search"]',
      userFilterRole: '[data-testid="user-filter-role"]',
      userFilterStatus: '[data-testid="user-filter-status"]',
      clearUserFilters: '[data-testid="clear-user-filters"]',

      // System settings
      settingsForm: '[data-testid="settings-form"]',
      maxSearchResults: '[data-testid="max-search-results"]',
      searchTimeout: '[data-testid="search-timeout"]',
      enableRegistration: '[data-testid="enable-registration"]',
      requireEmailVerification: '[data-testid="require-email-verification"]',
      defaultUserRole: '[data-testid="default-user-role"]',
      saveSettingsButton: '[data-testid="save-settings"]',
      resetSettingsButton: '[data-testid="reset-settings"]',

      // Logs
      logsContainer: '[data-testid="logs-container"]',
      logEntry: '[data-testid="log-entry"]',
      logLevel: '[data-testid="log-level"]',
      logMessage: '[data-testid="log-message"]',
      logTimestamp: '[data-testid="log-timestamp"]',
      refreshLogsButton: '[data-testid="refresh-logs"]',
      clearLogsButton: '[data-testid="clear-logs"]',
      downloadLogsButton: '[data-testid="download-logs"]',

      // Analytics
      analyticsChart: '[data-testid="analytics-chart"]',
      searchesChart: '[data-testid="searches-chart"]',
      usersChart: '[data-testid="users-chart"]',
      performanceChart: '[data-testid="performance-chart"]',
      dateRangeSelector: '[data-testid="date-range-selector"]',

      // Notifications and alerts
      successMessage: '[data-testid="success-message"]',
      errorMessage: '[data-testid="error-message"]',
      warningMessage: '[data-testid="warning-message"]',
      confirmDialog: '[data-testid="confirm-dialog"]',
      confirmYes: '[data-testid="confirm-yes"]',
      confirmNo: '[data-testid="confirm-no"]',

      // Bulk actions
      selectAllUsers: '[data-testid="select-all-users"]',
      bulkDeleteUsers: '[data-testid="bulk-delete-users"]',
      bulkActivateUsers: '[data-testid="bulk-activate-users"]',
      bulkDeactivateUsers: '[data-testid="bulk-deactivate-users"]',
      selectedUsersCount: '[data-testid="selected-users-count"]'
    };
  }

  /**
   * Navigate to admin dashboard
   */
  async navigateToAdmin() {
    await this.goto('/admin');
    await this.waitForElement(this.elements.adminDashboard);
  }

  /**
   * Get dashboard statistics
   */
  async getDashboardStats() {
    await this.waitForElement(this.elements.dashboardStats);

    return {
      totalUsers: await this.getTextByTestId('total-users'),
      activeUsers: await this.getTextByTestId('active-users'),
      totalSearches: await this.getTextByTestId('total-searches'),
      systemHealth: await this.getTextByTestId('system-health')
    };
  }

  /**
   * Navigate to user management
   */
  async navigateToUserManagement() {
    await this.clickTestId('user-management');
    await this.waitForElement(this.elements.userTable);
  }

  /**
   * Get all users from the table
   */
  async getAllUsers() {
    await this.waitForElement(this.elements.userTable);

    const userRows = this.page.locator(this.elements.userRow);
    const count = await userRows.count();
    const users = [];

    for (let i = 0; i < count; i++) {
      const row = userRows.nth(i);

      const user = {
        username: await row.locator('[data-testid="username"]').textContent(),
        email: await row.locator('[data-testid="email"]').textContent(),
        roles: await row.locator('[data-testid="roles"]').textContent(),
        status: await row.locator('[data-testid="status"]').textContent(),
        lastLogin: await row.locator('[data-testid="last-login"]').textContent()
      };

      users.push(user);
    }

    return users;
  }

  /**
   * Search for users
   */
  async searchUsers(searchTerm) {
    await this.fillTestId('user-search', searchTerm);
    await this.pressKey('Enter');
    await this.waitForElement(this.elements.userTable);
  }

  /**
   * Filter users by role
   */
  async filterUsersByRole(role) {
    await this.selectOptionByTestId('user-filter-role', role);
    await this.waitForElement(this.elements.userTable);
  }

  /**
   * Filter users by status
   */
  async filterUsersByStatus(status) {
    await this.selectOptionByTestId('user-filter-status', status);
    await this.waitForElement(this.elements.userTable);
  }

  /**
   * Clear user filters
   */
  async clearUserFilters() {
    await this.clickTestId('clear-user-filters');
    await this.waitForElement(this.elements.userTable);
  }

  /**
   * Add new user
   */
  async addUser(userData) {
    await this.clickTestId('add-user');
    await this.waitForElement(this.elements.userForm);

    await this.fillTestId('user-form-username', userData.username);
    await this.fillTestId('user-form-email', userData.email);
    await this.fillTestId('user-form-password', userData.password);

    if (userData.roles) {
      await this.selectOptionByTestId('user-form-roles', userData.roles);
    }

    if (userData.active !== undefined) {
      if (userData.active) {
        await this.checkByTestId('user-form-active');
      } else {
        await this.uncheckByTestId('user-form-active');
      }
    }

    await this.clickTestId('save-user');

    // Wait for success message or error
    try {
      await this.waitForElement(this.elements.successMessage, 5000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getErrorMessage();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Edit user
   */
  async editUser(userIndex, userData) {
    const userRows = this.page.locator(this.elements.userRow);
    const row = userRows.nth(userIndex);

    await row.locator(this.elements.editUserButton).click();
    await this.waitForElement(this.elements.userForm);

    if (userData.username) {
      await this.fillTestId('user-form-username', userData.username);
    }

    if (userData.email) {
      await this.fillTestId('user-form-email', userData.email);
    }

    if (userData.password) {
      await this.fillTestId('user-form-password', userData.password);
    }

    if (userData.roles) {
      await this.selectOptionByTestId('user-form-roles', userData.roles);
    }

    await this.clickTestId('save-user');

    try {
      await this.waitForElement(this.elements.successMessage, 5000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getErrorMessage();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Delete user
   */
  async deleteUser(userIndex) {
    const userRows = this.page.locator(this.elements.userRow);
    const row = userRows.nth(userIndex);

    await row.locator(this.elements.deleteUserButton).click();

    // Handle confirmation dialog
    await this.waitForElement(this.elements.confirmDialog);
    await this.clickTestId('confirm-yes');

    try {
      await this.waitForElement(this.elements.successMessage, 5000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getErrorMessage();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Activate/Deactivate user
   */
  async toggleUserStatus(userIndex, activate = true) {
    const userRows = this.page.locator(this.elements.userRow);
    const row = userRows.nth(userIndex);

    const button = activate ? this.elements.activateUserButton : this.elements.deactivateUserButton;
    await row.locator(button).click();

    try {
      await this.waitForElement(this.elements.successMessage, 5000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getErrorMessage();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Navigate to system settings
   */
  async navigateToSystemSettings() {
    await this.clickTestId('system-settings');
    await this.waitForElement(this.elements.settingsForm);
  }

  /**
   * Update system settings
   */
  async updateSystemSettings(settings) {
    await this.navigateToSystemSettings();

    if (settings.maxSearchResults) {
      await this.fillTestId('max-search-results', settings.maxSearchResults.toString());
    }

    if (settings.searchTimeout) {
      await this.fillTestId('search-timeout', settings.searchTimeout.toString());
    }

    if (settings.enableRegistration !== undefined) {
      if (settings.enableRegistration) {
        await this.checkByTestId('enable-registration');
      } else {
        await this.uncheckByTestId('enable-registration');
      }
    }

    if (settings.requireEmailVerification !== undefined) {
      if (settings.requireEmailVerification) {
        await this.checkByTestId('require-email-verification');
      } else {
        await this.uncheckByTestId('require-email-verification');
      }
    }

    if (settings.defaultUserRole) {
      await this.selectOptionByTestId('default-user-role', settings.defaultUserRole);
    }

    await this.clickTestId('save-settings');

    try {
      await this.waitForElement(this.elements.successMessage, 5000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getErrorMessage();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Navigate to logs
   */
  async navigateToLogs() {
    await this.clickTestId('logs-tab');
    await this.waitForElement(this.elements.logsContainer);
  }

  /**
   * Get recent logs
   */
  async getRecentLogs(limit = 10) {
    await this.waitForElement(this.elements.logsContainer);

    const logEntries = this.page.locator(this.elements.logEntry);
    const count = Math.min(await logEntries.count(), limit);
    const logs = [];

    for (let i = 0; i < count; i++) {
      const entry = logEntries.nth(i);

      const log = {
        level: await entry.locator(this.elements.logLevel).textContent(),
        message: await entry.locator(this.elements.logMessage).textContent(),
        timestamp: await entry.locator(this.elements.logTimestamp).textContent()
      };

      logs.push(log);
    }

    return logs;
  }

  /**
   * Refresh logs
   */
  async refreshLogs() {
    await this.clickTestId('refresh-logs');
    await this.waitForElement(this.elements.logsContainer);
  }

  /**
   * Clear logs
   */
  async clearLogs() {
    await this.clickTestId('clear-logs');

    // Handle confirmation
    await this.waitForElement(this.elements.confirmDialog);
    await this.clickTestId('confirm-yes');

    await this.waitForElement(this.elements.successMessage);
  }

  /**
   * Download logs
   */
  async downloadLogs() {
    const downloadPromise = this.page.waitForDownload();
    await this.clickTestId('download-logs');
    const download = await downloadPromise;
    return download;
  }

  /**
   * Get success message
   */
  async getSuccessMessage() {
    if (await this.isVisibleByTestId('success-message')) {
      return await this.getTextByTestId('success-message');
    }
    return null;
  }

  /**
   * Get error message
   */
  async getErrorMessage() {
    if (await this.isVisibleByTestId('error-message')) {
      return await this.getTextByTestId('error-message');
    }
    return null;
  }

  /**
   * Get warning message
   */
  async getWarningMessage() {
    if (await this.isVisibleByTestId('warning-message')) {
      return await this.getTextByTestId('warning-message');
    }
    return null;
  }

  /**
   * Check if user has admin access
   */
  async hasAdminAccess() {
    try {
      await this.navigateToAdmin();
      return await this.isVisibleByTestId('admin-dashboard');
    } catch (error) {
      return false;
    }
  }
}

module.exports = AdminPage;
