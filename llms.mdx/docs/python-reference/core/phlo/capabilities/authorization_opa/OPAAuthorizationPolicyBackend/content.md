# OPAAuthorizationPolicyBackend (/docs/python-reference/core/phlo/capabilities/authorization_opa/OPAAuthorizationPolicyBackend)



Authorization policy backend backed by Open Policy Agent.

This provider sends authorization requests to an OPA server and translates
the response into the standard AuthorizationDecision format.

Expected OPA input format:
\{
"principal": \{"subject": "...", "type": "...", "roles": \[...]},
"action": "dataset.read",
"resource": \{"type": "...", "id": "..."},
"context": \{"environment": "...", ...}
}

Expected OPA policy (Rego):
package phlo.authz

default allow = false

allow \{
input.principal.roles\[\_] == "analyst"
input.action == "dataset.read"
input.resource.type == "dataset"
}

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, opa_url=None, opa_policy_package='phlo.authz', timeout_seconds=5.0)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        opa_url: str | None = None,
        opa_policy_package: str = "phlo.authz",
        timeout_seconds: float = 5.0,
    ):
        self._opa_url = opa_url or "http://localhost:8181"
        self._opa_policy_package = opa_policy_package
        self._timeout = timeout_seconds
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;opa_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;opa_policy_package&#x22;" type="&#x22;str&#x22;" value="&#x22;'phlo.authz'&#x22;" />

    <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;5.0&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;is_allowed&#x22;" type="&#x22;(self, principal, action, resource, context=None) -> bool&#x22;">
  Check if an action is allowed via OPA.

  <PySourceCode>
    ```python
    def is_allowed(
        self,
        principal: Principal,
        action: str,
        resource: ResourceRef,
        context: DecisionContext | None = None,
    ) -> bool:
        """Check if an action is allowed via OPA."""
        decision = self.explain_decision(principal, action, resource, context)
        return decision.allowed
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;Principal&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource&#x22;" type="&#x22;ResourceRef&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;DecisionContext | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;explain_decision&#x22;" type="&#x22;(self, principal, action, resource, context=None) -> AuthorizationDecision&#x22;">
  Explain an authorization decision via OPA.

  <PySourceCode>
    ```python
    def explain_decision(
        self,
        principal: Principal,
        action: str,
        resource: ResourceRef,
        context: DecisionContext | None = None,
    ) -> AuthorizationDecision:
        """Explain an authorization decision via OPA."""
        try:
            input_data = self._build_input(principal, action, resource, context)

            response = self._evaluate(input_data)

            if response is None:
                return AuthorizationDecision(
                    allowed=False,
                    reason_code="backend_unavailable",
                    explanation="OPA server returned no response",
                )

            result = response.get("result", {})

            if isinstance(result, bool):
                if result:
                    return AuthorizationDecision(
                        allowed=True,
                        reason_code="opa_allow",
                        explanation="OPA granted access",
                    )
                return AuthorizationDecision(
                    allowed=False,
                    reason_code="opa_deny",
                    explanation="OPA denied access",
                )

            allow = result.get("allow", False)
            if allow:
                return AuthorizationDecision(
                    allowed=True,
                    reason_code="opa_allow",
                    explanation=result.get("reason", "OPA granted access"),
                )

            return AuthorizationDecision(
                allowed=False,
                reason_code=result.get("reason_code", "opa_deny"),
                explanation=result.get("reason", "OPA denied access"),
            )

        except httpx.ConnectError:
            return AuthorizationDecision(
                allowed=False,
                reason_code="backend_unavailable",
                policy_id=None,
                explanation="Cannot connect to OPA server",
            )
        except httpx.TimeoutException:
            return AuthorizationDecision(
                allowed=False,
                reason_code="backend_unavailable",
                policy_id=None,
                explanation="OPA request timed out",
            )
        except Exception as e:
            return AuthorizationDecision(
                allowed=False,
                reason_code="backend_unavailable",
                policy_id=None,
                explanation=f"OPA evaluation failed: {e}",
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;Principal&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource&#x22;" type="&#x22;ResourceRef&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;DecisionContext | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthorizationDecision&#x22;" />
</PyFunction>

<PyFunction name="&#x22;filter_resources&#x22;" type="&#x22;(self, principal, resources, action, context=None) -> list[ResourceRef]&#x22;">
  Filter resources via OPA batch evaluation.

  <PySourceCode>
    ```python
    def filter_resources(
        self,
        principal: Principal,
        resources: list[ResourceRef],
        action: str,
        context: DecisionContext | None = None,
    ) -> list[ResourceRef]:
        """Filter resources via OPA batch evaluation."""
        allowed: list[ResourceRef] = []

        for resource in resources:
            if self.is_allowed(principal, action, resource, context):
                allowed.append(resource)

        return allowed
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;Principal&#x22;" value="null" />

    <PyParameter name="&#x22;resources&#x22;" type="&#x22;list[ResourceRef]&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;DecisionContext | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.ResourceRef]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;health_check&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check if OPA server is reachable.

  <PySourceCode>
    ```python
    def health_check(self) -> bool:
        """Check if OPA server is reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self._opa_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_build_input&#x22;" type="&#x22;(self, principal, action, resource, context) -> dict[str, Any]&#x22;">
  Build the OPA input document.

  <PySourceCode>
    ```python
    def _build_input(
        self,
        principal: Principal,
        action: str,
        resource: ResourceRef,
        context: DecisionContext | None,
    ) -> dict[str, Any]:
        """Build the OPA input document."""
        return {
            "principal": {
                "subject": principal.subject,
                "type": principal.principal_type,
                "roles": list(principal.roles),
                "attributes": dict(principal.attributes),
            },
            "action": action,
            "resource": {
                "type": resource.resource_type,
                "id": resource.resource_id,
                "tenant": resource.tenant,
                "attributes": dict(resource.attributes),
            },
            "context": {
                "environment": context.environment if context else None,
                "request_id": context.request_id if context else None,
                "ip_address": context.ip_address if context else None,
                "attributes": dict(context.attributes) if context else {},
            },
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;Principal&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource&#x22;" type="&#x22;ResourceRef&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;DecisionContext | None&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_evaluate&#x22;" type="&#x22;(self, input_data) -> dict[str, Any] | None&#x22;">
  Evaluate the input against OPA.

  <PySourceCode>
    ```python
    def _evaluate(self, input_data: dict[str, Any]) -> dict[str, Any] | None:
        """Evaluate the input against OPA."""
        url = f"{self._opa_url}/v1/data/{self._opa_policy_package.replace('.', '/')}"
        payload = {"input": input_data}

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload)

            if response.status_code != 200:
                return None

            return response.json()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;input_data&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any] | None&#x22;" />
</PyFunction>
