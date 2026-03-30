# metrics (/docs/python-reference/core/phlo/cli/commands/metrics)



Core metrics CLI commands.

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;metrics_group&#x22;" type="&#x22;() -> None&#x22;">
      Pipeline and data metrics exposure.

      <PySourceCode>
        ```python
        @click.group(name="metrics")
        def metrics_group() -> None:
            """Pipeline and data metrics exposure."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;metrics_summary&#x22;" type="&#x22;(period) -> None&#x22;">
      Show key metrics overview.

      <PySourceCode>
        ```python
        @metrics_group.command(name="summary")
        @click.option("--period", type=str, default="24h", help="Time period to analyze (e.g., 24h, 7d)")
        def metrics_summary(period: str) -> None:
            """Show key metrics overview."""
            collector = get_metrics_collector()
            metrics = collector.collect_summary(_parse_period(period))
            summary_text = f"""
        [bold]Platform Metrics Summary[/bold]

        [cyan]Runs (last {period})[/cyan]
          Total:     {metrics.total_runs_24h}
          Success:   {metrics.successful_runs_24h} ({_percentage(metrics.successful_runs_24h, metrics.total_runs_24h)}%)
          Failure:   {metrics.failed_runs_24h} ({_percentage(metrics.failed_runs_24h, metrics.total_runs_24h)}%)

        [cyan]Data Volume[/cyan]
          Rows:      {_format_number(metrics.total_rows_processed_24h)}
          Bytes:     {_format_bytes(metrics.total_bytes_written_24h)}

        [cyan]Latency (seconds)[/cyan]
          p50:       {metrics.p50_duration_seconds:.2f}s
          p95:       {metrics.p95_duration_seconds:.2f}s
          p99:       {metrics.p99_duration_seconds:.2f}s

        [cyan]Assets[/cyan]
          Active:    {metrics.active_assets_count}
          Success:   {metrics.assets_by_status.get("success", 0)}
          Warning:   {metrics.assets_by_status.get("warning", 0)}
          Failure:   {metrics.assets_by_status.get("failure", 0)}
        """
            console.print(Panel(summary_text, title="Metrics Summary", expand=False))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;period&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;metrics_asset&#x22;" type="&#x22;(asset_name, runs) -> None&#x22;">
      Show per-asset metrics.

      <PySourceCode>
        ```python
        @metrics_group.command(name="asset")
        @click.argument("asset_name")
        @click.option("--runs", type=int, default=10, help="Number of past runs to display")
        def metrics_asset(asset_name: str, runs: int) -> None:
            """Show per-asset metrics."""
            collector = get_metrics_collector()
            metrics = collector.collect_asset(asset_name, runs=runs)

            table = Table(title=f"Metrics for {asset_name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_row("Last Run Status", metrics.last_run.status if metrics.last_run else "-")
            table.add_row(
                "Last Run Duration",
                (
                    f"{metrics.last_run.duration_seconds:.2f}s"
                    if metrics.last_run and metrics.last_run.duration_seconds
                    else "-"
                ),
            )
            table.add_row("Average Duration", f"{metrics.average_duration:.2f}s")
            table.add_row("Failure Rate", f"{metrics.failure_rate:.1%}")
            table.add_row("Avg Rows/Run", f"{metrics.average_rows_per_run:,.0f}")
            table.add_row("Data Size", _format_bytes(metrics.data_growth_bytes))
            console.print(table)

            if metrics.last_10_runs:
                console.print()
                run_table = Table(title=f"Last {len(metrics.last_10_runs)} Runs")
                run_table.add_column("Run ID", style="cyan")
                run_table.add_column("Status", style="magenta")
                run_table.add_column("Duration", style="yellow")
                run_table.add_column("Rows", style="green")
                for run in metrics.last_10_runs:
                    status_color = "green" if run.status == "success" else "red"
                    duration_str = f"{run.duration_seconds:.2f}s" if run.duration_seconds else "-"
                    run_table.add_row(
                        run.run_id[:8],
                        f"[{status_color}]{run.status}[/{status_color}]",
                        duration_str,
                        f"{run.rows_processed:,}",
                    )
                console.print(run_table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;runs&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;metrics_export&#x22;" type="&#x22;(export_format, output, period) -> None&#x22;">
      Export metrics to JSON, CSV, or Prometheus text.

      <PySourceCode>
        ```python
        @metrics_group.command(name="export")
        @click.option(
            "--format",
            "export_format",
            type=click.Choice(["json", "csv", "prometheus"]),
            default="json",
            help="Export format",
        )
        @click.option("--output", type=Path, required=True, help="Output file path")
        @click.option("--period", type=str, default="24h", help="Time period to analyze (e.g., 24h, 7d)")
        def metrics_export(export_format: str, output: Path, period: str) -> None:
            """Export metrics to JSON, CSV, or Prometheus text."""
            collector = get_metrics_collector()
            metrics = collector.collect_summary(_parse_period(period))
            try:
                if export_format == "json":
                    _export_json(metrics, output)
                elif export_format == "csv":
                    _export_csv(metrics, output)
                else:
                    output.write_text(render_maintenance_prometheus(), encoding="utf-8")
            except Exception:
                logger.warning(
                    "metrics_export_failed",
                    export_format=export_format,
                    output_path=str(output),
                    period=period,
                    exc_info=True,
                )
                raise
            console.print(f"[green]✓[/green] Metrics exported to {output}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;export_format&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;output&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;period&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_parse_period&#x22;" type="&#x22;(period_str) -> int&#x22;">
      <PySourceCode>
        ```python
        def _parse_period(period_str: str) -> int:
            raw_period = period_str
            period_str = period_str.strip()
            fallback_hours = 24
            if period_str.endswith("h"):
                try:
                    return int(period_str[:-1])
                except ValueError:
                    logger.debug("metrics_period_parse_invalid_hours", period=raw_period)
                    return fallback_hours
            if period_str.endswith("d"):
                try:
                    return int(period_str[:-1]) * 24
                except ValueError:
                    logger.debug("metrics_period_parse_invalid_days", period=raw_period)
                    return fallback_hours
            if period_str.endswith("w"):
                try:
                    return int(period_str[:-1]) * 24 * 7
                except ValueError:
                    logger.debug("metrics_period_parse_invalid_weeks", period=raw_period)
                    return fallback_hours
            logger.debug("metrics_period_parse_defaulted", period=raw_period)
            return fallback_hours
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;period_str&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_percentage&#x22;" type="&#x22;(part, total) -> float&#x22;">
      <PySourceCode>
        ```python
        def _percentage(part: int, total: int) -> float:
            if total == 0:
                return 0.0
            return (part / total) * 100
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;part&#x22;" type="&#x22;int&#x22;" value="null" />

        <PyParameter name="&#x22;total&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;float&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_format_number&#x22;" type="&#x22;(num) -> str&#x22;">
      <PySourceCode>
        ```python
        def _format_number(num: int) -> str:
            return f"{num:,}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;num&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_format_bytes&#x22;" type="&#x22;(bytes_val) -> str&#x22;">
      <PySourceCode>
        ```python
        def _format_bytes(bytes_val: int | float) -> str:
            val = float(bytes_val)
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if val < 1024:
                    return f"{val:.2f} {unit}"
                val /= 1024
            return f"{val:.2f} PB"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;bytes_val&#x22;" type="&#x22;int | float&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_export_json&#x22;" type="&#x22;(metrics, output) -> None&#x22;">
      <PySourceCode>
        ```python
        def _export_json(metrics: object, output: Path) -> None:
            result = _dataclass_to_dict(metrics)
            if isinstance(result, dict):
                result_dict = cast(dict[str, Any], result)
                result_dict["exported_at"] = datetime.now(UTC).isoformat()
                output.write_text(json.dumps(result_dict, indent=2, default=str), encoding="utf-8")
                return
            output.write_text(
                json.dumps(
                    {"data": result, "exported_at": datetime.now(UTC).isoformat()},
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;metrics&#x22;" type="&#x22;object&#x22;" value="null" />

        <PyParameter name="&#x22;output&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_export_csv&#x22;" type="&#x22;(metrics, output) -> None&#x22;">
      <PySourceCode>
        ```python
        def _export_csv(metrics: object, output: Path) -> None:
            import csv

            result = _dataclass_to_dict(metrics)
            if isinstance(result, dict):
                result_dict = cast(dict[str, Any], result)
                result_dict["exported_at"] = datetime.now(UTC).isoformat()
                with output.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=result_dict.keys())
                    writer.writeheader()
                    writer.writerow(result_dict)
                return

            with output.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["data", "exported_at"])
                writer.writerow([str(result), datetime.now(UTC).isoformat()])
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;metrics&#x22;" type="&#x22;object&#x22;" value="null" />

        <PyParameter name="&#x22;output&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_dataclass_to_dict&#x22;" type="&#x22;(obj) -> dict[str, Any] | object&#x22;">
      <PySourceCode>
        ```python
        def _dataclass_to_dict(obj: object) -> dict[str, Any] | object:
            import dataclasses

            if not dataclasses.is_dataclass(obj):
                return obj

            result: dict[str, Any] = {}
            for field in dataclasses.fields(obj):
                value = getattr(obj, field.name)
                if dataclasses.is_dataclass(value):
                    result[field.name] = _dataclass_to_dict(value)
                elif isinstance(value, dict):
                    result[field.name] = {k: _dataclass_to_dict(v) for k, v in value.items()}
                elif isinstance(value, list):
                    result[field.name] = [
                        _dataclass_to_dict(item) if dataclasses.is_dataclass(item) else item
                        for item in value
                    ]
                else:
                    result[field.name] = value
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;obj&#x22;" type="&#x22;object&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any] | object&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
