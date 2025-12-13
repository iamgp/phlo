# main.py - Main FastAPI application entry point for the Cascade Lakehouse REST API
# Configures the web service with authentication, routing, middleware, and monitoring
# Provides programmatic access to Iceberg tables and Postgres marts

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter
from app.routers import auth, glucose, iceberg, metadata, query

# --- Application Configuration ---
# FastAPI app setup with metadata, middleware, and routing
# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    REST API for Cascade Lakehouse data access.

    ## Features
    - JWT authentication (admin/analyst roles)
    - Cached responses for performance
    - Rate limiting
    - Query Iceberg tables via Trino
    - Fast access to Postgres marts
    - OpenAPI/Swagger documentation

    ## Authentication
    1. POST `/api/v1/auth/login` with username/password
    2. Use returned JWT token in `Authorization: Bearer <token>` header

    ## Default Users
    - **admin** / admin123 (full access)
    - **analyst** / analyst123 (read-only)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- Middleware Setup ---
# Configure middleware for security, monitoring, and performance
# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# --- Router Registration ---
# Register API route handlers for different endpoints
# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(glucose.router, prefix=settings.api_prefix)
app.include_router(iceberg.router, prefix=settings.api_prefix)
app.include_router(query.router, prefix=settings.api_prefix)
app.include_router(metadata.router, prefix=settings.api_prefix)


# --- API Endpoints ---
# Core API endpoints for service discovery and health checks
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Phlo Lakehouse API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/v1/metadata/health",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# --- Exception Handlers ---
# Global error handling for consistent API responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "path": request.url.path,
        },
    )
