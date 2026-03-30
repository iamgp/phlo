# scaffold (/docs/python-reference/core/phlo/cli/commands/plugin/scaffold)



Plugin package scaffolding — template strings and file-writing logic.

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_build_init_content&#x22;" type="&#x22;(plugin_name, plugin_type, module_name) -> str&#x22;">
      <PySourceCode>
        ```python
        def _build_init_content(plugin_name: str, plugin_type: str, module_name: str) -> str:
            class_name = plugin_name.replace("-", "_").title().replace("_", "") + "Plugin"
            return f'''"""
        {plugin_name} plugin for Phlo

        Plugin type: {plugin_type}
        """

        from phlo_{module_name}.plugin import {class_name}

        __all__ = ["{class_name}"]
        __version__ = "0.1.0"
        '''
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;module_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_plugin_content&#x22;" type="&#x22;(plugin_name, plugin_type, base_class, class_name) -> str&#x22;">
      <PySourceCode>
        ```python
        def _build_plugin_content(
            plugin_name: str, plugin_type: str, base_class: str, class_name: str
        ) -> str:
            content = f'''"""
        {plugin_name} plugin implementation.
        """

        from phlo.plugins import {base_class}, PluginMetadata
        '''

            if plugin_type in {"asset", "resource", "orchestrator"}:
                content += "\nfrom collections.abc import Iterable\n"
                spec_imports: list[str]
                if plugin_type == "resource":
                    spec_imports = ["ResourceSpec"]
                elif plugin_type == "asset":
                    spec_imports = ["AssetCheckSpec", "AssetSpec"]
                else:
                    spec_imports = ["AssetCheckSpec", "AssetSpec", "ResourceSpec"]
                content += f"from phlo.capabilities.specs import {', '.join(spec_imports)}\n"

            if plugin_type == "hook":
                content += f'''
        from phlo.hooks import HookEvent
        from phlo.plugins import HookFilter, HookRegistration


        class {class_name}({base_class}):
            """
            {plugin_name} hook plugin.

            Add your hook handlers here.
            """

            @property
            def metadata(self) -> PluginMetadata:
                """Return plugin metadata."""
                return PluginMetadata(
                    name="{plugin_name}",
                    version="0.1.0",
                    description="Add description here",
                    author="Your Name",
                )

            def get_hooks(self):
                """Return hook registrations."""
                return [
                    HookRegistration(
                        hook_name="handle_events",
                        handler=self.handle_event,
                        filters=HookFilter(event_types={{"quality.result"}}),
                    )
                ]

            def handle_event(self, event: HookEvent) -> None:
                """Handle hook events."""
                # Add your hook logic here
                raise NotImplementedError()
        '''
            else:
                content += f'''


        class {class_name}({base_class}):
            """
            {plugin_name} plugin.

            Add your implementation here.
            """

            @property
            def metadata(self) -> PluginMetadata:
                """Return plugin metadata."""
                return PluginMetadata(
                    name="{plugin_name}",
                    version="0.1.0",
                    description="Add description here",
                    author="Your Name",
                )

            def initialize(self, config: dict) -> None:
                """Initialize plugin with configuration."""
                super().initialize(config)
                # Add initialization logic here

            def cleanup(self) -> None:
                """Clean up plugin resources."""
                super().cleanup()
                # Add cleanup logic here
        '''

            content += _PLUGIN_TYPE_TEMPLATES.get(plugin_type, "")
            return content
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;base_class&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_test_content&#x22;" type="&#x22;(plugin_name, module_name, class_name) -> str&#x22;">
      <PySourceCode>
        ```python
        def _build_test_content(plugin_name: str, module_name: str, class_name: str) -> str:
            return f'''"""
        Tests for {plugin_name} plugin.
        """

        import pytest
        from phlo_{module_name}.plugin import {class_name}


        @pytest.fixture
        def plugin():
            """Create plugin instance."""
            return {class_name}()


        def test_plugin_metadata(plugin):
            """Test plugin metadata."""
            metadata = plugin.metadata
            assert metadata.name == "{plugin_name}"
            assert metadata.version == "0.1.0"
            assert metadata.author is not None


        def test_plugin_initialization(plugin):
            """Test plugin initialization."""
            if hasattr(plugin, "initialize"):
                config = {{}}
                plugin.initialize(config)
                # Add more initialization tests


        def test_plugin_cleanup(plugin):
            """Test plugin cleanup."""
            if hasattr(plugin, "cleanup"):
                plugin.cleanup()
                # Add more cleanup tests
        '''
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;module_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_pyproject_content&#x22;" type="&#x22;(plugin_name, plugin_type, module_name, class_name, entry_point_group) -> str&#x22;">
      <PySourceCode>
        ```python
        def _build_pyproject_content(
            plugin_name: str,
            plugin_type: str,
            module_name: str,
            class_name: str,
            entry_point_group: str,
        ) -> str:
            return f'''[build-system]
        requires = ["setuptools>=45", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{plugin_name}"
        version = "0.1.0"
        description = "Phlo {plugin_type} plugin"
        readme = "README.md"
        requires-python = ">=3.11"
        authors = [
            {{name = "Your Name", email = "your@email.com"}},
        ]
        license = {{text = "MIT"}}
        dependencies = [
            "phlo>=0.1.0",
        ]

        [project.optional-dependencies]
        dev = [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
            "basedpyright>=1.0.0",
        ]

        [project.entry-points."{entry_point_group}"]
        {plugin_name} = "phlo_{module_name}.plugin:{class_name}"

        [tool.setuptools]
        package-dir = {{"" = "src"}}

        [tool.setuptools.packages.find]
        where = ["src"]

        [tool.ruff]
        line-length = 100
        target-version = "py311"

        [tool.basedpyright]
        typeCheckingMode = "standard"
        '''
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;module_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;entry_point_group&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_readme_content&#x22;" type="&#x22;(plugin_name, plugin_type, module_name, class_name) -> str&#x22;">
      <PySourceCode>
        ````python
        def _build_readme_content(
            plugin_name: str, plugin_type: str, module_name: str, class_name: str
        ) -> str:
            accessor = _README_ACCESSOR_MAP.get(plugin_type, "get_plugin")

            content = f"""# {plugin_name}

        A Phlo {plugin_type} plugin.

        ## Installation

        \```bash
        pip install -e .
        \```

        ## Usage

        \```python
        from phlo.plugins import {accessor}
        from phlo_{module_name} import {class_name}

        plugin = {class_name}()
        \```
        """
            if accessor == "get_plugin":
                internal_type = _README_INTERNAL_TYPE_MAP.get(plugin_type, plugin_type)
                content += f"""
        \```python
        from phlo.plugins import get_plugin

        plugin = get_plugin("{internal_type}", "{plugin_name}")
        \```
        """
            content += """

        ## Development

        Run tests:
        \```bash
        pytest tests/
        \```

        Run linting:
        \```bash
        ruff check .
        basedpyright .
        \```

        ## License

        MIT
        """
            return content
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;module_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;create_plugin_package&#x22;" type="&#x22;(plugin_name, plugin_type, plugin_path)&#x22;">
      Create plugin package structure and files.

      <PySourceCode>
        ```python
        def create_plugin_package(plugin_name: str, plugin_type: str, plugin_path: Path):
            """Create plugin package structure and files."""
            src_dir = plugin_path / "src" / f"phlo_{plugin_name.replace('-', '_')}"
            src_dir.mkdir(parents=True, exist_ok=True)
            tests_dir = plugin_path / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)

            module_name = plugin_name.replace("-", "_")
            base_class = _TYPE_TO_BASE_CLASS.get(plugin_type)
            if base_class is None:
                raise ValueError(f"unknown plugin_type: {plugin_type}")

            entry_point_group = _TYPE_TO_ENTRY_POINT[plugin_type]
            class_name = plugin_name.replace("-", "_").title().replace("_", "") + "Plugin"

            (src_dir / "__init__.py").write_text(_build_init_content(plugin_name, plugin_type, module_name))
            (src_dir / "plugin.py").write_text(
                _build_plugin_content(plugin_name, plugin_type, base_class, class_name)
            )
            (tests_dir / "__init__.py").write_text("")
            (tests_dir / "test_plugin.py").write_text(
                _build_test_content(plugin_name, module_name, class_name)
            )
            (plugin_path / "pyproject.toml").write_text(
                _build_pyproject_content(
                    plugin_name, plugin_type, module_name, class_name, entry_point_group
                )
            )
            (plugin_path / "README.md").write_text(
                _build_readme_content(plugin_name, plugin_type, module_name, class_name)
            )
            (plugin_path / "MANIFEST.in").write_text("include README.md\nrecursive-include src *.py\n")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
