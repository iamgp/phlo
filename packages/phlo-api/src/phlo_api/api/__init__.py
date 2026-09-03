"""Platform API routers exposed by phlo-api.

This package contains core platform API routers for authentication,
authorization, maintenance, and observability operations.

Modules:
    authentication: Authentication provider integration for FastAPI.
    authorization: Authorization and permission checking.
    maintenance: Iceberg maintenance observability endpoints.
    observability: Platform health and metrics endpoints.

Example:
    Routers from this package are automatically registered by main.py:

    .. code-block:: python

        from phlo_api.api.maintenance import router as maintenance_router
        app.include_router(maintenance_router, prefix="/api/maintenance")

"""
