# HasuraMetadataSync (/docs/python-reference/packages/phlo-hasura/phlo_hasura/sync/HasuraMetadataSync)



Manage Hasura metadata export/import and version control.

Provides methods for exporting metadata to files, importing from files,
calculating diffs between metadata versions, and generating reports.

Attributes [#attributes]

<PyAttribute name="&#x22;client&#x22;" type="null" value="&#x22;client or HasuraClient()&#x22;">
  HasuraClient instance for API operations.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, client=None)&#x22;">
  Initialize metadata sync.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > syncer = HasuraMetadataSync()
    > > > custom\_syncer = HasuraMetadataSync(HasuraClient())
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, client: Optional[HasuraClient] = None):
        """Initialize metadata sync.

        Args:
            client: HasuraClient instance for API operations. If not provided,
                a new HasuraClient will be instantiated with default settings.

        Example:
            >>> syncer = HasuraMetadataSync()
            >>> custom_syncer = HasuraMetadataSync(HasuraClient())

        """
        self.client = client or HasuraClient()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;client&#x22;" type="&#x22;Optional[HasuraClient]&#x22;" value="&#x22;None&#x22;">
      HasuraClient instance for API operations. If not provided,
      a new HasuraClient will be instantiated with default settings.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;export_metadata&#x22;" type="&#x22;(self, output_path=None) -> dict[str, Any]&#x22;">
  Export Hasura metadata.

  Retrieves the complete Hasura metadata and optionally saves it
  to a JSON file.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > syncer = HasuraMetadataSync()
    > > > metadata = syncer.export\_metadata()
    > > > syncer.export\_metadata("backup.json")
  </Callout>

  <PySourceCode>
    ```python
    def export_metadata(self, output_path: Optional[str | Path] = None) -> dict[str, Any]:
        """Export Hasura metadata.

        Retrieves the complete Hasura metadata and optionally saves it
        to a JSON file.

        Args:
            output_path: Optional path to save metadata as JSON.
                If provided, metadata is written to this file.

        Returns:
            Complete metadata dictionary.

        Raises:
            IOError: If writing to the output file fails.

        Example:
            >>> syncer = HasuraMetadataSync()
            >>> metadata = syncer.export_metadata()
            >>> syncer.export_metadata("backup.json")

        """
        metadata = self.client.export_metadata()

        if output_path:
            output_path = Path(output_path)
            with open(output_path, "w") as f:
                json.dump(metadata, f, indent=2)

        return metadata
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;output_path&#x22;" type="&#x22;Optional[str | Path]&#x22;" value="&#x22;None&#x22;">
      Optional path to save metadata as JSON.
      If provided, metadata is written to this file.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Complete metadata dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;import_metadata&#x22;" type="&#x22;(self, input_path) -> dict[str, Any]&#x22;">
  Import Hasura metadata from file.

  Reads metadata from a JSON file and applies it to Hasura,
  replacing the current metadata.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > syncer = HasuraMetadataSync()
    > > > syncer.import\_metadata("backup.json")
  </Callout>

  <PySourceCode>
    ```python
    def import_metadata(self, input_path: str | Path) -> dict[str, Any]:
        """Import Hasura metadata from file.

        Reads metadata from a JSON file and applies it to Hasura,
        replacing the current metadata.

        Args:
            input_path: Path to the metadata JSON file.

        Returns:
            API response dictionary.

        Raises:
            FileNotFoundError: If the input file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            requests.RequestException: If the API call fails.

        Example:
            >>> syncer = HasuraMetadataSync()
            >>> syncer.import_metadata("backup.json")

        """
        input_path = Path(input_path)

        with open(input_path) as f:
            metadata = json.load(f)

        return self.client.apply_metadata(metadata)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;input_path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
      Path to the metadata JSON file.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;merge_metadata&#x22;" type="&#x22;(self, base, override) -> dict[str, Any]&#x22;">
  Merge two metadata dictionaries (override over base).

  Combines two metadata dictionaries, with values from override
  taking precedence over base. Handles top-level keys and sources.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > base = syncer.export\_metadata()
    > > > override = \{"version": 3}
    > > > merged = syncer.merge\_metadata(base, override)
  </Callout>

  <PySourceCode>
    ```python
    def merge_metadata(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Merge two metadata dictionaries (override over base).

        Combines two metadata dictionaries, with values from override
        taking precedence over base. Handles top-level keys and sources.

        Args:
            base: Base metadata dictionary.
            override: Metadata dictionary to merge on top of base.

        Returns:
            Merged metadata dictionary.

        Example:
            >>> base = syncer.export_metadata()
            >>> override = {"version": 3}
            >>> merged = syncer.merge_metadata(base, override)

        """
        merged = base.copy()

        # Merge top-level keys
        for key in ["version", "metadata"]:
            if key in override:
                merged[key] = override[key]

        # Merge sources (custom types, functions, etc.)
        if "sources" in override:
            # Replace entire sources list for simplicity
            merged["sources"] = override["sources"]

        return merged
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;base&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Base metadata dictionary.
    </PyParameter>

    <PyParameter name="&#x22;override&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Metadata dictionary to merge on top of base.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Merged metadata dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_diff&#x22;" type="&#x22;(self, current, desired) -> dict[str, Any]&#x22;">
  Calculate diff between current and desired metadata.

  Analyzes two metadata dictionaries and returns a structured diff
  showing what would need to be added, removed, or modified.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > current = syncer.export\_metadata()
    > > > desired = json.load(open("target.json"))
    > > > diff = syncer.get\_diff(current, desired)
    > > > print(f"Tables to add: \{len(diff\['tables']\['added'])}")
  </Callout>

  <PySourceCode>
    ```python
    def get_diff(self, current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
        """Calculate diff between current and desired metadata.

        Analyzes two metadata dictionaries and returns a structured diff
        showing what would need to be added, removed, or modified.

        Args:
            current: Current metadata state.
            desired: Desired metadata state to compare against.

        Returns:
            Diff dictionary with structure:
            {
                "sources": {"added": [...], "removed": [...], "modified": [...]},
                "tables": {"added": [...], "removed": [...], "modified": [...]},
                "relationships": {"added": [...], "removed": [...]},
                "permissions": {"added": [...], "removed": [...]}
            }

        Example:
            >>> current = syncer.export_metadata()
            >>> desired = json.load(open("target.json"))
            >>> diff = syncer.get_diff(current, desired)
            >>> print(f"Tables to add: {len(diff['tables']['added'])}")

        """
        diff = {
            "sources": {"added": [], "removed": [], "modified": []},
            "tables": {"added": [], "removed": [], "modified": []},
            "relationships": {"added": [], "removed": []},
            "permissions": {"added": [], "removed": []},
        }

        # Track current tables and sources
        current_sources = {s.get("name"): s for s in current.get("sources", [])}
        desired_sources = {s.get("name"): s for s in desired.get("sources", [])}

        # Check for added/removed sources
        for name in desired_sources:
            if name not in current_sources:
                diff["sources"]["added"].append(name)

        for name in current_sources:
            if name not in desired_sources:
                diff["sources"]["removed"].append(name)

        # Check table differences
        current_tables = self._extract_tables(current)
        desired_tables = self._extract_tables(desired)

        current_table_set = set(current_tables.keys())
        desired_table_set = set(desired_tables.keys())

        diff["tables"]["added"] = list(desired_table_set - current_table_set)
        diff["tables"]["removed"] = list(current_table_set - desired_table_set)

        # Check for modified tables
        for table_path in current_table_set & desired_table_set:
            if current_tables[table_path] != desired_tables[table_path]:
                diff["tables"]["modified"].append(table_path)

        # Check relationship and permission differences
        current_rels = self._extract_relationships(current)
        desired_rels = self._extract_relationships(desired)

        diff["relationships"]["added"] = list(set(desired_rels) - set(current_rels))
        diff["relationships"]["removed"] = list(set(current_rels) - set(desired_rels))

        return diff
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;current&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Current metadata state.
    </PyParameter>

    <PyParameter name="&#x22;desired&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Desired metadata state to compare against.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Diff dictionary with structure:
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_extract_tables&#x22;" type="&#x22;(self, metadata) -> dict[str, dict]&#x22;">
  Extract table information from metadata.

  Internal method to extract all tracked tables from metadata
  and organize them by their fully qualified path.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > tables = syncer.\_extract\_tables(metadata)
    > > > print(list(tables.keys()))
    > > > \['api.orders', 'api.customers']
  </Callout>

  <PySourceCode>
    ```python
    def _extract_tables(self, metadata: dict[str, Any]) -> dict[str, dict]:
        """Extract table information from metadata.

        Internal method to extract all tracked tables from metadata
        and organize them by their fully qualified path.

        Args:
            metadata: Metadata dictionary to extract from.

        Returns:
            Dictionary mapping table_path -> table_info.
            Example: {"api.orders": {...table metadata...}}

        Example:
            >>> tables = syncer._extract_tables(metadata)
            >>> print(list(tables.keys()))
            ['api.orders', 'api.customers']

        """
        tables = {}

        for source in metadata.get("sources", []):
            if source.get("name") != "default":
                continue

            for table in source.get("tables", []):
                schema = table.get("table", {}).get("schema", "public")
                name = table["table"]["name"]
                table_path = f"{schema}.{name}"
                tables[table_path] = table

        return tables
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Metadata dictionary to extract from.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping table\_path -> table\_info.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_extract_relationships&#x22;" type="&#x22;(self, metadata) -> list[tuple]&#x22;">
  Extract relationships from metadata.

  Internal method to extract all object and array relationships
  from metadata, organizing them as tuples for comparison.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > rels = syncer.*extract\_relationships(metadata)
    > > > for table, name, type* in rels:
    > > > ...     print(f"\{table}.\{name} (\{type\_})")
  </Callout>

  <PySourceCode>
    ```python
    def _extract_relationships(self, metadata: dict[str, Any]) -> list[tuple]:
        """Extract relationships from metadata.

        Internal method to extract all object and array relationships
        from metadata, organizing them as tuples for comparison.

        Args:
            metadata: Metadata dictionary to extract from.

        Returns:
            List of (table_path, relationship_name, relationship_type) tuples.
            Example: [("api.orders", "customer", "object"), ...]

        Example:
            >>> rels = syncer._extract_relationships(metadata)
            >>> for table, name, type_ in rels:
            ...     print(f"{table}.{name} ({type_})")

        """
        rels = []

        for source in metadata.get("sources", []):
            if source.get("name") != "default":
                continue

            for table in source.get("tables", []):
                schema = table.get("table", {}).get("schema", "public")
                table_name = table["table"]["name"]

                for rel in table.get("object_relationships", []):
                    rel_name = rel.get("name")
                    rels.append((f"{schema}.{table_name}", rel_name, "object"))

                for rel in table.get("array_relationships", []):
                    rel_name = rel.get("name")
                    rels.append((f"{schema}.{table_name}", rel_name, "array"))

        return rels
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Metadata dictionary to extract from.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of (table\_path, relationship\_name, relationship\_type) tuples.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;generate_diff_report&#x22;" type="&#x22;(self, current, desired) -> str&#x22;">
  Generate human-readable diff report.

  Creates a formatted string report showing the differences
  between two metadata states.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > report = syncer.generate\_diff\_report(current, desired)
    > > > print(report)
    > > > Hasura Metadata Diff Report
    > > > \============================
    > > > Tables to track: 5

    * api.orders
    * api.customers
      ...
  </Callout>

  <PySourceCode>
    ```python
    def generate_diff_report(self, current: dict[str, Any], desired: dict[str, Any]) -> str:
        """Generate human-readable diff report.

        Creates a formatted string report showing the differences
        between two metadata states.

        Args:
            current: Current metadata state.
            desired: Desired metadata state.

        Returns:
            Formatted diff report as a string.

        Example:
            >>> report = syncer.generate_diff_report(current, desired)
            >>> print(report)
            Hasura Metadata Diff Report
            ============================
            Tables to track: 5
              + api.orders
              + api.customers
            ...

        """
        diff = self.get_diff(current, desired)

        lines = ["Hasura Metadata Diff Report", "=" * 60]

        # Sources
        if diff["sources"]["added"]:
            lines.append(f"\nSources to add: {len(diff['sources']['added'])}")
            for source in diff["sources"]["added"]:
                lines.append(f"  + {source}")

        if diff["sources"]["removed"]:
            lines.append(f"\nSources to remove: {len(diff['sources']['removed'])}")
            for source in diff["sources"]["removed"]:
                lines.append(f"  - {source}")

        # Tables
        if diff["tables"]["added"]:
            lines.append(f"\nTables to track: {len(diff['tables']['added'])}")
            for table in sorted(diff["tables"]["added"]):
                lines.append(f"  + {table}")

        if diff["tables"]["removed"]:
            lines.append(f"\nTables to untrack: {len(diff['tables']['removed'])}")
            for table in sorted(diff["tables"]["removed"]):
                lines.append(f"  - {table}")

        if diff["tables"]["modified"]:
            lines.append(f"\nTables to modify: {len(diff['tables']['modified'])}")
            for table in sorted(diff["tables"]["modified"]):
                lines.append(f"  ~ {table}")

        # Relationships
        if diff["relationships"]["added"]:
            lines.append(f"\nRelationships to add: {len(diff['relationships']['added'])}")
            for table, rel, rel_type in sorted(diff["relationships"]["added"]):
                lines.append(f"  + {table}.{rel} ({rel_type})")

        if diff["relationships"]["removed"]:
            lines.append(f"\nRelationships to remove: {len(diff['relationships']['removed'])}")
            for table, rel, rel_type in sorted(diff["relationships"]["removed"]):
                lines.append(f"  - {table}.{rel} ({rel_type})")

        return "\n".join(lines)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;current&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Current metadata state.
    </PyParameter>

    <PyParameter name="&#x22;desired&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Desired metadata state.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Formatted diff report as a string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;reload_metadata&#x22;" type="&#x22;(self) -> None&#x22;">
  Reload metadata from database.

  Forces Hasura to reload its metadata from the underlying database.
  This is useful after direct database schema changes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > syncer.reload\_metadata()  # After manual DB changes
  </Callout>

  <PySourceCode>
    ```python
    def reload_metadata(self) -> None:
        """Reload metadata from database.

        Forces Hasura to reload its metadata from the underlying database.
        This is useful after direct database schema changes.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> syncer.reload_metadata()  # After manual DB changes

        """
        self.client.reload_metadata()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
