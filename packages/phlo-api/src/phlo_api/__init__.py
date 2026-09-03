"""Phlo REST API package.

This package provides the FastAPI-based REST API service for Phlo,
exposing platform internals to the Observatory web application.

Modules:
    main: FastAPI application and core endpoints.
    plugin: Service plugin registration for phlo-api.
    api: Platform API routers (authentication, authorization, maintenance, observability).
    observatory_api: Observatory-specific API routers (Dagster, Trino, Nessie, etc.).

Example:
    To start the API server locally:

    .. code-block:: python

        from phlo_api.main import app
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=4000)

"""
