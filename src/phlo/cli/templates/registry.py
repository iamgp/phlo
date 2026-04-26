from __future__ import annotations

from phlo.cli.templates.models import ProjectTemplate


def _builtin_templates() -> tuple[ProjectTemplate, ...]:
    from phlo.cli.templates.builtin import (
        ApiIngestionTemplate,
        BasicTemplate,
        CsvBatchTemplate,
        MinimalTemplate,
    )

    return (MinimalTemplate(), BasicTemplate(), CsvBatchTemplate(), ApiIngestionTemplate())


def list_templates() -> tuple[ProjectTemplate, ...]:
    return tuple(sorted(_builtin_templates(), key=lambda template: template.metadata.name))


def get_template(name: str) -> ProjectTemplate:
    for template in list_templates():
        if template.metadata.name == name:
            return template
    raise KeyError(name)
