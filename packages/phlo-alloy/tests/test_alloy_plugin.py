"""Tests for Alloy service plugin."""

from importlib import resources

from phlo_alloy.plugin import AlloyServicePlugin


def test_alloy_service_definition():
    """Validate Alloy service definition defaults."""
    plugin = AlloyServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "alloy"
    assert defn["profile"] == "observability"


def test_alloy_service_builds_patched_release_image() -> None:
    """Generated Alloy uses the stable release with fixed embedded Go dependencies."""
    definition = AlloyServicePlugin().service_definition

    assert definition["image"] == "ghcr.io/phlohouse/phlo-alloy:v1.18.0-go1.26.5"
    assert definition["build"] == {"context": ".", "dockerfile": "alloy/Dockerfile"}


def test_alloy_service_uses_writable_storage_for_the_non_root_runtime() -> None:
    """Alloy must not use its default relative state directory under an unwritable cwd."""
    definition = AlloyServicePlugin().service_definition

    assert "--storage.path=/tmp/alloy" in definition["compose"]["command"]


def test_alloy_runtime_image_sets_the_upstream_non_root_user() -> None:
    """The generated Dockerfile keeps Alloy's upstream runtime identity explicit."""
    dockerfile = resources.files("phlo_alloy").joinpath("Dockerfile").read_text()

    assert dockerfile.rstrip().endswith('USER "473"')


def test_alloy_builder_discards_source_control_and_dependency_caches() -> None:
    """The generated build must not retain multi-gigabyte transient dependency trees."""
    dockerfile = resources.files("phlo_alloy").joinpath("Dockerfile").read_text()

    assert "git init /src/alloy" in dockerfile
    assert "git -C /src/alloy fetch --depth 1 origin" in dockerfile
    assert "rm -rf /src/alloy/.git" in dockerfile
    assert "rm -rf internal/web/ui/node_modules /tmp/go-cache /tmp/go-mod" in dockerfile


def test_alloy_image_pins_fixed_transitive_dependencies() -> None:
    """The published image must not retain scanner-fixable Go dependencies."""
    dockerfile = resources.files("phlo_alloy").joinpath("Dockerfile").read_text()

    assert "github.com/docker/docker@v29.3.1+incompatible" in dockerfile
    assert "github.com/go-git/go-git/v5@v5.19.2" in dockerfile
    assert "golang.org/x/text@v0.39.0" in dockerfile


def test_alloy_plugin_metadata():
    """Validate Alloy plugin metadata."""
    plugin = AlloyServicePlugin()
    meta = plugin.metadata

    assert meta.name == "alloy"
    assert "observability" in meta.tags
