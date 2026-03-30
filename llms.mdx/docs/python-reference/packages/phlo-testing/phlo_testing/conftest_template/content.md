# conftest_template (/docs/python-reference/packages/phlo-testing/phlo_testing/conftest_template)



Conftest template for user projects.

This module provides a ready-to-use conftest.py template that users can copy
to their tests/ directory to get all phlo\_testing fixtures automatically.

The template includes:

* All standard phlo\_testing fixtures (mock resources, test data, etc.)
* Environment reset fixture for test isolation
* Project root fixture for path resolution

Usage:

> > > from phlo\_testing.conftest\_template import CONFTEST\_TEMPLATE, get\_conftest\_template
> > > from pathlib import Path
> > >
> > > Write template to tests/conftest.py [#write-template-to-testsconftestpy]
> > >
> > > Path("tests/conftest.py").write\_text(get\_conftest\_template())
> > >
> > > Or use the constant directly [#or-use-the-constant-directly]
> > >
> > > print(CONFTEST\_TEMPLATE)

The fixtures included in the template:

* mock\_iceberg\_catalog: Fresh MockIcebergCatalog for each test
* mock\_trino: Fresh MockTrinoResource for each test
* mock\_asset\_context: MockAssetContext with logging capture
* sample\_partition\_date: Standard test partition date
* sample\_dlt\_data: Sample DLT source data
* temp\_staging\_dir: Temporary directory for test files
* And more...

<PyAttribute name="&#x22;CONFTEST_TEMPLATE&#x22;" type="null" value="&#x22;'\&#x22;\&#x22;\&#x22;\\nPytest configuration and shared fixtures.\\n\\nPlace this file in tests/ directory to make fixtures available to all tests.\\n\&#x22;\&#x22;\&#x22;\\n\\nimport pytest\\nfrom pathlib import Path\\n\\n# Import fixtures from phlo_testing\\nfrom phlo_testing.fixtures import (\\n    mock_iceberg_catalog,\\n    mock_trino,\\n    mock_asset_context,\\n    mock_resources,\\n    sample_partition_date,\\n    sample_partition_range,\\n    sample_dlt_data,\\n    sample_dataframe,\\n    mock_dlt_source_fixture,\\n    temp_staging_dir,\\n    test_data_dir,\\n    setup_test_catalog,\\n    setup_test_trino,\\n    load_json_fixture,\\n    load_csv_fixture,\\n    test_config,\\n)\\n\\n\\n@pytest.fixture(autouse=True)\\ndef reset_test_env(monkeypatch):\\n    \&#x22;\&#x22;\&#x22;Reset environment variables before each test.\\n\\n    Ensures test isolation by setting PHLO_ENV and PHLO_LOG_LEVEL\\n    before each test execution.\\n\\n    Args:\\n        monkeypatch: pytest monkeypatch fixture.\\n    \&#x22;\&#x22;\&#x22;\\n    monkeypatch.setenv(\&#x22;PHLO_ENV\&#x22;, \&#x22;test\&#x22;)\\n    monkeypatch.setenv(\&#x22;PHLO_LOG_LEVEL\&#x22;, \&#x22;DEBUG\&#x22;)\\n\\n\\n@pytest.fixture\\ndef project_root() -> Path:\\n    \&#x22;\&#x22;\&#x22;Return path to project root.\\n\\n    Returns:\\n        Path to the project root directory (where pyproject.toml is located).\\n    \&#x22;\&#x22;\&#x22;\\n    return Path(__file__).parent.parent\\n'&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_conftest_template&#x22;" type="&#x22;() -> str&#x22;">
      Get the conftest.py template content.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > template = get\_conftest\_template()
        > > > Path("tests/conftest.py").write\_text(template)
      </Callout>

      <PySourceCode>
        ```python
        def get_conftest_template() -> str:
            """Get the conftest.py template content.

            Returns:
                String content for conftest.py that can be written to a file.

            Example:
                >>> template = get_conftest_template()
                >>> Path("tests/conftest.py").write_text(template)

            """
            return CONFTEST_TEMPLATE
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        String content for conftest.py that can be written to a file.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
