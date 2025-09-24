"""Authentication models for GitHound API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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


class TokenData(BaseModel):
    """Token data model."""

    user_id: str | None = None
    username: str | None = None
    roles: list[str] = []


class UserProfile(BaseModel):
    """User profile model."""

    user_id: str
    username: str
    email: str
    roles: list[str]
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None
    profile_data: dict[str, Any] = Field(default_factory=dict)


class PasswordChange(BaseModel):
    """Password change model."""

    current_password: str
    new_password: str
    confirm_password: str


class PasswordReset(BaseModel):
    """Password reset model."""

    email: str


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""

    token: str
    new_password: str
    confirm_password: str


class RoleAssignment(BaseModel):
    """Role assignment model."""

    user_id: str
    roles: list[str]


class Permission(BaseModel):
    """Permission model."""

    name: str
    description: str
    resource: str
    action: str


class Role(BaseModel):
    """Role model."""

    name: str
    description: str
    permissions: list[Permission]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
