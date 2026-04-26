from __future__ import annotations

import importlib.util

from phlo.cli.templates.models import ProjectTemplate

PACKAGE_IMPORTS = {
    "phlo": "phlo",
    "phlo-dbt": "phlo_dbt",
    "phlo-dlt": "phlo_dlt",
    "phlo-pandera": "phlo_pandera",
    "phlo-sling": "phlo_sling",
    "phlo-otel": "phlo_otel",
}


def _builtin_templates() -> tuple[ProjectTemplate, ...]:
    from phlo.cli.templates.builtin import (
        ApiIngestionTemplate,
        BasicTemplate,
        CsvBatchTemplate,
        DbtMedallionTemplate,
        MinimalTemplate,
        ObservabilityDemoTemplate,
        SlingReplicationTemplate,
    )

    return (
        MinimalTemplate(),
        BasicTemplate(),
        CsvBatchTemplate(),
        ApiIngestionTemplate(),
        DbtMedallionTemplate(),
        SlingReplicationTemplate(),
        ObservabilityDemoTemplate(),
    )


def list_templates() -> tuple[ProjectTemplate, ...]:
    return tuple(sorted(_builtin_templates(), key=lambda template: template.metadata.name))


def get_template(name: str) -> ProjectTemplate:
    for template in list_templates():
        if template.metadata.name == name:
            return template
    raise KeyError(name)


def missing_required_packages(template: ProjectTemplate) -> tuple[str, ...]:
    missing: list[str] = []
    for package in template.metadata.required_packages:
        import_name = PACKAGE_IMPORTS.get(package, package.replace("-", "_"))
        if importlib.util.find_spec(import_name) is None:
            missing.append(package)
    return tuple(missing)
