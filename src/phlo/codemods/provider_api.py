"""Codemod for migrating provider-coupled APIs to provider-neutral APIs."""

from __future__ import annotations

from dataclasses import dataclass

import libcst as cst


@dataclass(frozen=True)
class ProviderApiMigration:
    """Result of migrating one Python source string."""

    code: str
    changed: bool


def migrate_provider_api_source(source: str) -> ProviderApiMigration:
    """Migrate legacy provider-coupled decorators to the provider-neutral API."""
    module = cst.parse_module(source)
    migrated = module.visit(_ProviderApiTransformer())
    code = migrated.code
    return ProviderApiMigration(code=code, changed=code != source)


class _ProviderApiTransformer(cst.CSTTransformer):
    """Rewrite legacy Phlo provider API references."""

    def __init__(self) -> None:
        self.has_import_phlo = False
        self.needs_import_phlo = False
        self.ingestion_names: set[str] = {"phlo_ingestion"}
        self.quality_names: set[str] = {"phlo_quality"}

    def visit_Import(self, node: cst.Import) -> bool:
        for alias in node.names:
            if _name_value(alias.name) == "phlo":
                self.has_import_phlo = True
        return True

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        module_name = _module_name(node.module)
        if module_name == "phlo":
            for alias in _aliases(node.names):
                if _name_value(alias.name) == "phlo":
                    self.has_import_phlo = True

        if module_name in {"phlo_dlt", "phlo_dlt.decorator"}:
            for alias in _aliases(node.names):
                if _name_value(alias.name) == "phlo_ingestion":
                    self.ingestion_names.add(_local_name(alias))
                    self.needs_import_phlo = True

        if module_name == "phlo.quality":
            for alias in _aliases(node.names):
                if _name_value(alias.name) == "phlo_quality":
                    self.quality_names.add(_local_name(alias))
                    self.needs_import_phlo = True

        return True

    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        module_name = _module_name(original_node.module)
        names = updated_node.names
        if not isinstance(names, tuple):
            return updated_node

        if module_name in {"phlo_dlt", "phlo_dlt.decorator"}:
            filtered = [alias for alias in names if _name_value(alias.name) != "phlo_ingestion"]
            return _replace_import_aliases(updated_node, filtered)

        if module_name == "phlo.quality":
            filtered = [alias for alias in names if _name_value(alias.name) != "phlo_quality"]
            return _replace_import_aliases(updated_node, filtered)

        return updated_node

    def leave_Decorator(
        self,
        original_node: cst.Decorator,
        updated_node: cst.Decorator,
    ) -> cst.Decorator:
        return updated_node.with_changes(
            decorator=self._migrate_decorator_expression(updated_node.decorator)
        )

    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        if not self.needs_import_phlo or self.has_import_phlo:
            return updated_node

        import_phlo = cst.SimpleStatementLine(
            body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("phlo"))])]
        )
        body = list(updated_node.body)
        insert_at = _import_insert_index(body)
        body.insert(insert_at, import_phlo)
        return updated_node.with_changes(body=body)

    def _migrate_decorator_expression(self, expression: cst.BaseExpression) -> cst.BaseExpression:
        if isinstance(expression, cst.Call):
            return expression.with_changes(func=self._migrate_decorator_target(expression.func))
        return self._migrate_decorator_target(expression)

    def _migrate_decorator_target(self, expression: cst.BaseExpression) -> cst.BaseExpression:
        if isinstance(expression, cst.Name):
            if expression.value in self.ingestion_names:
                self.needs_import_phlo = True
                return cst.parse_expression("phlo.ingest.dlt")
            if expression.value in self.quality_names:
                self.needs_import_phlo = True
                return cst.parse_expression("phlo.quality.pandera")

        if _matches_dotted_name(expression, ("phlo", "ingestion")):
            self.needs_import_phlo = True
            return cst.parse_expression("phlo.ingest.dlt")

        return expression


def _aliases(names: cst.ImportStar | tuple[cst.ImportAlias, ...]) -> tuple[cst.ImportAlias, ...]:
    if isinstance(names, cst.ImportStar):
        return ()
    return names


def _local_name(alias: cst.ImportAlias) -> str:
    if alias.asname is None:
        return _name_value(alias.name)
    return alias.asname.name.value


def _module_name(node: cst.BaseExpression | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        base = _module_name(node.value)
        if base is None:
            return node.attr.value
        return f"{base}.{node.attr.value}"
    return None


def _name_value(node: cst.BaseExpression) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return _module_name(node) or ""
    return ""


def _matches_dotted_name(expression: cst.BaseExpression, parts: tuple[str, ...]) -> bool:
    return _module_name(expression) == ".".join(parts)


def _replace_import_aliases(
    import_from: cst.ImportFrom,
    aliases: list[cst.ImportAlias],
) -> cst.ImportFrom | cst.RemovalSentinel:
    if not aliases:
        return cst.RemoveFromParent()
    return import_from.with_changes(names=tuple(aliases))


def _import_insert_index(body: list[cst.CSTNode]) -> int:
    index = 0
    if body and _is_module_docstring(body[0]):
        index = 1

    while index < len(body) and _is_future_import(body[index]):
        index += 1

    return index


def _is_module_docstring(node: cst.CSTNode) -> bool:
    if not isinstance(node, cst.SimpleStatementLine) or len(node.body) != 1:
        return False
    statement = node.body[0]
    return isinstance(statement, cst.Expr) and isinstance(statement.value, cst.SimpleString)


def _is_future_import(node: cst.CSTNode) -> bool:
    if not isinstance(node, cst.SimpleStatementLine) or len(node.body) != 1:
        return False
    statement = node.body[0]
    if not isinstance(statement, cst.ImportFrom):
        return False
    return _module_name(statement.module) == "__future__"
