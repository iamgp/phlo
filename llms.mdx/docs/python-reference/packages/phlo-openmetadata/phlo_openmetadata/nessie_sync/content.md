# nessie_sync (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/nessie_sync)



Sync Nessie-discovered tables to OpenMetadata.

This module bridges the Nessie catalog backend (`phlo-nessie`) with the OpenMetadata publisher
(`phlo-openmetadata`).

Example:

> > > from phlo\_openmetadata.nessie\_sync import sync\_nessie\_tables\_to\_openmetadata
> > > from phlo.capabilities import resolve\_capability
> > > scanner = resolve\_capability("catalog\_scanner").provider
> > > stats = sync\_nessie\_tables\_to\_openmetadata(scanner, om\_client)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_map_iceberg_to_openmetadata_type&#x22;" type="&#x22;(iceberg_type) -> str&#x22;">
      Map an Iceberg column type string to an OpenMetadata type.

      <PySourceCode>
        ```python
        def _map_iceberg_to_openmetadata_type(iceberg_type: str) -> str:
            """Map an Iceberg column type string to an OpenMetadata type.

            Args:
                iceberg_type: Raw Iceberg type string from table schema metadata.

            Returns:
                str: OpenMetadata-compatible type name.

            """
            type_map = {
                "boolean": "BOOLEAN",
                "int": "INT",
                "long": "BIGINT",
                "float": "FLOAT",
                "double": "DOUBLE",
                "decimal": "DECIMAL",
                "date": "DATE",
                "time": "TIME",
                "timestamp": "TIMESTAMP",
                "timestamptz": "TIMESTAMPZ",
                "string": "STRING",
                "uuid": "STRING",
                "fixed": "BINARY",
                "binary": "BINARY",
                "struct": "STRUCT",
                "list": "ARRAY",
                "map": "MAP",
            }
            base_type = iceberg_type.split("<")[0].lower()
            return type_map.get(base_type, "STRING")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;iceberg_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          Raw Iceberg type string from table schema metadata.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        OpenMetadata-compatible type name.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;nessie_table_metadata_to_openmetadata_table&#x22;" type="&#x22;(table_metadata, description=None) -> OpenMetadataTable&#x22;">
      Convert Nessie table metadata into an OpenMetadata table payload.

      <PySourceCode>
        ```python
        def nessie_table_metadata_to_openmetadata_table(
            table_metadata: dict[str, Any], description: str | None = None
        ) -> OpenMetadataTable:
            """Convert Nessie table metadata into an OpenMetadata table payload.

            Args:
                table_metadata: Nessie table metadata dictionary.
                description: Optional override for the table description.

            Returns:
                OpenMetadataTable: OpenMetadata table model built from Nessie metadata.

            """
            table_name = table_metadata.get("name", "unknown")
            schema = (
                table_metadata.get("schema", {}) if isinstance(table_metadata.get("schema"), dict) else {}
            )

            columns: list[OpenMetadataColumn] = []
            for ordinal, field in enumerate(
                schema.get("fields", []) if isinstance(schema.get("fields"), list) else []
            ):
                if not isinstance(field, dict):
                    continue
                col_type = _map_iceberg_to_openmetadata_type(str(field.get("type", "unknown")))
                columns.append(
                    OpenMetadataColumn(
                        name=str(field.get("name", f"col_{ordinal}")),
                        dataType=col_type,
                        description=field.get("doc"),
                        ordinalPosition=ordinal,
                    )
                )

            location = None
            props = table_metadata.get("properties")
            if isinstance(props, dict):
                location = props.get("location")

            return OpenMetadataTable(
                name=str(table_name),
                description=description or table_metadata.get("doc"),
                columns=columns or None,
                tableType="Regular",
                location=location,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Nessie table metadata dictionary.
        </PyParameter>

        <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional override for the table description.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_openmetadata.openmetadata.OpenMetadataTable&#x22;">
        OpenMetadata table model built from Nessie metadata.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sync_nessie_tables_to_openmetadata&#x22;" type="&#x22;(scanner, om_client, include_namespaces=None, exclude_namespaces=None) -> dict[str, int]&#x22;">
      Sync Nessie tables to OpenMetadata and return aggregate sync stats.

      <PySourceCode>
        ```python
        def sync_nessie_tables_to_openmetadata(
            scanner: CatalogScanner,
            om_client: OpenMetadataClient,
            include_namespaces: list[str] | None = None,
            exclude_namespaces: list[str] | None = None,
        ) -> dict[str, int]:
            """Sync Nessie tables to OpenMetadata and return aggregate sync stats.

            Args:
                scanner: Nessie table scanner used to discover and fetch metadata.
                om_client: OpenMetadata client used to upsert table entities.
                include_namespaces: Optional namespace allowlist.
                exclude_namespaces: Optional namespace denylist.

            Returns:
                dict[str, int]: Counts for successful and failed sync operations.

            """
            stats = {"created": 0, "failed": 0}
            include = set(include_namespaces) if include_namespaces else None
            exclude = set(exclude_namespaces or [])

            catalog = scanner.scan_all_tables()
            for namespace, tables in catalog.items():
                if include is not None and namespace not in include:
                    continue
                if namespace in exclude:
                    continue

                for table_entry in tables:
                    if not isinstance(table_entry, dict):
                        continue
                    name = table_entry.get("name")
                    if not isinstance(name, str):
                        continue
                    try:
                        full_metadata = scanner.get_table_metadata(namespace, name) or table_entry
                        om_table = nessie_table_metadata_to_openmetadata_table(full_metadata)
                        om_client.create_or_update_table(namespace, om_table)
                        stats["created"] += 1
                    except Exception as e:
                        logger.error("Failed to sync %s.%s: %s", namespace, name, e)
                        stats["failed"] += 1

            return stats
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;scanner&#x22;" type="&#x22;CatalogScanner&#x22;" value="undefined">
          Nessie table scanner used to discover and fetch metadata.
        </PyParameter>

        <PyParameter name="&#x22;om_client&#x22;" type="&#x22;OpenMetadataClient&#x22;" value="undefined">
          OpenMetadata client used to upsert table entities.
        </PyParameter>

        <PyParameter name="&#x22;include_namespaces&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
          Optional namespace allowlist.
        </PyParameter>

        <PyParameter name="&#x22;exclude_namespaces&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
          Optional namespace denylist.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, int]: Counts for successful and failed sync operations.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
