/**
 * Login Page Object Model for GitHound web tests.
 * Handles authentication-related interactions and validations.
 */

const { expect } = require('@playwright/test');
const BasePage = require('./base-page');

class LoginPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Page elements
    this.elements = {
      // Login form elements
      loginButton: '[data-testid="login-button"]',
      usernameInput: '[data-testid="username-input"]',
      passwordInput: '[data-testid="password-input"]',
      submitLoginButton: '[data-testid="submit-login"]',
      loginError: '[data-testid="login-error"]',
      loginForm: '[data-testid="login-form"]',
      
      // Registration form elements
      registerButton: '[data-testid="register-button"]',
      registerUsername: '[data-testid="register-username"]',
      registerEmail: '[data-testid="register-email"]',
      registerPassword: '[data-testid="register-password"]',
      registerConfirmPassword: '[data-testid="register-confirm-password"]',
      submitRegistrationButton: '[data-testid="submit-registration"]',
      registrationSuccess: '[data-testid="registration-success"]',
      registrationError: '[data-testid="registration-error"]',
      
      // User menu elements
      userMenu: '[data-testid="user-menu"]',
      usernameDisplay: '[data-testid="username-display"]',
      logoutButton: '[data-testid="logout-button"]',
      profileLink: '[data-testid="profile-link"]',
      
      // Validation error elements
      usernameError: '[data-testid="username-error"]',
      passwordError: '[data-testid="password-error"]',
      emailError: '[data-testid="email-error"]',
      passwordMismatchError: '[data-testid="password-mismatch-error"]',
      
      // Password change elements
      changePasswordTab: '[data-testid="change-password-tab"]',
      currentPassword: '[data-testid="current-password"]',
      newPassword: '[data-testid="new-password"]',
      confirmNewPassword: '[data-testid="confirm-new-password"]',
      submitPasswordChange: '[data-testid="submit-password-change"]',
      passwordChangeSuccess: '[data-testid="password-change-success"]',
      
      // Admin elements
      adminPanelLink: '[data-testid="admin-panel-link"]',
      adminDashboard: '[data-testid="admin-dashboard"]',
      userManagement: '[data-testid="user-management"]'
    };
  }

  /**
   * Navigate to the login page
   */
  async navigateToLogin() {
    await this.goto('/');
    await this.waitForElement(this.elements.loginButton);
  }

  /**
   * Click the login button to open login form
   */
  async openLoginForm() {
    await this.page.click(this.elements.loginButton);
    await this.waitForElement(this.elements.loginForm);
  }

  /**
   * Fill login credentials
   */
  async fillLoginCredentials(username, password) {
    await this.page.fill(this.elements.usernameInput, username);
    await this.page.fill(this.elements.passwordInput, password);
  }

  /**
   * Submit login form
   */
  async submitLogin() {
    await this.page.click(this.elements.submitLoginButton);
  }

  /**
   * Complete login process
   */
  async login(username, password) {
    await this.navigateToLogin();
    await this.openLoginForm();
    await this.fillLoginCredentials(username, password);
    await this.submitLogin();
    
    // Wait for either success (user menu) or error
    try {
      await this.waitForElement(this.elements.userMenu, 10000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getLoginError();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Get login error message
   */
  async getLoginError() {
    try {
      return await this.page.textContent(this.elements.loginError);
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if user is logged in
   */
  async isLoggedIn() {
    return await this.page.isVisible(this.elements.userMenu);
  }

  /**
   * Get logged in username
   */
  async getLoggedInUsername() {
    if (await this.isLoggedIn()) {
      return await this.page.textContent(this.elements.usernameDisplay);
    }
    return null;
  }

  /**
   * Logout user
   */
  async logout() {
    if (await this.isLoggedIn()) {
      await this.page.click(this.elements.userMenu);
      await this.page.click(this.elements.logoutButton);
      await this.waitForElement(this.elements.loginButton);
    }
  }

  /**
   * Navigate to registration
   */
  async navigateToRegistration() {
    await this.navigateToLogin();
    await this.page.click(this.elements.registerButton);
  }

  /**
   * Fill registration form
   */
  async fillRegistrationForm(userData) {
    await this.page.fill(this.elements.registerUsername, userData.username);
    await this.page.fill(this.elements.registerEmail, userData.email);
    await this.page.fill(this.elements.registerPassword, userData.password);
    await this.page.fill(this.elements.registerConfirmPassword, userData.confirmPassword || userData.password);
  }

  /**
   * Submit registration form
   */
  async submitRegistration() {
    await this.page.click(this.elements.submitRegistrationButton);
  }

  /**
   * Complete registration process
   */
  async register(userData) {
    await this.navigateToRegistration();
    await this.fillRegistrationForm(userData);
    await this.submitRegistration();
    
    // Wait for either success or error
    try {
      await this.waitForElement(this.elements.registrationSuccess, 10000);
      return { success: true };
    } catch (error) {
      const errorMessage = await this.getRegistrationError();
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Get registration error message
   */
  async getRegistrationError() {
    try {
      return await this.page.textContent(this.elements.registrationError);
    } catch (error) {
      return null;
    }
  }

  /**
   * Check for validation errors
   */
  async getValidationErrors() {
    const errors = {};
    
    if (await this.page.isVisible(this.elements.usernameError)) {
      errors.username = await this.page.textContent(this.elements.usernameError);
    }
    
    if (await this.page.isVisible(this.elements.passwordError)) {
      errors.password = await this.page.textContent(this.elements.passwordError);
    }
    
    if (await this.page.isVisible(this.elements.emailError)) {
      errors.email = await this.page.textContent(this.elements.emailError);
    }
    
    if (await this.page.isVisible(this.elements.passwordMismatchError)) {
      errors.passwordMismatch = await this.page.textContent(this.elements.passwordMismatchError);
    }
    
    return errors;
  }

  /**
   * Navigate to user profile
   */
  async navigateToProfile() {
    if (await this.isLoggedIn()) {
      await this.page.click(this.elements.userMenu);
      await this.page.click(this.elements.profileLink);
    }
  }

  /**
   * Change password
   */
  async changePassword(currentPassword, newPassword) {
    await this.navigateToProfile();
    await this.page.click(this.elements.changePasswordTab);
    
    await this.page.fill(this.elements.currentPassword, currentPassword);
    await this.page.fill(this.elements.newPassword, newPassword);
    await this.page.fill(this.elements.confirmNewPassword, newPassword);
    
    await this.page.click(this.elements.submitPasswordChange);
    
    // Wait for success message
    try {
      await this.waitForElement(this.elements.passwordChangeSuccess, 10000);
      return { success: true };
    } catch (error) {
      return { success: false, error: 'Password change failed' };
    }
  }

  /**
   * Check if user has admin access
   */
  async hasAdminAccess() {
    if (await this.isLoggedIn()) {
      await this.page.click(this.elements.userMenu);
      return await this.page.isVisible(this.elements.adminPanelLink);
    }
    return false;
  }

  /**
   * Navigate to admin panel
   */
  async navigateToAdminPanel() {
    if (await this.hasAdminAccess()) {
      await this.page.click(this.elements.userMenu);
      await this.page.click(this.elements.adminPanelLink);
      await this.waitForElement(this.elements.adminDashboard);
    }
  }

  /**
   * Verify login form validation
   */
  async verifyLoginFormValidation() {
    await this.navigateToLogin();
    await this.openLoginForm();
    
    // Try to submit empty form
    await this.submitLogin();
    
    const errors = await this.getValidationErrors();
    return {
      hasUsernameError: !!errors.username,
      hasPasswordError: !!errors.password,
      errors
    };
  }

  /**
   * Verify registration form validation
   */
  async verifyRegistrationFormValidation() {
    await this.navigateToRegistration();
    
    // Try to submit empty form
    await this.submitRegistration();
    
    const errors = await this.getValidationErrors();
    return {
      hasUsernameError: !!errors.username,
      hasPasswordError: !!errors.password,
      hasEmailError: !!errors.email,
      errors
    };
  }

  /**
   * Test password mismatch validation
   */
  async testPasswordMismatchValidation(userData) {
    await this.navigateToRegistration();
    
    const mismatchData = {
      ...userData,
      confirmPassword: 'different_password'
    };
    
    await this.fillRegistrationForm(mismatchData);
    await this.submitRegistration();
    
    const errors = await this.getValidationErrors();
    return {
      hasPasswordMismatchError: !!errors.passwordMismatch,
      error: errors.passwordMismatch
    };
  }

  /**
   * Test session persistence
   */
  async testSessionPersistence() {
    const wasLoggedIn = await this.isLoggedIn();
    if (wasLoggedIn) {
      const username = await this.getLoggedInUsername();
      await this.reload();
      await this.waitForPageLoad();
      
      const stillLoggedIn = await this.isLoggedIn();
      const usernameAfterReload = await this.getLoggedInUsername();
      
      return {
        persistedSession: stillLoggedIn,
        usernameMatches: username === usernameAfterReload
      };
    }
    
    return { persistedSession: false, usernameMatches: false };
  }
}

module.exports = LoginPage;
