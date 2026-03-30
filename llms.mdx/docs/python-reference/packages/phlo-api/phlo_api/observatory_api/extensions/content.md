# extensions (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/extensions)



Observatory extension manifest and asset endpoints.

Provides endpoints for discovering and serving Observatory extension plugins.
Extensions are Python packages that register via entry points and provide
UI components, pages, and asset files to customize the Observatory interface.

Key Endpoints:
GET /api/observatory/extensions: List all installed extensions.
GET /api/observatory/extensions/\{name}: Get single extension manifest.
GET /api/observatory/extensions/\{name}/assets/\{path}: Serve extension assets.

Example:
Listing available extensions:

.. code-block:: bash

curl [http://localhost:4000/api/observatory/extensions](http://localhost:4000/api/observatory/extensions)

Response includes manifest and base paths for each extension's assets.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(prefix='/api/observatory', tags=['observatory'])&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;discover_observatory_extensions&#x22;" type="&#x22;() -> list[Any]&#x22;">
      Return no extensions when Observatory package is unavailable.

      <PySourceCode>
        ```python
        def discover_observatory_extensions() -> list[Any]:
            """Return no extensions when Observatory package is unavailable."""
            return []
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_extensions&#x22;" type="&#x22;() -> list[Any]&#x22;">
      <PySourceCode>
        ```python
        def _load_extensions() -> list[Any]:
            global _cached_extensions, _cache_timestamp
            now = time.monotonic()
            with _cache_lock:
                if _cached_extensions is not None and _cache_timestamp is not None:
                    if now - _cache_timestamp < _CACHE_TTL_SECONDS:
                        return _cached_extensions

            observatory_version = _get_observatory_version()
            extensions = []
            for plugin in discover_observatory_extensions():
                if not _is_compatible(plugin, observatory_version):
                    logger.warning(
                        "Skipping incompatible Observatory extension: %s",
                        plugin.metadata.name,
                    )
                    continue
                extensions.append(plugin)

            with _cache_lock:
                _cached_extensions = extensions
                _cache_timestamp = now

            return extensions
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_extension_payload&#x22;" type="&#x22;(plugin) -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _extension_payload(plugin: Any) -> dict[str, Any]:
            manifest = plugin.get_manifest()
            return {
                "manifest": manifest.model_dump(),
                "assets_base_path": f"/api/observatory/extensions/{plugin.metadata.name}/assets",
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_observatory_version&#x22;" type="&#x22;() -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _get_observatory_version() -> str | None:
            try:
                return importlib.metadata.version("phlo-observatory")
            except importlib.metadata.PackageNotFoundError:
                return None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_parse_version&#x22;" type="&#x22;(value) -> tuple[int, ...]&#x22;">
      <PySourceCode>
        ```python
        def _parse_version(value: str) -> tuple[int, ...]:
            parts = re.split(r"[.+-]", value)
            numbers = tuple(int(p) for p in itertools.takewhile(str.isdigit, parts))
            return numbers or (0,)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[int, ...]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_is_compatible&#x22;" type="&#x22;(plugin, observatory_version) -> bool&#x22;">
      <PySourceCode>
        ```python
        def _is_compatible(plugin: Any, observatory_version: str | None) -> bool:
            if not observatory_version:
                return True
            manifest = plugin.get_manifest()
            required = manifest.compat.observatory_min
            return _parse_version(observatory_version) >= _parse_version(required)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;observatory_version&#x22;" type="&#x22;str | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;list_extensions&#x22;" type="&#x22;() -> dict[str, list[dict[str, Any]]]&#x22;">
      List all installed Observatory extensions.

      Returns manifest and asset paths for each discovered extension.

      <PySourceCode>
        ```python
        @router.get("/extensions")
        def list_extensions() -> dict[str, list[dict[str, Any]]]:
            """List all installed Observatory extensions.

            Returns manifest and asset paths for each discovered extension.

            Args:
                None: No arguments required.

            Returns:
                Dictionary with "extensions" key containing list of extension payloads.

            Raises:
                None: No exceptions raised directly.

            """
            extensions = _load_extensions()
            return {"extensions": [_extension_payload(plugin) for plugin in extensions]}
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with "extensions" key containing list of extension payloads.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_extension&#x22;" type="&#x22;(name) -> dict[str, Any]&#x22;">
      Get a single Observatory extension manifest.

      <PySourceCode>
        ```python
        @router.get("/extensions/{name}")
        def get_extension(name: str) -> dict[str, Any]:
            """Get a single Observatory extension manifest.

            Args:
                name: Extension name to retrieve.

            Returns:
                Extension payload dictionary with manifest and assets_base_path.

            Raises:
                HTTPException: If extension not found (404).

            """
            extensions = _load_extensions()
            plugin = next((p for p in extensions if p.metadata.name == name), None)
            if not plugin:
                raise HTTPException(status_code=404, detail=f"Observatory extension not found: {name}")
            return _extension_payload(plugin)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Extension name to retrieve.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Extension payload dictionary with manifest and assets\_base\_path.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_cleanup_temp_dir&#x22;" type="&#x22;(dir_path) -> None&#x22;">
      Remove temporary directory and contents after response is sent.

      <PySourceCode>
        ```python
        def _cleanup_temp_dir(dir_path: Path) -> None:
            """Remove temporary directory and contents after response is sent."""
            shutil.rmtree(dir_path, ignore_errors=True)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dir_path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_extension_asset&#x22;" type="&#x22;(name, asset_path, background_tasks)&#x22;">
      Serve extension asset files.

      <PySourceCode>
        ```python
        @router.get("/extensions/{name}/assets/{asset_path:path}")
        def get_extension_asset(name: str, asset_path: str, background_tasks: BackgroundTasks):
            """Serve extension asset files.

            Args:
                name: Extension name.
                asset_path: Relative path to the asset file.
                background_tasks: FastAPI background tasks for cleanup.

            Returns:
                FileResponse with the asset content.

            Raises:
                HTTPException: If extension not found (404), asset path invalid (400),
                    or asset not found (404).

            """
            extensions = _load_extensions()
            plugin = next((p for p in extensions if p.metadata.name == name), None)
            if not plugin:
                raise HTTPException(status_code=404, detail=f"Observatory extension not found: {name}")

            if not asset_path:
                raise HTTPException(status_code=404, detail="Asset path required")

            path = PurePosixPath(asset_path)
            if path.is_absolute() or ".." in path.parts:
                raise HTTPException(status_code=400, detail="Invalid asset path")

            asset = plugin.asset_root.joinpath(*path.parts)
            try:
                if not asset.is_file():
                    raise HTTPException(status_code=404, detail="Asset not found")
            except (AttributeError, OSError):
                raise HTTPException(status_code=404, detail="Asset not found")

            try:
                with as_file(asset) as resolved:
                    temp_dir = Path(tempfile.mkdtemp())
                    temp_file = temp_dir / resolved.name
                    shutil.copy2(resolved, temp_file)

                background_tasks.add_task(_cleanup_temp_dir, temp_dir)
                return FileResponse(temp_file)
            except Exception as exc:
                logger.exception("Failed to serve extension asset")
                raise HTTPException(status_code=500, detail="Failed to serve asset") from exc
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Extension name.
        </PyParameter>

        <PyParameter name="&#x22;asset_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Relative path to the asset file.
        </PyParameter>

        <PyParameter name="&#x22;background_tasks&#x22;" type="&#x22;BackgroundTasks&#x22;" value="undefined">
          FastAPI background tasks for cleanup.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        FileResponse with the asset content.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
