# SyncController (/docs/python-reference/core/phlo/rbac/sync/SyncController)



Controller for synchronizing canonical RBAC to backend-native enforcement.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, loader=None, compilers=None)&#x22;">
  Initialize the sync controller.

  <PySourceCode>
    ```python
    def __init__(
        self,
        loader: RBACConfigLoader | None = None,
        compilers: dict[str, GovernanceCompiler] | None = None,
    ):
        """Initialize the sync controller.

        Args:
            loader: RBAC config loader. Defaults to new loader with default path.
            compilers: Dict of backend name to compiler instance.
        """
        self._loader = loader or RBACConfigLoader()
        self._compilers = compilers or {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;loader&#x22;" type="&#x22;RBACConfigLoader | None&#x22;" value="&#x22;None&#x22;">
      RBAC config loader. Defaults to new loader with default path.
    </PyParameter>

    <PyParameter name="&#x22;compilers&#x22;" type="&#x22;dict[str, GovernanceCompiler] | None&#x22;" value="&#x22;None&#x22;">
      Dict of backend name to compiler instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;load_rbac&#x22;" type="&#x22;(self) -> CanonicalRBAC&#x22;">
  Load the canonical RBAC model.

  <PySourceCode>
    ```python
    def load_rbac(self) -> CanonicalRBAC:
        """Load the canonical RBAC model."""
        return self._loader.load()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.CanonicalRBAC&#x22;" />
</PyFunction>

