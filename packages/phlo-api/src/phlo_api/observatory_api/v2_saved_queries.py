"""Saved-query read model persistence for Observatory v2."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from uuid import uuid4

from fastapi import HTTPException

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import V2SavedQuery, V2SavedQueryRequest

READ_QUERY_RE = re.compile(
    r"^\s*select\s+\*\s+from\s+(?P<table>[A-Za-z0-9_.:-]+)(?:\s+limit\s+(?P<limit>\d+))?\s*;?\s*$",
    re.IGNORECASE,
)


def saved_queries_path(project_root: Path) -> Path:
    state_dir = project_root / ".phlo" / "observatory-v2"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "saved_queries.json"


def load_saved_queries(project_root: Path) -> list[V2SavedQuery]:
    path = saved_queries_path(project_root)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = payload.get("items") if isinstance(payload, Mapping) else None
    if not isinstance(items, list):
        return []
    queries: list[V2SavedQuery] = []
    for item in items:
        if isinstance(item, Mapping):
            try:
                queries.append(V2SavedQuery.model_validate(item))
            except Exception:
                continue
    return dedupe_saved_queries(queries)


def dedupe_saved_queries(queries: list[V2SavedQuery]) -> list[V2SavedQuery]:
    unique: dict[tuple[str, str, str], V2SavedQuery] = {}
    for query in sorted(queries, key=lambda item: item.updated_at, reverse=True):
        key = (
            query.name.strip().casefold(),
            " ".join(query.sql.split()).casefold(),
            (query.branch or "main").strip().casefold(),
        )
        unique.setdefault(key, query)
    return list(unique.values())


def write_saved_queries(project_root: Path, queries: list[V2SavedQuery]) -> None:
    saved_queries_path(project_root).write_text(
        json.dumps({"items": [query.model_dump() for query in queries]}, indent=2),
        encoding="utf-8",
    )


def save_query(project_root: Path, request: V2SavedQueryRequest) -> V2SavedQuery:
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Saved query name is required.")
    validate_error = validate_saved_query_sql(request.sql)
    if validate_error:
        raise HTTPException(status_code=400, detail=validate_error)

    now = datetime.now(UTC).isoformat()
    query = V2SavedQuery(
        id=f"query-{uuid4().hex[:12]}",
        name=request.name.strip(),
        sql=request.sql.strip(),
        branch=request.branch,
        created_at=now,
        updated_at=now,
        metadata=safe_metadata(request.metadata),
    )
    queries = dedupe_saved_queries([query, *load_saved_queries(project_root)])
    write_saved_queries(project_root, queries[:100])
    return query


def validate_saved_query_sql(sql: str) -> str | None:
    if READ_QUERY_RE.match(sql):
        return None
    return "Only simple SELECT preview queries can be saved."
