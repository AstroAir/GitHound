"""
Main FastAPI application for GitHound.

Consolidates all API components into a single, unified application.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .apis.analysis_api import router as analysis_router
from .apis.search_api import router as search_router
from .middleware.rate_limiting import get_limiter
from .models.api_models import ApiResponse, HealthResponse
from .services.auth_service import Token, UserCreate, UserLogin, auth_manager
from .utils.validation import get_request_id


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    print("🚀 GitHound API starting up...")
    
    # Initialize components
    try:
        # Test rate limiting
        limiter = get_limiter()
        print("✅ Rate limiting initialized")
        
        # Initialize search orchestrator
        from .core.search_orchestrator import create_search_orchestrator
        orchestrator = create_search_orchestrator()
        print("✅ Search orchestrator initialized")
        
        print("🎉 GitHound API startup complete!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("👋 GitHound API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="GitHound API",
    description="""
    Comprehensive Git repository analysis and search API.
    
    ## Features
    
    ### 🔍 Advanced Search
    - Multi-modal search across commits, content, authors, and messages
    - Fuzzy search with configurable similarity thresholds
    - File and directory pattern matching
    - Historical code search across repository timeline
    - Real-time search progress via WebSocket
    
    ### 📊 Git Analysis
    - Git blame with line-by-line authorship tracking
    - Diff analysis between commits, branches, and files
    - Merge conflict detection and resolution assistance
    - Repository statistics and contributor analysis
    - File history tracking
    
    ### 🔗 Integration Features
    - Export capabilities (JSON, YAML, CSV formats)
    - Webhook support for repository events
    - Batch operations for multiple repositories
    - Real-time updates via WebSocket connections
    
    ### 🔐 Security & Performance
    - JWT-based authentication with role-based access control
    - Configurable rate limiting with Redis backend
    - Comprehensive error handling and validation
    - Async operations for optimal performance
    """,
    version="1.0.0",
    contact={
        "name": "GitHound Team",
        "url": "https://github.com/your-org/githound",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add rate limiting error handler
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": {"error_type": type(exc).__name__},
            "request_id": getattr(request.state, "request_id", None),
            "timestamp": time.time()
        }
    )

# Include API routers
from .apis.auth_api import router as auth_router
from .apis.integration_api import router as integration_router
from .apis.repository_api import router as repository_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(repository_router, prefix="/api/v1")
app.include_router(integration_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="githound/web/static"), name="static")

# Root endpoints

@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """API root endpoint with basic information."""
    return {
        "name": "GitHound API",
        "version": "1.0.0",
        "description": "Comprehensive Git repository analysis and search API",
        "documentation": "/docs",
        "health_check": "/health",
        "authentication": "/auth/login",
        "features": [
            "Advanced Search",
            "Git Analysis", 
            "Integration Features",
            "Security & Performance"
        ]
    }

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """API health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=time.time(),  # This would be actual uptime in production
        active_searches=0,  # This would be actual count in production
        system_info={
            "python_version": "3.11+",
            "fastapi_version": "0.100+",
            "features_enabled": [
                "search",
                "analysis",
                "authentication",
                "rate_limiting"
            ]
        }
    )

# Authentication endpoints

@app.post("/auth/register", response_model=ApiResponse, tags=["authentication"])
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    request_id: str = get_request_id()
) -> ApiResponse:
    """Register a new user."""
    try:
        user = auth_manager.create_user(user_data)
        
        return ApiResponse(
            success=True,
            message="User registered successfully",
            data={
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles
            },
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=Token, tags=["authentication"])
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: UserLogin
) -> Token:
    """Login and receive an access token."""
    try:
        token = auth_manager.login(login_data)
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/auth/logout", response_model=ApiResponse, tags=["authentication"])
async def logout(
    request: Request,
    request_id: str = get_request_id()
) -> ApiResponse:
    """Logout and revoke the access token."""
    # In a real implementation, you would extract the token from the request
    # and revoke it. For now, this is a placeholder.
    
    return ApiResponse(
        success=True,
        message="Logged out successfully",
        data={"message": "Token revoked"},
        request_id=request_id
    )

# API Information endpoint

@app.get("/api/info", response_model=ApiResponse, tags=["information"])
async def api_info(request_id: str = get_request_id()) -> ApiResponse:
    """Get comprehensive API information."""
    return ApiResponse(
        success=True,
        message="API information retrieved",
        data={
            "name": "GitHound API",
            "version": "1.0.0",
            "description": "Comprehensive Git repository analysis and search API",
            "endpoints": {
                "search": "Advanced search capabilities",
                "analysis": "Git analysis and statistics",
                "auth": "Authentication and authorization"
            },
            "authentication": "JWT Bearer token",
            "rate_limits": "Configurable per endpoint",
            "supported_formats": ["JSON"],
            "documentation": {
                "openapi": "/openapi.json",
                "swagger": "/docs",
                "redoc": "/redoc"
            }
        },
        request_id=request_id
    )

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next) -> Any:
    """Add request ID to all requests."""
    request.state.request_id = get_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response
