# cli_lineage (/docs/python-reference/packages/phlo-lineage/phlo_lineage/cli_lineage)



CLI commands for lineage visualization and analysis.

This module implements the complete lineage CLI command group using Click and
Rich for formatting. It provides commands for:

* Displaying lineage trees (ASCII visualization)
* Exporting to various formats (DOT, Mermaid, JSON)
* Impact analysis (downstream dependency counting)
* Status overview (graph statistics)
* Column-level lineage import and querying

Command Structure:
lineage
├── show          Display ASCII tree for an asset
├── export        Export to external formats
├── impact        Analyze downstream impact
├── status        Show graph statistics
└── column
├── import-dbt  Import from dbt manifest
├── upstream    Query upstream columns
└── downstream  Query downstream columns

Asset Name Resolution:
Commands accepting asset names implement fuzzy matching:

1. Exact match on asset key
2. Replace "/" with "." and retry
3. Suffix matching on path segments
4. List all candidates if ambiguous

Example:

> > > Display lineage for an asset [#display-lineage-for-an-asset]

$ phlo lineage show orders
$ phlo lineage show orders --direction upstream --depth 2

> > > Export to Graphviz [#export-to-graphviz]

$ phlo lineage export orders --format dot --output lineage.dot

> > > Check impact before changes [#check-impact-before-changes]

$ phlo lineage impact silver.stg\_orders

Dependencies:

* click: Command-line interface framework
* rich: Terminal formatting and styling
* phlo\_lineage.graph: Lineage graph operations
* phlo\_lineage.store: Database operations

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_asset_name&#x22;" type="&#x22;(graph, asset_name) -> tuple[str | None, list[str]]&#x22;">
      Resolve a user-provided asset name to a known graph asset key.

      Implements a multi-stage resolution strategy for flexible asset naming:

      1. Exact match on asset\_name
      2. Normalized match ("/" replaced with ".")
      3. Suffix matching on path segments (handles partial paths)

      <Callout title="&#x22;Resolution Logic&#x22;" type="&#x22;resolution-logic&#x22;">
        * Exact match: "orders" matches asset "orders"
        * Normalized: "bronze/orders" matches "bronze.orders"
        * Suffix: "stg\_orders" matches "silver.stg\_orders"
        * Multiple suffix matches → ambiguous (return None with candidates)
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > graph = LineageGraph()
        > > > graph.add\_asset("silver.stg\_orders")
        > > > graph.add\_asset("bronze.raw\_orders")
        > > >
        > > > name, matches = \_resolve\_asset\_name(graph, "stg\_orders")
        > > > print(name)  # "silver.stg\_orders"
        > > >
        > > > name, matches = \_resolve\_asset\_name(graph, "orders")
        > > > print(name)  # None (ambiguous)
        > > > print(matches)  # \["bronze.raw\_orders", "silver.stg\_orders"]
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal helper function. Resolution is case-sensitive.
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_asset_name(graph, asset_name: str) -> tuple[str | None, list[str]]:
            """Resolve a user-provided asset name to a known graph asset key.

            Implements a multi-stage resolution strategy for flexible asset naming:
            1. Exact match on asset_name
            2. Normalized match ("/" replaced with ".")
            3. Suffix matching on path segments (handles partial paths)

            Args:
                graph: LineageGraph instance to search.
                asset_name: User-provided asset identifier (may be partial).

            Returns:
                Tuple of (resolved_name, matches):
                - resolved_name: The matched asset key, or None if ambiguous/no match
                - matches: List of candidate asset keys (for disambiguation hints)

            Resolution Logic:
                - Exact match: "orders" matches asset "orders"
                - Normalized: "bronze/orders" matches "bronze.orders"
                - Suffix: "stg_orders" matches "silver.stg_orders"
                - Multiple suffix matches → ambiguous (return None with candidates)

            Example:
                >>> graph = LineageGraph()
                >>> graph.add_asset("silver.stg_orders")
                >>> graph.add_asset("bronze.raw_orders")
                >>>
                >>> name, matches = _resolve_asset_name(graph, "stg_orders")
                >>> print(name)  # "silver.stg_orders"
                >>>
                >>> name, matches = _resolve_asset_name(graph, "orders")
                >>> print(name)  # None (ambiguous)
                >>> print(matches)  # ["bronze.raw_orders", "silver.stg_orders"]

            Note:
                This is an internal helper function. Resolution is case-sensitive.

            """
            if asset_name in graph.assets:
                return asset_name, [asset_name]

            normalized = asset_name.replace("/", ".")
            if normalized in graph.assets:
                return normalized, [normalized]

            query_segments = [seg for seg in re.split(r"[./]", asset_name) if seg]
            matches: list[str] = []
            for name in graph.assets.keys():
                name_segments = [seg for seg in re.split(r"[./]", name) if seg]
                if (
                    len(name_segments) >= len(query_segments)
                    and name_segments[-len(query_segments) :] == query_segments
                ):
                    matches.append(name)

            if len(matches) == 1:
                return matches[0], matches

            return None, matches
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;graph&#x22;" type="null" value="undefined">
          LineageGraph instance to search.
        </PyParameter>

        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          User-provided asset identifier (may be partial).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Tuple of (resolved\_name, matches):
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;lineage_group&#x22;" type="&#x22;()&#x22;">
      Asset dependency and lineage visualization commands.

      This command group provides tools for exploring data lineage:

      * Visualize dependencies as ASCII trees
      * Export to external formats (Graphviz, Mermaid, JSON)
      * Analyze impact of changes
      * Query column-level lineage

      The lineage graph is loaded from the persistent store on first access
      and cached for the duration of the CLI session.

      Example:
      $ phlo lineage show orders
      $ phlo lineage export orders --format dot -o lineage.dot
      $ phlo lineage impact silver.stg\_orders

      Quick Start:

      1. Ensure lineage database is configured (LINEAGE\_DB\_URL)
      2. Run pipeline to populate lineage graph
      3. Use 'phlo lineage status' to verify graph population
      4. Explore with 'phlo lineage show \<asset>'

      <PySourceCode>
        ```python
        @click.group(name="lineage")
        def lineage_group():
            """Asset dependency and lineage visualization commands.

            This command group provides tools for exploring data lineage:
            - Visualize dependencies as ASCII trees
            - Export to external formats (Graphviz, Mermaid, JSON)
            - Analyze impact of changes
            - Query column-level lineage

            The lineage graph is loaded from the persistent store on first access
            and cached for the duration of the CLI session.

            Example:
                $ phlo lineage show orders
                $ phlo lineage export orders --format dot -o lineage.dot
                $ phlo lineage impact silver.stg_orders

            Quick Start:
                1. Ensure lineage database is configured (LINEAGE_DB_URL)
                2. Run pipeline to populate lineage graph
                3. Use 'phlo lineage status' to verify graph population
                4. Explore with 'phlo lineage show <asset>'

            """
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;show_lineage&#x22;" type="&#x22;(asset_name, direction, depth) -> None&#x22;">
      Display asset dependencies in ASCII tree format.

      Shows upstream dependencies (sources) and/or downstream dependents
      (assets that depend on this one) in a visual tree structure.

      <Callout title="&#x22;Fuzzy Matching&#x22;" type="&#x22;fuzzy-matching&#x22;">
        The asset\_name argument supports partial matching:

        * Exact: "silver.stg\_orders"
        * Short: "stg\_orders" (matches "silver.stg\_orders")
        * Slash: "bronze/orders" (matches "bronze.orders")

        If multiple assets match, candidates are displayed for selection.
      </Callout>

      <Callout title="&#x22;Visual Indicators&#x22;" type="&#x22;visual-indicators&#x22;">
        * \[upstream] / \[downstream]: Section labels
        * ✓: Asset with status="success"
        * ✗: Asset with status="warning" or "failure"
        * (ingestion), (transform), (publish): Asset type annotations
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Success
        1: Asset not found or ambiguous
      </Callout>

      <PySourceCode>
        ```python
        @lineage_group.command(name="show")
        @click.argument("asset_name")
        @click.option(
            "--direction",
            type=click.Choice(["upstream", "downstream", "both"]),
            default="both",
            help="Direction to show (default: both)",
        )
        @click.option(
            "--depth",
            type=int,
            default=None,
            help="Maximum depth to traverse",
        )
        def show_lineage(asset_name: str, direction: str, depth: Optional[int]) -> None:
            """Display asset dependencies in ASCII tree format.

            Shows upstream dependencies (sources) and/or downstream dependents
            (assets that depend on this one) in a visual tree structure.

            Args:
                asset_name: Asset to display lineage for. Supports fuzzy matching.
                direction: Which relationships to show:
                    - upstream: Show only dependencies (what this asset depends on)
                    - downstream: Show only dependents (what depends on this asset)
                    - both: Show both directions (default)
                depth: Maximum traversal depth. Unlimited if not specified.

            Fuzzy Matching:
                The asset_name argument supports partial matching:
                - Exact: "silver.stg_orders"
                - Short: "stg_orders" (matches "silver.stg_orders")
                - Slash: "bronze/orders" (matches "bronze.orders")

                If multiple assets match, candidates are displayed for selection.

            Visual Indicators:
                - [upstream] / [downstream]: Section labels
                - ✓: Asset with status="success"
                - ✗: Asset with status="warning" or "failure"
                - (ingestion), (transform), (publish): Asset type annotations

            Examples:
                $ phlo lineage show orders
                $ phlo lineage show orders --direction upstream
                $ phlo lineage show orders --direction downstream --depth 2
                $ phlo lineage show silver.stg_orders --depth 3

            Exit Codes:
                0: Success
                1: Asset not found or ambiguous

            """
            graph = get_lineage_graph()

            resolved_name, matches = _resolve_asset_name(graph, asset_name)
            if not resolved_name:
                console.print(f"[yellow]⚠[/yellow]  Asset '{asset_name}' not found in lineage graph")
                if matches:
                    console.print("\nPossible matches:")
                    for name in sorted(matches):
                        asset = graph.assets[name]
                        console.print(
                            f"  • {name} ({asset.asset_type})",
                            style="cyan" if asset.status == "success" else "red",
                        )
                else:
                    console.print("\nAvailable assets:")
                    for name in sorted(graph.assets.keys()):
                        asset = graph.assets[name]
                        console.print(
                            f"  • {name} ({asset.asset_type})",
                            style="cyan" if asset.status == "success" else "red",
                        )
                return

            # Generate ASCII tree
            tree = graph.to_ascii_tree(resolved_name, direction=direction, depth=depth)

            # Display with panel
            title = f"Lineage: {resolved_name}"
            if depth:
                title += f" (depth ≤ {depth})"

            console.print(Panel(tree, title=title, expand=False))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset to display lineage for. Supports fuzzy matching.
        </PyParameter>

        <PyParameter name="&#x22;direction&#x22;" type="&#x22;str&#x22;" value="undefined">
          Which relationships to show:

          * upstream: Show only dependencies (what this asset depends on)
          * downstream: Show only dependents (what depends on this asset)
          * both: Show both directions (default)
        </PyParameter>

        <PyParameter name="&#x22;depth&#x22;" type="&#x22;Optional[int]&#x22;" value="undefined">
          Maximum traversal depth. Unlimited if not specified.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;export_lineage&#x22;" type="&#x22;(asset_name, format, output) -> None&#x22;">
      Export lineage to external visualization formats.

      Generates lineage diagrams in formats suitable for external tools:

      * dot: Graphviz format (render to PNG/SVG/PDF)
      * mermaid: Markdown-native diagrams (GitHub/GitLab/Notion)
      * json: Machine-readable serialization

      <Callout title="&#x22;Format Details&#x22;" type="&#x22;format-details&#x22;">
        dot:
        Graphviz DOT language. Render with:
        $ dot -Tpng lineage.dot -o lineage.png
        $ dot -Tsvg lineage.dot -o lineage.svg

        mermaid:
        Mermaid.js flowchart syntax. Embed in markdown:

        <Mermaid
          chart="graph TD
..."
        />

        json:
        Structured data with assets and edges. Schema:
        \{
        "assets": \{"name": \{"type": "...", "status": "..."}},
        "edges": \{"source": \["target1", "target2"]}
        }
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Success
        1: Empty graph or unknown format
      </Callout>

      <PySourceCode>
        ````python
        @lineage_group.command(name="export")
        @click.argument("asset_name")
        @click.option(
            "--format",
            type=click.Choice(["dot", "mermaid", "json"]),
            default="dot",
            help="Export format",
        )
        @click.option(
            "--output",
            type=Path,
            required=True,
            help="Output file path",
        )
        def export_lineage(asset_name: str, format: str, output: Path) -> None:
            """Export lineage to external visualization formats.

            Generates lineage diagrams in formats suitable for external tools:
            - dot: Graphviz format (render to PNG/SVG/PDF)
            - mermaid: Markdown-native diagrams (GitHub/GitLab/Notion)
            - json: Machine-readable serialization

            Args:
                asset_name: Asset to export lineage for (fuzzy matching supported).
                format: Output format (dot, mermaid, json).
                output: Path to write the exported file.

            Format Details:
                dot:
                    Graphviz DOT language. Render with:
                    $ dot -Tpng lineage.dot -o lineage.png
                    $ dot -Tsvg lineage.dot -o lineage.svg

                mermaid:
                    Mermaid.js flowchart syntax. Embed in markdown:
                    \```mermaid
                    graph TD
                    ...
                    \```

                json:
                    Structured data with assets and edges. Schema:
                    {
                      "assets": {"name": {"type": "...", "status": "..."}},
                      "edges": {"source": ["target1", "target2"]}
                    }

            Examples:
                $ phlo lineage export orders --format dot --output lineage.dot
                $ phlo lineage export orders --format mermaid --output lineage.md
                $ phlo lineage export orders --format json --output lineage.json

                $ dot -Tpng lineage.dot -o lineage.png

            Exit Codes:
                0: Success
                1: Empty graph or unknown format

            """
            graph = get_lineage_graph()

            if not graph.assets:
                console.print("[red]✗[/red] Lineage graph is empty")
                return

            # Export based on format
            if format == "dot":
                content = graph.to_dot()
            elif format == "mermaid":
                content = graph.to_mermaid()
            elif format == "json":
                content = graph.to_json()
            else:
                console.print(f"[red]✗[/red] Unknown format: {format}")
                return

            # Write to file
            with open(output, "w") as f:
                f.write(content)

            console.print(f"[green]✓[/green] Lineage exported to {output}")

            # Show preview
            if format == "dot":
                console.print(
                    "\n[dim]Tip: Render with Graphviz:[/dim] "
                    "[cyan]dot -Tpng lineage.dot -o lineage.png[/cyan]"
                )
            elif format == "mermaid":
                console.print("\n[dim]Tip: View in GitHub markdown or Mermaid Live Editor[/dim]")
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset to export lineage for (fuzzy matching supported).
        </PyParameter>

        <PyParameter name="&#x22;format&#x22;" type="&#x22;str&#x22;" value="undefined">
          Output format (dot, mermaid, json).
        </PyParameter>

        <PyParameter name="&#x22;output&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to write the exported file.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;analyze_impact&#x22;" type="&#x22;(asset_name) -> None&#x22;">
      Analyze downstream impact of an asset.

      Calculates the scope of potential impact if the specified asset were
      to fail or change. This is useful for:

      * Pre-deployment impact assessment
      * Incident scope evaluation
      * Change management workflows

      <Callout title="&#x22;Metrics Reported&#x22;" type="&#x22;metrics-reported&#x22;">
        - Directly Affected: Assets with direct dependency (depth=1)
        - Indirectly Affected: Transitively dependent assets
        - Publishing Assets Affected: Whether any "publish" type assets impacted
        - Affected Assets: Complete list with types
      </Callout>

      <Callout title="&#x22;Warning&#x22;" type="&#x22;warning&#x22;">
        A warning is displayed if any "publish" type assets are affected,
        as this indicates potential external impact.
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Analysis complete (regardless of impact level)
        1: Asset not found
      </Callout>

      <PySourceCode>
        ```python
        @lineage_group.command(name="impact")
        @click.argument("asset_name")
        def analyze_impact(asset_name: str) -> None:
            """Analyze downstream impact of an asset.

            Calculates the scope of potential impact if the specified asset were
            to fail or change. This is useful for:
            - Pre-deployment impact assessment
            - Incident scope evaluation
            - Change management workflows

            Args:
                asset_name: Asset to analyze for downstream impact.

            Metrics Reported:
                - Directly Affected: Assets with direct dependency (depth=1)
                - Indirectly Affected: Transitively dependent assets
                - Publishing Assets Affected: Whether any "publish" type assets impacted
                - Affected Assets: Complete list with types

            Warning:
                A warning is displayed if any "publish" type assets are affected,
                as this indicates potential external impact.

            Examples:
                $ phlo lineage impact orders
                $ phlo lineage impact stg_orders
                $ phlo lineage impact silver.stg_orders --depth 5

            Exit Codes:
                0: Analysis complete (regardless of impact level)
                1: Asset not found

            """
            graph = get_lineage_graph()

            resolved_name, matches = _resolve_asset_name(graph, asset_name)
            if not resolved_name:
                console.print(f"[yellow]⚠[/yellow]  Asset '{asset_name}' not found in lineage graph")
                if matches:
                    console.print("\nPossible matches:")
                    for name in sorted(matches):
                        console.print(f"  • {name}")
                return

            impact = graph.get_impact(resolved_name)

            # Display impact analysis
            console.print(f"\n[bold]Impact Analysis: {resolved_name}[/bold]\n")

            console.print(f"Directly Affected: {impact['direct_count']} asset(s)")
            console.print(f"Indirectly Affected: {impact['indirect_count']} asset(s)")
            console.print(
                f"Publishing Assets Affected: {'[red]Yes[/red]' if impact['publishing_affected'] else '[green]No[/green]'}"
            )

            if impact["affected_assets"]:
                console.print(f"\n[bold]Affected Assets ({len(impact['affected_assets'])} total):[/bold]")
                for asset in sorted(impact["affected_assets"]):
                    asset_obj = graph.assets.get(asset)
                    console.print(f"  • {asset} ({asset_obj.asset_type if asset_obj else 'unknown'})")

            if impact["publishing_affected"]:
                console.print("\n[bold red]⚠ WARNING:[/bold red] This change would affect published data!")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset to analyze for downstream impact.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;lineage_status&#x22;" type="&#x22;() -> None&#x22;">
      Show lineage graph status and statistics.

      Displays summary statistics about the current lineage graph:

      * Total number of assets
      * Total number of dependency edges
      * Distribution by asset type
      * Distribution by materialization status

      Use this command to verify that the lineage graph is populated
      and to get a high-level view of the data landscape.

      <Callout title="&#x22;Statistics Shown&#x22;" type="&#x22;statistics-shown&#x22;">
        * Total Assets: Count of unique asset nodes
        * Total Dependencies: Sum of all edges
        * Assets by Type: Breakdown of ingestion/transform/publish
        * Assets by Status: Breakdown of success/warning/failure
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Always succeeds (empty graph is valid status)
      </Callout>

      <PySourceCode>
        ```python
        @lineage_group.command(name="status")
        def lineage_status() -> None:
            """Show lineage graph status and statistics.

            Displays summary statistics about the current lineage graph:
            - Total number of assets
            - Total number of dependency edges
            - Distribution by asset type
            - Distribution by materialization status

            Use this command to verify that the lineage graph is populated
            and to get a high-level view of the data landscape.

            Statistics Shown:
                - Total Assets: Count of unique asset nodes
                - Total Dependencies: Sum of all edges
                - Assets by Type: Breakdown of ingestion/transform/publish
                - Assets by Status: Breakdown of success/warning/failure

            Examples:
                $ phlo lineage status

            Exit Codes:
                0: Always succeeds (empty graph is valid status)

            """
            graph = get_lineage_graph()

            console.print("[bold]Lineage Graph Status[/bold]\n")

            # Statistics
            asset_count = len(graph.assets)
            edge_count = sum(len(targets) for targets in graph.edges.values())

            console.print(f"Total Assets: {asset_count}")
            console.print(f"Total Dependencies: {edge_count}")

            # Count by type
            type_counts = {}
            for asset in graph.assets.values():
                type_counts[asset.asset_type] = type_counts.get(asset.asset_type, 0) + 1

            if type_counts:
                console.print("\n[bold]Assets by Type:[/bold]")
                for asset_type, count in sorted(type_counts.items()):
                    console.print(f"  • {asset_type}: {count}")

            # Count by status
            status_counts = {}
            for asset in graph.assets.values():
                status_counts[asset.status] = status_counts.get(asset.status, 0) + 1

            if status_counts:
                console.print("\n[bold]Assets by Status:[/bold]")
                for status, count in sorted(status_counts.items()):
                    console.print(f"  • {status}: {count}")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;column_group&#x22;" type="&#x22;()&#x22;">
      Column-level lineage commands.

      This subcommand group provides operations for importing and querying
      column-level lineage information:

      Commands:
      import-dbt: Import column mappings from dbt manifest.json
      upstream: Show upstream columns for an asset
      downstream: Show downstream columns for an asset

      Column lineage tracks data flow at the column level, showing which
      source columns contribute to which target columns through transformations.

      <PySourceCode>
        ```python
        @lineage_group.group(name="column")
        def column_group():
            """Column-level lineage commands.

                This subcommand group provides operations for importing and querying
            column-level lineage information:

                Commands:
                    import-dbt: Import column mappings from dbt manifest.json
                    upstream: Show upstream columns for an asset
                    downstream: Show downstream columns for an asset

                Column lineage tracks data flow at the column level, showing which
                source columns contribute to which target columns through transformations.

            Examples:
                    $ phlo lineage column import-dbt --manifest target/manifest.json
                    $ phlo lineage column upstream silver.stg_orders --column order_id
                    $ phlo lineage column downstream bronze.raw_orders

            """
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;import_dbt&#x22;" type="&#x22;(manifest) -> None&#x22;">
      Import column lineage from a dbt manifest.json file.

      Extracts column-level lineage from dbt's compiled manifest using same-name
      heuristics. For each model, it compares column names with upstream models
      and creates lineage mappings for matching names.

      <Callout title="&#x22;Heuristic Method&#x22;" type="&#x22;heuristic-method&#x22;">
        A column is considered to have lineage from an upstream model if:

        1. The column exists in both the model and upstream model
        2. The upstream model is listed in the model's depends\_on.nodes

        This is a naming-based heuristic, not SQL parsing. Column renames
        are not detected.
      </Callout>

      <Callout title="&#x22;Requirements&#x22;" type="&#x22;requirements&#x22;">
        * dbt must have been compiled (dbt compile or dbt build)
        * Models must have columns defined in YAML or inferred by dbt
        * Lineage database must be configured
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Success (or no mappings found - not an error)
        1: Database not configured or file not found
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        phlo\_lineage.dbt\_column\_lineage for extraction logic.
      </Callout>

      <PySourceCode>
        ```python
        @column_group.command(name="import-dbt")
        @click.option(
            "--manifest",
            type=click.Path(exists=True, dir_okay=False, path_type=Path),
            required=True,
            help="Path to dbt manifest.json",
        )
        def import_dbt(manifest: Path) -> None:
            """Import column lineage from a dbt manifest.json file.

            Extracts column-level lineage from dbt's compiled manifest using same-name
            heuristics. For each model, it compares column names with upstream models
            and creates lineage mappings for matching names.

            Args:
                manifest: Path to dbt's manifest.json file (typically at
                    target/manifest.json after dbt compile or build).

            Heuristic Method:
                A column is considered to have lineage from an upstream model if:
                1. The column exists in both the model and upstream model
                2. The upstream model is listed in the model's depends_on.nodes

                This is a naming-based heuristic, not SQL parsing. Column renames
                are not detected.

            Requirements:
                - dbt must have been compiled (dbt compile or dbt build)
                - Models must have columns defined in YAML or inferred by dbt
                - Lineage database must be configured

            Examples:
                $ phlo lineage column import-dbt --manifest target/manifest.json
                $ phlo lineage column import-dbt --manifest /path/to/manifest.json

            Exit Codes:
                0: Success (or no mappings found - not an error)
                1: Database not configured or file not found

            See Also:
                phlo_lineage.dbt_column_lineage for extraction logic.

            """
            from phlo_lineage.dbt_column_lineage import extract_column_lineage
            from phlo_lineage.store import LineageStore, resolve_lineage_db_url_with_postgres_fallback

            with open(manifest) as f:
                manifest_data = json.load(f)

            mappings = extract_column_lineage(manifest_data)

            if not mappings:
                console.print("[yellow]⚠[/yellow]  No column lineage mappings found in manifest")
                return

            connection_string = resolve_lineage_db_url_with_postgres_fallback()
            if not connection_string:
                console.print("[red]✗[/red]  No lineage database configured")
                return

            store = LineageStore(connection_string)
            count = store.record_column_lineage(mappings)
            console.print(f"[green]✓[/green]  Imported {count} column lineage mapping(s)")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;manifest&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to dbt's manifest.json file (typically at
          target/manifest.json after dbt compile or build).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;column_upstream&#x22;" type="&#x22;(asset, column) -> None&#x22;">
      Show upstream column lineage for an asset.

      Queries the lineage database for columns that feed into the specified
      asset. Shows which source columns from upstream assets map to columns
      in this asset.

      <Callout title="&#x22;Output Format&#x22;" type="&#x22;output-format&#x22;">
        Results are displayed as a Rich table with columns:

        * Source Asset: Upstream table/model name
        * Source Column: Column name in upstream asset
        * Target Column: Column name in this asset
        * Source Type: Origin of mapping (e.g., "dbt\_heuristic")
      </Callout>

      <Callout title="&#x22;Database Required&#x22;" type="&#x22;database-required&#x22;">
        This command requires the lineage database to be configured.
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Success (or no results found - not an error)
        1: Database not configured
      </Callout>

      <PySourceCode>
        ```python
        @column_group.command(name="upstream")
        @click.argument("asset")
        @click.option("--column", default=None, help="Filter to a specific column")
        def column_upstream(asset: str, column: str | None) -> None:
            """Show upstream column lineage for an asset.

            Queries the lineage database for columns that feed into the specified
            asset. Shows which source columns from upstream assets map to columns
            in this asset.

            Args:
                asset: Fully qualified asset name (e.g., "silver.stg_orders").
                column: Optional column name to filter results. If provided, only
                    lineage for this specific column is shown.

            Output Format:
                Results are displayed as a Rich table with columns:
                - Source Asset: Upstream table/model name
                - Source Column: Column name in upstream asset
                - Target Column: Column name in this asset
                - Source Type: Origin of mapping (e.g., "dbt_heuristic")

            Examples:
                $ phlo lineage column upstream silver.stg_orders
                $ phlo lineage column upstream silver.stg_orders --column order_id
                $ phlo lineage column upstream gold.fct_orders --column customer_id

            Database Required:
                This command requires the lineage database to be configured.

            Exit Codes:
                0: Success (or no results found - not an error)
                1: Database not configured

            """
            from phlo_lineage.store import LineageStore, resolve_lineage_db_url_with_postgres_fallback

            connection_string = resolve_lineage_db_url_with_postgres_fallback()
            if not connection_string:
                console.print("[red]✗[/red]  No lineage database configured")
                return

            store = LineageStore(connection_string)
            results = store.get_upstream_columns(asset, target_column=column)

            if not results:
                console.print("[yellow]⚠[/yellow]  No upstream column lineage found")
                return

            table = Table(title=f"Upstream columns for {asset}")
            table.add_column("Source Asset", style="cyan")
            table.add_column("Source Column", style="green")
            table.add_column("Target Column", style="green")
            table.add_column("Source Type", style="dim")

            for r in results:
                table.add_row(r.source_asset, r.source_column, r.target_column, r.source_type)

            console.print(table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset&#x22;" type="&#x22;str&#x22;" value="undefined">
          Fully qualified asset name (e.g., "silver.stg\_orders").
        </PyParameter>

        <PyParameter name="&#x22;column&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional column name to filter results. If provided, only
          lineage for this specific column is shown.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;column_downstream&#x22;" type="&#x22;(asset, column) -> None&#x22;">
      Show downstream column lineage for an asset.

      Queries the lineage database for columns derived from the specified asset.
      Shows which columns in downstream assets are mapped from columns in this
      asset.

      <Callout title="&#x22;Output Format&#x22;" type="&#x22;output-format&#x22;">
        Results are displayed as a Rich table with columns:

        * Target Asset: Downstream table/model name
        * Target Column: Column name in downstream asset
        * Source Column: Column name in this asset
        * Source Type: Origin of mapping (e.g., "dbt\_heuristic")
      </Callout>

      <Callout title="&#x22;Database Required&#x22;" type="&#x22;database-required&#x22;">
        This command requires the lineage database to be configured.
      </Callout>

      <Callout title="&#x22;Exit Codes&#x22;" type="&#x22;exit-codes&#x22;">
        0: Success (or no results found - not an error)
        1: Database not configured
      </Callout>

      <PySourceCode>
        ```python
        @column_group.command(name="downstream")
        @click.argument("asset")
        @click.option("--column", default=None, help="Filter to a specific column")
        def column_downstream(asset: str, column: str | None) -> None:
            """Show downstream column lineage for an asset.

            Queries the lineage database for columns derived from the specified asset.
            Shows which columns in downstream assets are mapped from columns in this
            asset.

            Args:
                asset: Fully qualified asset name (e.g., "bronze.dlt_orders").
                column: Optional column name to filter results. If provided, only
                    lineage for this specific column is shown.

            Output Format:
                Results are displayed as a Rich table with columns:
                - Target Asset: Downstream table/model name
                - Target Column: Column name in downstream asset
                - Source Column: Column name in this asset
                - Source Type: Origin of mapping (e.g., "dbt_heuristic")

            Examples:
                $ phlo lineage column downstream bronze.dlt_orders
                $ phlo lineage column downstream bronze.dlt_orders --column order_total
                $ phlo lineage column downstream silver.stg_customers --column customer_id

            Database Required:
                This command requires the lineage database to be configured.

            Exit Codes:
                0: Success (or no results found - not an error)
                1: Database not configured

            """
            from phlo_lineage.store import LineageStore, resolve_lineage_db_url_with_postgres_fallback

            connection_string = resolve_lineage_db_url_with_postgres_fallback()
            if not connection_string:
                console.print("[red]✗[/red]  No lineage database configured")
                return

            store = LineageStore(connection_string)
            results = store.get_downstream_columns(asset, source_column=column)

            if not results:
                console.print("[yellow]⚠[/yellow]  No downstream column lineage found")
                return

            table = Table(title=f"Downstream columns for {asset}")
            table.add_column("Target Asset", style="cyan")
            table.add_column("Target Column", style="green")
            table.add_column("Source Column", style="green")
            table.add_column("Source Type", style="dim")

            for r in results:
                table.add_row(r.target_asset, r.target_column, r.source_column, r.source_type)

            console.print(table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset&#x22;" type="&#x22;str&#x22;" value="undefined">
          Fully qualified asset name (e.g., "bronze.dlt\_orders").
        </PyParameter>

        <PyParameter name="&#x22;column&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional column name to filter results. If provided, only
          lineage for this specific column is shown.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
