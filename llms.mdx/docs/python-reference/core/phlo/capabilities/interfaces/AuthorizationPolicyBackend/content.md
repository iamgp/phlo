# AuthorizationPolicyBackend (/docs/python-reference/core/phlo/capabilities/interfaces/AuthorizationPolicyBackend)



Protocol for authorization policy decision point (PDP) providers.

Functions [#functions]

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
        ...
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
        ...
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
        ...
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
