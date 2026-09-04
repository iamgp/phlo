"""Plugin install command.

Resolves a plugin name against the registry to a pinned package spec,
decides the install through the shared pure preflight (issue #857), and
only then installs with pip. The preflight verdict — candidate identity,
digest binding, core/capability compatibility, project policy, and trust
tier — is enforced before any environment mutation; rejected candidates
never reach the installer. Treated as a mutation: the whole command sits
behind require_mutation_authorization.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from phlo.cli.authorization_wrappers import require_mutation_authorization
from phlo.cli.commands.plugin.utils import collect_installed_plugins, console, run_pip
from phlo.cli.output import json_envelope
from phlo.infrastructure import load_project_config
from phlo.logging import get_logger
from phlo.plugins import preflight
from phlo.plugins.preflight import PreflightDecision
from phlo.plugins.registry_client import RegistryPlugin
from phlo.plugins.registry_client import get_plugin as get_registry_plugin

logger = get_logger(__name__)


def resolve_install_target(plugin_name: str) -> tuple[str, str]:
    """Resolve plugin name to package spec and display name."""
    if "==" in plugin_name:
        name_part, version_part = plugin_name.split("==", 1)
    else:
        name_part, version_part = plugin_name, None

    registry_plugin = get_registry_plugin(name_part)
    if registry_plugin:
        if version_part:
            package_spec = f"{registry_plugin.package}=={version_part}"
        elif registry_plugin.version:
            package_spec = f"{registry_plugin.package}=={registry_plugin.version}"
        else:
            package_spec = registry_plugin.package
        display_name = f"{registry_plugin.name} ({registry_plugin.package})"
        return package_spec, display_name

    return plugin_name, plugin_name


def _descriptor_from_registry(registry_plugin: RegistryPlugin | None) -> dict | None:
    """Build the strict descriptor input from a registry entry."""
    if registry_plugin is None:
        return None
    return {
        "type": registry_plugin.type,
        "package": registry_plugin.package,
        "version": registry_plugin.version,
        "description": registry_plugin.description,
        "author": registry_plugin.author,
        "homepage": registry_plugin.homepage,
        "tags": list(registry_plugin.tags),
    }


def _evidence_paths(extra: tuple[Path, ...]) -> list[Path]:
    """Evidence paths from --evidence plus $PHLO_CONFORMANCE_EVIDENCE."""
    configured = os.environ.get("PHLO_CONFORMANCE_EVIDENCE", "")
    paths = [Path(part) for part in configured.split(os.pathsep) if part.strip()]
    paths.extend(extra)
    return paths


@click.command(name="install")
@click.argument("plugin_name")
@click.option(
    "--artifact",
    "artifact",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    default=None,
    help="Install this exact wheel file instead of a registry spec; the "
    "preflight binds the decision to its SHA-256 digest.",
)
@click.option(
    "--descriptor",
    "descriptor_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    default=None,
    help="Static descriptor JSON for an --artifact install (defaults to "
    "the registry entry for the plugin name).",
)
@click.option(
    "--evidence",
    "evidence_paths",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    multiple=True,
    help="Conformance evidence document to trust for this install (repeatable).",
)
@click.option(
    "--allow-community",
    "allow_community",
    is_flag=True,
    default=False,
    help="Explicitly override the project's minimum-tier bar (the candidate's "
    "tier never changes; requires --override-reason).",
)
@click.option(
    "--override-reason",
    "override_reason",
    default=None,
    help="Recorded reason accompanying --allow-community.",
)
@click.option("--json", "output_json", is_flag=True, help="Emit machine-readable JSON.")
@require_mutation_authorization("plugin.install")
def install_cmd(
    plugin_name: str,
    artifact: Path | None,
    descriptor_path: Path | None,
    evidence_paths: tuple[Path, ...],
    allow_community: bool,
    override_reason: str | None,
    output_json: bool,
):
    """Install a plugin from the registry (wraps pip).

    The shared pure preflight decides before anything is installed;
    malformed, digest-mismatched, core-incompatible, capability-
    incompatible, and evidence-condemned candidates are rejected even
    with an override.
    """
    try:
        name_part = plugin_name.split("==", 1)[0]
        package_spec, display_name = resolve_install_target(plugin_name)

        if allow_community and not (override_reason and override_reason.strip()):
            raise click.UsageError("--allow-community requires --override-reason.")

        registry_plugin = get_registry_plugin(name_part)
        if descriptor_path is not None:
            descriptor_data = json.loads(descriptor_path.read_text(encoding="utf-8"))
            plugin_key = str(descriptor_data.get("package", name_part))
        else:
            descriptor_data = _descriptor_from_registry(registry_plugin)
            plugin_key = name_part

        evidence = preflight.load_conformance_evidence(_evidence_paths(evidence_paths))
        decision = preflight.evaluate_install_preflight(
            descriptor_data=descriptor_data,
            plugin_name=plugin_key,
            artifact=artifact,
            conformance_results=evidence,
            project_requirements=preflight.read_project_requirements(
                load_project_config(Path.cwd())
            ),
            override_reason=override_reason if allow_community else None,
            legacy_verified=bool(registry_plugin.verified) if registry_plugin else False,
        )
        if not decision.accepted:
            logger.info(
                "plugin_install_preflight_rejected",
                plugin_name=plugin_name,
                failures=decision.rejection_messages(),
            )
            if output_json:
                click.echo(
                    json_envelope(
                        data={
                            "plugin_name": plugin_name,
                            "preflight": _preflight_summary(decision),
                        },
                        warnings=decision.rejection_messages(),
                    )
                )
                sys.exit(1)
            console.print(f"[red]✗ Install rejected by preflight: {display_name}[/red]")
            for message in decision.rejection_messages():
                console.print(f"[red]  - {message}[/red]")
            console.print(
                "[yellow]Nothing was installed. If the candidate is a compatible "
                "community provider, retry with --allow-community --override-reason "
                "<reason> (the installed tier stays community).[/yellow]"
            )
            sys.exit(1)

        logger.info(
            "plugin_install_preflight_accepted",
            plugin_name=plugin_name,
            tier=decision.tier.value,
            override=decision.override_rule,
        )

        install_spec = str(artifact) if artifact is not None else package_spec
        logger.info(
            "plugin_install_started",
            plugin_name=plugin_name,
            package_spec=install_spec,
        )
        if not output_json:
            console.print(f"Installing {display_name}...")
        run_pip(["install", install_spec])
        installed = collect_installed_plugins("all")
        maybe_installed = [
            plugin
            for plugin in installed
            if plugin["name"] == name_part or install_spec.startswith(plugin["name"])
        ]
        logger.info(
            "plugin_install_succeeded",
            plugin_name=plugin_name,
            package_spec=install_spec,
        )
        warnings = []
        for plugin in maybe_installed:
            missing_capabilities = plugin.get("missing_capabilities") or []
            if missing_capabilities:
                warnings.append(
                    f"Installed plugin has unmet capabilities: {plugin['name']} -> "
                    f"{', '.join(missing_capabilities)}"
                )
        if decision.override_rule:
            warnings.append(
                f"Installed under explicit override ({decision.override_rule}): the "
                f"provider remains tier {decision.tier.value}; the override never "
                "changes a tier."
            )
        if output_json:
            click.echo(
                json_envelope(
                    data={
                        "plugin_name": plugin_name,
                        "package_spec": install_spec,
                        "display_name": display_name,
                        "installed_plugins": maybe_installed,
                        "preflight": _preflight_summary(decision),
                    },
                    warnings=warnings,
                )
            )
            return

        console.print(f"[green]✓ Installed {display_name}[/green]")
        for warning in warnings:
            console.print(f"[yellow]{warning}[/yellow]")
    except Exception as e:
        logger.exception("plugin_install_failed", plugin_name=plugin_name)
        console.print(f"[red]Error installing plugin: {e}[/red]")
        sys.exit(1)


def _preflight_summary(decision: PreflightDecision) -> dict:
    """Machine-readable summary of the preflight decision."""
    return {
        "accepted": decision.accepted,
        "tier": decision.tier.value,
        "required_tier": decision.required_tier.value,
        "artifact_digest": decision.artifact_digest,
        "matched_family": decision.matched_family,
        "legacy_verified": decision.legacy_verified,
        "override_rule": decision.override_rule,
        "failures": decision.rejection_messages(),
    }
