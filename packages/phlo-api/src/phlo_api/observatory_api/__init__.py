"""Observatory API.

FastAPI routers for Observatory backend functionality.
These replace the TanStack Start server functions and enable
Observatory to run as a pure SPA with a Python backend.

This package provides the provider-neutral Observatory API.

Example:
    Routers are auto-discovered and registered by main.py:

    .. code-block:: python

        from phlo_api.observatory_api.observatory import router
        app.include_router(router, prefix="/api/observatory")

"""
