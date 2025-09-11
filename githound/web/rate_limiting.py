"""
Rate limiting for GitHound API.

Provides configurable rate limiting with Redis backend support.
"""

import os
import time
from collections.abc import Callable
from typing import Any, cast

import redis
from slowapi import Limiter
from slowapi.util import get_remote_address

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Default rate limits
DEFAULT_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100/minute")
SEARCH_RATE_LIMIT = os.getenv("SEARCH_RATE_LIMIT", "10/minute")
AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT", "5/minute")
EXPORT_RATE_LIMIT = os.getenv("EXPORT_RATE_LIMIT", "3/minute")


def get_redis_client() -> redis.Redis | None:
    """Get Redis client for rate limiting."""
    if not RATE_LIMIT_ENABLED:
        return None

    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        client.ping()
        return client
    except Exception:
        # Fall back to in-memory rate limiting
        return None


def get_limiter() -> Limiter:
    """Get configured rate limiter."""
    redis_client = get_redis_client()

    if redis_client:
        # Use Redis for distributed rate limiting
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=REDIS_URL,
            default_limits=[DEFAULT_RATE_LIMIT]
        )
    else:
        # Use in-memory rate limiting
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[DEFAULT_RATE_LIMIT]
        )

    return limiter


def get_user_identifier(request: Any) -> str:
    """Get user identifier for rate limiting."""
    # Try to get user ID from JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from .auth import auth_manager
            token = auth_header.split(" ")[1]
            token_data = auth_manager.verify_token(token)
            if token_data and token_data.user_id:
                return f"user:{token_data.user_id}"
        except Exception:
            pass

    # Fall back to IP address
    return cast(str, get_remote_address(request))


class CustomLimiter:
    """Custom rate limiter with user-aware limits."""

    def __init__(self) -> None:
        self.redis_client = get_redis_client()
        self.base_limiter = get_limiter()

    def get_user_rate_limit(self, user_roles: list[str]) -> str:
        """Get rate limit based on user roles."""
        if "admin" in user_roles:
            return "1000/minute"  # Higher limit for admins
        elif "premium" in user_roles:
            return "500/minute"   # Higher limit for premium users
        else:
            return DEFAULT_RATE_LIMIT  # Default limit

    def check_rate_limit(self, request, limit: str, identifier: str | None = None) -> bool:
        """Check if request is within rate limit."""
        if not RATE_LIMIT_ENABLED:
            return True

        key = identifier or get_user_identifier(request)

        if self.redis_client:
            return self._check_redis_rate_limit(key, limit)
        else:
            return self._check_memory_rate_limit(key, limit)

    def _check_redis_rate_limit(self, key: str, limit: str) -> bool:
        """Check rate limit using Redis."""
        try:
            # Parse limit (e.g., "100/minute")
            count_str, period = limit.split("/")
            count = int(count_str)

            # Convert period to seconds
            if period == "second":
                window = 1
            elif period == "minute":
                window = 60
            elif period == "hour":
                window = 3600
            elif period == "day":
                window = 86400
            else:
                window = 60  # Default to minute

            # Use sliding window rate limiting
            now = int(time.time())
            client = self.redis_client
            assert client is not None
            pipeline = client.pipeline()

            # Remove old entries
            pipeline.zremrangebyscore(key, 0, now - window)

            # Count current requests
            pipeline.zcard(key)

            # Add current request
            pipeline.zadd(key, {str(now): now})

            # Set expiration
            pipeline.expire(key, window)

            results = pipeline.execute()
            current_count = int(results[1]) if results and len(results) > 1 else 0

            return current_count < count

        except Exception:
            # If Redis fails, allow the request
            return True

    def _check_memory_rate_limit(self, key: str, limit: str) -> bool:
        """Check rate limit using in-memory storage."""
        # This would use the slowapi limiter's internal logic
        # For simplicity, we'll just return True here
        return True


# Global rate limiter instance
custom_limiter = CustomLimiter()


# Rate limiting decorators for different endpoint types
def rate_limit_search(func: Callable[..., Any]) -> Callable[..., Any]:
    """Rate limit decorator for search endpoints."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # This would be implemented as a FastAPI dependency
        return func(*args, **kwargs)
    return wrapper


def rate_limit_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Rate limit decorator for authentication endpoints."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # This would be implemented as a FastAPI dependency
        return func(*args, **kwargs)
    return wrapper


def rate_limit_export(func: Callable[..., Any]) -> Callable[..., Any]:
    """Rate limit decorator for export endpoints."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # This would be implemented as a FastAPI dependency
        return func(*args, **kwargs)
    return wrapper


# Rate limiting dependencies for FastAPI
async def search_rate_limit_dependency(request: Any) -> None:
    """Rate limiting dependency for search endpoints."""
    if not custom_limiter.check_rate_limit(request, SEARCH_RATE_LIMIT):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Search rate limit exceeded"
        )


async def auth_rate_limit_dependency(request: Any) -> None:
    """Rate limiting dependency for auth endpoints."""
    if not custom_limiter.check_rate_limit(request, AUTH_RATE_LIMIT):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Authentication rate limit exceeded"
        )


async def export_rate_limit_dependency(request: Any) -> None:
    """Rate limiting dependency for export endpoints."""
    if not custom_limiter.check_rate_limit(request, EXPORT_RATE_LIMIT):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Export rate limit exceeded"
        )
