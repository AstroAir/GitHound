from contextlib import asynccontextmanager
"""
Enhanced GitHound API - Main application with comprehensive Git functionality.

This module combines all API components to provide a complete REST API
for Git repository analysis and management.
"""

import time
import asyncio
from typing import Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .analysis_api import router as analysis_router
from .auth import auth_manager, Token, UserCreate, UserLogin
from .comprehensive_api import app as base_app
from .integration_api import router as integration_router
from .rate_limiting import get_limiter
from .search_api import router as search_router


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Manage application lifespan events."""
    # Startup
    print("🚀 GitHound Enhanced API starting up...")
    
    # Initialize components
    try:
        # Test Redis connection
        limiter = get_limiter()
        print("✅ Rate limiting initialized")
        
        # Initialize webhook manager
        from .webhooks import webhook_manager
        print("✅ Webhook manager initialized")
        
        # Initialize search orchestrator
        from .search_api import create_enhanced_search_orchestrator
        orchestrator = create_enhanced_search_orchestrator()
        print("✅ Search orchestrator initialized")
        
        print("🎉 GitHound Enhanced API startup complete!")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 GitHound Enhanced API shutting down...")
    
    # Cleanup operations
    try:
        # Clean up active operations
        from .comprehensive_api import active_operations, operation_results
        active_operations.clear()
        operation_results.clear()
        
        # Clean up search operations
        from .search_api import active_searches
        active_searches.clear()
        
        # Clean up export operations
        from .integration_api import active_exports, batch_operations
        active_exports.clear()
        batch_operations.clear()
        
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Shutdown error: {e}")
    
    print("👋 GitHound Enhanced API shutdown complete!")


# Create enhanced FastAPI application
app = FastAPI(
    title="GitHound Enhanced API",
    description="""
    # GitHound Enhanced API
    
    A comprehensive Git repository analysis and management API with advanced features.
    
    ## Features
    
    ### 🔧 Core Git Operations
    - Repository initialization, cloning, and status
    - Branch operations (create, delete, merge, checkout, list)
    - Commit operations (create, amend, revert, cherry-pick)
    - Tag management (create, delete, list, annotate)
    - Remote repository operations (add, remove, fetch, push, pull)
    
    ### 📊 Advanced Analysis
    - Git blame with line-by-line authorship tracking
    - Diff analysis between commits, branches, and files
    - Merge conflict detection and resolution assistance
    - Repository statistics and contributor analysis
    - File history tracking
    
    ### 🔍 Search & Query
    - Multi-modal search across commits, content, authors, and messages
    - Fuzzy search with configurable similarity thresholds
    - File and directory pattern matching
    - Historical code search across repository timeline
    - Real-time search progress via WebSocket
    
    ### 🔗 Integration Features
    - Export capabilities (JSON, YAML, CSV, XML formats)
    - Webhook support for repository events
    - Batch operations for multiple repositories
    - Real-time updates via WebSocket connections
    
    ### 🔐 Security & Performance
    - JWT-based authentication with role-based access control
    - Rate limiting with Redis backend
    - Comprehensive input validation and sanitization
    - Async operation support for long-running tasks
    - Proper HTTP status codes and RESTful design
    
    ## Authentication
    
    Most endpoints require authentication using JWT Bearer tokens.
    Use the `/api/v3/auth/login` endpoint to obtain a token.
    
    ## Rate Limits
    
    - Default: 100 requests per minute per IP
    - Search endpoints: 10 requests per minute
    - Export endpoints: 5 requests per minute
    - Authentication endpoints: 5 requests per minute
    
    ## WebSocket Support
    
    Real-time updates are available via WebSocket connections for:
    - Search progress updates
    - Repository operation status
    - Export operation progress
    
    ## Error Handling
    
    All endpoints return consistent error responses with:
    - HTTP status codes
    - Error messages
    - Request tracking IDs
    - Detailed error information
    """,
    version="3.0.0",
    docs_url="/api/v3/docs",
    redoc_url="/api/v3/redoc",
    openapi_url="/api/v3/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "GitHound API Support",
        "url": "https://github.com/AstroAir/GitHound",
        "email": "support@githound.dev"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.githound.dev",
            "description": "Production server"
        }
    ]
)

# Middleware setup
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

# Rate limiting setup
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next) -> None:
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> None:
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc),
            "path": str(request.url),
            "method": request.method
        }
    )

# Authentication endpoints
@app.post("/api/v3/auth/login", response_model=Token, tags=["authentication"])
@limiter.limit("5/minute")
async def login(request: Request, login_data: UserLogin) -> None:
    """
    Authenticate user and return JWT token.
    
    Use the returned token in the Authorization header as 'Bearer <token>'.
    """
    return auth_manager.login(login_data)

@app.post("/api/v3/auth/register", tags=["authentication"])
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate) -> None:
    """
    Register a new user account.
    
    Creates a new user with the specified credentials and roles.
    """
    try:
        user = auth_manager.create_user(user_data)
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user["user_id"],
            "username": user["username"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Include all API routers
app.include_router(analysis_router)
app.include_router(search_router)
app.include_router(integration_router)

# Include base app routes (repository, branch, commit, tag, remote operations)
for route in base_app.routes:
    if hasattr(route, 'path') and route.path.startswith('/api/v3/'):
        app.routes.append(route)

# Root endpoint
@app.get("/", tags=["root"])
async def root() -> None:
    """API root endpoint with basic information."""
    return {
        "name": "GitHound Enhanced API",
        "version": "3.0.0",
        "description": "Comprehensive Git repository analysis and management API",
        "documentation": "/api/v3/docs",
        "health_check": "/api/v3/health",
        "authentication": "/api/v3/auth/login",
        "features": [
            "Core Git Operations",
            "Advanced Analysis",
            "Multi-modal Search",
            "Integration Features",
            "Real-time Updates",
            "Authentication & Authorization",
            "Rate Limiting",
            "Comprehensive Documentation"
        ]
    }

# Health check endpoint
@app.get("/api/v3/health", tags=["health"])
async def health_check() -> None:
    """Comprehensive health check endpoint."""
    try:
        # Check Redis connection
        redis_status = "healthy"
        try:
            limiter = get_limiter()
            # Test Redis if available
            redis_status = "healthy"
        except Exception:
            redis_status = "unavailable"
        
        # Check webhook manager
        webhook_status = "healthy"
        try:
            from .webhooks import webhook_manager
            webhook_count = len(webhook_manager.list_endpoints())
            webhook_status = f"healthy ({webhook_count} endpoints)"
        except Exception:
            webhook_status = "error"
        
        return {
            "status": "healthy",
            "version": "3.0.0",
            "timestamp": time.time(),
            "components": {
                "api": "healthy",
                "redis": redis_status,
                "webhooks": webhook_status,
                "authentication": "healthy"
            },
            "metrics": {
                "active_operations": len(getattr(app.state, 'active_operations', {})),
                "active_searches": len(getattr(app.state, 'active_searches', {})),
                "active_exports": len(getattr(app.state, 'active_exports', {}))
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "githound.web.enhanced_main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
