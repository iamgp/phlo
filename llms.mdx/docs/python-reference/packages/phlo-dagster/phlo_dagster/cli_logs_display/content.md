# cli_logs_display (/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_logs_display)



Rich formatting and display functions for log output.

This module provides formatted display functions for Dagster logs, utilizing
the Rich library for visually appealing output in the terminal. It handles
both batch display and real-time tailing modes.

Features:

* Rich table formatting with color-coded log levels
* Real-time log tailing with Live display
* JSON syntax highlighting for structured log messages
* Message truncation control for readability
* Duplicate detection in tail mode

Color Coding:

* ERROR: Red
* WARNING: Yellow
* DEBUG: Dimmed
* INFO: Green
* Timestamps: Cyan

Display Components:

* \_tail\_logs: Real-time following with Live updates
* \_display\_logs: Batch display in formatted table
* Log level badges and timestamps
* Run ID and job name columns

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_tail_logs&#x22;" type="&#x22;(filters, full=False, output_json=False) -> None&#x22;">
      Tail logs in real-time (follow mode).

      <PySourceCode>
        ```python
        def _tail_logs(
            filters: dict,
            full: bool = False,
            output_json: bool = False,
        ) -> None:
            """Tail logs in real-time (follow mode).

            Args:
                filters: Filter criteria.
                full: Whether to show full messages.
                output_json: JSON output format.

            Returns:
                None

            Raises:
                KeyboardInterrupt: When user stops tailing.

            """
            from phlo_dagster.cli_logs import _get_logs

            logger.info(
                "dagster_logs_tail_started",
                full=full,
                output_json=output_json,
                has_asset_filter=filters.get("asset") is not None,
                has_job_filter=filters.get("job") is not None,
                level=filters.get("level"),
                run_id=filters.get("run_id"),
            )
            console.print("[yellow]Tailing logs (press Ctrl+C to stop)...[/yellow]\n")

            last_fetch_time = datetime.now(timezone.utc)
            seen_logs = set()

            def generate_logs_table():
                """Build a table for newly fetched log entries.

                Returns:
                    Rich renderable containing log rows or an empty-state message.

                """
                nonlocal last_fetch_time

                # Fetch new logs
                filters["start_time"] = last_fetch_time
                logs_data = _get_logs(filters)
                last_fetch_time = datetime.now(timezone.utc)

                if not logs_data:
                    return Text("[dim]No new logs...[/dim]")

                table = Table(show_header=True, header_style="bold blue")
                table.add_column("Time", style="cyan", width=19)
                table.add_column("Level", style="white", width=8)
                table.add_column("Message", style="white")

                for log in logs_data:
                    log_id = f"{log['timestamp']}-{log['message'][:20]}"
                    if log_id in seen_logs:
                        continue
                    seen_logs.add(log_id)

                    # Format timestamp
                    try:
                        ts = datetime.fromisoformat(log["timestamp"])
                        time_str = ts.strftime("%H:%M:%S")
                    except (ValueError, TypeError):
                        time_str = str(log["timestamp"])[:8]

                    # Color-code level
                    level = log["level"]
                    if level == "ERROR":
                        level_str = f"[red]{level}[/red]"
                    elif level == "WARNING":
                        level_str = f"[yellow]{level}[/yellow]"
                    elif level == "DEBUG":
                        level_str = f"[dim]{level}[/dim]"
                    else:
                        level_str = f"[green]{level}[/green]"

                    # Truncate message
                    message = log["message"]
                    if not full and len(message) > 80:
                        message = message[:77] + "..."

                    table.add_row(time_str, level_str, message)

                return table if table.row_count > 0 else Text("[dim]No new logs...[/dim]")

            # Live display for real-time updates
            try:
                with Live(
                    generate_logs_table(),
                    refresh_per_second=0.5,
                    console=console,
                ) as live:
                    while True:
                        live.update(generate_logs_table())
                        time.sleep(2)  # Poll every 2 seconds
            except KeyboardInterrupt:
                logger.info("dagster_logs_tail_stopped")
                console.print("\n[yellow]Stopped tailing logs[/yellow]")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;filters&#x22;" type="&#x22;dict&#x22;" value="undefined">
          Filter criteria.
        </PyParameter>

        <PyParameter name="&#x22;full&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          Whether to show full messages.
        </PyParameter>

        <PyParameter name="&#x22;output_json&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          JSON output format.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_display_logs&#x22;" type="&#x22;(logs_data, full=False, output_json=False) -> None&#x22;">
      Display logs in formatted output.

      <PySourceCode>
        ```python
        def _display_logs(
            logs_data: list[dict],
            full: bool = False,
            output_json: bool = False,
        ) -> None:
            """Display logs in formatted output.

            Args:
                logs_data: List of log dictionaries.
                full: Whether to show full messages.
                output_json: JSON output format.

            Returns:
                None

            """
            if not logs_data:
                logger.info("dagster_logs_display_no_results", output_json=output_json)
                console.print("[yellow]No logs found[/yellow]")
                return

            if output_json:
                logger.info("dagster_logs_display_json_output", log_count=len(logs_data))
                click.echo(json.dumps(logs_data, indent=2, default=str))
                return

            # Build table
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Time", style="cyan", width=19)
            table.add_column("Level", style="white", width=8)
            table.add_column("Run ID", style="magenta", width=8)
            table.add_column("Job", style="white")
            table.add_column("Message", style="white")

            for log in logs_data:
                # Format timestamp
                try:
                    ts = datetime.fromisoformat(log["timestamp"])
                    time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    time_str = str(log["timestamp"])[:19]

                # Color-code level
                level = log["level"]
                if level == "ERROR":
                    level_str = f"[red]{level}[/red]"
                elif level == "WARNING":
                    level_str = f"[yellow]{level}[/yellow]"
                elif level == "DEBUG":
                    level_str = f"[dim]{level}[/dim]"
                else:
                    level_str = f"[green]{level}[/green]"

                # Truncate message
                message = log.get("message", "")
                if not full and len(message) > 80:
                    message = message[:77] + "..."

                # Check if message contains JSON and syntax highlight
                if _is_json(message) and full:
                    try:
                        parsed = json.loads(message)
                        message = Syntax(
                            json.dumps(parsed, indent=2),
                            "json",
                            theme="monokai",
                            line_numbers=False,
                        )
                    except json.JSONDecodeError:
                        pass

                run_id = log.get("run_id", "-")[:8]
                job = log.get("job_name", "-")[:20]

                table.add_row(time_str, level_str, run_id, job, message)

            console.print(table)
            console.print(f"\n[dim]Total: {len(logs_data)} logs[/dim]")
            logger.info("dagster_logs_display_table_output", log_count=len(logs_data), full=full)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;logs_data&#x22;" type="&#x22;list[dict]&#x22;" value="undefined">
          List of log dictionaries.
        </PyParameter>

        <PyParameter name="&#x22;full&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          Whether to show full messages.
        </PyParameter>

        <PyParameter name="&#x22;output_json&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          JSON output format.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_is_json&#x22;" type="&#x22;(text) -> bool&#x22;">
      Check if text is valid JSON.

      <PySourceCode>
        ```python
        def _is_json(text: str) -> bool:
            """Check if text is valid JSON.

            Args:
                text: String to check.

            Returns:
                True if valid JSON, False otherwise.

            """
            try:
                json.loads(text)
                return True
            except (json.JSONDecodeError, TypeError, ValueError):
                return False
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;text&#x22;" type="&#x22;str&#x22;" value="undefined">
          String to check.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if valid JSON, False otherwise.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
