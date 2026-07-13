"""Tests for the shipped Dagster webserver enforcement boundary."""

from pathlib import Path
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from dagster_graphql.schema import create_schema
from dagster_webserver.webserver import DagsterWebserver
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from phlo_dagster.authorization import validate_graphql_schema
from phlo_dagster.authorization_middleware import DagsterGraphQLAuthorizationMiddleware
from phlo_dagster.webserver import (
    GRAPHQL_WS_INIT_TIMEOUT_ENV,
    GraphQLWebSocketAuthenticationASGI,
    PhloDagsterWebserver,
)
from _oidc_test_helpers import (
    AUDIENCE,
    ISSUER,
    JWKS_URL,
    JWKSResponse,
    key_and_jwks,
    token,
)


def _websocket(
    headers: dict[str, str],
    *,
    connection_init: dict[str, object] | None = None,
    host: str = "127.0.0.1",
) -> SimpleNamespace:
    return SimpleNamespace(
        headers=headers,
        client=SimpleNamespace(host=host),
        path="/graphql",
        scope={"phlo_graphql_connection_init": connection_init}
        if connection_init is not None
        else {},
    )


def test_installed_dagster_schema_is_fully_classified() -> None:
    validate_graphql_schema(create_schema().graphql_schema)


def test_shipped_webserver_builds_authorization_middleware() -> None:
    server = object.__new__(PhloDagsterWebserver)
    server._graphene_schema = create_schema()

    middleware = server.build_graphql_middleware()

    assert len(middleware) == 1
    assert isinstance(middleware[0], DagsterGraphQLAuthorizationMiddleware)


def test_service_entrypoint_uses_secured_webserver_module() -> None:
    service_yaml = Path(__file__).parents[1] / "src" / "phlo_dagster" / "service.yaml"
    text = service_yaml.read_text()

    assert '"phlo_dagster.webserver"' in text
    assert '"dagster-webserver"' not in text.split("command:", 1)[1].split("ports:", 1)[0]


def test_ordinary_generated_dagster_service_keeps_oidc_optional(monkeypatch) -> None:
    service_yaml = Path(__file__).parents[1] / "src" / "phlo_dagster" / "service.yaml"
    text = service_yaml.read_text()

    monkeypatch.delenv("PHLO_DAGSTER_OIDC_REQUIRED", raising=False)
    assert not PhloDagsterWebserver._oidc_required()
    assert "PHLO_DAGSTER_OIDC_REQUIRED:-false" in text


