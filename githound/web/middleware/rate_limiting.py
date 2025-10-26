"""
Rate limiting middleware for GitHound API.

Provides configurable rate limiting with Redis backend support.
"""

import os
import time
from collections.abc import Callable
from typing import Any

import redis
from redis import Redis
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
        client: Redis = redis.from_url(REDIS_URL, decode_responses=True)
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
            key_func=get_remote_address, storage_uri=REDIS_URL, default_limits=[DEFAULT_RATE_LIMIT]
        )
    else:
        # Use in-memory rate limiting
        limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_RATE_LIMIT])

    return limiter


def get_user_rate_limiter() -> Callable[[str], str]:
    """Get user-based rate limiter key function."""

    def user_key_func(user_id: str) -> str:
        return f"user:{user_id}"

    return user_key_func


def get_endpoint_rate_limiter() -> Callable[[str, str], str]:
    """Get endpoint-based rate limiter key function."""

    def endpoint_key_func(endpoint: str, user_id: str) -> str:
        return f"endpoint:{endpoint}:user:{user_id}"

    return endpoint_key_func


# Rate limit decorators for different endpoint types


def search_rate_limit() -> Any:
    """Rate limit decorator for search endpoints."""
    limiter = get_limiter()
    return limiter.limit(SEARCH_RATE_LIMIT)


def auth_rate_limit() -> Any:
    """Rate limit decorator for authentication endpoints."""
    limiter = get_limiter()
    return limiter.limit(AUTH_RATE_LIMIT)


def export_rate_limit() -> Any:
    """Rate limit decorator for export endpoints."""
    limiter = get_limiter()
    return limiter.limit(EXPORT_RATE_LIMIT)


def default_rate_limit() -> Any:
    """Rate limit decorator for general endpoints."""
    limiter = get_limiter()
    return limiter.limit(DEFAULT_RATE_LIMIT)


# Rate limiting utilities


class RateLimitConfig:
    """Rate limiting configuration."""

    def __init__(self) -> None:
        self.enabled = RATE_LIMIT_ENABLED
        self.redis_url = REDIS_URL
        self.default_limit = DEFAULT_RATE_LIMIT
        self.search_limit = SEARCH_RATE_LIMIT
        self.auth_limit = AUTH_RATE_LIMIT
        self.export_limit = EXPORT_RATE_LIMIT

    def get_limit_for_endpoint(self, endpoint_type: str) -> str:
        """Get rate limit for specific endpoint type."""
        limits = {
            "search": self.search_limit,
            "auth": self.auth_limit,
            "export": self.export_limit,
            "default": self.default_limit,
        }
        return limits.get(endpoint_type, self.default_limit)


def check_rate_limit_status(client_id: str, endpoint: str) -> dict[str, Any]:
    """Check current rate limit status for a client."""
    redis_client = get_redis_client()

    if not redis_client:
        return {
            "rate_limiting_enabled": False,
            "message": "Rate limiting disabled or Redis unavailable",
        }

    try:
        # Get current usage
        key = f"rate_limit:{endpoint}:{client_id}"
        current_usage: str | None = redis_client.get(key)  # type: ignore[assignment]
        ttl: int = redis_client.ttl(key)  # type: ignore[assignment]

        return {
            "rate_limiting_enabled": True,
            "endpoint": endpoint,
            "client_id": client_id,
            "current_usage": int(current_usage) if current_usage else 0,
            "ttl_seconds": ttl if ttl > 0 else 0,
            "limit_reset_time": time.time() + ttl if ttl > 0 else None,
        }

    except Exception as e:
        return {
            "rate_limiting_enabled": True,
            "error": f"Failed to check rate limit status: {str(e)}",
        }


def reset_rate_limit(client_id: str, endpoint: str) -> dict[str, Any]:
    """Reset rate limit for a specific client and endpoint."""
    redis_client = get_redis_client()

    if not redis_client:
        return {"success": False, "message": "Rate limiting disabled or Redis unavailable"}

    try:
        key = f"rate_limit:{endpoint}:{client_id}"
        redis_client.delete(key)

        return {
            "success": True,
            "message": f"Rate limit reset for {client_id} on {endpoint}",
            "endpoint": endpoint,
            "client_id": client_id,
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to reset rate limit: {str(e)}"}


# Global rate limiting configuration
rate_limit_config = RateLimitConfig()
