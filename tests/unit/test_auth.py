"""
Unit tests for authentication and authorization system.

Tests JWT token generation, validation, role-based access control,
and user management functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt

from githound.web.auth import (
    AuthManager, 
    Token, 
    TokenData, 
    UserCreate, 
    UserLogin,
    get_current_user,
    get_current_active_user,
    require_roles
)
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture
def auth_manager() -> None:
    """Create AuthManager instance for testing."""
    return AuthManager()


class TestAuthManager:
    """Test AuthManager class functionality."""
    
    def test_hash_password(self, auth_manager) -> None:
        """Test password hashing."""
        password = "test_password"
        hashed = auth_manager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_verify_password_correct(self, auth_manager) -> None:
        """Test password verification with correct password."""
        password = "test_password"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, auth_manager) -> None:
        """Test password verification with incorrect password."""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(wrong_password, hashed) is False
    
    def test_get_user_exists(self, auth_manager) -> None:
        """Test getting existing user."""
        user = auth_manager.get_user("admin")
        
        assert user is not None
        assert user["username"] == "admin"
        assert user["email"] == "admin@githound.dev"
        assert "admin" in user["roles"]
    
    def test_get_user_not_exists(self, auth_manager) -> None:
        """Test getting non-existent user."""
        user = auth_manager.get_user("nonexistent")
        assert user is None
    
    def test_authenticate_user_success(self, auth_manager) -> None:
        """Test successful user authentication."""
        user = auth_manager.authenticate_user("admin", "admin123")
        
        assert user is not None
        assert user["username"] == "admin"
        assert user["is_active"] is True
        assert user["last_login"] is not None
    
    def test_authenticate_user_wrong_password(self, auth_manager) -> None:
        """Test authentication with wrong password."""
        user = auth_manager.authenticate_user("admin", "wrong_password")
        assert user is None
    
    def test_authenticate_user_not_exists(self, auth_manager) -> None:
        """Test authentication with non-existent user."""
        user = auth_manager.authenticate_user("nonexistent", "password")
        assert user is None
    
    def test_create_access_token(self, auth_manager) -> None:
        """Test JWT token creation."""
        data = {"sub": "test_user", "username": "test_user", "roles": ["user"]}
        token = auth_manager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Verify token can be decoded
        decoded = jwt.decode(token, auth_manager.SECRET_KEY, algorithms=["HS256"])
        assert decoded["sub"] == "test_user"
        assert decoded["username"] == "test_user"
        assert decoded["roles"] == ["user"]
        assert "exp" in decoded
    
    def test_create_access_token_with_expiry(self, auth_manager) -> None:
        """Test JWT token creation with custom expiry."""
        data = {"sub": "test_user"}
        expires_delta = timedelta(minutes=30)
        token = auth_manager.create_access_token(data, expires_delta)
        
        decoded = jwt.decode(token, auth_manager.SECRET_KEY, algorithms=["HS256"])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        expected_time = datetime.utcnow() + expires_delta

        # Allow 1 minute tolerance
        assert abs((exp_time - expected_time).total_seconds()) < 60
    
    def test_verify_token_valid(self, auth_manager) -> None:
        """Test verification of valid token."""
        data = {"sub": "test_user", "username": "test_user", "roles": ["user"]}
        token = auth_manager.create_access_token(data)
        
        token_data = auth_manager.verify_token(token)
        
        assert token_data is not None
        assert token_data.user_id = = "test_user"
        assert token_data.username = = "test_user"
        assert token_data.roles = = ["user"]
    
    def test_verify_token_invalid(self, auth_manager) -> None:
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        token_data = auth_manager.verify_token(invalid_token)
        assert token_data is None
    
    def test_verify_token_expired(self, auth_manager) -> None:
        """Test verification of expired token."""
        data = {"sub": "test_user"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = auth_manager.create_access_token(data, expires_delta)
        
        token_data = auth_manager.verify_token(token)
        assert token_data is None
    
    def test_create_user_success(self, auth_manager) -> None:
        """Test successful user creation."""
        user_data = UserCreate(
            username="new_user",
            email="new@example.com",
            password="password123",
            roles=["user"]
        )
        
        user = auth_manager.create_user(user_data)
        
        assert user["username"] == "new_user"
        assert user["email"] == "new@example.com"
        assert user["roles"] == ["user"]
        assert user["is_active"] is True
        assert "password_hash" in user
        assert user["password_hash"] != "password123"  # Should be hashed
    
    def test_create_user_already_exists(self, auth_manager) -> None:
        """Test creating user that already exists."""
        user_data = UserCreate(
            username="admin",  # Already exists
            email="admin@example.com",
            password="password123"
        )
        
        with pytest.raises(ValueError, match="already exists"):
            auth_manager.create_user(user_data)
    
    def test_login_success(self, auth_manager) -> None:
        """Test successful login."""
        login_data = UserLogin(username="admin", password="admin123")
        token = auth_manager.login(login_data)
        
        assert isinstance(token, Token)
        assert token.token_type = = "bearer"
        assert token.user_id = = "admin"
        assert "admin" in token.roles
        assert len(token.access_token) > 50
        assert token.expires_in > 0
    
    def test_login_invalid_credentials(self, auth_manager) -> None:
        """Test login with invalid credentials."""
        login_data = UserLogin(username="admin", password="wrong_password")
        
        with pytest.raises(HTTPException) as exc_info:
            auth_manager.login(login_data)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in str(exc_info.value.detail)
    
    def test_has_permission_admin(self, auth_manager) -> None:
        """Test permission check for admin user."""
        user_roles = ["admin", "user"]
        required_roles = ["user"]
        
        assert auth_manager.has_permission(user_roles, required_roles) is True
    
    def test_has_permission_exact_match(self, auth_manager) -> None:
        """Test permission check with exact role match."""
        user_roles = ["user"]
        required_roles = ["user"]
        
        assert auth_manager.has_permission(user_roles, required_roles) is True
    
    def test_has_permission_multiple_roles(self, auth_manager) -> None:
        """Test permission check with multiple roles."""
        user_roles = ["user", "editor"]
        required_roles = ["editor", "admin"]
        
        assert auth_manager.has_permission(user_roles, required_roles) is True
    
    def test_has_permission_no_match(self, auth_manager) -> None:
        """Test permission check with no matching roles."""
        user_roles = ["read_only"]
        required_roles = ["user", "admin"]
        
        assert auth_manager.has_permission(user_roles, required_roles) is False


class TestAuthDependencies:
    """Test FastAPI authentication dependencies."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, auth_manager) -> None:
        """Test getting current user with valid token."""
        # Create a valid token
        token_data = auth_manager.create_access_token({
            "sub": "test_user",
            "username": "admin",
            "roles": ["admin", "user"]
        })
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token_data
        )
        
        with patch('githound.web.auth.auth_manager', auth_manager):
            user = await get_current_user(credentials)
            
            assert user["username"] == "admin"
            assert user["user_id"] == "admin"
            assert "admin" in user["roles"]
            assert user["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self) -> None:
        """Test getting current user with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self, auth_manager) -> None:
        """Test getting current active user."""
        current_user = {
            "user_id": "test_user",
            "username": "test_user",
            "is_active": True,
            "roles": ["user"]
        }
        
        user = await get_current_active_user(current_user)
        assert user == current_user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self) -> None:
        """Test getting inactive user."""
        current_user = {
            "user_id": "test_user",
            "username": "test_user",
            "is_active": False,
            "roles": ["user"]
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in str(exc_info.value.detail)
    
    def test_require_roles_decorator(self, auth_manager) -> None:
        """Test role requirement decorator."""
        require_admin = require_roles(["admin"])
        
        # Test with admin user
        admin_user = {
            "user_id": "admin",
            "username": "admin",
            "roles": ["admin", "user"],
            "is_active": True
        }
        
        with patch('githound.web.auth.auth_manager', auth_manager):
            result = require_admin(admin_user)
            assert result == admin_user
    
    def test_require_roles_insufficient_permissions(self, auth_manager) -> None:
        """Test role requirement with insufficient permissions."""
        require_admin = require_roles(["admin"])
        
        # Test with regular user
        regular_user = {
            "user_id": "user",
            "username": "user",
            "roles": ["user"],
            "is_active": True
        }
        
        with patch('githound.web.auth.auth_manager', auth_manager):
            with pytest.raises(HTTPException) as exc_info:
                require_admin(regular_user)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Insufficient permissions" in str(exc_info.value.detail)


class TestTokenData:
    """Test TokenData model."""
    
    def test_token_data_creation(self) -> None:
        """Test TokenData model creation."""
        token_data = TokenData(
            user_id="test_user",
            username="test_user",
            roles=["user", "editor"]
        )
        
        assert token_data.user_id = = "test_user"
        assert token_data.username = = "test_user"
        assert token_data.roles = = ["user", "editor"]
    
    def test_token_data_defaults(self) -> None:
        """Test TokenData model with default values."""
        token_data = TokenData()
        
        assert token_data.user_id is None
        assert token_data.username is None
        assert token_data.roles = = []


class TestUserModels:
    """Test user-related Pydantic models."""
    
    def test_user_create_model(self) -> None:
        """Test UserCreate model."""
        user_data = UserCreate(
            username="test_user",
            email="test@example.com",
            password="password123",
            roles=["user", "editor"]
        )
        
        assert user_data.username = = "test_user"
        assert user_data.email = = "test@example.com"
        assert user_data.password = = "password123"
        assert user_data.roles = = ["user", "editor"]
    
    def test_user_create_default_roles(self) -> None:
        """Test UserCreate model with default roles."""
        user_data = UserCreate(
            username="test_user",
            email="test@example.com",
            password="password123"
        )
        
        assert user_data.roles = = ["user"]
    
    def test_user_login_model(self) -> None:
        """Test UserLogin model."""
        login_data = UserLogin(
            username="test_user",
            password="password123"
        )
        
        assert login_data.username = = "test_user"
        assert login_data.password = = "password123"
    
    def test_token_model(self) -> None:
        """Test Token model."""
        token = Token(
            access_token="jwt.token.here",
            expires_in=3600,
            user_id="test_user",
            roles=["user"]
        )
        
        assert token.access_token = = "jwt.token.here"
        assert token.token_type = = "bearer"
        assert token.expires_in = = 3600
        assert token.user_id = = "test_user"
        assert token.roles = = ["user"]