def test_regulated_dagster_startup_fails_without_complete_oidc(monkeypatch) -> None:
    for name in (
        "PHLO_DAGSTER_OIDC_ISSUER",
        "PHLO_DAGSTER_OIDC_AUDIENCE",
        "PHLO_DAGSTER_OIDC_JWKS_URL",
        "PHLO_DAGSTER_OIDC_CA_FILE",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_REQUIRED", "true")
    server = object.__new__(PhloDagsterWebserver)
    server._graphene_schema = create_schema()

    with pytest.raises(RuntimeError, match="OIDC identity is required"):
        server.build_graphql_middleware()


def test_server_info_route_binds_to_phlo_readiness_override(monkeypatch) -> None:
    server = object.__new__(PhloDagsterWebserver)
    server._app_path_prefix = None
    monkeypatch.setattr(server, "build_static_routes", lambda: [])

    routes = server.build_routes()
    server_info = next(route for route in routes if route.path == "/server_info")

    assert server_info.endpoint.__self__ is server
    assert server_info.endpoint.__func__ is PhloDagsterWebserver.webserver_info_endpoint


def test_dagster_cli_factory_instantiates_phlo_webserver(monkeypatch) -> None:
    import dagster_webserver.app as dagster_app

    marker = object()
    monkeypatch.setattr(dagster_app.check, "inst_param", lambda *args, **kwargs: None)
    monkeypatch.setattr(dagster_app, "warn_if_compute_logs_disabled", lambda: None)
    monkeypatch.setattr(dagster_app, "log_workspace_stats", lambda *args, **kwargs: None)
    monkeypatch.setattr(PhloDagsterWebserver, "create_asgi_app", lambda self, **kwargs: marker)

    result = dagster_app.create_app_from_workspace_process_context(
        SimpleNamespace(instance=SimpleNamespace())
    )

    assert dagster_app.DagsterWebserver is PhloDagsterWebserver
    assert result is marker


def test_graphql_ws_requires_authenticated_human(monkeypatch) -> None:
    monkeypatch.delenv("PHLO_DAGSTER_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("PHLO_DAGSTER_OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("PHLO_DAGSTER_OIDC_JWKS_URL", raising=False)
    server = object.__new__(PhloDagsterWebserver)

    result = asyncio.run(
        server.execute_graphql_subscription(
            _websocket({}),
            "1",
            "subscription Logs { pipelineRunLogs { __typename } }",
            None,
            "Logs",
        )
    )

    assert result[0] is None
    assert result[1]["extensions"]["code"] == "UNAUTHENTICATED"


def test_graphql_ws_verified_oidc_human_can_pass_or_is_denied_by_policy(monkeypatch) -> None:
    private_key, jwks = key_and_jwks()
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setattr(
        "phlo_dagster.oidc_identity.httpx.stream",
        lambda *_args, **_kwargs: JWKSResponse(jwks),
    )
    server = object.__new__(PhloDagsterWebserver)
    accepted = MagicMock(allowed=True, reason_code=None)

    async def fake_super(*_args, **_kwargs):
        return "started", None

    with patch("phlo_dagster.authorization_middleware.enforce", return_value=accepted):
        with patch.object(
            DagsterWebserver,
            "execute_graphql_subscription",
            new=fake_super,
        ):
            result = asyncio.run(
                server.execute_graphql_subscription(
                    _websocket({"X-Auth-Request-Access-Token": token(private_key)}),
                    "1",
                    "subscription Logs { pipelineRunLogs { __typename } }",
                    None,
                    "Logs",
                )
            )
    assert result == ("started", None)

    with patch(
        "phlo_dagster.authorization_middleware.enforce",
        return_value=MagicMock(allowed=False, reason_code="default_deny"),
    ):
        result = asyncio.run(
            server.execute_graphql_subscription(
                _websocket({"X-Auth-Request-Access-Token": token(private_key)}),
                "1",
                "subscription Logs { pipelineRunLogs { __typename } }",
                None,
                "Logs",
            )
        )
    assert result[0] is None
    assert result[1]["extensions"]["code"] == "FORBIDDEN"


def test_graphql_ws_connection_init_requires_access_token_field(monkeypatch) -> None:
    private_key, jwks = key_and_jwks()
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setattr(
        "phlo_dagster.oidc_identity.httpx.stream",
        lambda *_args, **_kwargs: JWKSResponse(jwks),
    )
    server = object.__new__(PhloDagsterWebserver)

    result = asyncio.run(
        server.execute_graphql_subscription(
            _websocket(
                {"X-Auth-Request-User": "forged"},
                connection_init={"token": token(private_key)},
            ),
            "1",
            "subscription Logs { pipelineRunLogs { __typename } }",
            None,
            "Logs",
        )
    )

    assert result[0] is None
    assert result[1]["extensions"]["code"] == "UNAUTHENTICATED"


def test_graphql_ws_asgi_protocol_authenticates_connection_init(monkeypatch) -> None:
    private_key, jwks = key_and_jwks()
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setattr(
        "phlo_dagster.oidc_identity.httpx.stream",
        lambda *_args, **_kwargs: JWKSResponse(jwks),
    )
    middleware = DagsterGraphQLAuthorizationMiddleware()

    async def endpoint(websocket):  # noqa: ANN001
        await websocket.receive()
        await websocket.accept(subprotocol="graphql-ws")
        init = await websocket.receive_json()
        assert init["type"] == "connection_init"
        await websocket.send_json({"type": "connection_ack"})
        await websocket.close()

    downstream = Starlette(routes=[WebSocketRoute("/graphql", endpoint)])
    asgi = GraphQLWebSocketAuthenticationASGI(downstream, middleware)

    with TestClient(asgi) as client:
        with client.websocket_connect("/graphql", subprotocols=["graphql-ws"]) as websocket:
            websocket.send_json(
                {"type": "connection_init", "payload": {"access_token": token(private_key)}}
            )
            assert websocket.accepted_subprotocol == "graphql-ws"
            assert websocket.receive_json() == {"type": "connection_ack"}


def _websocket_downstream():
    async def endpoint(websocket):  # noqa: ANN001
        await websocket.receive()
        await websocket.accept(subprotocol="graphql-ws")
        await websocket.receive_json()
        await websocket.send_json({"type": "connection_ack"})
        await websocket.close()

    return Starlette(routes=[WebSocketRoute("/graphql", endpoint)])


@pytest.mark.parametrize("offered", [None, ["graphql-transport-ws"]])
def test_graphql_ws_rejects_missing_or_unsupported_subprotocol(offered) -> None:
    asgi = GraphQLWebSocketAuthenticationASGI(
        _websocket_downstream(), DagsterGraphQLAuthorizationMiddleware()
    )

    with TestClient(asgi) as client:
        with pytest.raises(WebSocketDisconnect) as error:
            if offered is None:
                with client.websocket_connect("/graphql"):
                    pass
            else:
                with client.websocket_connect("/graphql", subprotocols=offered):
                    pass

    assert error.value.code == 4406


def test_graphql_ws_invalid_connection_init_token_closes_unauthenticated(monkeypatch) -> None:
    asgi = GraphQLWebSocketAuthenticationASGI(
        _websocket_downstream(), DagsterGraphQLAuthorizationMiddleware()
    )

    with TestClient(asgi) as client:
        with client.websocket_connect("/graphql", subprotocols=["graphql-ws"]) as websocket:
            websocket.send_json({"type": "connection_init", "payload": {"access_token": "invalid"}})
            error = websocket.receive()

    assert error == {"type": "websocket.close", "code": 4401}


def test_graphql_ws_idle_connection_init_times_out(monkeypatch) -> None:
    monkeypatch.setenv(GRAPHQL_WS_INIT_TIMEOUT_ENV, "0.05")
    asgi = GraphQLWebSocketAuthenticationASGI(
        _websocket_downstream(), DagsterGraphQLAuthorizationMiddleware()
    )

    with TestClient(asgi) as client:
        with client.websocket_connect("/graphql", subprotocols=["graphql-ws"]) as websocket:
            error = websocket.receive()

    assert error == {"type": "websocket.close", "code": 4408}


def test_graphql_ws_timeout_configuration_is_bounded(monkeypatch) -> None:
    monkeypatch.setenv(GRAPHQL_WS_INIT_TIMEOUT_ENV, "61")

    with pytest.raises(ValueError, match=GRAPHQL_WS_INIT_TIMEOUT_ENV):
        GraphQLWebSocketAuthenticationASGI(
            _websocket_downstream(), DagsterGraphQLAuthorizationMiddleware()
        )


def test_server_info_readiness_tracks_expired_jwks_refresh(monkeypatch) -> None:
    private_key, jwks = key_and_jwks()
    del private_key
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_REQUIRED", "true")
    responses = [JWKSResponse(jwks)]

    def stream(*_args, **_kwargs):  # noqa: ANN001, ANN202
        if responses:
            return responses.pop(0)
        raise httpx.HTTPError("JWKS unavailable")

    monkeypatch.setattr("phlo_dagster.oidc_identity.httpx.stream", stream)
    server = object.__new__(PhloDagsterWebserver)
    middleware = server._get_graphql_authorization_middleware()

    healthy = asyncio.run(server.webserver_info_endpoint(None))
    middleware._oidc_validator._keys_fetched_at = 0
    unhealthy = asyncio.run(server.webserver_info_endpoint(None))

    assert healthy.status_code == 200
    assert unhealthy.status_code == 503
    assert unhealthy.body == b'{"status":"unhealthy","reason":"oidc_unready"}'
