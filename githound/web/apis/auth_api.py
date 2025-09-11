"""
Authentication API endpoints for GitHound.

Provides user authentication, registration, and token management.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..middleware.rate_limiting import get_limiter
from ..models.api_models import ApiResponse
from ..models.auth_models import (
    PasswordChange,
    Token,
    User,
    UserCreate,
    UserLogin,
    UserProfile,
)
from ..services.auth_service import auth_manager, get_current_user, require_admin
from ..utils.validation import get_request_id

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])
limiter = get_limiter()


# Authentication Models
class LoginResponse(BaseModel):
    """Response for successful login."""
    token: Token = Field(..., description="Access token")
    user: UserProfile = Field(..., description="User profile")


class RegisterResponse(BaseModel):
    """Response for successful registration."""
    user: UserProfile = Field(..., description="Created user profile")
    message: str = Field(..., description="Success message")


# Authentication Endpoints

@router.post("/register", response_model=RegisterResponse)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    request_id: str = Depends(get_request_id)
) -> RegisterResponse:
    """
    Register a new user account.
    
    Creates a new user with the provided credentials.
    Rate limited to prevent abuse.
    """
    try:
        # Check if user already exists
        existing_user = auth_manager.get_user(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Create the user
        user_profile = auth_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            roles=user_data.roles
        )
        
        return RegisterResponse(
            user=user_profile,
            message="User registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login_user(
    request: Request,
    login_data: UserLogin,
    request_id: str = Depends(get_request_id)
) -> LoginResponse:
    """
    Authenticate user and return access token.
    
    Validates credentials and returns JWT token for API access.
    """
    try:
        # Authenticate user
        token = auth_manager.authenticate_user(
            username=login_data.username,
            password=login_data.password
        )
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Get user profile
        user_data = auth_manager.get_user(login_data.username)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user_profile = UserProfile(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            roles=user_data["roles"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            last_login=user_data.get("last_login")
        )
        
        return LoginResponse(
            token=token,
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate user: {str(e)}"
        )


@router.get("/profile", response_model=UserProfile)
@limiter.limit("30/minute")
async def get_user_profile(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
) -> UserProfile:
    """
    Get current user profile.
    
    Returns detailed information about the authenticated user.
    """
    try:
        return UserProfile(
            user_id=current_user["user_id"],
            username=current_user["username"],
            email=current_user["email"],
            roles=current_user["roles"],
            is_active=current_user["is_active"],
            created_at=current_user["created_at"],
            last_login=current_user.get("last_login")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.put("/profile", response_model=ApiResponse)
@limiter.limit("10/minute")
async def update_user_profile(
    request: Request,
    profile_updates: dict[str, Any],
    current_user: dict[str, Any] = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Update user profile information.
    
    Allows users to update their profile data.
    """
    try:
        # Update user profile
        success = auth_manager.update_user(
            user_id=current_user["user_id"],
            updates=profile_updates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
        
        return ApiResponse(
            success=True,
            message="Profile updated successfully",
            data={"user_id": current_user["user_id"]},
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/change-password", response_model=ApiResponse)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: dict[str, Any] = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Change user password.
    
    Allows users to change their password with current password verification.
    """
    try:
        # Verify new password confirmation
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match"
            )
        
        # Change password
        success = auth_manager.change_password(
            username=current_user["username"],
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return ApiResponse(
            success=True,
            message="Password changed successfully",
            data={"user_id": current_user["user_id"]},
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
) -> Token:
    """
    Refresh access token.
    
    Issues a new access token for the authenticated user.
    """
    try:
        # Generate new token
        token = auth_manager.create_access_token(
            user_id=current_user["user_id"],
            username=current_user["username"],
            roles=current_user["roles"]
        )
        
        return token
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh token: {str(e)}"
        )


# Admin Endpoints

@router.get("/users", response_model=ApiResponse)
@limiter.limit("20/minute")
async def list_users(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    List all users (admin only).
    
    Returns a list of all registered users.
    """
    try:
        users = auth_manager.list_users()
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(users)} users",
            data={"users": users, "total_count": len(users)},
            request_id=request_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=ApiResponse)
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: str,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Delete a user (admin only).
    
    Permanently removes a user account.
    """
    try:
        # Prevent self-deletion
        if user_id == current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        success = auth_manager.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ApiResponse(
            success=True,
            message="User deleted successfully",
            data={"user_id": user_id},
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
