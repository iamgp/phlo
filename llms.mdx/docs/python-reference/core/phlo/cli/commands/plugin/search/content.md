# search (/docs/python-reference/core/phlo/cli/commands/plugin/search)



Plugin search command.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;search_cmd&#x22;" type="&#x22;(query, plugin_type, tags, output_json)&#x22;">
      Search plugin registry.

      <PySourceCode>
        ```python
        @click.command(name="search")
        @click.argument("query", required=False)
        @click.option(
            "--type",
            "plugin_type",
            type=click.Choice(PLUGIN_TYPE_CHOICES),
            help="Filter by plugin type",
        )
        @click.option(
            "--tag",
            "tags",
            multiple=True,
            help="Filter by one or more tags",
        )
        @click.option(
            "--json",
            "output_json",
            is_flag=True,
            default=False,
            help="Output as JSON",
        )
        def search_cmd(
            query: str | None, plugin_type: str | None, tags: tuple[str, ...], output_json: bool
        ):
            """Search plugin registry."""
            try:
                logger.info(
                    "plugin_search_started",
                    has_query=query is not None,
                    plugin_type=plugin_type,
                    tag_count=len(tags),
                    output_json=output_json,
                )
                if plugin_type:
                    plugin_type = INTERNAL_TO_REGISTRY_TYPE.get(plugin_type, plugin_type)
                results = search_plugins(
                    query=query,
                    plugin_type=plugin_type,
                    tags=list(tags) if tags else None,
                )

                output = [registry_plugin_to_dict(plugin) for plugin in results]

                if output_json:
                    console.print(json.dumps(output, indent=2))
                    logger.info("plugin_search_succeeded", result_count=len(output), output_json=True)
                    return

                if not output:
                    console.print("No plugins found.")
                    logger.info("plugin_search_succeeded", result_count=0, output_json=False)
                    return

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Version", style="yellow")
                table.add_column("Package", style="white")
                table.add_column("Verified", style="blue")

                for plugin in output:
                    table.add_row(
                        plugin["name"],
                        plugin["type"],
                        plugin["version"],
                        plugin["package"],
                        "yes" if plugin["verified"] else "no",
                    )

                console.print(table)
                logger.info("plugin_search_succeeded", result_count=len(output), output_json=False)

            except Exception as e:
                logger.exception(
                    "plugin_search_failed",
                    has_query=query is not None,
                    plugin_type=plugin_type,
                    tag_count=len(tags),
                    output_json=output_json,
                )
                console.print(f"[red]Error searching registry: {e}[/red]")
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;tags&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;output_json&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
