"""Observatory API.

FastAPI routers for Observatory backend functionality.
These replace the TanStack Start server functions and enable
Observatory to run as a pure SPA with a Python backend.

This package provides endpoints for:
- Data exploration (Trino, Iceberg tables)
- Orchestration (Dagster integration)
- Data versioning (Nessie)
- Quality monitoring
- Log analysis (Loki)
- Lineage tracking
- Search and discovery
- Settings management

Example:
    Routers are auto-discovered and registered by main.py:

    .. code-block:: python

        from phlo_api.observatory_api.trino import router
        app.include_router(router, prefix="/api/trino")

"""
