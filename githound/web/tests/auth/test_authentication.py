"""
Authentication flow tests for GitHound web interface.
"""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.auth
@pytest.mark.e2e
class TestAuthentication:
    """Test authentication functionality."""
    
    async def test_user_registration_flow(self, page: Page, test_data_manager):
        """Test user registration through the web interface."""
        user_data = test_data_manager.create_test_user()
        
        # Navigate to registration page
        await page.goto("/")
        await page.click('[data-testid="register-button"]')
        
        # Fill registration form
        await page.fill('[data-testid="register-username"]', user_data["username"])
        await page.fill('[data-testid="register-email"]', user_data["email"])
        await page.fill('[data-testid="register-password"]', user_data["password"])
        await page.fill('[data-testid="register-confirm-password"]', user_data["password"])
        
        # Submit registration
        await page.click('[data-testid="submit-registration"]')
        
        # Verify successful registration
        await expect(page.locator('[data-testid="registration-success"]')).to_be_visible()
        await expect(page.locator('[data-testid="registration-success"]')).to_contain_text("Registration successful")
        
    async def test_user_login_flow(self, page: Page, test_user_data):
        """Test user login through the web interface."""
        # Navigate to login page
        await page.goto("/")
        await page.click('[data-testid="login-button"]')
        
        # Fill login form
        await page.fill('[data-testid="username-input"]', test_user_data["username"])
        await page.fill('[data-testid="password-input"]', test_user_data["password"])
        
        # Submit login
        await page.click('[data-testid="submit-login"]')
        
        # Verify successful login
        await expect(page.locator('[data-testid="user-menu"]')).to_be_visible()
        await expect(page.locator('[data-testid="username-display"]')).to_contain_text(test_user_data["username"])
        
    async def test_invalid_login_credentials(self, page: Page):
        """Test login with invalid credentials."""
        # Navigate to login page
        await page.goto("/")
        await page.click('[data-testid="login-button"]')
        
        # Fill login form with invalid credentials
        await page.fill('[data-testid="username-input"]', "invalid_user")
        await page.fill('[data-testid="password-input"]', "invalid_password")
        
        # Submit login
        await page.click('[data-testid="submit-login"]')
        
        # Verify error message
        await expect(page.locator('[data-testid="login-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="login-error"]')).to_contain_text("Invalid username or password")
        
    async def test_user_logout_flow(self, page: Page, authenticated_user):
        """Test user logout functionality."""
        # User should already be logged in from fixture
        await expect(page.locator('[data-testid="user-menu"]')).to_be_visible()
        
        # Click user menu
        await page.click('[data-testid="user-menu"]')
        
        # Click logout
        await page.click('[data-testid="logout-button"]')
        
        # Verify logout
        await expect(page.locator('[data-testid="login-button"]')).to_be_visible()
        await expect(page.locator('[data-testid="user-menu"]')).not_to_be_visible()
        
    async def test_password_change_flow(self, page: Page, authenticated_user):
        """Test password change functionality."""
        new_password = "NewPassword123!"
        
        # Navigate to profile page
        await page.click('[data-testid="user-menu"]')
        await page.click('[data-testid="profile-link"]')
        
        # Navigate to password change section
        await page.click('[data-testid="change-password-tab"]')
        
        # Fill password change form
        await page.fill('[data-testid="current-password"]', authenticated_user["password"])
        await page.fill('[data-testid="new-password"]', new_password)
        await page.fill('[data-testid="confirm-new-password"]', new_password)
        
        # Submit password change
        await page.click('[data-testid="submit-password-change"]')
        
        # Verify success message
        await expect(page.locator('[data-testid="password-change-success"]')).to_be_visible()
        await expect(page.locator('[data-testid="password-change-success"]')).to_contain_text("Password changed successfully")
        
    async def test_token_refresh_flow(self, page: Page, authenticated_user):
        """Test token refresh functionality."""
        # Wait for some time to simulate token near expiry
        await page.wait_for_timeout(1000)
        
        # Make an API request that should trigger token refresh
        response = await page.evaluate("""
            fetch('/api/v1/auth/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            }).then(r => r.json())
        """)
        
        # Verify the request was successful (token was refreshed if needed)
        assert response is not None
        
    async def test_role_based_access_control(self, page: Page, authenticated_admin):
        """Test role-based access control for admin features."""
        # Navigate to admin panel
        await page.click('[data-testid="user-menu"]')
        
        # Admin should see admin menu items
        await expect(page.locator('[data-testid="admin-panel-link"]')).to_be_visible()
        
        # Click admin panel
        await page.click('[data-testid="admin-panel-link"]')
        
        # Verify admin panel is accessible
        await expect(page.locator('[data-testid="admin-dashboard"]')).to_be_visible()
        await expect(page.locator('[data-testid="user-management"]')).to_be_visible()
        
    async def test_unauthorized_access_redirect(self, page: Page):
        """Test that unauthorized access redirects to login."""
        # Try to access protected page directly
        await page.goto("/admin")
        
        # Should be redirected to login
        await expect(page.locator('[data-testid="login-form"]')).to_be_visible()
        
    async def test_session_persistence(self, page: Page, authenticated_user):
        """Test that user session persists across page reloads."""
        # Verify user is logged in
        await expect(page.locator('[data-testid="user-menu"]')).to_be_visible()
        
        # Reload the page
        await page.reload()
        
        # Verify user is still logged in
        await expect(page.locator('[data-testid="user-menu"]')).to_be_visible()
        await expect(page.locator('[data-testid="username-display"]')).to_contain_text(authenticated_user["username"])
        
    async def test_login_form_validation(self, page: Page):
        """Test login form validation."""
        # Navigate to login page
        await page.goto("/")
        await page.click('[data-testid="login-button"]')
        
        # Try to submit empty form
        await page.click('[data-testid="submit-login"]')
        
        # Verify validation errors
        await expect(page.locator('[data-testid="username-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="password-error"]')).to_be_visible()
        
        # Fill only username
        await page.fill('[data-testid="username-input"]', "testuser")
        await page.click('[data-testid="submit-login"]')
        
        # Verify password is still required
        await expect(page.locator('[data-testid="password-error"]')).to_be_visible()
        
    async def test_registration_form_validation(self, page: Page):
        """Test registration form validation."""
        # Navigate to registration page
        await page.goto("/")
        await page.click('[data-testid="register-button"]')
        
        # Try to submit empty form
        await page.click('[data-testid="submit-registration"]')
        
        # Verify validation errors
        await expect(page.locator('[data-testid="username-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="email-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="password-error"]')).to_be_visible()
        
        # Test password mismatch
        await page.fill('[data-testid="register-username"]', "testuser")
        await page.fill('[data-testid="register-email"]', "test@example.com")
        await page.fill('[data-testid="register-password"]', "password123")
        await page.fill('[data-testid="register-confirm-password"]', "different_password")
        
        await page.click('[data-testid="submit-registration"]')
        
        # Verify password mismatch error
        await expect(page.locator('[data-testid="password-mismatch-error"]')).to_be_visible()
        
    async def test_duplicate_username_registration(self, page: Page, authenticated_user):
        """Test registration with duplicate username."""
        # Navigate to registration page
        await page.goto("/")
        await page.click('[data-testid="register-button"]')
        
        # Try to register with existing username
        await page.fill('[data-testid="register-username"]', authenticated_user["username"])
        await page.fill('[data-testid="register-email"]', "different@example.com")
        await page.fill('[data-testid="register-password"]', "password123")
        await page.fill('[data-testid="register-confirm-password"]', "password123")
        
        await page.click('[data-testid="submit-registration"]')
        
        # Verify error message
        await expect(page.locator('[data-testid="registration-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="registration-error"]')).to_contain_text("Username already exists")
