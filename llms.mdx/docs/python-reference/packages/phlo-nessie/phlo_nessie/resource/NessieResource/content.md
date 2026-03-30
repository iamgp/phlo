# NessieResource (/docs/python-reference/packages/phlo-nessie/phlo_nessie/resource/NessieResource)



Lightweight Nessie REST client.

Provides low-level Nessie API operations with automatic retry logic
for transient failures. Supports branch management operations including
list, create, delete, and merge.

Attributes [#attributes]

<PyAttribute name="&#x22;base_url&#x22;" type="null" value="&#x22;base_url.rstrip('/')&#x22;">
  Full Nessie base URL including host and port.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, base_url=None)&#x22;">
  Initialize a Nessie client.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nessie = NessieResource()  # Uses default settings
    > > > nessie = NessieResource("[http://custom:19120](http://custom:19120)")  # Explicit URL
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, base_url: str | None = None):
        """Initialize a Nessie client.

        Args:
            base_url: Optional explicit Nessie base URL.
                If not provided, uses settings from configuration.

        Example:
            >>> nessie = NessieResource()  # Uses default settings
            >>> nessie = NessieResource("http://custom:19120")  # Explicit URL

        """
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            settings = get_settings()
            self.base_url = f"http://{settings.nessie_host}:{settings.nessie_port}"
        logger.debug(
            "nessie_resource_initialized",
            base_url=self.base_url,
            explicit_base_url=base_url is not None,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;base_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional explicit Nessie base URL.
      If not provided, uses settings from configuration.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_url&#x22;" type="&#x22;(self, path) -> str&#x22;">
  Build a full Nessie URL.

  <PySourceCode>
    ```python
    def _url(self, path: str) -> str:
        """Build a full Nessie URL.

        Args:
            path: Nessie API path.

        Returns:
            Fully qualified API URL.

        """
        return f"{self.base_url}{path}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Nessie API path.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Fully qualified API URL.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_request&#x22;" type="&#x22;(self, method, url, **kwargs) -> requests.Response&#x22;">
  Execute an HTTP request with retry logic.

  Retries up to `_MAX_RETRIES` times on connection errors and 5xx
  responses, using exponential backoff defined by `_BACKOFF_SCHEDULE`.

  <PySourceCode>
    ```python
    def _request(
        self,
        method: str,
        url: str,
        **kwargs: object,
    ) -> requests.Response:
        """Execute an HTTP request with retry logic.

        Retries up to ``_MAX_RETRIES`` times on connection errors and 5xx
        responses, using exponential backoff defined by ``_BACKOFF_SCHEDULE``.

        Args:
            method: HTTP method (``GET``, ``POST``, ``DELETE``).
            url: Fully qualified URL.
            **kwargs: Forwarded to :func:`requests.request`.

        Returns:
            The successful :class:`requests.Response`.

        Raises:
            requests.exceptions.ConnectionError: After all retries exhausted.
            requests.exceptions.RequestException: On non-retryable failures.

        """
        request_fn = getattr(requests, method.lower())
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = request_fn(url, **kwargs)
                if response.status_code >= 500 and attempt < _MAX_RETRIES:
                    logger.warning(
                        "nessie_resource_request_retry",
                        method=method,
                        url=url,
                        status_code=response.status_code,
                        attempt=attempt,
                    )
                    time.sleep(_BACKOFF_SCHEDULE[attempt - 1])
                    continue
                return response
            except RequestsConnectionError as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "nessie_resource_request_connection_retry",
                        method=method,
                        url=url,
                        attempt=attempt,
                        error=str(exc),
                    )
                    time.sleep(_BACKOFF_SCHEDULE[attempt - 1])
                    continue
                raise
        raise last_exc  # type: ignore[misc]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;method&#x22;" type="&#x22;str&#x22;" value="undefined">
      HTTP method (`GET`, `POST`, `DELETE`).
    </PyParameter>

    <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified URL.
    </PyParameter>

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;object&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;requests.Response&#x22;">
    The successful :class:`requests.Response`.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_branches&#x22;" type="&#x22;(self) -> list[BranchInfo]&#x22;">
  List all branch references from Nessie.

  Fetches branch metadata including name, hash, and creation timestamp
  from the Nessie API.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nessie = NessieResource()
    > > > branches = nessie.list\_branches()
    > > > for branch in branches:
    > > > ...     print(f"\{branch.name}: \{branch.hash\[:8]}")
  </Callout>

  <PySourceCode>
    ```python
    def list_branches(self) -> list[BranchInfo]:
        """List all branch references from Nessie.

        Fetches branch metadata including name, hash, and creation timestamp
        from the Nessie API.

        Returns:
            list[BranchInfo]: Parsed branch information for each branch reference.

        Raises:
            Exception: Propagates HTTP or parsing errors.

        Example:
            >>> nessie = NessieResource()
            >>> branches = nessie.list_branches()
            >>> for branch in branches:
            ...     print(f"{branch.name}: {branch.hash[:8]}")

        """
        logger.info(
            "nessie_resource_list_branches_requested",
            base_url=self.base_url,
        )
        try:
            response = self._request("GET", self._url("/api/v1/trees"), timeout=10)
            response.raise_for_status()
            payload = response.json() or {}
        except Exception:
            logger.error(
                "nessie_resource_list_branches_failed",
                base_url=self.base_url,
                exc_info=True,
            )
            raise
        branches: list[BranchInfo] = []
        for ref in payload.get("references", []):
            if ref.get("type") != "BRANCH":
                continue
            created_at = None
            metadata = ref.get("metadata") or {}
            if isinstance(metadata, dict):
                created_raw = metadata.get("createdAt") or metadata.get("created_at")
                if isinstance(created_raw, str):
                    try:
                        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                    except ValueError:
                        logger.warning(
                            "nessie_resource_branch_created_at_parse_failed",
                            branch_name=ref.get("name", ""),
                            created_at_raw=created_raw,
                        )
                        created_at = None
            branches.append(
                BranchInfo(name=ref.get("name", ""), hash=ref.get("hash"), created_at=created_at)
            )
        logger.info(
            "nessie_resource_list_branches_succeeded",
            base_url=self.base_url,
            branch_count=len(branches),
        )
        return branches
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[BranchInfo]: Parsed branch information for each branch reference.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_branch_hash&#x22;" type="&#x22;(self, name) -> str | None&#x22;">
  Fetch the current hash for a branch.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nessie = NessieResource()
    > > > hash = nessie.get\_branch\_hash("main")
    > > > 'abc123def456...'
  </Callout>

  <PySourceCode>
    ```python
    def get_branch_hash(self, name: str) -> str | None:
        """Fetch the current hash for a branch.

        Args:
            name: Branch name.

        Returns:
            str | None: Branch hash when found, otherwise ``None``.

        Example:
            >>> nessie = NessieResource()
            >>> hash = nessie.get_branch_hash("main")
            'abc123def456...'

        """
        logger.debug(
            "nessie_resource_get_branch_hash_requested",
            branch_name=name,
            base_url=self.base_url,
        )
        response = self._request("GET", self._url(f"/api/v1/trees/tree/{name}"), timeout=10)
        if response.status_code >= 400:
            logger.info(
                "nessie_resource_get_branch_hash_missing",
                branch_name=name,
                status_code=response.status_code,
            )
            return None
        data = response.json() or {}
        branch_hash = data.get("hash")
        logger.debug(
            "nessie_resource_get_branch_hash_succeeded",
            branch_name=name,
            hash_found=branch_hash is not None,
        )
        return branch_hash
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Branch name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;">
    str | None: Branch hash when found, otherwise `None`.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;delete_branch&#x22;" type="&#x22;(self, name) -> bool&#x22;">
  Delete a branch by name.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nessie = NessieResource()
    > > > deleted = nessie.delete\_branch("feature/old")
    > > > True
  </Callout>

  <PySourceCode>
    ```python
    def delete_branch(self, name: str) -> bool:
        """Delete a branch by name.

        Args:
            name: Branch name.

        Returns:
            bool: ``True`` if deletion succeeded, else ``False``.

        Example:
            >>> nessie = NessieResource()
            >>> deleted = nessie.delete_branch("feature/old")
            True

        """
        logger.info(
            "nessie_resource_delete_branch_requested",
            branch_name=name,
        )
        branch_hash = self.get_branch_hash(name)
        if not branch_hash:
            logger.info(
                "nessie_resource_delete_branch_missing_hash",
                branch_name=name,
            )
            return False
        response = self._request(
            "DELETE",
            self._url(f"/api/v1/trees/branch/{name}"),
            params={"expectedHash": branch_hash},
            timeout=10,
        )
        deleted = response.status_code < 300
        logger.info(
            "nessie_resource_delete_branch_completed",
            branch_name=name,
            status_code=response.status_code,
            deleted=deleted,
        )
        return deleted
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Branch name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    `True` if deletion succeeded, else `False`.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_branch&#x22;" type="&#x22;(self, name, from_ref='main') -> str | None&#x22;">
  Create a new branch from an existing reference.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nessie = NessieResource()
    > > > new\_hash = nessie.create\_branch("feature/new", from\_ref="main")
    > > > 'abc123def456...'
  </Callout>

  <PySourceCode>
    ```python
    def create_branch(self, name: str, from_ref: str = "main") -> str | None:
        """Create a new branch from an existing reference.

        Args:
            name: New branch name.
            from_ref: Source reference to branch from.

        Returns:
            str | None: Hash of the new branch, or ``None`` on failure.

        Example:
            >>> nessie = NessieResource()
            >>> new_hash = nessie.create_branch("feature/new", from_ref="main")
            'abc123def456...'

        """
        logger.info(
            "nessie_resource_create_branch_requested",
            branch_name=name,
            from_ref=from_ref,
        )
        source_hash = self.get_branch_hash(from_ref)
        if not source_hash:
            logger.warning(
                "nessie_resource_create_branch_source_missing",
                branch_name=name,
                from_ref=from_ref,
            )
            return None
        response = self._request(
            "POST",
            self._url("/api/v1/trees/tree"),
            json={"name": name, "type": "BRANCH", "hash": source_hash},
            timeout=10,
        )
        if response.status_code >= 400:
            logger.warning(
                "nessie_resource_create_branch_failed",
                branch_name=name,
                from_ref=from_ref,
                status_code=response.status_code,
                body=response.text[:200],
            )
            return None
        new_hash = (response.json() or {}).get("hash")
        logger.info(
            "nessie_resource_create_branch_succeeded",
            branch_name=name,
            from_ref=from_ref,
            hash=new_hash,
        )
        return new_hash
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      New branch name.
    </PyParameter>

    <PyParameter name="&#x22;from_ref&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
      Source reference to branch from.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;">
    str | None: Hash of the new branch, or `None` on failure.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;merge_branch&#x22;" type="&#x22;(self, source, target='main') -> bool&#x22;">
  Merge source branch into target branch.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nessie = NessieResource()
    > > > merged = nessie.merge\_branch("feature/new", target="main")
    > > > True
  </Callout>

  <PySourceCode>
    ```python
    def merge_branch(self, source: str, target: str = "main") -> bool:
        """Merge source branch into target branch.

        Args:
            source: Source branch name.
            target: Target branch name to merge into.

        Returns:
            bool: ``True`` if merge succeeded, else ``False``.

        Example:
            >>> nessie = NessieResource()
            >>> merged = nessie.merge_branch("feature/new", target="main")
            True

        """
        logger.info(
            "nessie_resource_merge_branch_requested",
            source=source,
            target=target,
        )
        source_hash = self.get_branch_hash(source)
        target_hash = self.get_branch_hash(target)
        if not source_hash or not target_hash:
            logger.warning(
                "nessie_resource_merge_branch_hash_missing",
                source=source,
                target=target,
                source_hash_found=source_hash is not None,
                target_hash_found=target_hash is not None,
            )
            return False
        response = self._request(
            "POST",
            self._url(f"/api/v2/trees/{target}@{target_hash}/history/merge"),
            json={
                "fromRefName": source,
                "fromHash": source_hash,
                "message": f"Merge {source} into {target}",
            },
            timeout=30,
        )
        merged = response.status_code < 300
        logger.info(
            "nessie_resource_merge_branch_completed",
            source=source,
            target=target,
            status_code=response.status_code,
            body=response.text[:200] if response.status_code >= 400 else None,
            merged=merged,
        )
        return merged
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;str&#x22;" value="undefined">
      Source branch name.
    </PyParameter>

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
      Target branch name to merge into.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    `True` if merge succeeded, else `False`.
  </PyFunctionReturn>
</PyFunction>
