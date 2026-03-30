# nessie (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie)



Nessie API Router.

Endpoints for interacting with the Nessie REST API.
Enables git-like data versioning features in Observatory.

This module provides a proxy to the Project Nessie REST API, enabling
branching, tagging, merging, and history tracking for Iceberg tables.
It abstracts the Nessie API complexity and provides Observatory-compatible
response formats.

Key Endpoints:
GET /connection: Check Nessie connectivity.
GET /branches: List all branches and tags.
GET /branches/\{name}: Get specific branch info.
GET /branches/\{name}/history: Get commit history.
GET /branches/\{name}/entries: List branch contents.
GET /diff/\{from}/\{to}: Compare two branches.
POST /branches: Create a new branch.
DELETE /branches/\{name}: Delete a branch.
POST /merge: Merge branches.

Environment Variables:
NESSIE\_URL: URL for the Nessie server.

Example:
Listing branches:

.. code-block:: bash

curl [http://localhost:4000/api/nessie/branches](http://localhost:4000/api/nessie/branches)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['nessie'])&#x22;" />

<PyAttribute name="&#x22;DEFAULT_NESSIE_URL&#x22;" type="null" value="&#x22;'http://nessie:19120/api/v2'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;Branch&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie/Branch&#x22;" />

      <Card title="&#x22;CommitMeta&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie/CommitMeta&#x22;" />

      <Card title="&#x22;LogEntry&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie/LogEntry&#x22;" />

      <Card title="&#x22;NessieConnectionStatus&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie/NessieConnectionStatus&#x22;" />

      <Card title="&#x22;NessieContent&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie/NessieContent&#x22;" />

      <Card title="&#x22;MergeResult&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie/MergeResult&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_nessie_url&#x22;" type="&#x22;(override=None) -> str&#x22;">
      Resolve the Nessie API URL.

      <PySourceCode>
        ```python
        def resolve_nessie_url(override: str | None = None) -> str:
            """Resolve the Nessie API URL.

            Args:
                override: Optional explicit Nessie URL.

            Returns:
                Nessie URL from override, environment, or default.

            """
            env_url = os.environ.get("NESSIE_URL")
            if override and override.strip():
                if env_url and override.strip() == "http://localhost:19120/api/v2":
                    return env_url
                return override
            return env_url or DEFAULT_NESSIE_URL
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;override&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit Nessie URL.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Nessie URL from override, environment, or default.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;check_connection&#x22;" type="&#x22;(nessie_url=None) -> NessieConnectionStatus&#x22;">
      Check whether Nessie is reachable.

      <PySourceCode>
        ```python
        @router.get("/connection", response_model=NessieConnectionStatus)
        async def check_connection(
            nessie_url: str | None = None,
        ) -> NessieConnectionStatus:
            """Check whether Nessie is reachable.

            Args:
                nessie_url: Optional Nessie URL override.

            Returns:
                NessieConnectionStatus with connection state and default branch info.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/config")

                    if response.status_code != 200:
                        return NessieConnectionStatus(
                            connected=False,
                            error=f"HTTP {response.status_code}: {response.reason_phrase}",
                        )

                    config = response.json()
                    return NessieConnectionStatus(
                        connected=True,
                        default_branch=config.get("defaultBranch", "main"),
                    )
            except Exception as e:
                return NessieConnectionStatus(connected=False, error=str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.nessie.NessieConnectionStatus&#x22;">
        NessieConnectionStatus with connection state and default branch info.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_branches&#x22;" type="&#x22;(nessie_url=None) -> list[Branch] | dict[str, str]&#x22;">
      List all Nessie references (branches and tags).

      <PySourceCode>
        ```python
        @router.get("/branches", response_model=list[Branch] | dict)
        async def get_branches(nessie_url: str | None = None) -> list[Branch] | dict[str, str]:
            """List all Nessie references (branches and tags).

            Args:
                nessie_url: Optional Nessie URL override.

            Returns:
                List of Branch objects (includes tags), or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{url}/trees")

                    if response.status_code != 200:
                        return {"error": f"HTTP {response.status_code}: {response.reason_phrase}"}

                    payload = response.json()
                    references = payload.get("references", [])

                    return [
                        Branch(
                            type=ref.get("type", "BRANCH"),
                            name=ref["name"],
                            hash=ref["hash"],
                        )
                        for ref in references
                    ]
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[Branch] | dict[str, str]&#x22;">
        List of Branch objects (includes tags), or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_branch&#x22;" type="&#x22;(branch_name, nessie_url=None) -> Branch | dict[str, str]&#x22;">
      Get a branch by name.

      <PySourceCode>
        ```python
        @router.get("/branches/{branch_name}", response_model=Branch | dict)
        async def get_branch(branch_name: str, nessie_url: str | None = None) -> Branch | dict[str, str]:
            """Get a branch by name.

            Args:
                branch_name: Branch name.
                nessie_url: Optional Nessie URL override.

            Returns:
                Branch details or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/trees/{quote(branch_name, safe='')}")

                    if response.status_code == 404:
                        return {"error": f"Branch '{branch_name}' not found"}
                    if response.status_code != 200:
                        return {"error": f"HTTP {response.status_code}: {response.reason_phrase}"}

                    payload = response.json()
                    return Branch(
                        type=payload.get("type", "BRANCH"),
                        name=payload["name"],
                        hash=payload["hash"],
                    )
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;branch_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Branch name.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Branch | dict[str, str]&#x22;">
        Branch details or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_commits&#x22;" type="&#x22;(branch_name, limit=Query(default=50, le=200), nessie_url=None) -> list[LogEntry] | dict[str, str]&#x22;">
      Get commit history for a branch.

      <PySourceCode>
        ```python
        @router.get("/branches/{branch_name}/history", response_model=list[LogEntry] | dict)
        async def get_commits(
            branch_name: str,
            limit: int = Query(default=50, le=200),
            nessie_url: str | None = None,
        ) -> list[LogEntry] | dict[str, str]:
            """Get commit history for a branch.

            Args:
                branch_name: Branch name.
                limit: Maximum commit entries to return.
                nessie_url: Optional Nessie URL override.

            Returns:
                Commit log entries or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{url}/trees/{quote(branch_name, safe='')}/history",
                        params={"maxRecords": str(limit)},
                    )

                    if response.status_code == 404:
                        return {"error": f"Branch '{branch_name}' not found"}
                    if response.status_code != 200:
                        return {"error": f"HTTP {response.status_code}: {response.reason_phrase}"}

                    data = response.json()
                    log_entries = data.get("logEntries", [])

                    return [
                        LogEntry(
                            commit_meta=CommitMeta(
                                hash=entry["commitMeta"]["hash"],
                                message=entry["commitMeta"].get("message", ""),
                                committer=entry["commitMeta"].get("committer"),
                                authors=entry["commitMeta"].get("authors", []),
                                commit_time=entry["commitMeta"].get("commitTime"),
                                author_time=entry["commitMeta"].get("authorTime"),
                                parent_commit_hashes=entry["commitMeta"].get("parentCommitHashes", []),
                            ),
                            parent_commit_hash=entry.get("parentCommitHash"),
                            operations=entry.get("operations"),
                        )
                        for entry in log_entries
                    ]
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;branch_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Branch name.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=50, le=200)&#x22;">
          Maximum commit entries to return.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[LogEntry] | dict[str, str]&#x22;">
        Commit log entries or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_contents&#x22;" type="&#x22;(branch_name, prefix=None, nessie_url=None) -> list[dict[str, Any]] | dict[str, str]&#x22;">
      Get branch contents.

      <PySourceCode>
        ```python
        @router.get("/branches/{branch_name}/entries", response_model=list[dict] | dict)
        async def get_contents(
            branch_name: str,
            prefix: str | None = None,
            nessie_url: str | None = None,
        ) -> list[dict[str, Any]] | dict[str, str]:
            """Get branch contents.

            Args:
                branch_name: Branch name.
                prefix: Optional namespace prefix filter.
                nessie_url: Optional Nessie URL override.

            Returns:
                Content entries or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                params = {}
                if prefix:
                    params["filter"] = f"entry.namespace.startsWith('{prefix}')"

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{url}/trees/{quote(branch_name, safe='')}/entries",
                        params=params,
                    )

                    if response.status_code != 200:
                        return {"error": f"HTTP {response.status_code}: {response.reason_phrase}"}

                    data = response.json()
                    return data.get("entries", [])
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;branch_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Branch name.
        </PyParameter>

        <PyParameter name="&#x22;prefix&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional namespace prefix filter.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[dict[str, Any]] | dict[str, str]&#x22;">
        Content entries or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;compare_branches&#x22;" type="&#x22;(from_branch, to_branch, nessie_url=None) -> dict[str, Any]&#x22;">
      Compare two branches.

      <PySourceCode>
        ```python
        @router.get("/diff/{from_branch}/{to_branch}", response_model=dict)
        async def compare_branches(
            from_branch: str,
            to_branch: str,
            nessie_url: str | None = None,
        ) -> dict[str, Any]:
            """Compare two branches.

            Args:
                from_branch: Source branch for diff.
                to_branch: Target branch for diff.
                nessie_url: Optional Nessie URL override.

            Returns:
                Diff payload or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{url}/trees/{quote(to_branch, safe='')}/diff/{quote(from_branch, safe='')}"
                    )

                    if response.status_code != 200:
                        return {"error": f"HTTP {response.status_code}: {response.reason_phrase}"}

                    return response.json()
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;from_branch&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source branch for diff.
        </PyParameter>

        <PyParameter name="&#x22;to_branch&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target branch for diff.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Diff payload or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;create_branch&#x22;" type="&#x22;(name, from_branch, nessie_url=None) -> Branch | dict[str, str]&#x22;">
      Create a new branch.

      <PySourceCode>
        ```python
        @router.post("/branches", response_model=Branch | dict)
        async def create_branch(
            name: str,
            from_branch: str,
            nessie_url: str | None = None,
        ) -> Branch | dict[str, str]:
            """Create a new branch.

            Args:
                name: New branch name.
                from_branch: Existing source branch name.
                nessie_url: Optional Nessie URL override.

            Returns:
                Created branch or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Get source branch hash
                    source_response = await client.get(f"{url}/trees/{quote(from_branch, safe='')}")

                    if source_response.status_code != 200:
                        return {"error": f"Source branch '{from_branch}' not found"}

                    source_branch = source_response.json()

                    # Create new branch
                    create_response = await client.post(
                        f"{url}/trees",
                        json={
                            "type": "BRANCH",
                            "name": name,
                            "hash": source_branch["hash"],
                        },
                    )

                    if create_response.status_code not in (200, 201):
                        error_text = create_response.text
                        return {"error": f"Failed to create branch: {error_text}"}

                    new_branch = create_response.json()
                    return Branch(
                        type="BRANCH",
                        name=new_branch["name"],
                        hash=new_branch["hash"],
                    )
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          New branch name.
        </PyParameter>

        <PyParameter name="&#x22;from_branch&#x22;" type="&#x22;str&#x22;" value="undefined">
          Existing source branch name.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Branch | dict[str, str]&#x22;">
        Created branch or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;delete_branch&#x22;" type="&#x22;(branch_name, expected_hash, nessie_url=None) -> dict[str, Any]&#x22;">
      Delete a branch.

      <PySourceCode>
        ```python
        @router.delete("/branches/{branch_name}", response_model=dict)
        async def delete_branch(
            branch_name: str,
            expected_hash: str,
            nessie_url: str | None = None,
        ) -> dict[str, Any]:
            """Delete a branch.

            Args:
                branch_name: Branch name to delete.
                expected_hash: Expected head hash for optimistic concurrency.
                nessie_url: Optional Nessie URL override.

            Returns:
                Success payload or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.delete(
                        f"{url}/trees/{quote(branch_name, safe='')}",
                        params={"expectedHash": expected_hash},
                    )

                    if response.status_code != 200:
                        error_text = response.text
                        return {"error": f"Failed to delete branch: {error_text}"}

                    return {"success": True}
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;branch_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Branch name to delete.
        </PyParameter>

        <PyParameter name="&#x22;expected_hash&#x22;" type="&#x22;str&#x22;" value="undefined">
          Expected head hash for optimistic concurrency.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Success payload or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;merge_branch&#x22;" type="&#x22;(from_branch, into_branch, message=None, nessie_url=None) -> MergeResult | dict[str, str]&#x22;">
      Merge one branch into another.

      <PySourceCode>
        ```python
        @router.post("/merge", response_model=MergeResult | dict)
        async def merge_branch(
            from_branch: str,
            into_branch: str,
            message: str | None = None,
            nessie_url: str | None = None,
        ) -> MergeResult | dict[str, str]:
            """Merge one branch into another.

            Args:
                from_branch: Source branch name.
                into_branch: Target branch name.
                message: Optional merge commit message.
                nessie_url: Optional Nessie URL override.

            Returns:
                Merge result or an error dictionary.

            """
            url = resolve_nessie_url(nessie_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Get source branch hash
                    source_response = await client.get(f"{url}/trees/{quote(from_branch, safe='')}")
                    if source_response.status_code != 200:
                        return {"error": f"Source branch '{from_branch}' not found"}
                    source_branch = source_response.json()

                    # Get target branch hash
                    target_response = await client.get(f"{url}/trees/{quote(into_branch, safe='')}")
                    if target_response.status_code != 200:
                        return {"error": f"Target branch '{into_branch}' not found"}
                    target_branch = target_response.json()

                    # Perform merge
                    merge_response = await client.post(
                        f"{url}/trees/{quote(into_branch, safe='')}/history/merge",
                        params={"expectedHash": target_branch["hash"]},
                        json={
                            "fromRefName": from_branch,
                            "fromHash": source_branch["hash"],
                            "message": message or f"Merge {from_branch} into {into_branch}",
                        },
                    )

                    if merge_response.status_code not in (200, 201):
                        error_text = merge_response.text
                        return {"error": f"Merge failed: {error_text}"}

                    result = merge_response.json()
                    return MergeResult(success=True, hash=result.get("resultantTargetHash"))
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;from_branch&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source branch name.
        </PyParameter>

        <PyParameter name="&#x22;into_branch&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target branch name.
        </PyParameter>

        <PyParameter name="&#x22;message&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional merge commit message.
        </PyParameter>

        <PyParameter name="&#x22;nessie_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Nessie URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;MergeResult | dict[str, str]&#x22;">
        Merge result or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
