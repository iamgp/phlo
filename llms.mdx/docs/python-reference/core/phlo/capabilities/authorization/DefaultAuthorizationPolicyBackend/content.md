# DefaultAuthorizationPolicyBackend (/docs/python-reference/core/phlo/capabilities/authorization/DefaultAuthorizationPolicyBackend)



Simple RBAC-backed authorization policy backend.

This provider implements basic role-based access control with pattern
matching for resource identifiers. It follows the decision semantics
from the spec:

* Explicit deny overrides explicit allow
* No matching rule means deny
* Provider failures fail closed

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, policies=None)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        policies: list[dict[str, Any]] | None = None,
    ):
        self._policies = self._parse_policies(policies or [])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policies&#x22;" type="&#x22;list[dict[str, Any]] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_parse_policies&#x22;" type="&#x22;(self, policy_configs) -> list[PolicyRule]&#x22;">
  Parse policy configuration into PolicyRule objects.

  <PySourceCode>
    ```python
    def _parse_policies(self, policy_configs: list[dict[str, Any]]) -> list[PolicyRule]:
        """Parse policy configuration into PolicyRule objects."""
        rules: list[PolicyRule] = []
        for config in policy_configs:
            effect = config.get("effect", "deny")
            principal = config.get("principal", {})
            resource = config.get("resource", {})

            rule = PolicyRule(
                policy_id=config.get("policy_id", "unknown"),
                effect=effect,
                principal_roles=tuple(principal.get("roles", [])),
                principal_attributes=principal.get("attributes", {}),
                action=config.get("action", "*"),
                resource_type=resource.get("type", "*"),
                resource_id_pattern=resource.get("id_pattern", "*"),
                resource_attributes=resource.get("attributes", {}),
            )
            rules.append(rule)
        return rules
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_configs&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.authorization.PolicyRule]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;is_allowed&#x22;" type="&#x22;(self, principal, action, resource, context=None) -> bool&#x22;">
  Check if an action is allowed.

  <PySourceCode>
    ```python
    def is_allowed(
        self,
        principal: Principal,
        action: str,
        resource: ResourceRef,
        context: DecisionContext | None = None,
    ) -> bool:
        """Check if an action is allowed."""
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
  Explain an authorization decision with full details.

  <PySourceCode>
    ```python
    def explain_decision(
        self,
        principal: Principal,
        action: str,
        resource: ResourceRef,
        context: DecisionContext | None = None,
    ) -> AuthorizationDecision:
        """Explain an authorization decision with full details."""
        try:
            matching_deny: AuthorizationDecision | None = None
            matching_allow: AuthorizationDecision | None = None

            for rule in self._policies:
                if self._rule_matches(rule, principal, action, resource):
                    if rule.effect == "deny":
                        matching_deny = AuthorizationDecision(
                            allowed=False,
                            reason_code="explicit_deny",
                            policy_id=rule.policy_id,
                            explanation=f"Matched deny rule {rule.policy_id}",
                        )
                        break
                    if rule.effect == "allow":
                        matching_allow = AuthorizationDecision(
                            allowed=True,
                            reason_code="explicit_allow",
                            policy_id=rule.policy_id,
                            explanation=f"Matched allow rule {rule.policy_id}",
                        )

            if matching_deny is not None:
                return matching_deny
            if matching_allow is not None:
                return matching_allow

            return AuthorizationDecision(
                allowed=False,
                reason_code="default_deny",
                policy_id=None,
                explanation="No matching policy rule",
            )
        except Exception:
            return AuthorizationDecision(
                allowed=False,
                reason_code="backend_unavailable",
                policy_id=None,
                explanation="Authorization backend failed",
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
  Filter resources to only those the principal can access.

  <PySourceCode>
    ```python
    def filter_resources(
        self,
        principal: Principal,
        resources: list[ResourceRef],
        action: str,
        context: DecisionContext | None = None,
    ) -> list[ResourceRef]:
        """Filter resources to only those the principal can access."""
        return [r for r in resources if self.is_allowed(principal, action, r, context)]
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

<PyFunction name="&#x22;_rule_matches&#x22;" type="&#x22;(self, rule, principal, action, resource) -> bool&#x22;">
  Check if a rule matches the given request.

  <PySourceCode>
    ```python
    def _rule_matches(
        self,
        rule: PolicyRule,
        principal: Principal,
        action: str,
        resource: ResourceRef,
    ) -> bool:
        """Check if a rule matches the given request."""
        if not self._action_matches(rule.action, action):
            return False

        if not self._resource_type_matches(rule.resource_type, resource.resource_type):
            return False

        if not self._resource_id_matches(rule.resource_id_pattern, resource.resource_id):
            return False

        if not self._principal_roles_match(rule.principal_roles, principal.roles):
            return False

        if not self._attributes_match(rule.principal_attributes, principal.attributes):
            return False

        return self._attributes_match(rule.resource_attributes, resource.attributes)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rule&#x22;" type="&#x22;PolicyRule&#x22;" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;Principal&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource&#x22;" type="&#x22;ResourceRef&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_action_matches&#x22;" type="&#x22;(self, rule_action, request_action) -> bool&#x22;">
  Check if action matches (supports wildcards).

  <PySourceCode>
    ```python
    def _action_matches(self, rule_action: str, request_action: str) -> bool:
        """Check if action matches (supports wildcards)."""
        if rule_action == "*":
            return True
        return fnmatch.fnmatch(request_action, rule_action)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rule_action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;request_action&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_resource_type_matches&#x22;" type="&#x22;(self, rule_type, request_type) -> bool&#x22;">
  Check if resource type matches (supports wildcards).

  <PySourceCode>
    ```python
    def _resource_type_matches(self, rule_type: str, request_type: str) -> bool:
        """Check if resource type matches (supports wildcards)."""
        if rule_type == "*":
            return True
        return fnmatch.fnmatch(request_type, rule_type)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rule_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;request_type&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_resource_id_matches&#x22;" type="&#x22;(self, pattern, resource_id) -> bool&#x22;">
  Check if resource ID matches pattern (supports wildcards).

  <PySourceCode>
    ```python
    def _resource_id_matches(self, pattern: str, resource_id: str) -> bool:
        """Check if resource ID matches pattern (supports wildcards)."""
        if pattern == "*":
            return True
        return fnmatch.fnmatch(resource_id, pattern)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;pattern&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource_id&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_principal_roles_match&#x22;" type="&#x22;(self, rule_roles, principal_roles) -> bool&#x22;">
  Check if principal roles match rule roles.

  <PySourceCode>
    ```python
    def _principal_roles_match(
        self,
        rule_roles: tuple[str, ...],
        principal_roles: tuple[str, ...],
    ) -> bool:
        """Check if principal roles match rule roles."""
        if not rule_roles:
            return True
        return any(role in principal_roles for role in rule_roles)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rule_roles&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

    <PyParameter name="&#x22;principal_roles&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_attributes_match&#x22;" type="&#x22;(self, rule_attrs, request_attrs) -> bool&#x22;">
  Check if attributes match.

  <PySourceCode>
    ```python
    def _attributes_match(
        self,
        rule_attrs: Mapping[str, str],
        request_attrs: Mapping[str, str],
    ) -> bool:
        """Check if attributes match."""
        for key, value in rule_attrs.items():
            if key not in request_attrs:
                return False
            if not fnmatch.fnmatch(request_attrs[key], value):
                return False
        return True
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rule_attrs&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />

    <PyParameter name="&#x22;request_attrs&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
