# compiler (/docs/python-reference/core/phlo/rbac/compiler)



Governance backend compiler interface and implementations.

This module provides the base compiler interface for converting canonical
RBAC policies into backend-native artifacts.

<PyAttribute name="&#x22;COMPILER_REGISTRY&#x22;" type="&#x22;dict[str, type[GovernanceCompiler]]&#x22;" value="&#x22;{'trino': TrinoCompiler, 'postgresql': PostgreSQLCompiler, 'hasura': HasuraCompiler, 'minio': MinIOCompiler, 'nessie': NessieCompiler}&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;CompilerContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/CompilerContext&#x22;" />

      <Card title="&#x22;GovernanceCompiler&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/GovernanceCompiler&#x22;" />

      <Card title="&#x22;TrinoCompiler&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/TrinoCompiler&#x22;" />

      <Card title="&#x22;PostgreSQLCompiler&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/PostgreSQLCompiler&#x22;" />

      <Card title="&#x22;HasuraCompiler&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/HasuraCompiler&#x22;" />

      <Card title="&#x22;MinIOCompiler&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/MinIOCompiler&#x22;" />

      <Card title="&#x22;NessieCompiler&#x22;" href="&#x22;/docs/python-reference/core/phlo/rbac/compiler/NessieCompiler&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_compiler&#x22;" type="&#x22;(backend_name, backend=None) -> GovernanceCompiler | None&#x22;">
      Get a compiler instance for the specified backend.

      <PySourceCode>
        ```python
        def get_compiler(
            backend_name: str,
            backend: GovernanceBackend | None = None,
        ) -> GovernanceCompiler | None:
            """Get a compiler instance for the specified backend.

            Args:
                backend_name: Name of the backend.
                backend: Optional governance backend instance.

            Returns:
                Compiler instance or None if not found.
            """
            compiler_class = COMPILER_REGISTRY.get(backend_name)
            if compiler_class is None:
                return None
            return compiler_class(backend=backend)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;backend_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the backend.
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;GovernanceBackend | None&#x22;" value="&#x22;None&#x22;">
          Optional governance backend instance.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;GovernanceCompiler | None&#x22;">
        Compiler instance or None if not found.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
