"""
Authentication and authorization for GitHound API.

Provides JWT-based authentication with role-based access control.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class User(BaseModel):
    """User model."""
    user_id: str
    username: str
    email: str
    roles: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class UserCreate(BaseModel):
    """User creation model."""
    username: str
    email: str
    password: str
    roles: List[str] = ["user"]


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    roles: List[str]


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = []


class AuthManager:
    """Manages authentication and authorization."""

    def __init__(self) -> None:
        self.SECRET_KEY = SECRET_KEY
        self.ALGORITHM = ALGORITHM

        # In-memory user store (replace with database in production)
        self.users: Dict[str, Dict[str, Any]] = {
            "admin": {
                "user_id": "admin",
                "username": "admin",
                "email": "admin@githound.dev",
                "password_hash": self.hash_password("admin123"),
                "roles": ["admin", "user"],
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            },
            "user": {
                "user_id": "user",
                "username": "user",
                "email": "user@githound.dev",
                "password_hash": self.hash_password("user123"),
                "roles": ["user"],
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            }
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self.users.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user."""
        user = self.get_user(username)
        if not user:
            return None
        
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        if not user["is_active"]:
            return None
        
        # Update last login
        user["last_login"] = datetime.now()
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")
            roles = payload.get("roles", [])
            
            if user_id is None:
                return None
            
            return TokenData(user_id=user_id, username=username, roles=roles)
        
        except jwt.PyJWTError:
            return None
    
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user."""
        if user_data.username in self.users:
            raise ValueError(f"User {user_data.username} already exists")
        
        user = {
            "user_id": user_data.username,  # Simple ID for demo
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": self.hash_password(user_data.password),
            "roles": user_data.roles,
            "is_active": True,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        self.users[user_data.username] = user
        return user
    
    def login(self, login_data: UserLogin) -> Token:
        """Login a user and return a token."""
        user = self.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        access_token = self.create_access_token(
            data={
                "sub": user["user_id"],
                "username": user["username"],
                "roles": user["roles"]
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user_id=user["user_id"],
            roles=user["roles"]
        )
    
    def has_permission(self, user_roles: List[str], required_roles: List[str]) -> bool:
        """Check if user has required permissions."""
        if "admin" in user_roles:
            return True
        
        return any(role in user_roles for role in required_roles)


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = auth_manager.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        
        user = auth_manager.get_user(token_data.username)
        if user is None:
            raise credentials_exception
        
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "is_active": user["is_active"]
        }
    
    except Exception:
        raise credentials_exception


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user."""
    if not current_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_roles(required_roles: List[str]) -> Any:
    """Decorator to require specific roles."""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
        if not auth_manager.has_permission(current_user["roles"], required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


# Role-based dependencies
require_admin = require_roles(["admin"])
require_user = require_roles(["user", "admin"])
require_read_only = require_roles(["read_only", "user", "admin"])
