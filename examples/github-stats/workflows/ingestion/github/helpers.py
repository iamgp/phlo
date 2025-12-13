"""Helper functions to reduce GitHub API boilerplate in this project.

This is project-specific code to avoid repetition, not a phlo framework feature.
"""

from __future__ import annotations

import os
from typing import Any

from dlt.sources.rest_api import rest_api


def github_api(
    resource: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Helper to create DLT sources for GitHub API endpoints.

    Reduces repetition across GitHub ingestion workflows in this project.

    Args:
        resource: DLT resource name
        path: GitHub API path (can use {username} placeholder)
        params: Query parameters

    Returns:
        DLT rest_api source
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_username = os.getenv("GITHUB_USERNAME", "iamgp")

    # Replace {username} placeholder if present
    final_path = path.replace("{username}", github_username)

    return rest_api(
        client={
            "base_url": "https://api.github.com",
            # GitHub paginates most collection endpoints using the `Link` header.
            # Without this, we only fetch the first page (often 30/100 items).
            "paginator": "header_link",
            "headers": {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        },
        resources=[
            {
                "name": resource,
                "endpoint": {
                    "path": final_path,
                    "params": params or {},
                },
            }
        ],
    )
