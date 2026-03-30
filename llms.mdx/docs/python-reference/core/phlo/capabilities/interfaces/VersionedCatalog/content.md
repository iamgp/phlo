# VersionedCatalog (/docs/python-reference/core/phlo/capabilities/interfaces/VersionedCatalog)



Protocol for optional catalog/versioning providers.

Providers opt in when they support explicit branch lifecycle management
for versioned analytical storage.

Functions [#functions]

<PyFunction name="&#x22;list_branches&#x22;" type="&#x22;(self) -> list[Any]&#x22;">
  List known branch references.

  <PySourceCode>
    ```python
    def list_branches(self) -> list[Any]:
        """List known branch references."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_branch_hash&#x22;" type="&#x22;(self, name) -> str | None&#x22;">
  Resolve the current hash for a branch.

  <PySourceCode>
    ```python
    def get_branch_hash(self, name: str) -> str | None:
        """Resolve the current hash for a branch."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;create_branch&#x22;" type="&#x22;(self, name, from_ref='main') -> str | None&#x22;">
  Create a new branch from an existing reference.

  <PySourceCode>
    ```python
    def create_branch(self, name: str, from_ref: str = "main") -> str | None:
        """Create a new branch from an existing reference."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;from_ref&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;merge_branch&#x22;" type="&#x22;(self, source, target='main') -> bool&#x22;">
  Merge a source branch into a target branch.

  <PySourceCode>
    ```python
    def merge_branch(self, source: str, target: str = "main") -> bool:
        """Merge a source branch into a target branch."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;delete_branch&#x22;" type="&#x22;(self, name) -> bool&#x22;">
  Delete a branch reference.

  <PySourceCode>
    ```python
    def delete_branch(self, name: str) -> bool:
        """Delete a branch reference."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
