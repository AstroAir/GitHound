"""
Authentication service for GitHound API.

Provides JWT-based authentication with role-based access control.
"""

import os
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-in-production")
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
    roles: list[str]
    is_active: bool = True
    created_at: datetime
    last_login: datetime | None = None


class UserCreate(BaseModel):
    """User creation model."""
    username: str
    email: str
    password: str
    roles: list[str] = ["user"]


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    roles: list[str]


class AuthManager:
    """Manages authentication and authorization."""

    def __init__(self) -> None:
        self.users: dict[str, dict[str, Any]] = {}
        self.active_tokens: set[str] = set()

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        self.active_tokens.add(encoded_jwt)
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            if token not in self.active_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            self.active_tokens.discard(token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        if user_data.username in self.users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        user_id = f"user_{len(self.users) + 1}"
        hashed_password = self.hash_password(user_data.password)
        
        user_dict = {
            "user_id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": hashed_password,
            "roles": user_data.roles,
            "is_active": True,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        self.users[user_data.username] = user_dict
        
        return User(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            roles=user_data.roles,
            created_at=user_dict["created_at"]
        )

    def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user with username and password."""
        user_dict = self.users.get(username)
        if not user_dict:
            return None
        
        if not self.verify_password(password, user_dict["password_hash"]):
            return None
        
        if not user_dict["is_active"]:
            return None
        
        # Update last login
        user_dict["last_login"] = datetime.now()
        
        return User(
            user_id=user_dict["user_id"],
            username=user_dict["username"],
            email=user_dict["email"],
            roles=user_dict["roles"],
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
            last_login=user_dict["last_login"]
        )

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        for user_dict in self.users.values():
            if user_dict["user_id"] == user_id:
                return User(
                    user_id=user_dict["user_id"],
                    username=user_dict["username"],
                    email=user_dict["email"],
                    roles=user_dict["roles"],
                    is_active=user_dict["is_active"],
                    created_at=user_dict["created_at"],
                    last_login=user_dict["last_login"]
                )
        return None

    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self.active_tokens:
            self.active_tokens.remove(token)
            return True
        return False

    def login(self, login_data: UserLogin) -> Token:
        """Login a user and return a token."""
        user = self.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        access_token = self.create_access_token(
            data={"sub": user.user_id, "username": user.username, "roles": user.roles},
            expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user_id=user.user_id,
            roles=user.roles
        )


# Global auth manager instance
auth_manager = AuthManager()


# Dependency functions

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, Any]:
    """Get the current authenticated user."""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = auth_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "roles": user.roles,
        "is_active": user.is_active
    }


def require_roles(required_roles: list[str]):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        
        return current_user
    
    return role_checker


# Common role dependencies
require_user = require_roles(["user", "admin"])
require_admin = require_roles(["admin"])


# Optional authentication (for public endpoints with optional auth)
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict[str, Any] | None:
    """Get the current user if authenticated, otherwise return None."""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