<PyFunction name="&#x22;validate&#x22;" type="&#x22;(self) -> tuple[bool, list[str]]&#x22;">
  Validate the RBAC configuration.

  <PySourceCode>
    ```python
    def validate(self) -> tuple[bool, list[str]]:
        """Validate the RBAC configuration.

        Returns:
            Tuple of (is_valid, error_messages).
        """
        return self._loader.validate()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of (is\_valid, error\_messages).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;plan&#x22;" type="&#x22;(self, backends=None, environment='development') -> dict[str, SyncPlan]&#x22;">
  Create sync plans for specified backends.

  <PySourceCode>
    ```python
    def plan(
        self,
        backends: list[str] | None = None,
        environment: str = "development",
    ) -> dict[str, SyncPlan]:
        """Create sync plans for specified backends.

        Args:
            backends: List of backend names to plan for. Defaults to all registered.
            environment: Environment name for context.

        Returns:
            Dict of backend name to sync plan.
        """
        rbac = self.load_rbac()
        plans: dict[str, SyncPlan] = {}

        target_backends = backends or list(COMPILER_REGISTRY.keys())

        for backend_name in target_backends:
            compiler = self._get_or_create_compiler(backend_name)
            if compiler is None:
                logger.warning("compiler_not_found", backend=backend_name)
                continue

            context = CompilerContext(
                environment=environment,
                backend_name=backend_name,
            )

            try:
                plan = compiler.plan(rbac, context)
                plans[backend_name] = plan
                logger.info(
                    "sync_plan_created",
                    backend=backend_name,
                    changes=len(plan.changes),
                )
            except Exception as e:
                logger.error(
                    "sync_plan_failed",
                    backend=backend_name,
                    error=str(e),
                )

        return plans
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;backends&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of backend names to plan for. Defaults to all registered.
    </PyParameter>

    <PyParameter name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="&#x22;'development'&#x22;">
      Environment name for context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dict of backend name to sync plan.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;sync&#x22;" type="&#x22;(self, backends=None, environment='development', dry_run=False) -> dict[str, SyncResult]&#x22;">
  Synchronize RBAC to backends.

  <PySourceCode>
    ```python
    def sync(
        self,
        backends: list[str] | None = None,
        environment: str = "development",
        dry_run: bool = False,
    ) -> dict[str, SyncResult]:
        """Synchronize RBAC to backends.

        Args:
            backends: List of backend names to sync. Defaults to all registered.
            environment: Environment name for context.
            dry_run: If True, only plan without applying.

        Returns:
            Dict of backend name to sync result.
        """
        rbac = self.load_rbac()
        results: dict[str, SyncResult] = {}

        target_backends = backends or list(COMPILER_REGISTRY.keys())

        for backend_name in target_backends:
            compiler = self._get_or_create_compiler(backend_name)
            if compiler is None:
                logger.warning("compiler_not_found", backend=backend_name)
                continue

            context = CompilerContext(
                environment=environment,
                backend_name=backend_name,
                dry_run=dry_run,
            )

            try:
                plan = compiler.plan(rbac, context)

                if dry_run:
                    results[backend_name] = SyncResult(
                        success=True,
                        backend=backend_name,
                        version_hash=plan.version_hash,
                        applied_count=0,
                        failed_count=0,
                        errors=(),
                        revert_ids=(),
                    )
                    continue

                success_ids, errors = compiler.apply(plan, context)

                results[backend_name] = SyncResult(
                    success=len(errors) == 0,
                    backend=backend_name,
                    version_hash=plan.version_hash,
                    applied_count=len(success_ids),
                    failed_count=len(errors),
                    errors=tuple(errors),
                    revert_ids=tuple(success_ids),
                )

                logger.info(
                    "sync_completed",
                    backend=backend_name,
                    success=results[backend_name].success,
                    applied=results[backend_name].applied_count,
                    failed=results[backend_name].failed_count,
                )

            except Exception as e:
                logger.error(
                    "sync_failed",
                    backend=backend_name,
                    error=str(e),
                )
                results[backend_name] = SyncResult(
                    success=False,
                    backend=backend_name,
                    version_hash=rbac.version_hash or "",
                    applied_count=0,
                    failed_count=1,
                    errors=(str(e),),
                )

        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;backends&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of backend names to sync. Defaults to all registered.
    </PyParameter>

    <PyParameter name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="&#x22;'development'&#x22;">
      Environment name for context.
    </PyParameter>

    <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      If True, only plan without applying.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dict of backend name to sync result.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;verify&#x22;" type="&#x22;(self, backends=None, environment='development') -> dict[str, VerifyResult]&#x22;">
  Verify backend state matches desired state.

  <PySourceCode>
    ```python
    def verify(
        self,
        backends: list[str] | None = None,
        environment: str = "development",
    ) -> dict[str, VerifyResult]:
        """Verify backend state matches desired state.

        Args:
            backends: List of backend names to verify. Defaults to all registered.
            environment: Environment name for context.

        Returns:
            Dict of backend name to verify result.
        """
        rbac = self.load_rbac()
        results: dict[str, VerifyResult] = {}

        target_backends = backends or list(COMPILER_REGISTRY.keys())

        for backend_name in target_backends:
            compiler = self._get_or_create_compiler(backend_name)
            if compiler is None:
                logger.warning("compiler_not_found", backend=backend_name)
                continue

            context = CompilerContext(
                environment=environment,
                backend_name=backend_name,
            )

            try:
                result = compiler.verify(rbac, context)
                results[backend_name] = result

                logger.info(
                    "verify_completed",
                    backend=backend_name,
                    in_sync=result.in_sync,
                    missing=len(result.missing),
                    extra=len(result.extra),
                )

            except Exception as e:
                logger.error(
                    "verify_failed",
                    backend=backend_name,
                    error=str(e),
                )

        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;backends&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of backend names to verify. Defaults to all registered.
    </PyParameter>

    <PyParameter name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="&#x22;'development'&#x22;">
      Environment name for context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dict of backend name to verify result.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;revert&#x22;" type="&#x22;(self, revert_ids, backends=None, environment='development') -> dict[str, tuple[list[str], list[str]]]&#x22;">
  Revert previously applied changes.

  <PySourceCode>
    ```python
    def revert(
        self,
        revert_ids: list[str],
        backends: list[str] | None = None,
        environment: str = "development",
    ) -> dict[str, tuple[list[str], list[str]]]:
        """Revert previously applied changes.

        Args:
            revert_ids: List of revert IDs to undo.
            backends: List of backend names to revert. Defaults to all registered.
            environment: Environment name for context.

        Returns:
            Dict of backend name to (success_ids, errors) tuple.
        """
        results: dict[str, tuple[list[str], list[str]]] = {}

        target_backends = backends or list(COMPILER_REGISTRY.keys())

        for backend_name in target_backends:
            compiler = self._get_or_create_compiler(backend_name)
            if compiler is None:
                continue

            context = CompilerContext(
                environment=environment,
                backend_name=backend_name,
            )

            try:
                success_ids, errors = compiler.revert(revert_ids, context)
                results[backend_name] = (success_ids, errors)

                logger.info(
                    "revert_completed",
                    backend=backend_name,
                    success=len(success_ids),
                    errors=len(errors),
                )

            except Exception as e:
                logger.error(
                    "revert_failed",
                    backend=backend_name,
                    error=str(e),
                )
                results[backend_name] = ([], [str(e)])

        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;revert_ids&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of revert IDs to undo.
    </PyParameter>

    <PyParameter name="&#x22;backends&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of backend names to revert. Defaults to all registered.
    </PyParameter>

    <PyParameter name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="&#x22;'development'&#x22;">
      Environment name for context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dict of backend name to (success\_ids, errors) tuple.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_or_create_compiler&#x22;" type="&#x22;(self, backend_name) -> GovernanceCompiler | None&#x22;">
  Get or create a compiler for the specified backend.

  Looks up a registered governance backend from the capability registry
  and wires it to the compiler for actual enforcement.

  <PySourceCode>
    ```python
    def _get_or_create_compiler(
        self,
        backend_name: str,
    ) -> GovernanceCompiler | None:
        """Get or create a compiler for the specified backend.

        Looks up a registered governance backend from the capability registry
        and wires it to the compiler for actual enforcement.
        """
        if backend_name in self._compilers:
            return self._compilers[backend_name]

        from phlo.capabilities.registry import get_capability_registry
        from phlo.rbac.compiler import get_compiler

        registry = get_capability_registry()
        registered_backends = registry.list_governance_backends()

        backend_instance = None
        for spec in registered_backends:
            if spec.name == backend_name:
                backend_instance = spec.provider
                break

        compiler = get_compiler(backend_name, backend=backend_instance)
        if compiler:
            self._compilers[backend_name] = compiler

        return compiler
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;backend_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.compiler.GovernanceCompiler | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_available_backends&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List available backend names.

  <PySourceCode>
    ```python
    def list_available_backends(self) -> list[str]:
        """List available backend names."""
        return list(COMPILER_REGISTRY.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>
