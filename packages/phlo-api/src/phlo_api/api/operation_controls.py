"""Controls for scoped operation routes: auth scopes, audit, rate limits, idempotency."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request

from phlo_api.api.authentication import get_request_principal

_TOKEN_CONFIG_ENV = "PHLO_API_TOKENS"
_DEFAULT_IDEMPOTENCY_RETENTION_HOURS = 24
_RATE_LIMITS: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def project_root() -> Path:
    return Path(os.environ.get("PHLO_PROJECT_PATH", ".")).resolve()


def require_scope(request: Request, required_scope: str) -> dict[str, Any]:
    """Require a bearer token with the requested scope or admin."""
    principal = get_request_principal(request)
    if principal is not None:
        scopes = _principal_scopes(principal.claims, principal.attributes, principal.groups)
        if required_scope in scopes or "admin" in scopes:
            return {"subject": principal.subject, "scopes": sorted(scopes)}
        raise HTTPException(
            status_code=403, detail={"error": "forbidden", "required_scope": required_scope}
        )

    token = _bearer_token(request)
    token_config = _load_token_config()
    token_data = token_config.get(token) if token else None
    if token_data is None:
        raise HTTPException(
            status_code=401, detail={"error": "unauthorized", "reason": "missing_or_invalid_token"}
        )

    scopes = _principal_scopes(
        token_data.get("claims", {}), token_data.get("attributes", {}), token_data.get("scopes", ())
    )
    if required_scope not in scopes and "admin" not in scopes:
        raise HTTPException(
            status_code=403, detail={"error": "forbidden", "required_scope": required_scope}
        )
    return {"subject": str(token_data.get("subject") or "token"), "scopes": sorted(scopes)}


def enforce_rate_limit(subject: str, operation: str) -> None:
    """Enforce a per-subject, per-operation token bucket."""
    limit = _operation_limit(operation)
    now = time.monotonic()
    bucket = _RATE_LIMITS[(subject, operation)]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=429, detail={"error": "rate_limited", "limit_per_minute": limit}
        )
    bucket.append(now)


def audit_operation(
    *,
    operation: str,
    target: str,
    dry_run: bool,
    auth: dict[str, Any],
    payload: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
) -> None:
    """Append an API-side mutation audit record."""
    audit_dir = project_root() / ".phlo" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "operations.jsonl"
    _rotate_audit_log(audit_path)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "surface": "phlo-api",
        "operation": operation,
        "target": target,
        "dry_run": dry_run,
        "subject": auth["subject"],
        "scopes": auth["scopes"],
        "payload": payload or {},
        "result": result or {},
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _rotate_audit_log(path: Path) -> None:
    max_bytes = int(os.environ.get("PHLO_API_AUDIT_MAX_BYTES", str(10 * 1024 * 1024)))
    max_files = int(os.environ.get("PHLO_API_AUDIT_MAX_FILES", "5"))
    if max_bytes <= 0 or max_files <= 0 or not path.exists() or path.stat().st_size < max_bytes:
        return
    oldest = path.with_name(f"{path.name}.{max_files}")
    if oldest.exists():
        oldest.unlink()
    for index in range(max_files - 1, 0, -1):
        candidate = path.with_name(f"{path.name}.{index}")
        if candidate.exists():
            candidate.replace(path.with_name(f"{path.name}.{index + 1}"))
    path.replace(path.with_name(f"{path.name}.1"))


def replay_or_execute(
    *,
    idempotency_key: str | None,
    operation: str,
    target: str,
    execute: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Return a previous idempotent response or execute and persist the new response."""
    if not idempotency_key:
        return execute()

    conn = _idempotency_connection()
    try:
        _delete_expired(conn)
        key_hash = _idempotency_hash(idempotency_key)
        existing = conn.execute(
            """
            SELECT response_json FROM operations
            WHERE project = ? AND key_hash = ? AND operation = ? AND target = ?
            """,
            (str(project_root()), key_hash, operation, target),
        ).fetchone()
        if existing:
            return json.loads(existing[0])

        response = execute()
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=_DEFAULT_IDEMPOTENCY_RETENTION_HOURS)
        conn.execute(
            """
            INSERT INTO operations(project, key_hash, operation, target, response_json, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(project_root()),
                key_hash,
                operation,
                target,
                json.dumps(response, sort_keys=True),
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        conn.commit()
        return response
    finally:
        conn.close()


async def replay_or_execute_async(
    *,
    idempotency_key: str | None,
    operation: str,
    target: str,
    execute: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    """Async variant of replay_or_execute."""
    if not idempotency_key:
        return await execute()

    existing = await asyncio.to_thread(
        _load_idempotent_response,
        idempotency_key=idempotency_key,
        operation=operation,
        target=target,
    )
    if existing is not None:
        return existing

    response = await execute()
    await asyncio.to_thread(
        _store_idempotent_response,
        idempotency_key=idempotency_key,
        operation=operation,
        target=target,
        response=response,
    )
    return response


def _load_idempotent_response(
    *, idempotency_key: str, operation: str, target: str
) -> dict[str, Any] | None:
    conn = _idempotency_connection()
    try:
        _delete_expired(conn)
        key_hash = _idempotency_hash(idempotency_key)
        existing = conn.execute(
            """
            SELECT response_json FROM operations
            WHERE project = ? AND key_hash = ? AND operation = ? AND target = ?
            """,
            (str(project_root()), key_hash, operation, target),
        ).fetchone()
        if existing:
            return json.loads(existing[0])
        return None
    finally:
        conn.close()


def _store_idempotent_response(
    *,
    idempotency_key: str,
    operation: str,
    target: str,
    response: dict[str, Any],
) -> None:
    conn = _idempotency_connection()
    try:
        key_hash = _idempotency_hash(idempotency_key)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=_DEFAULT_IDEMPOTENCY_RETENTION_HOURS)
        conn.execute(
            """
            INSERT INTO operations(project, key_hash, operation, target, response_json, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(project_root()),
                key_hash,
                operation,
                target,
                json.dumps(response, sort_keys=True),
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _principal_scopes(claims: dict[str, Any], attributes: dict[str, Any], groups: Any) -> set[str]:
    raw_scopes: list[Any] = []
    for source in (claims, attributes):
        raw_scopes.extend(_scope_values(source.get("scope")))
        raw_scopes.extend(_scope_values(source.get("scopes")))
    raw_scopes.extend(_scope_values(groups))
    return {str(scope) for scope in raw_scopes if str(scope).strip()}


def _scope_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item for item in value.replace(",", " ").split() if item]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    return header[7:]


def _load_token_config() -> dict[str, dict[str, Any]]:
    raw = os.environ.get(_TOKEN_CONFIG_ENV)
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail=f"{_TOKEN_CONFIG_ENV} must be a JSON object")
    return {str(key): value for key, value in payload.items() if isinstance(value, dict)}


def _operation_limit(operation: str) -> int:
    if operation in {"materialize_asset", "backfill_asset"}:
        return int(os.environ.get("PHLO_API_RATE_LIMIT_MATERIALIZE", "10"))
    if operation == "retry_failed_run":
        return int(os.environ.get("PHLO_API_RATE_LIMIT_RETRY", "30"))
    if operation == "cancel_run":
        return int(os.environ.get("PHLO_API_RATE_LIMIT_CANCEL", "60"))
    return int(os.environ.get("PHLO_API_RATE_LIMIT_MUTATION", "60"))


def _idempotency_connection() -> sqlite3.Connection:
    state_dir = project_root() / ".phlo" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(state_dir / "operations.sqlite")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operations(
            project TEXT NOT NULL,
            key_hash TEXT NOT NULL,
            operation TEXT NOT NULL,
            target TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            PRIMARY KEY(project, key_hash, operation, target)
        )
        """
    )
    return conn


def _delete_expired(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM operations WHERE expires_at < ?", (datetime.now(UTC).isoformat(),))
    conn.commit()


def _idempotency_hash(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
