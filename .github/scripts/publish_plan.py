from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from collections import deque
from pathlib import Path


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True).strip()


def try_run(args: list[str]) -> str:
    try:
        return run(args)
    except subprocess.CalledProcessError:
        return ""


def normalize_dep(dep: str) -> str:
    dep = dep.split(";", 1)[0].strip()
    if not dep:
        return ""
    dep = dep.split("[", 1)[0]
    name = re.split(r"[<>=!~ ]", dep, 1)[0]
    return name.strip()


def load_packages(root: Path) -> tuple[dict[str, Path], dict[str, dict]]:
    package_paths: dict[str, Path] = {}
    package_meta: dict[str, dict] = {}

    root_pyproject = root / "pyproject.toml"
    root_data = tomllib.loads(root_pyproject.read_text(encoding="utf-8"))
    root_name = root_data["project"]["name"]
    package_paths[root_name] = root
    package_meta[root_name] = root_data

    packages_dir = root / "packages"
    if packages_dir.exists():
        for pkg_dir in packages_dir.iterdir():
            if not pkg_dir.is_dir():
                continue
            pyproject = pkg_dir / "pyproject.toml"
            if not pyproject.exists():
                continue
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            name = data["project"]["name"]
            package_paths[name] = pkg_dir
            package_meta[name] = data

    return package_paths, package_meta


def collect_internal_deps(package_meta: dict[str, dict], internal: set[str]) -> dict[str, list[str]]:
    def deps_for(name: str) -> list[str]:
        data = package_meta[name]
        deps = list(data.get("project", {}).get("dependencies", []) or [])
        optional = data.get("project", {}).get("optional-dependencies", {}) or {}
        for group in optional.values():
            deps.extend(group)
        internal_deps = []
        for dep in deps:
            dep_name = normalize_dep(dep)
            if dep_name in internal:
                internal_deps.append(dep_name)
        return sorted(set(internal_deps))

    return {name: deps_for(name) for name in internal}


def find_base_ref(event: str, base_ref_env: str, current_tag: str) -> str:
    if base_ref_env:
        return base_ref_env
    if event == "release" and current_tag:
        return try_run(["git", "describe", "--tags", "--abbrev=0", f"{current_tag}^"])
    return try_run(["git", "describe", "--tags", "--abbrev=0"])


def collect_changed_files(base_ref: str) -> list[str]:
    if base_ref:
        diff = try_run(["git", "diff", "--name-only", f"{base_ref}..HEAD"])
        return diff.splitlines() if diff else []
    return try_run(["git", "ls-files"]).splitlines()


def select_changed_packages(
    changed_files: list[str],
    package_paths: dict[str, Path],
    root_name: str,
    root_path: Path,
) -> set[str]:
    package_dir_to_name = {
        path.name: name for name, path in package_paths.items() if path != root_path
    }

    changed_packages: set[str] = set()
    for file in changed_files:
        if file.startswith("packages/"):
            parts = file.split("/", 2)
            if len(parts) > 1:
                name = package_dir_to_name.get(parts[1])
                if name:
                    changed_packages.add(name)
            continue
        if (
            file == "pyproject.toml"
            or file.startswith("src/phlo/")
            or file.startswith("registry/")
            or file in {"README.md", "CHANGELOG.md"}
        ):
            changed_packages.add(root_name)

    return changed_packages


def topo_sort(selected: set[str], dep_map: dict[str, list[str]]) -> list[str]:
    in_deg = {name: 0 for name in selected}
    dependents: dict[str, list[str]] = {name: [] for name in selected}
    for name in selected:
        for dep in dep_map.get(name, []):
            if dep in selected:
                in_deg[name] += 1
                dependents.setdefault(dep, []).append(name)

    queue = deque(sorted([name for name, deg in in_deg.items() if deg == 0]))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for dep in sorted(dependents.get(node, [])):
            in_deg[dep] -= 1
            if in_deg[dep] == 0:
                queue.append(dep)

    remaining = sorted([name for name in selected if name not in order])
    order.extend(remaining)
    return order


def main() -> None:
    root = Path(".")
    package_paths, package_meta = load_packages(root)
    internal = set(package_paths)

    dep_map = collect_internal_deps(package_meta, internal)

    event = os.environ.get("GITHUB_EVENT_NAME", "")
    base_ref_env = os.environ.get("BASE_REF", "").strip()
    current_tag = os.environ.get("GITHUB_REF_NAME", "") if event == "release" else ""

    base_ref = find_base_ref(event, base_ref_env, current_tag)
    changed_files = collect_changed_files(base_ref)

    root_name = next(name for name, path in package_paths.items() if path == root)

    selected = select_changed_packages(changed_files, package_paths, root_name, root)
    order = topo_sort(selected, dep_map)

    dry_run = os.environ.get("DRY_RUN", "false").strip().lower() == "true"
    outputs = {
        "packages": json.dumps(order),
        "has_packages": "true" if order else "false",
        "dry_run": "true" if dry_run else "false",
    }

    output_path = os.environ["GITHUB_OUTPUT"]
    with open(output_path, "a", encoding="utf-8") as fh:
        for key, value in outputs.items():
            fh.write(f"{key}={value}\n")

    print(f"Base ref: {base_ref or '(none)'}")
    print(f"Changed files: {len(changed_files)}")
    print(f"Packages: {order}")


if __name__ == "__main__":
    main()
