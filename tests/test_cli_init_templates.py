import pytest

from phlo.cli.templates.registry import get_template, list_templates


def test_registry_contains_existing_templates() -> None:
    names = [template.metadata.name for template in list_templates()]

    assert "minimal" in names
    assert "basic" in names


def test_get_template_rejects_unknown_template() -> None:
    with pytest.raises(KeyError, match="unknown-template"):
        get_template("unknown-template")
