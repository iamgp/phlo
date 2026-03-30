# BranchManagerResource (/docs/python-reference/packages/phlo-nessie/phlo_nessie/resource/BranchManagerResource)



Convenience wrapper for cleaning up Nessie branches.

Provides high-level operations for managing pipeline branches,
filtering out system branches like 'main' and 'dev'.

Attributes [#attributes]

<PyAttribute name="&#x22;_nessie&#x22;" type="null" value="&#x22;nessie or NessieResource()&#x22;">
  Internal NessieResource instance.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, nessie=None)&#x22;">
  Initialize a branch manager.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > manager = BranchManagerResource()  # Uses default NessieResource
    > > > custom = BranchManagerResource(NessieResource("[http://custom:19120](http://custom:19120)"))
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, nessie: NessieResource | None = None):
        """Initialize a branch manager.

        Args:
            nessie: Optional Nessie client instance.
                If not provided, creates a new NessieResource.

        Example:
            >>> manager = BranchManagerResource()  # Uses default NessieResource
            >>> custom = BranchManagerResource(NessieResource("http://custom:19120"))

        """
        self._nessie = nessie or NessieResource()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;nessie&#x22;" type="&#x22;NessieResource | None&#x22;" value="&#x22;None&#x22;">
      Optional Nessie client instance.
      If not provided, creates a new NessieResource.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;get_all_pipeline_branches&#x22;" type="&#x22;(self) -> list[BranchInfo]&#x22;">
  Return non-system branches used for pipelines.

  Excludes 'main' and 'dev' branches which are considered
  system branches.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > manager = BranchManagerResource()
    > > > pipeline\_branches = manager.get\_all\_pipeline\_branches()
    > > > print(\[b.name for b in pipeline\_branches])
    > > > \['feature/analytics', 'feature/ml-pipeline']
  </Callout>

  <PySourceCode>
    ```python
    def get_all_pipeline_branches(self) -> list[BranchInfo]:
        """Return non-system branches used for pipelines.

        Excludes 'main' and 'dev' branches which are considered
        system branches.

        Returns:
            list[BranchInfo]: Branches excluding ``main`` and ``dev``.

        Example:
            >>> manager = BranchManagerResource()
            >>> pipeline_branches = manager.get_all_pipeline_branches()
            >>> print([b.name for b in pipeline_branches])
            ['feature/analytics', 'feature/ml-pipeline']

        """
        branches = self._nessie.list_branches()
        pipeline_branches = [branch for branch in branches if branch.name not in {"main", "dev"}]
        logger.info(
            "nessie_branch_manager_pipeline_branches_resolved",
            total_branch_count=len(branches),
            pipeline_branch_count=len(pipeline_branches),
        )
        return pipeline_branches
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[BranchInfo]: Branches excluding `main` and `dev`.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;cleanup_branch&#x22;" type="&#x22;(self, name) -> bool&#x22;">
  Delete a pipeline branch.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > manager = BranchManagerResource()
    > > > cleaned = manager.cleanup\_branch("feature/old-experiment")
    > > > True
  </Callout>

  <PySourceCode>
    ```python
    def cleanup_branch(self, name: str) -> bool:
        """Delete a pipeline branch.

        Args:
            name: Branch name.

        Returns:
            bool: ``True`` when cleanup succeeds, else ``False``.

        Example:
            >>> manager = BranchManagerResource()
            >>> cleaned = manager.cleanup_branch("feature/old-experiment")
            True

        """
        logger.info(
            "nessie_branch_manager_cleanup_requested",
            branch_name=name,
        )
        cleaned = self._nessie.delete_branch(name)
        logger.info(
            "nessie_branch_manager_cleanup_completed",
            branch_name=name,
            cleaned=cleaned,
        )
        return cleaned
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Branch name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    `True` when cleanup succeeds, else `False`.
  </PyFunctionReturn>
</PyFunction>
