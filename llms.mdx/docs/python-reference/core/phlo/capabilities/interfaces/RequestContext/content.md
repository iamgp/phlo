# RequestContext (/docs/python-reference/core/phlo/capabilities/interfaces/RequestContext)



Request-scoped input presented to the authentication provider.

This is a simple container that adapters can populate with request data
(headers, cookies, etc.) for the authentication provider to validate.

Attributes [#attributes]

<PyAttribute name="&#x22;headers&#x22;" type="null" value="&#x22;dict(headers) if headers else {}&#x22;" />

<PyAttribute name="&#x22;cookies&#x22;" type="null" value="&#x22;dict(cookies) if cookies else {}&#x22;" />

<PyAttribute name="&#x22;query_params&#x22;" type="null" value="&#x22;dict(query_params) if query_params else {}&#x22;" />

<PyAttribute name="&#x22;method&#x22;" type="null" value="&#x22;method&#x22;" />

<PyAttribute name="&#x22;path&#x22;" type="null" value="&#x22;path&#x22;" />

<PyAttribute name="&#x22;remote_addr&#x22;" type="null" value="&#x22;remote_addr&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, headers=None, cookies=None, query_params=None, method=None, path=None, remote_addr=None)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        headers: Mapping[str, str] | None = None,
        cookies: Mapping[str, str] | None = None,
        query_params: Mapping[str, str] | None = None,
        method: str | None = None,
        path: str | None = None,
        remote_addr: str | None = None,
    ):
        self.headers = dict(headers) if headers else {}
        self.cookies = dict(cookies) if cookies else {}
        self.query_params = dict(query_params) if query_params else {}
        self.method = method
        self.path = path
        self.remote_addr = remote_addr
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;headers&#x22;" type="&#x22;Mapping[str, str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;cookies&#x22;" type="&#x22;Mapping[str, str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;query_params&#x22;" type="&#x22;Mapping[str, str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;method&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;path&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;remote_addr&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
