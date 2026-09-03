"""Polaris management API client.

Wraps the Apache Polaris management REST API (catalog, principal, and grant
administration) plus a health probe. Used by the bootstrap hook, the CLI, and
the security readiness inspector. Requests authenticate with the bootstrap
principal over HTTP basic auth, matching Polaris's management API contract.
"""

from __future__ import annotations

from typing import Any

import requests

from phlo.logging import get_logger
from phlo_polaris.settings import PolarisSettings, get_settings

logger = get_logger(__name__)

REQUEST_TIMEOUT_SECONDS = 15


class PolarisResource:
    """HTTP client for the Polaris management API."""

    def __init__(self, settings: PolarisSettings | None = None) -> None:
        self._settings = settings

    @property
    def settings(self) -> PolarisSettings:
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def _auth(self) -> tuple[str, str]:
        client_id, _, client_secret = self.settings.polaris_root_credentials.partition(":")
        return client_id, client_secret

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        url = f"{self.settings.polaris_api_uri()}{path}"
        response = requests.request(
            method,
            url,
            auth=self._auth(),
            json=json_body,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        logger.debug(
            "polaris_api_request",
            method=method,
            path=path,
            status_code=response.status_code,
        )
        return response

    def health_check(self) -> bool:
        """Return whether the Polaris service responds on its health endpoint."""
        try:
            response = requests.get(
                f"{self.settings.polaris_api_uri()}/q/health",
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException:
            logger.warning("polaris_health_check_failed", exc_info=True)
            return False
        return response.status_code == 200

    def list_catalogs(self) -> list[dict[str, Any]]:
        """List catalogs registered in Polaris."""
        response = self._request("GET", "/api/manager/v1/catalogs")
        response.raise_for_status()
        return list(response.json().get("catalogs", []))

    def get_catalog(self, name: str) -> dict[str, Any] | None:
        """Return one catalog by name, or None when absent."""
        response = self._request("GET", f"/api/manager/v1/catalogs/{name}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return dict(response.json())

    def create_catalog(self, *, name: str, warehouse: str) -> dict[str, Any]:
        """Create an internal Polaris catalog backed by the S3 warehouse."""
        payload = {
            "catalogName": name,
            "catalogType": "INTERNAL",
            "defaultBaseLocation": warehouse,
            "properties": {},
            "storageConfigInfo": {
                "storageType": "S3",
                "roleArn": "",
                "externalId": "",
                "userArn": "",
                "allowedLocations": [warehouse],
            },
        }
        response = self._request("POST", "/api/manager/v1/catalogs", json_body=payload)
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Polaris catalog creation failed for {name!r}: "
                f"{response.status_code} {response.text[:200]}"
            )
        return dict(response.json())

    def list_principals(self) -> list[dict[str, Any]]:
        """List service principals registered in Polaris."""
        response = self._request("GET", "/api/manager/v1/principals")
        response.raise_for_status()
        return list(response.json().get("principals", []))

    def create_principal(self, *, name: str) -> dict[str, Any]:
        """Create a service principal and return its client credentials."""
        response = self._request(
            "POST", "/api/manager/v1/principals", json_body={"principalName": name}
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Polaris principal creation failed for {name!r}: "
                f"{response.status_code} {response.text[:200]}"
            )
        return dict(response.json())

    def grant_catalog_privilege(self, *, principal: str, privilege: str) -> bool:
        """Grant one catalog-level privilege to a principal."""
        response = self._request(
            "PUT",
            f"/api/manager/v1/catalogs/{self.settings.polaris_catalog}/grants/{principal}",
            json_body={"privilege": privilege},
        )
        if response.status_code in (200, 201):
            return True
        logger.warning(
            "polaris_grant_failed",
            principal=principal,
            privilege=privilege,
            status_code=response.status_code,
        )
        return False

    def bootstrap_grants(self) -> dict[str, list[str]]:
        """Grant the standard Phlo writer/reader privilege sets.

        The writer manages catalog content and writes table data; the reader
        lists and reads. Privilege names follow the pinned Polaris release and
        are re-validated by the compatibility pass.
        """
        writer_privileges = [
            "CATALOG_MANAGE_CONTENT",
            "CATALOG_MANAGE_METADATA",
            "CATALOG_MANAGE_ACCESS",
            "TABLE_WRITE_DATA",
            "TABLE_READ_DATA",
            "TABLE_LIST",
            "TABLE_READ_PROPERTIES",
        ]
        reader_privileges = [
            "TABLE_READ_DATA",
            "TABLE_LIST",
            "TABLE_READ_PROPERTIES",
            "VIEW_LIST",
        ]
        grants: dict[str, list[str]] = {
            self.settings.polaris_writer_client_id: [],
            self.settings.polaris_reader_client_id: [],
        }
        for principal, privileges in (
            (self.settings.polaris_writer_client_id, writer_privileges),
            (self.settings.polaris_reader_client_id, reader_privileges),
        ):
            for privilege in privileges:
                if self.grant_catalog_privilege(principal=principal, privilege=privilege):
                    grants[principal].append(privilege)
        return grants
