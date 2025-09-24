"""Middleware components for GitHound web interface.

This module contains FastAPI middleware components that provide cross-cutting
concerns for the GitHound web application, including security, logging,
rate limiting, and request/response processing.

Key Middleware:
    - AuthenticationMiddleware: JWT token validation and user context
    - RateLimitingMiddleware: Redis-backed rate limiting with configurable rules
    - LoggingMiddleware: Structured request/response logging with correlation IDs
    - SecurityMiddleware: Security headers, CORS, and content security policy
    - ErrorHandlingMiddleware: Centralized error handling and response formatting
    - MetricsMiddleware: Performance metrics collection and monitoring

These middleware components are automatically applied to all API routes
and provide consistent behavior across the entire web application.
"""
