# AuthenticatedSession (/docs/python-reference/core/phlo/capabilities/interfaces/AuthenticatedSession)



Validated auth state associated with a caller.

Attributes [#attributes]

<PyAttribute name="&#x22;principal&#x22;" type="&#x22;AuthPrincipal&#x22;" value="null" />

<PyAttribute name="&#x22;auth_method&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;provider_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;session_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;expires_at&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;issued_at&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;attributes&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, principal, auth_method, provider_name, session_id=None, expires_at=None, issued_at=None, attributes=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;AuthPrincipal&#x22;" value="null" />

    <PyParameter name="&#x22;auth_method&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;provider_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;session_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;expires_at&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;issued_at&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;attributes&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
