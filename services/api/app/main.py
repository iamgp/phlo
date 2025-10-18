from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter
from app.routers import auth, glucose, iceberg, metadata, query

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

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(glucose.router, prefix=settings.api_prefix)
app.include_router(iceberg.router, prefix=settings.api_prefix)
app.include_router(query.router, prefix=settings.api_prefix)
app.include_router(metadata.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Cascade Lakehouse API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/v1/metadata/health",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


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
